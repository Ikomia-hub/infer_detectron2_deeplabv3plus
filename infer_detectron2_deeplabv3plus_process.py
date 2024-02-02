from infer_detectron2_deeplabv3plus import update_path
from ikomia import core, dataprocess
import copy
from detectron2.checkpoint import DetectionCheckpointer
from detectron2.config import CfgNode, get_cfg
from detectron2.modeling import build_model
from detectron2.projects.deeplab.config import add_deeplab_config
from detectron2.projects.deeplab.resnet import build_resnet_deeplab_backbone
from torchvision.transforms import Resize
import torch
import numpy as np
import os


# --------------------
# - Class to handle the process parameters
# - Inherits PyCore.CProtocolTaskParam from Ikomia API
# --------------------
class Deeplabv3plusParam(core.CWorkflowTaskParam):

    def __init__(self):
        core.CWorkflowTaskParam.__init__(self)
        # Place default value initialization here
        self.config_file = ""
        self.model_weight_file = ""
        self.dataset = "Cityscapes"

    def set_values(self, params):
        # Set parameters values from Ikomia application
        # Parameters values are stored as string and accessible like a python dict
        self.config_file_file = params["config_file"]
        self.model_weight_file = params["model_weight_file"]
        self.dataset = params["dataset"]
        pass

    def get_values(self):
        # Send parameters values to Ikomia application
        # Create the specific dict structure (string container)
        params = {"config_file": self.config_file,
                  "model_weight_file": self.model_weight_file,
                  "dataset": self.dataset}
        return params


# --------------------
# - Class which implements the process
# - Inherits PyCore.CProtocolTask or derived from Ikomia API
# --------------------
class DeepLabv3plus(dataprocess.CSemanticSegmentationTask):

    def __init__(self, name, param):
        dataprocess.CSemanticSegmentationTask.__init__(self, name)
        self.model = None
        self.cfg = None
        self.dataset = ""
        self.update = False

        # Create parameters class
        if param is None:
            self.set_param_object(Deeplabv3plusParam())
        else:
            self.set_param_object(copy.deepcopy(param))

    def get_progress_steps(self):
        # Function returning the number of progress steps for this process
        # This is handled by the main progress bar of Ikomia application
        return 2

    def run(self):
        # Core function of your process
        # Call beginTaskRun for initialization
        self.begin_task_run()
        # Get input :
        img_input = self.get_input(0)
        src_image = img_input.get_image()

        # Get parameters :
        param = self.get_param_object()

        # Config file and model file needed are in the output folder generated by the train plugin
        if param.model_weight_file != "":
            if os.path.exists(param.model_weight_file):
                param.dataset = "Custom"
            else:
                print("Model file not found, inference will be run using Cityscapes pretrained model")

        if (self.cfg is None or param.update) and param.config_file != "":
            with open(param.config_file, 'r') as file:
                cfg_data = file.read()
                self.cfg = CfgNode.load_cfg(cfg_data)
                add_deeplab_config(self.cfg)
                self.set_names(self.cfg.CLASS_NAMES)

        if self.model is None or param.update:
            # Set cache dir in the algorithm folder to simplify deployment
            os.environ["FVCORE_CACHE"] = os.path.join(os.path.dirname(__file__), "models")

            if param.dataset == "Cityscapes":
                url = "https://dl.fbaipublicfiles.com/detectron2/DeepLab/Cityscapes-" \
                      "SemanticSegmentation/deeplab_v3_plus_R_103_os16_mg124_poly_90k_bs16/" \
                      "28054032/model_final_a8a355.pkl"
                self.cfg = get_cfg()
                cfg_file = os.path.join(os.path.dirname(__file__),
                                        os.path.join("configs", "deeplab_v3_plus_R_103_os16_mg124_poly_90k_bs16.yaml"))
                add_deeplab_config(self.cfg)
                self.cfg.merge_from_file(cfg_file)
                self.cfg.MODEL.WEIGHTS = url
                classes = ['road', 'sidewalk', 'building', 'wall', 'fence', 'pole', 'traffic light',
                           'traffic sign', 'vegetation', 'terrain', 'sky', 'person', 'rider', 'car', 'truck',
                           'bus', 'train', 'motorcycle', 'bicycle']
                self.set_names(classes)

            elif self.cfg is not None:
                self.cfg.MODEL.WEIGHTS = param.model_weight_file

            if not torch.cuda.is_available():
                self.cfg.MODEL.DEVICE = "cpu"
                self.cfg.MODEL.RESNETS.NORM = "BN"
                self.cfg.MODEL.SEM_SEG_HEAD.NORM = "BN"

            self.model = build_model(self.cfg)
            DetectionCheckpointer(self.model).load(self.cfg.MODEL.WEIGHTS)
            self.model.eval()

            os.environ.pop("FVCORE_CACHE")

        # Step progress bar:
        self.emit_step_progress()

        if self.model is not None and src_image is not None:
            # Convert numpy image to detectron2 input format
            input_tensor = {}
            h, w, c = np.shape(src_image)
            input_tensor["image"] = (torch.tensor(src_image).permute(2, 0, 1))

            if param.dataset == "Cityscapes":
                input_tensor["image"] = Resize([512, 1024])(input_tensor["image"])

            input_tensor["height"] = h
            input_tensor["width"] = w

            # Inference with pretrained model
            with torch.no_grad():
                pred = self.model([input_tensor])
                pred = pred[0]["sem_seg"].cpu().numpy()

            # Convert logits to labelled image
            dst_image = (np.argmax(pred, axis=0)).astype(dtype=np.uint8)
            # Set segmentation mask (numpy array):
            # dstImage +1 because value 0 is for background but no background here
            self.set_mask(dst_image)
            param.update = False

        # Step progress bar:
        self.emit_step_progress()
        # Call endTaskRun to finalize process
        self.end_task_run()


# --------------------
# - Factory class to build process object
# - Inherits PyDataProcess.CProcessFactory from Ikomia API
# --------------------
class Deeplabv3plusFactory(dataprocess.CTaskFactory):

    def __init__(self):
        dataprocess.CTaskFactory.__init__(self)
        # Set process information as string here
        self.info.name = "infer_detectron2_deeplabv3plus"
        self.info.short_description = "DeepLabv3+ inference model of Detectron2 for semantic segmentation."
        self.info.authors = "Liang-Chieh Chen, Yukun Zhu, George Papandreou, Florian Schroff, Hartwig Adam"
        # relative path -> as displayed in Ikomia application process tree
        self.info.path = "Plugins/Python/Segmentation"
        self.info.version = "1.1.2"
        self.info.icon_path = "icons/detectron2.png"
        self.info.article = "Encoder-Decoder with Atrous Separable Convolution for Semantic Image Segmentation"
        self.info.journal = "ECCV 2018"
        self.info.year = 2018
        self.info.license = "Apache-2.0 License"
        # URL of documentation
        self.info.documentation_link = "https://detectron2.readthedocs.io/index.html"
        # Code source repository
        self.info.repository = "https://github.com/Ikomia-hub/infer_detectron2_deeplabv3plus"
        self.info.original_repository = "https://github.com/facebookresearch/detectron2"
        # Keywords used for search
        self.info.keywords = "semantic, segmentation, detectron2, facebook, atrous, convolution, encoder, decoder"
        self.info.algo_type = core.AlgoType.INFER
        self.info.algo_tasks = "SEMANTIC_SEGMENTATION"

    def create(self, param=None):
        # Create process object
        return DeepLabv3plus(self.info.name, param)
