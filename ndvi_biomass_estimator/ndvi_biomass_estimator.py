"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing, QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer, QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber, QgsRasterLayer, QgsProcessingUtils,
    QgsProcessingProvider)
import numpy as np
from osgeo import gdal

class NDVIBiomassEstimatorAlgorithm(QgsProcessingAlgorithm):
    """
    NDVI and Biomass estimation algorithm for satellite imagery.
    """
    
    INPUT_NIR = 'INPUT_NIR'
    INPUT_RED = 'INPUT_RED'
    OUTPUT_NDVI = 'OUTPUT_NDVI'
    OUTPUT_BIOMASS = 'OUTPUT_BIOMASS'
    BIOMASS_COEFFICIENT = 'BIOMASS_COEFFICIENT'
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return NDVIBiomassEstimatorAlgorithm()
        
    def name(self):
        return 'ndvibiomassestimator'
        
    def displayName(self):
        return self.tr('NDVI & Biomass Estimator')
        
    def group(self):
        return self.tr('Vegetation Analysis')
        
    def groupId(self):
        return 'vegetationanalysis'
        
    def shortHelpString(self):
        return self.tr('Calculates NDVI and estimates biomass from satellite imagery')
        
    def initAlgorithm(self, config=None):
        # Add input parameters
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_NIR,
                self.tr('NIR Band'),
                optional=False
            )
        )
        
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_RED,
                self.tr('Red Band'),
                optional=False
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.BIOMASS_COEFFICIENT,
                self.tr('Biomass Coefficient'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.5,
                optional=False
            )
        )
        
        # Add output parameters
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_NDVI,
                self.tr('Output NDVI'),
                fileFilter='GeoTIFF files (*.tif)'
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_BIOMASS,
                self.tr('Output Biomass Estimation'),
                fileFilter='GeoTIFF files (*.tif)'
            )
        )
        
    def processAlgorithm(self, parameters, context, feedback):
        # Get parameters
        nir_layer = self.parameterAsRasterLayer(parameters, self.INPUT_NIR, context)
        red_layer = self.parameterAsRasterLayer(parameters, self.INPUT_RED, context)
        biomass_coef = self.parameterAsDouble(parameters, self.BIOMASS_COEFFICIENT, context)
        output_ndvi = self.parameterAsOutputLayer(parameters, self.OUTPUT_NDVI, context)
        output_biomass = self.parameterAsOutputLayer(parameters, self.OUTPUT_BIOMASS, context)
        
        # Read raster bands
        nir_ds = gdal.Open(nir_layer.source())
        red_ds = gdal.Open(red_layer.source())
        
        nir_array = nir_ds.GetRasterBand(1).ReadAsArray().astype(float)
        red_array = red_ds.GetRasterBand(1).ReadAsArray().astype(float)
        
        # Calculate NDVI
        ndvi = np.where(
            (nir_array + red_array) == 0,
            0,
            (nir_array - red_array) / (nir_array + red_array)
        )
        
        # Calculate Biomass (using simple linear relationship)
        biomass = ndvi * biomass_coef
        
        # Get geotransform and projection
        geotransform = nir_ds.GetGeoTransform()
        projection = nir_ds.GetProjection()
        
        # Save NDVI
        driver = gdal.GetDriverByName('GTiff')
        ndvi_ds = driver.Create(output_ndvi,
                              nir_ds.RasterXSize,
                              nir_ds.RasterYSize,
                              1,
                              gdal.GDT_Float32)
        
        ndvi_ds.SetGeoTransform(geotransform)
        ndvi_ds.SetProjection(projection)
        ndvi_ds.GetRasterBand(1).WriteArray(ndvi)
        
        # Save Biomass
        biomass_ds = driver.Create(output_biomass,
                                 nir_ds.RasterXSize,
                                 nir_ds.RasterYSize,
                                 1,
                                 gdal.GDT_Float32)
        
        biomass_ds.SetGeoTransform(geotransform)
        biomass_ds.SetProjection(projection)
        biomass_ds.GetRasterBand(1).WriteArray(biomass)
        
        # Calculate statistics
        ndvi_mean = np.nanmean(ndvi)
        biomass_mean = np.nanmean(biomass)
        
        feedback.pushInfo(f'Mean NDVI: {ndvi_mean:.4f}')
        feedback.pushInfo(f'Mean Biomass: {biomass_mean:.4f}')
        
        # Clean up
        ndvi_ds = None
        biomass_ds = None
        nir_ds = None
        red_ds = None
        
        return {
            self.OUTPUT_NDVI: output_ndvi,
            self.OUTPUT_BIOMASS: output_biomass
        }

class NDVIBiomassEstimator(QgsProcessingProvider):
    def __init__(self):
        super().__init__()

    def loadAlgorithms(self):
        self.addAlgorithm(NDVIBiomassEstimatorAlgorithm())

    def id(self):
        return 'ndvibiomassestimator'

    def name(self):
        return self.tr('NDVI Biomass Estimator')

    def icon(self):
        return QgsProcessingProvider.icon(self)

    def longName(self):
        return self.name() 