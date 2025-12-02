# *****************************************************
# *****************************************************
# XSEC_BoreholeIntervals.py
# Version: 1.0
# Date: 7/9/2024
# Last Modified Date: 12/2/2025
# Original Author: Matthew Bell, Michigan Geological Survey, matthew.e.bell@wmich.edu
# Description: Command python code to create and place borehole sticks with segmented borehole lithologies onto a cross-sectional view.
# *****************************************************
# *****************************************************

import arcpy
import os
import Utility_Functions as uf
import XSEC_Boreholes

wkt = 'PROJCS["Cross-Section Coordinate System",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Local"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Scale_Factor",1.0],PARAMETER["Azimuth",45.0],PARAMETER["Longitude_Of_Center",-75.0],PARAMETER["Latitude_Of_Center",40.0],UNIT["Meter",1.0]];-6386900 -6357100 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision'
unknown = arcpy.SpatialReference(text=wkt)
uf.management.checkExtensions(self="")

# Environment Variables
arcpy.env.overwriteOutput = True
prj = arcpy.mp.ArcGISProject("CURRENT")
scratchDir = prj.defaultGeodatabase
arcpy.env.preserveGlobalIds = True
arcpy.env.transferGDBAttributeProperties = True
arcpy.env.transferDomains = True
uf.management.AddMsgAndPrint("Scratch Geodatabase: {}".format(os.path.basename(scratchDir)))
version = "XSEC_BoreholesIntervals.py, Version 1.2.6"
url = "https://raw.githubusercontent.com/MichiganGeologicalSurvey/Michigan-Geological-Survey-Cross-Section-Tool/refs/heads/Master/Scripts/XSEC_BoreholesIntervals.py"
uf.management.githubVersion(
    vString=version,
    rawurl=url
)
uf.management.AddMsgAndPrint("-----------------------------")

def boreholeIntervals(lines,xsec,dem,elevUnits,elevField,wellPoints,buff,ve,outGDB,stickType,intervalTable,depth_top,depth_bot):
    bhSticks,bhLines = XSEC_Boreholes.boreholeSticks(
        lineFeature=lines,
        xsec=xsec,
        surfDEM=dem,
        elev_units=elevUnits,
        elev_field=elevField,
        well_points=wellPoints,
        buff=buff,
        ve=ve,
        outGDB=outGDB,
        stickType=stickType
    )
    intervalRoutes = os.path.join(scratchDir,"XSEC_{}_bhRoutes_{}".format(xsec,os.path.splitext(os.path.basename(intervalTable))[0]))
    uf.management.testAndDelete(intervalRoutes)
    arcpy.lr.CreateRoutes(bhLines,"WELLID",intervalRoutes,"ONE_FIELD","WELL_DEPTH","#","UPPER_LEFT")
    Lprop = "WELLID LINE {} {}".format(depth_top,depth_bot)
    arcpy.lr.MakeRouteEventLayer(
        in_routes=intervalRoutes,
        route_id_field="WELLID",
        in_table=intervalTable,
        in_event_properties=Lprop,
        out_layer="lyr2",
        add_error_field="ERROR_FIELD"
    )
    intervalFeat = os.path.join(scratchDir,"XSEC_{}_intervals_{}".format(xsec,os.path.splitext(os.path.basename(intervalTable))[0]))
    uf.management.testAndDelete(intervalFeat)
    arcpy.conversion.ExportFeatures(
        in_features="lyr2",
        out_features=intervalFeat
    )
    with arcpy.da.UpdateCursor(intervalFeat,["LOC_ERROR"]) as cursor:
        for row in cursor:
            if row[0] == "ROUTE NOT FOUND":
                cursor.deleteRow()
        del row,cursor
    arcpy.management.AddField(intervalFeat, "Dist2Xsec", "FLOAT")
    arcpy.management.AddField(intervalFeat, "PERCENT_DIST", "FLOAT")
    arcpy.env.qualifiedFieldNames = False
    arcpy.management.JoinField(intervalFeat, "WELLID", os.path.join(scratchDir,"XSEC_{}_wellsLocated".format(xsec)), "WELLID", "Distance")
    arcpy.management.CalculateField(intervalFeat, "Dist2Xsec", "abs(!Distance!)", "PYTHON3")
    arcpy.management.CalculateField(intervalFeat, "PERCENT_DIST",
                                    "(!Dist2Xsec!/{}) * 100".format(buff.split(" ")[0]), "PYTHON3")
    arcpy.management.DeleteField(intervalFeat, "Distance")
    nameID_Labels = 1
    while True:
        labelName = "XSEC_{}_{}_{}x_v{}".format(
            xsec.replace("-", "_").replace(" ", "_"),
            os.path.splitext(os.path.basename(intervalTable))[0],
            ve,
            nameID_Labels
        )
        finalInterval = os.path.join(outGDB, "XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")), labelName)
        if arcpy.Exists(finalInterval):
            nameID_Labels = nameID_Labels + 1
        else:
            break
    if stickType == "Polygon":
        arcpy.analysis.Buffer(intervalFeat, finalInterval, "10 Unknown", "FULL", "FLAT", "NONE", None, "PLANAR")
        arcpy.management.DeleteField(finalInterval, ["BUFF_DIST", "ORIG_FID"])
    else:
        arcpy.management.CopyFeatures(intervalFeat,finalInterval)
    arcpy.management.Delete([intervalRoutes,intervalFeat])
    return finalInterval

