from qgis.core import QgsApplication
from .ndvi_biomass_estimator import NDVIBiomassEstimator

def classFactory(iface):
    return NDVIBiomassEstimatorPlugin(iface)

class NDVIBiomassEstimatorPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initGui(self):
        self.provider = NDVIBiomassEstimator()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider) 