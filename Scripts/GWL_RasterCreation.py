# *****************************************************
# *****************************************************
# GWL_RasterCreation.py
# Version: 2.2
# Date: 7/26/2024
# Last Modified Date: 4/30/2025
# Original Author: Matthew Bell, Michigan Geological Survey, matthew.e.bell@wmich.edu
# Description: A Python custom script to generate groundwater raster surfaces based on water well points.
# *****************************************************
# *****************************************************

import os
import arcpy
import Utility_Functions as uf
import datetime
import Dictonary
import DataFormatting

# Establish the parameters...
# Establish coordinate system
wkt = 'PROJCS["NAD_1983_Hotine_Oblique_Mercator_Azimuth_Natural_Origin",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Hotine_Oblique_Mercator_Azimuth_Natural_Origin"],PARAMETER["False_Easting",2546731.496],PARAMETER["False_Northing",-4354009.816],PARAMETER["Scale_Factor",0.9996],PARAMETER["Azimuth",337.25556],PARAMETER["Longitude_Of_Center",-86.0],PARAMETER["Latitude_Of_Center",45.30916666666666],UNIT["Meter",1.0]];-28810000 -30359300 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision'
src = arcpy.SpatialReference(text=wkt)
uf.management.checkExtensions(self="")

# Environment Variables
arcpy.env.overwriteOutput = True
arcpy.env.outputCoordinateSystem = src
prj = arcpy.mp.ArcGISProject("CURRENT")
scratchDir = prj.defaultGeodatabase
arcpy.env.preserveGlobalIds = True
arcpy.env.transferGDBAttributeProperties = True
arcpy.env.transferDomains = True
uf.management.AddMsgAndPrint("Scratch Geodatabase: {}".format(os.path.basename(scratchDir)))
version = "GWL_RasterCreation.py, Version 1.2.2"
url = "https://raw.githubusercontent.com/MichiganGeologicalSurvey/Michigan-Geological-Survey-Cross-Section-Tools/refs/heads/Master/Scripts/GWL_RasterCreation.py"
uf.management.githubVersion(
    vString=version,
    rawurl=url
)

