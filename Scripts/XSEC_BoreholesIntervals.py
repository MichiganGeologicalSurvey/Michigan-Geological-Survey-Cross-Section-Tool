# *****************************************************
# *****************************************************
# XSEC_BoreholeLithology.py
# Version: 1.0
# Date: 7/9/2024
# Last Modified Date: 7/9/2024
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
        arcpy.analysis.Buffer(intervalFeat, finalInterval, "25 Unknown", "FULL", "FLAT", "NONE", None, "PLANAR")
        arcpy.management.DeleteField(finalInterval, ["BUFF_DIST", "ORIG_FID"])
    else:
        arcpy.management.CopyFeatures(intervalFeat,finalInterval)
    arcpy.management.Delete([intervalRoutes,intervalFeat])
    return finalInterval

if __name__ == "__main__":
    lines = arcpy.GetParameterAsText(0)
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
    uf.management.AddMsgAndPrint("Preparing points and interval table...")
    try:
        updateBhPoint = os.path.join(scratchDir, "{}_BH_MGS".format(
            os.path.splitext(os.path.basename(arcpy.GetParameterAsText(2)))[0]))
        uf.management.testAndDelete(updateBhPoint)
    except:
        updateBhPoint = os.path.join(scratchDir, "{}_BH_MGS".format(arcpy.GetParameterAsText(2).replace(" ","_")))

    try:
        updateIntTable = os.path.join(scratchDir, "{}_INT_MGS".format(
            os.path.splitext(os.path.basename(arcpy.GetParameterAsText(3)))[0]))
        uf.management.testAndDelete(updateIntTable)
    except:
        updateIntTable = os.path.join(scratchDir, "{}_INT_MGS".format(arcpy.GetParameterAsText(3).replace(" ","_")))

    uf.management.AddMsgAndPrint(" - Extracting elevation measurements from DEM...")
    featExtent = os.path.join(scratchDir, "RasterArea_{}".format(os.path.splitext(os.path.basename(arcpy.GetParameterAsText(1)))[0]))
    uf.management.testAndDelete(featExtent)
    arcpy.ddd.RasterDomain(arcpy.GetParameterAsText(1), featExtent, "POLYGON")
    locationsOutside = arcpy.management.SelectLayerByLocation(
        in_layer=arcpy.GetParameterAsText(2),
        overlap_type="WITHIN",
        select_features=featExtent,
        selection_type="NEW_SELECTION",
        invert_spatial_relationship="INVERT"
    )
    if int(arcpy.management.GetCount(locationsOutside)[0]) > 10:
        arcpy.management.Delete([featExtent])
        arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=arcpy.GetParameterAsText(2),
            selection_type="CLEAR_SELECTION"
        )
        uf.management.AddMsgAndPrint("Too many locations outside the raster boundary (Limit: 10). Please review the wells and select only the records inside the defined DEM.",2)
        quit()
    else:
        arcpy.management.Delete([featExtent])
        arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=arcpy.GetParameterAsText(2),
            selection_type="CLEAR_SELECTION"
        )
    arcpy.sa.ExtractValuesToPoints(
        in_point_features=arcpy.GetParameterAsText(2),
        in_raster=arcpy.GetParameterAsText(1),
        out_point_features=updateBhPoint
    )
    arcpy.management.AddField(
        in_table=updateBhPoint,
        field_name="DEM_ELEV",
        field_type="DOUBLE",
        field_is_nullable="NULLABLE",
        field_is_required="NON_REQUIRED"
    )
    arcpy.management.CalculateField(
        in_table=updateBhPoint,
        field="DEM_ELEV",
        expression='!RASTERVALU!'
    )
    arcpy.management.DeleteField(updateBhPoint, ["RASTERVALU"])
    uf.management.AddMsgAndPrint(" - Copying intervals table...")
    arcpy.management.CopyRows(arcpy.GetParameterAsText(3), updateIntTable)

    if arcpy.GetParameterAsText(4) == "true":
        bhFields = arcpy.ValueTable(3)
        bhFields.loadFromString(arcpy.GetParameterAsText(5))
        idField = bhFields.getValue(0, 0)
        depthField = bhFields.getValue(0, 1)
        elevField = bhFields.getValue(0, 2)

        intervFields = arcpy.ValueTable(3)
        intervFields.loadFromString(arcpy.GetParameterAsText(6))
        interIdField = intervFields.getValue(0, 0)
        topDepthField = intervFields.getValue(0, 1)
        botDepthField = intervFields.getValue(0, 2)
        with arcpy.da.UpdateCursor(updateIntTable, [botDepthField, topDepthField]) as cursor:
            for row in cursor:
                if (row[0] == 0 and row[1] == 0):
                    cursor.deleteRow()
                else:
                    pass
            del row, cursor
        try:
            arcpy.management.AlterField(
                in_table=updateBhPoint,
                field=idField,
                new_field_name="WELLID"
            )
        except:
            pass
        try:
            arcpy.management.AlterField(
                in_table=updateBhPoint,
                field=depthField,
                new_field_name="WELL_DEPTH"
            )
        except:
            pass
        if elevField == "":
            newElevField = ""
        else:
            newElevField = elevField

        try:
            arcpy.management.AlterField(
                in_table=updateIntTable,
                field=interIdField,
                new_field_name="WELLID"
            )
        except:
            pass
        try:
            arcpy.management.AlterField(
                in_table=updateIntTable,
                field=topDepthField,
                new_field_name="DEPTH_TOP"
            )
            newTopDepthField = "DEPTH_TOP"
        except:
            pass
        try:
            arcpy.management.AlterField(
                in_table=updateIntTable,
                field=botDepthField,
                new_field_name="DEPTH"
            )
            newBotDepthField = "DEPTH"
        except:
            pass
    else:
        updateIntTable = arcpy.GetParameterAsText(3)
        newIdField = "WELLID"
        newElevField = "DEM_ELEV"
        newWellDepth = "WELL_DEPTH"
        newTopDepthField = "DEPTH_TOP"
        newBotDepthField = "DEPTH"

    if newTopDepthField in [f.name for f in arcpy.ListFields(updateIntTable)]:
        pass
    else:
        arcpy.management.AddField(
            in_table=updateIntTable,
            field_name="DEPTH_TOP",
            field_type="DOUBLE",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED"
        )
        arcpy.management.CalculateField(
            in_table=updateIntTable,
            field="DEPTH_TOP",
            expression='!DEPTH! - !THICKNESS!'
        )
    uf.management.AddMsgAndPrint(" - Locating wells near cross-section line(s)...")
    wellIds = []
    locations = arcpy.management.SelectLayerByLocation(
        in_layer=updateBhPoint,
        overlap_type="WITHIN_A_DISTANCE",
        select_features=lines,
        search_distance=arcpy.GetParameterAsText(8),
        selection_type="NEW_SELECTION"
    )
    with arcpy.da.SearchCursor(locations, ["WELLID"]) as cursor:
        for row in cursor:
            wellIds.append(row[0])
        del row, cursor
    arcpy.management.SelectLayerByAttribute(
        in_layer_or_view=updateBhPoint,
        selection_type="CLEAR_SELECTION"
    )
    xsecInterval = os.path.join(scratchDir, "{}_Select".format(os.path.splitext(os.path.basename(updateIntTable))[0]))
    uf.management.testAndDelete(xsecInterval)
    arcpy.management.CopyRows(updateIntTable, xsecInterval)
    with arcpy.da.UpdateCursor(xsecInterval,["WELLID"]) as cursor:
        for row in cursor:
            if row[0] not in wellIds:
                cursor.deleteRow()
        del row, cursor
    arcpy.management.SelectLayerByAttribute(updateIntTable, "CLEAR_SELECTION")
    routeWells = arcpy.management.SelectLayerByAttribute(
        in_layer_or_view=updateBhPoint,
        selection_type="ADD_TO_SELECTION",
        where_clause="WELLID IN {}".format(wellIds).replace("[", "(").replace("]", ")"),
        invert_where_clause=None)
    xsecPoints = os.path.join(scratchDir, "{}_Select".format(os.path.splitext(os.path.basename(updateBhPoint))[0]))
    uf.management.testAndDelete(xsecPoints)
    arcpy.management.CopyFeatures(routeWells, xsecPoints)
    arcpy.management.SelectLayerByAttribute(updateBhPoint, "CLEAR_SELECTION")
    uf.management.AddMsgAndPrint("-----------------------------")

    for xsec in allValues:
        uf.management.AddMsgAndPrint("PROCESSING {}...".format(xsec))
        intervalBoreholes = boreholeIntervals(
            lines=lines,
            xsec=xsec,
            dem=arcpy.GetParameterAsText(1),
            elevUnits=arcpy.GetParameterAsText(7),
            elevField=newElevField,
            wellPoints=xsecPoints,
            buff=arcpy.GetParameterAsText(8),
            ve=arcpy.GetParameterAsText(9),
            outGDB=arcpy.GetParameterAsText(11),
            stickType=arcpy.GetParameterAsText(10),
            intervalTable=xsecInterval,
            depth_top="DEPTH_TOP",
            depth_bot="DEPTH"
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
    arcpy.management.Delete([xsecInterval,xsecPoints,updateBhPoint,updateIntTable])