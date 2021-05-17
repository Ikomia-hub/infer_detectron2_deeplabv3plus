import update_path
from ikomia import core, dataprocess
import copy

# Your imports below

from detectron2.checkpoint import DetectionCheckpointer
from detectron2.config import CfgNode,get_cfg
from detectron2.modeling import build_model
from detectron2.projects.deeplab.config import add_deeplab_config
from torchvision.transforms import Resize
import torch
import numpy as np
import random
import os
import cv2

# --------------------
# - Class to handle the process parameters
# - Inherits PyCore.CProtocolTaskParam from Ikomia API
# --------------------
class Detectron2_DeepLabV3PlusParam(core.CProtocolTaskParam):

    def __init__(self):
        core.CProtocolTaskParam.__init__(self)
        # Place default value initialization here
        self.configFile=""
        self.modelFile=""
        self.dataset="Cityscapes"

    def setParamMap(self, paramMap):
        # Set parameters values from Ikomia application
        # Parameters values are stored as string and accessible like a python dict
        self.configFile = paramMap["configFile"]
        self.modelFile = paramMap["modelFile"]
        self.dataset = paramMap["dataset"]
        pass

    def getParamMap(self):
        # Send parameters values to Ikomia application
        # Create the specific dict structure (string container)
        paramMap = core.ParamMap()
        paramMap["configFile"] = self.configFile
        paramMap["modelFile"] = self.modelFile
        paramMap["dataset"] = self.dataset
        return paramMap