def gwlRasterCreation(wellType,wwPoints,wwPoints_aq,wwPoints_swlElev,wwPoints_constDate,dateRange,boundary,rasterGDB):
    uf.management.AddMsgAndPrint("BEGIN CREATING GROUNDWATER RASTER SURFACES FOR THE AREA...")
    uf.management.AddMsgAndPrint(" - Types of wells being analyzed: {}".format(wellType))
    pm = prj.activeMap
    if wellType == "All Wells":
        allYears = os.path.join(rasterGDB,os.path.splitext(os.path.basename(wwPoints))[0] + "_AllYears")
        uf.format.createGWLraster(
            points=wwPoints,
            outraster=allYears,
            boundary=boundary,
            map=pm,
            swl_elev=wwPoints_swlElev
        )
        for date in dateRange:
            uf.management.AddMsgAndPrint("Beginning: {}\nEnding: {}".format(date[0],date[1]))
            firstDate = datetime.datetime.strptime(date[0],"%Y-%m-%d %H:%M:%S")
            secondDate = datetime.datetime.strptime(date[1],"%Y-%m-%d %H:%M:%S")
            firstYear = int(firstDate.year)
            secondYear = int(secondDate.year)
            rasterProject = os.path.join(rasterGDB,os.path.splitext(os.path.basename(wwPoints))[0] + "_{}_{}".format(firstYear,secondYear))
            selectWells = arcpy.management.SelectLayerByAttribute(
                in_layer_or_view=wwPoints,
                selection_type="NEW_SELECTION",
                where_clause="{0} >= timestamp '{1}' And {0} <= timestamp '{2}'".format(wwPoints_constDate,date[0],date[1]),
                invert_where_clause=None
            )
            uf.format.createGWLraster(
                points=selectWells,
                outraster=rasterProject,
                boundary=boundary,
                map=pm,
                swl_elev=wwPoints_swlElev
            )
    elif wellType == "Bedrock Wells":
        allYears = os.path.join(rasterGDB, os.path.splitext(os.path.basename(wwPoints))[0] + "_AllYears_BDRK")
        selectWells_BDRK = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=wwPoints,
            selection_type="NEW_SELECTION",
            where_clause="{} = 'ROCK'",
            invert_where_clause=None
        )
        uf.format.createGWLraster(
            points=selectWells_BDRK,
            outraster=allYears,
            boundary=boundary,
            map=pm,
            swl_elev=wwPoints_swlElev
        )
        for date in dateRange:
            uf.management.AddMsgAndPrint("Beginning: {}\nEnding: {}".format(date[0], date[1]))
            firstDate = datetime.datetime.strptime(date[0], "%Y-%m-%d %H:%M:%S")
            secondDate = datetime.datetime.strptime(date[1], "%Y-%m-%d %H:%M:%S")
            firstYear = int(firstDate.year)
            secondYear = int(secondDate.year)
            rasterProject = os.path.join(rasterGDB,
                                         os.path.splitext(os.path.basename(wwPoints))[0] + "_{}_{}_BDRK".format(firstYear,
                                                                                                           secondYear))
            selectWells = arcpy.management.SelectLayerByAttribute(
                in_layer_or_view=wwPoints,
                selection_type="NEW_SELECTION",
                where_clause="{0} = 'ROCK' And {1} >= timestamp '{2}' And {1} <= timestamp '{3}'".format(wwPoints_aq,wwPoints_constDate, date[0],
                                                                                        date[1]),
                invert_where_clause=None
            )
            uf.format.createGWLraster(
                points=selectWells,
                outraster=rasterProject,
                boundary=boundary,
                map=pm,
                swl_elev=wwPoints_swlElev
            )
    elif wellType == "Glacial Wells":
        allYears = os.path.join(rasterGDB, os.path.splitext(os.path.basename(wwPoints))[0] + "_AllYears_DRFT")
        selectWells_DRFT = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=wwPoints,
            selection_type="NEW_SELECTION",
            where_clause="{} = 'DRIFT'",
            invert_where_clause=None
        )
        uf.format.createGWLraster(
            points=selectWells_DRFT,
            outraster=allYears,
            boundary=boundary,
            map=pm,
            swl_elev=wwPoints_swlElev
        )
        for date in dateRange:
            uf.management.AddMsgAndPrint("Beginning: {}\nEnding: {}".format(date[0], date[1]))
            firstDate = datetime.datetime.strptime(date[0], "%Y-%m-%d %H:%M:%S")
            secondDate = datetime.datetime.strptime(date[1], "%Y-%m-%d %H:%M:%S")
            firstYear = int(firstDate.year)
            secondYear = int(secondDate.year)
            rasterProject = os.path.join(rasterGDB,
                                         os.path.splitext(os.path.basename(wwPoints))[0] + "_{}_{}_DRFT".format(
                                             firstYear,
                                             secondYear))
            selectWells = arcpy.management.SelectLayerByAttribute(
                in_layer_or_view=wwPoints,
                selection_type="NEW_SELECTION",
                where_clause="{0} = 'DRIFT' And {1} >= timestamp '{2}' And {1} <= timestamp '{3}'".format(wwPoints_aq,
                                                                                                         wwPoints_constDate,
                                                                                                         date[0],
                                                                                                         date[1]),
                invert_where_clause=None
            )
            uf.format.createGWLraster(
                points=selectWells,
                outraster=rasterProject,
                boundary=boundary,
                map=pm,
                swl_elev=wwPoints_swlElev
            )
if __name__ == "__main__":
    wwPoints = arcpy.GetParameterAsText(0)
    wwFields = arcpy.ValueTable(3)
    wwFields.loadFromString(arcpy.GetParameterAsText(1))
    featExtent = arcpy.GetParameterAsText(2)
    wellType = arcpy.GetParameterAsText(3)
    dateRanges = arcpy.ValueTable(2)
    dateRanges.loadFromString(arcpy.GetParameterAsText(4))

    dateInterval = []
    for i in range(0,dateRanges.rowCount):
        startYear = int(dateRanges.getValue(i,0))
        endYear = int(dateRanges.getValue(i,1))
        genDate = datetime.datetime(year=1900,month=1,day=1)
        date1 = genDate.replace(year=startYear).strftime('%Y-%m-%d %H:%M:%S')
        date2 = genDate.replace(year=endYear,month=12,day=31).strftime('%Y-%m-%d %H:%M:%S')
        dateInterval.append([date1,date2])
    gwlRasterCreation(
        wellType=wellType,
        wwPoints=wwPoints,
        wwPoints_aq=wwFields.getValue(0,1),
        wwPoints_swlElev=wwFields.getValue(0,0),
        wwPoints_constDate=wwFields.getValue(0,2),
        dateRange=dateInterval,
        boundary=featExtent,
        rasterGDB=arcpy.GetParameterAsText(5)
    )
