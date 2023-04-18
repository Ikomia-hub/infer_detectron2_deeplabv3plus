from ikomia import core, dataprocess
from infer_detectron2_deeplabv3plus.infer_detectron2_deeplabv3plus_process import Deeplabv3plusParam
# PyQt GUI framework
from PyQt5.QtWidgets import *
from ikomia.utils import qtconversion
from ikomia.utils.pyqtutils import BrowseFileWidget


# --------------------
# - Class which implements widget associated with the process
# - Inherits PyCore.CProtocolTaskWidget from Ikomia API
# --------------------
class Deeplabv3plusWidget(core.CWorkflowTaskWidget):

    def __init__(self, param, parent):
        core.CWorkflowTaskWidget.__init__(self, parent)

        if param is None:
            self.parameters = Deeplabv3plusParam()
        else:
            self.parameters = param

        # Create layout : QGridLayout by default
        self.grid_layout = QGridLayout()

        self.qcomboLabel = QLabel("Trained on")
        self.combo_dataset = QComboBox()
        self.combo_dataset.addItem("Custom")
        self.combo_dataset.addItem("Cityscapes")
        self.combo_dataset.setCurrentIndex(0 if self.parameters.dataset == "Custom" else 1)
        self.combo_dataset.currentIndexChanged.connect(self.on_combo_dataset_changed)

        self.qlabelConfigFile = QLabel("Select a config file (.yaml) :")
        self.qbrowseWidgetConfigFile = BrowseFileWidget(path=self.parameters.config, mode=QFileDialog.ExistingFile)

        self.qlabelModelFile = QLabel("Select a model file (.pth) :")
        self.qbrowseWidgetModelFile = BrowseFileWidget(path=self.parameters.model_path, mode=QFileDialog.ExistingFile)

        self.grid_layout.addWidget(self.qcomboLabel, 0, 0, 1, 1)
        self.grid_layout.addWidget(self.combo_dataset, 0, 1, 1, 2)
        self.grid_layout.addWidget(self.qlabelConfigFile, 1, 0, 1, 1)
        self.grid_layout.addWidget(self.qbrowseWidgetConfigFile, 1, 1, 1, 2)
        self.grid_layout.addWidget(self.qlabelModelFile, 2, 0, 1, 1)
        self.grid_layout.addWidget(self.qbrowseWidgetModelFile, 2, 1, 1, 2)

        # PyQt -> Qt wrapping
        layout_ptr = qtconversion.PyQtToQt(self.grid_layout)

        # Set widget layout
        self.set_layout(layout_ptr)
        if self.parameters.dataset != "Custom":
            self.qlabelModelFile.setEnabled(False)
            self.qlabelConfigFile.setEnabled(False)
            self.qbrowseWidgetConfigFile.setEnabled(False)
            self.qbrowseWidgetModelFile.setEnabled(False)

    def on_combo_dataset_changed(self, index):
        if self.combo_dataset.itemText(index) != "Custom":
            self.qlabelModelFile.setEnabled(False)
            self.qlabelConfigFile.setEnabled(False)
            self.qbrowseWidgetConfigFile.setEnabled(False)
            self.qbrowseWidgetModelFile.setEnabled(False)
        else:
            self.qlabelModelFile.setEnabled(True)
            self.qlabelConfigFile.setEnabled(True)
            self.qbrowseWidgetConfigFile.setEnabled(True)
            self.qbrowseWidgetModelFile.setEnabled(True)

    def on_apply(self):
        # Apply button clicked slot
        # Get parameters from widget
        # Send signal to launch the process
        self.parameters.config = self.qbrowseWidgetConfigFile.qedit_file.text()
        self.parameters.model_path = self.qbrowseWidgetModelFile.qedit_file.text()
        self.parameters.dataset = self.combo_dataset.currentText()
        self.parameters.update = True
        self.emit_apply(self.parameters)


# --------------------
# - Factory class to build process widget object
# - Inherits PyDataProcess.CWidgetFactory from Ikomia API
# --------------------
class Deeplabv3plusWidgetFactory(dataprocess.CWidgetFactory):

    def __init__(self):
        dataprocess.CWidgetFactory.__init__(self)
        # Set the name of the process -> it must be the same as the one declared in the process factory class
        self.name = "infer_detectron2_deeplabv3plus"

    def create(self, param):
        # Create widget object
        return Deeplabv3plusWidget(param, None)