# --------------------
# - Class which implements the process
# - Inherits PyCore.CProtocolTask or derived from Ikomia API
# --------------------
class Detectron2_DeepLabV3PlusProcess(dataprocess.CImageProcess2d):

    def __init__(self, name, param):
        dataprocess.CImageProcess2d.__init__(self, name)

        # add output + set data type
        self.setOutputDataType(core.IODataType.IMAGE_LABEL, 0)
        self.addOutput(dataprocess.CImageProcessIO(core.IODataType.IMAGE))
        self.addOutput(dataprocess.CImageProcessIO(core.IODataType.IMAGE))
        self.model = None
        self.cfg = None
        self.colors = None
        self.dataset = ""
        self.update = False
        self.classes = None
        # Create parameters class
        if param is None:
            self.setParam(Detectron2_DeepLabV3PlusParam())
        else:
            self.setParam(copy.deepcopy(param))

    def getProgressSteps(self, eltCount=1):
        # Function returning the number of progress steps for this process
        # This is handled by the main progress bar of Ikomia application
        return 1

    def run(self):
        # Core function of your process
        # Call beginTaskRun for initialization
        self.beginTaskRun()
        # we use seed to keep the same color for our masks + boxes + labels (same random each time)
        random.seed(10)
        # Get input :
        input = self.getInput(0)
        srcImage = input.getImage()

        # Get output :
        mask_output = self.getOutput(0)
        graph_output = self.getOutput(2)

        # Get parameters :
        param = self.getParam()

        # Config file and model file needed are in the output folder generated by the train plugin
        if (self.cfg is None or param.update) and param.configFile!="":
            with open(param.configFile, 'r') as file:
                cfg_data = file.read()
                self.cfg = CfgNode.load_cfg(cfg_data)
                self.classes=self.cfg.CLASS_NAMES

        if self.model is None or param.update:
            if param.dataset == "Cityscapes":
                url = "https://dl.fbaipublicfiles.com/detectron2/DeepLab/Cityscapes-" \
                      "SemanticSegmentation/deeplab_v3_plus_R_103_os16_mg124_poly_90k_bs16/" \
                      "28054032/model_final_a8a355.pkl"
                self.cfg = get_cfg()
                cfg_file = os.path.join(os.path.dirname(__file__),os.path.join("configs","deeplab_v3_plus_R_103_os16_mg124_poly_90k_bs16.yaml"))
                add_deeplab_config(self.cfg)
                self.cfg.merge_from_file(cfg_file)
                self.cfg.MODEL.WEIGHTS = url

                self.classes =['ignore','road','sidewalk','building','wall','fence','pole','traffic light','traffic sign'
                                ,'vegetation','terrain','sky','person','rider','car','truck','bus' ,
                                'train','motorcycle','bicycle']

            elif self.cfg is not None:
                self.cfg.MODEL.WEIGHTS = param.modelFile

            if not torch.cuda.is_available():
                self.cfg.MODEL.DEVICE = "cpu"
                self.cfg.MODEL.RESNETS.NORM = "BN"
                self.cfg.MODEL.SEM_SEG_HEAD.NORM = "BN"

            self.model=build_model(self.cfg)
            DetectionCheckpointer(self.model).load(self.cfg.MODEL.WEIGHTS)
            self.model.eval()

        if self.model is not None and srcImage is not None :
            # Convert numpy image to detectron2 input format
            input={}
            h,w,c = np.shape(srcImage)
            input["image"] = (torch.tensor(srcImage).permute(2, 0, 1))

            if param.dataset == "Cityscapes":
                input["image"]=Resize([512,1024])(input["image"])

            input["height"]= h
            input["width"]= w

            # Inference with pretrained model
            with torch.no_grad():
                pred = self.model([input])
                pred = pred[0]["sem_seg"].cpu().numpy()

            # Convert logits to labelled image
            dstImage = (np.argmax(pred,axis=0)).astype(dtype=np.uint8)
            # Set image of input/output (numpy array):
            # dstImage +1 because value 0 is for background but no background here
            mask_output.setImage(dstImage+1)

            # Create random color map
            if self.colors == None or param.update :
                n = len(self.classes)
                self.colors = [[0, 0, 0]]
                for i in range(n-1):
                    self.colors.append([random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255])

                # Apply color map on labelled image
                self.setOutputColorMap(1, 0, self.colors)
            self.forwardInputImage(0, 1)

            graph_output.setImage(self.draw_legend())
            param.update = False

        # Step progress bar:
        self.emitStepProgress()

        # Call endTaskRun to finalize process
        self.endTaskRun()

    def draw_legend(self):
        img_h = 1000
        img_w = 1000
        max_height = 100
        rectangle_height = min(max_height,img_h // len(self.colors))
        rectangle_width = img_w // 3
        offset_x = 10
        offset_y = 5
        interline = 5
        legend = np.full((img_h, img_w, 3), dtype=np.int, fill_value=255)
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontscale = 1
        thickness = 2
        for i, c in enumerate(self.colors):
            legend = cv2.rectangle(legend, (offset_x, i * rectangle_height + offset_y + interline),
                                   (offset_x + rectangle_width, (i + 1) * rectangle_height + offset_y - interline),
                                   color=c, thickness=-1)
            legend = cv2.putText(legend,self.classes[i],(3*offset_x+rectangle_width,(i+1)*rectangle_height+
                                                           offset_y-interline - rectangle_height//3),
                                  font, fontscale, color=[0,0,0], thickness=thickness)
        return legend

# --------------------
# - Factory class to build process object
# - Inherits PyDataProcess.CProcessFactory from Ikomia API
# --------------------
class Detectron2_DeepLabV3PlusProcessFactory(dataprocess.CProcessFactory):

    def __init__(self):
        dataprocess.CProcessFactory.__init__(self)
        # Set process information as string here
        self.info.name = "Detectron2_DeepLabV3Plus"
        self.info.shortDescription = "DeepLabv3+ inference model of Detectron2 for semantic segmentation."
        self.info.description = "Implementation from Detectron2 (Facebook Research). " \
                                "This Ikomia plugin can make inference of pre-trained model from " \
                                "a given config file and a weight file produced by the Ikomia " \
                                "plugin Detectron2_DeepLabV3Plus_Train."
        self.info.authors = "Liang-Chieh Chen, Yukun Zhu, George Papandreou, Florian Schroff, Hartwig Adam"
        # relative path -> as displayed in Ikomia application process tree
        self.info.path = "Plugins/Python"
        self.info.version = "1.0.0"
        # self.info.iconPath = "your path to a specific icon"
        self.info.article = "Encoder-Decoder with Atrous Separable Convolution for Semantic Image Segmentation"
        self.info.journal = "ECCV 2018"
        self.info.year = 2018
        self.info.license = "Apache-2.0 License"
        # URL of documentation
        self.info.documentationLink = "https://detectron2.readthedocs.io/index.html"
        # Code source repository
        self.info.repository = "https://github.com/facebookresearch/detectron2"
        # Keywords used for search
        self.info.keywords = "semantic, segmentation, detectron2, facebook, atrous, convolution, encoder, decoder"

    def create(self, param=None):
        # Create process object
        return Detectron2_DeepLabV3PlusProcess(self.info.name, param)
