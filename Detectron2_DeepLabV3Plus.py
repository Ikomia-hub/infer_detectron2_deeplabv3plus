from ikomia import dataprocess


# --------------------
# - Interface class to integrate the process with Ikomia application
# - Inherits PyDataProcess.CPluginProcessInterface from Ikomia API
# --------------------
class Detectron2_DeepLabV3Plus(dataprocess.CPluginProcessInterface):

    def __init__(self):
        dataprocess.CPluginProcessInterface.__init__(self)

    def getProcessFactory(self):
        from Detectron2_DeepLabV3Plus.Detectron2_DeepLabV3Plus_process import Detectron2_DeepLabV3PlusProcessFactory
        # Instantiate process object
        return Detectron2_DeepLabV3PlusProcessFactory()

    def getWidgetFactory(self):
        from Detectron2_DeepLabV3Plus.Detectron2_DeepLabV3Plus_widget import Detectron2_DeepLabV3PlusWidgetFactory
        # Instantiate associated widget object
        return Detectron2_DeepLabV3PlusWidgetFactory()
