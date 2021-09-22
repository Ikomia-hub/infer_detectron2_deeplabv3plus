from ikomia import dataprocess


# --------------------
# - Interface class to integrate the process with Ikomia application
# - Inherits PyDataProcess.CPluginProcessInterface from Ikomia API
# --------------------
class IkomiaPlugin(dataprocess.CPluginProcessInterface):

    def __init__(self):
        dataprocess.CPluginProcessInterface.__init__(self)

    def getProcessFactory(self):
        from infer_detectron2_deeplabv3plus.infer_detectron2_deeplabv3plus_process import Deeplabv3plusFactory
        # Instantiate process object
        return Deeplabv3plusFactory()

    def getWidgetFactory(self):
        from infer_detectron2_deeplabv3plus.infer_detectron2_deeplabv3plus_widget import Deeplabv3plusWidgetFactory
        # Instantiate associated widget object
        return Deeplabv3plusWidgetFactory()
