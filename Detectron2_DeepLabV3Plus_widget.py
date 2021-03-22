from ikomia import utils, core, dataprocess
import Detectron2_DeepLabV3Plus_process as processMod

#PyQt GUI framework
from PyQt5.QtWidgets import *
from ikomia.utils.pyqtutils import BrowseFileWidget


# --------------------
# - Class which implements widget associated with the process
# - Inherits PyCore.CProtocolTaskWidget from Ikomia API
# --------------------
class Detectron2_DeepLabV3PlusWidget(core.CProtocolTaskWidget):

    def __init__(self, param, parent):
        core.CProtocolTaskWidget.__init__(self, parent)

        if param is None:
            self.parameters = processMod.Detectron2_DeepLabV3PlusParam()
        else:
            self.parameters = param

        # Create layout : QGridLayout by default
        self.gridLayout = QGridLayout()

        qlabelConfigFile = QLabel("Select a config file (.yaml) :")
        self.qbrowseWidgetConfigFile = BrowseFileWidget(path=self.parameters.configFile, mode=QFileDialog.ExistingFile)

        qlabelModelFile = QLabel("Select a model file (.pth) :")
        self.qbrowseWidgetModelFile = BrowseFileWidget(path=self.parameters.modelFile, mode=QFileDialog.ExistingFile)

        self.gridLayout.addWidget(qlabelConfigFile,0,0,1,1)
        self.gridLayout.addWidget(self.qbrowseWidgetConfigFile, 0, 1, 1, 2)
        self.gridLayout.addWidget(qlabelModelFile,1,0,1,1)
        self.gridLayout.addWidget(self.qbrowseWidgetModelFile, 1, 1, 1, 2)

        # PyQt -> Qt wrapping
        layout_ptr = utils.PyQtToQt(self.gridLayout)

        # Set widget layout
        self.setLayout(layout_ptr)

    def onApply(self):
        # Apply button clicked slot

        # Get parameters from widget
        # Example : self.parameters.windowSize = self.spinWindowSize.value()
        # Send signal to launch the process
        self.parameters.configFile= self.qbrowseWidgetConfigFile.qedit_file.text()
        self.parameters.modelFile= self.qbrowseWidgetModelFile.qedit_file.text()

        self.emitApply(self.parameters)


# --------------------
# - Factory class to build process widget object
# - Inherits PyDataProcess.CWidgetFactory from Ikomia API
# --------------------
class Detectron2_DeepLabV3PlusWidgetFactory(dataprocess.CWidgetFactory):

    def __init__(self):
        dataprocess.CWidgetFactory.__init__(self)
        # Set the name of the process -> it must be the same as the one declared in the process factory class
        self.name = "Detectron2_DeepLabV3Plus"

    def create(self, param):
        # Create widget object
        return Detectron2_DeepLabV3PlusWidget(param, None)