if __name__ == "__main__":
    uf.management.AddMsgAndPrint(" -- Pre-Cross-Section Checks -- ")
    lines = arcpy.GetParameterAsText(0)
    surfRaster = uf.xsec.rasterProject_GeoProj(
        surfRaster=arcpy.GetParameterAsText(1),
        lines=lines,
        scratchDir=scratchDir
    )
    allValues = uf.management.unique_values(table=lines, field="XSEC")
    # Create the cross-section maps if they do not exist already
    mapList = []
    for Value in allValues:
        mapName = "XSEC_" + Value.replace("-", "_").replace(" ", "_")
        mapList.append(mapName)
    oldMaps = []
    for map in prj.listMaps():
        oldMaps.append(map.name)
    for m in mapList:
        if m in oldMaps:
            pass
        else:
            prj.createMap(m)
    for map in prj.listMaps("XSEC_*"):
        uf.management.removeBasemaps(map)
    for xsec in allValues:
        FDSname = "XSEC_" + xsec.replace("-", "_").replace(" ", "_")
        outFDS = os.path.join(arcpy.GetParameterAsText(11),FDSname)
        if not arcpy.Exists(outFDS):
            arcpy.management.CreateFeatureDataset(arcpy.GetParameterAsText(11),FDSname,unknown)
    uf.management.AddMsgAndPrint("-----------------------------")
    uf.management.AddMsgAndPrint("BEGIN CREATING BOREHOLE LITHOLOGY STICKS...")

    updateBhPoint, updateIntTable, newIdField, newElevField, newWellDepth, newTopDepthField, newBotDepthField = uf.xsec.pointsNearLine(
        custom=arcpy.GetParameterAsText(4),
        points=arcpy.GetParameterAsText(2),
        raster=surfRaster,
        int_table=arcpy.GetParameterAsText(3),
        xsecline=lines,
        searchDist=arcpy.GetParameterAsText(8),
        parm_bhFields=arcpy.GetParameterAsText(5),
        parm_intFields=arcpy.GetParameterAsText(6),
        scratchDir=scratchDir
    )

    for xsec in allValues:
        uf.management.AddMsgAndPrint("PROCESSING {}...".format(xsec))
        intervalBoreholes = boreholeIntervals(
            lines=lines,
            xsec=xsec,
            dem=surfRaster,
            elevUnits=arcpy.GetParameterAsText(7),
            elevField=newElevField,
            wellPoints=updateBhPoint,
            buff=arcpy.GetParameterAsText(8),
            ve=arcpy.GetParameterAsText(9),
            outGDB=arcpy.GetParameterAsText(11),
            stickType=arcpy.GetParameterAsText(10),
            intervalTable=updateIntTable,
            depth_top=newTopDepthField,
            depth_bot=newBotDepthField
        )
        # Now, to clean up the database for the next cross-section or other steps...
        uf.management.AddMsgAndPrint("Cleaning default geodatabse...")
        arcpy.management.Delete(
            [os.path.join(scratchDir, "XSEC_{}_zm_{}".format(xsec,os.path.splitext(os.path.basename(lines))[0])),
             os.path.join(scratchDir, "XSEC_{}_z".format(xsec)),
             os.path.join(scratchDir,
                          "XSEC_{}_wellsLocated".format(xsec)),
             os.path.join(scratchDir, "XSEC_{}_bhLines".format(xsec)),
             os.path.join(scratchDir, "XSEC_{}_zWells".format(xsec))])
        arcpy.management.DeleteField(lines,
                                     ["ROUTEID", "{}_{}_ID".format(os.path.splitext(os.path.basename(lines))[0], xsec)])
        xsecMap = prj.listMaps("XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")))[0]
        xsecMap.addDataFromPath(intervalBoreholes)
        uf.management.AddMsgAndPrint("-----------------------------")
    arcpy.management.Delete([updateBhPoint,updateIntTable])