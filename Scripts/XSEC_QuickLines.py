# *****************************************************
# *****************************************************
# XSEC_QuickLines.py
# Version: 1.2
# Date: 8/6/2024
# Last Modified Date: 4/30/2025
# Original Author: Matthew Bell, Michigan Geological Survey, matthew.e.bell@wmich.edu
# Description: Command python code to create quick cross-sectional views of the essential products, such as borehole
# data, surface profiles, and grid lines.
# *****************************************************
# *****************************************************

import arcpy
import os
import numpy as np
import threading
import Utility_Functions as uf
import XSEC_BoreholesIntervals
import XSEC_Profiles
import XSEC_SegmentProfiles
import XSEC_GridLines

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
version = "XSEC_QuickLines.py, Version 1.2.2"
url = "https://raw.githubusercontent.com/MichiganGeologicalSurvey/Michigan-Geological-Survey-Cross-Section-Tools/refs/heads/Master/Scripts/XSEC_QuickLines.py"
uf.management.githubVersion(
    vString=version,
    rawurl=url
)
uf.management.AddMsgAndPrint("-----------------------------")

if __name__ == "__main__":
    lines1 = arcpy.GetParameterAsText(0)
    allValues = uf.management.unique_values(table=lines1, field="XSEC")
    demSR = arcpy.Describe(arcpy.GetParameterAsText(1)).spatialReference
    linesSR = arcpy.Describe(arcpy.GetParameterAsText(0)).spatialReference
    if demSR.name == linesSR.name:
        lines = lines1
    else:
        newLines = os.path.join(scratchDir,"XSEC_Lines_Projection")
        arcpy.management.Project(lines1,newLines,demSR)
        lines = newLines
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
        outFDS = os.path.join(arcpy.GetParameterAsText(16),FDSname)
        if not arcpy.Exists(outFDS):
            arcpy.management.CreateFeatureDataset(arcpy.GetParameterAsText(16),FDSname,unknown)
    uf.management.AddMsgAndPrint("-----------------------------")
    uf.management.AddMsgAndPrint("BEGIN CREATING BOREHOLE LITHOLOGY STICKS...")
    uf.management.AddMsgAndPrint("* Preparing points and interval table...")
    try:
        updateBhPoint = os.path.join(scratchDir, "{}_BH_MGS".format(
            os.path.splitext(os.path.basename(arcpy.GetParameterAsText(2)))[0]))
        uf.management.testAndDelete(updateBhPoint)
    except:
        updateBhPoint = os.path.join(scratchDir, "{}_BH_MGS".format(arcpy.GetParameterAsText(2).replace(" ", "_")))

    try:
        updateIntTable = os.path.join(scratchDir, "{}_INT_MGS".format(
            os.path.splitext(os.path.basename(arcpy.GetParameterAsText(3)))[0]))
        uf.management.testAndDelete(updateIntTable)
    except:
        updateIntTable = os.path.join(scratchDir, "{}_INT_MGS".format(arcpy.GetParameterAsText(3).replace(" ", "_")))

    uf.management.AddMsgAndPrint("* Extracting elevation measurements from DEM...")
    arcpy.management.CopyFeatures(
        in_features=arcpy.GetParameterAsText(2),
        out_feature_class=updateBhPoint
    )
    arcpy.ddd.AddSurfaceInformation(
        in_feature_class=updateBhPoint,
        in_surface=arcpy.GetParameterAsText(1),
        out_property="Z",
        method="BILINEAR",
        sample_distance=None,
        z_factor=1,
        pyramid_level_resolution=0,
        noise_filtering=""
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
        expression='!Z!'
    )
    arcpy.management.DeleteField(updateBhPoint, ["Z"])
    with arcpy.da.UpdateCursor(updateBhPoint,["DEM_ELEV"]) as cursor:
        for row in cursor:
            if row[0] is None:
                cursor.deleteRow()
        del row, cursor
    uf.management.AddMsgAndPrint("* Copying intervals table...")
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
            newElevField = "DEM_ELEV"
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
        newIdField = "WELLID"
        newElevField = "DEM_ELEV"
        newWellDepth = "WELL_DEPTH"
        newTopDepthField = "DEPTH_TOP"
        newBotDepthField = "DEPTH"
    if "DEPTH_TOP" in [f.name for f in arcpy.ListFields(updateIntTable)]:
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
    constDateField = "CONST_DATE"
    bdrkDepthField = "MGS_DEPTH_2_BDRK"
    if constDateField in [f.name for f in arcpy.ListFields(updateBhPoint)]:
        if arcpy.ListFields(updateBhPoint,constDateField)[0].type != "Date":
            arcpy.management.AddField(
                in_table=updateBhPoint,
                field_name="CONST_DATE_2",
                field_type="DATE",
                field_is_nullable="NULLABLE",
                field_is_required="NON_REQUIRED"
            )
            arcpy.management.CalculateField(
                in_table=updateBhPoint,
                field="CONST_DATE_2",
                expression='!CONST_DATE!'
            )
            newConstDateField = "CONST_DATE_2"
        else:
            newConstDateField = "CONST_DATE"
    else:
        newConstDateField = None
    with arcpy.da.UpdateCursor(updateIntTable,["DEPTH","DEPTH_TOP"]) as cursor:
        for row in cursor:
            if (row[0] == 0 and row[1] == 0):
                cursor.deleteRow()
            else:
                pass
        del row, cursor
    uf.management.AddMsgAndPrint("* Locating wells near cross-section line(s)...")
    wellIds = []
    locations = arcpy.management.SelectLayerByLocation(
        in_layer=updateBhPoint,
        overlap_type="WITHIN_A_DISTANCE",
        select_features=lines,
        search_distance=arcpy.GetParameterAsText(13),
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
    with arcpy.da.UpdateCursor(xsecInterval, ["WELLID"]) as cursor:
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

    for xsec in allValues:
        uf.management.AddMsgAndPrint("PROCESSING {}...".format(xsec))
        intervalBoreholes = XSEC_BoreholesIntervals.boreholeIntervals(
            lines=lines,
            xsec=xsec,
            dem=arcpy.GetParameterAsText(1),
            elevUnits=arcpy.GetParameterAsText(8),
            elevField=newElevField,
            wellPoints=xsecPoints,
            buff=arcpy.GetParameterAsText(13),
            ve=arcpy.GetParameterAsText(14),
            outGDB=arcpy.GetParameterAsText(16),
            stickType=arcpy.GetParameterAsText(12),
            intervalTable=xsecInterval,
            depth_top="DEPTH_TOP",
            depth_bot="DEPTH"
        )
        # Now, to clean up the database for the next cross-section or other steps...
        uf.management.AddMsgAndPrint(" - Cleaning default geodatabse...")
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
    uf.management.AddMsgAndPrint("BEGIN TOPOGRAPHIC SURFACE PROFILE VIEW...")
    for xsec in allValues:
        profile_view = XSEC_Profiles.profileViews(
            xsecLine=lines,
            xsecName=xsec,
            raster=arcpy.GetParameterAsText(1),
            ve=arcpy.GetParameterAsText(14),
            elev_units=arcpy.GetParameterAsText(8),
            outGDB=arcpy.GetParameterAsText(16)
        )
        # Now, to clean up the database for the next cross-section or other steps...
        uf.management.AddMsgAndPrint(" - Cleaning default geodatabse...")
        arcpy.management.Delete(
            [os.path.join(scratchDir, "XSEC_{}_zm".format(os.path.splitext(os.path.basename(lines))[0], xsec)),
             os.path.join(scratchDir, "XSEC_{}_z".format(os.path.splitext(os.path.basename(lines))[0], xsec))])
        arcpy.management.DeleteField(lines, ["ROUTEID",
                                             "{}_{}_ID".format(os.path.splitext(os.path.basename(lines))[0], xsec)])
        xsecMap = prj.listMaps("XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")))[0]
        xsecMap.addDataFromPath(profile_view)
        uf.management.AddMsgAndPrint("-----------------------------")
    if arcpy.GetParameterAsText(9) == "":
        uf.management.AddMsgAndPrint("NO GROUNDWATER SURFACE PROFILE...")
    else:
        uf.management.AddMsgAndPrint("BEGIN GROUNDWATER SURFACE PROFILE...")
        for xsec in allValues:
            uf.management.AddMsgAndPrint("PROCESSING {}...".format(xsec))
            rasterPolys = arcpy.ValueTable(3)
            rasterPolys.loadFromString(arcpy.GetParameterAsText(9))
            for i in range(0, rasterPolys.rowCount):
                raster = rasterPolys.getValue(i, 0)
                year1 = rasterPolys.getValue(i, 1)
                year2 = rasterPolys.getValue(i, 2)

                uf.management.AddMsgAndPrint(" - Producing confidence polygon for {} surface...".format(os.path.splitext(os.path.basename(raster))[0]))
                featExtent = os.path.join(scratchDir,"RasterExtent_{}".format(os.path.splitext(os.path.basename(raster))[0]))
                arcpy.ddd.RasterDomain(raster,featExtent,"POLYGON")
                if (year1 == "" and year2 == ""):
                    buffWW = os.path.join(scratchDir,os.path.basename(xsecPoints)+"_{}_buff_AllYears".format(arcpy.GetParameterAsText(13).replace(" ","")))
                    arcpy.analysis.Buffer(xsecPoints,buffWW,"{}".format(arcpy.GetParameterAsText(13)),"FULL","ROUND","ALL",None,"PLANAR")
                    unionWW = os.path.join(scratchDir, os.path.basename(xsecPoints) + "_{}_Union_AllYears".format(
                        arcpy.GetParameterAsText(13).replace(" ", "")))
                    inFeatures = [featExtent,buffWW]
                    arcpy.analysis.Union(inFeatures,unionWW,"ONLY_FID",None,"GAPS")
                    confidenceZone = os.path.join(scratchDir,os.path.basename(raster) + "_ConZone")
                    arcpy.management.CopyFeatures(unionWW,confidenceZone)
                    arcpy.management.AddField(
                        in_table=confidenceZone,
                        field_name="CONFIDENCE",
                        field_type="TEXT",
                        field_length="255",
                        field_is_nullable="NULLABLE",
                        field_is_required="NON_REQUIRED"
                    )
                    with arcpy.da.UpdateCursor(confidenceZone,
                                               ["FID_{}".format(uf.management.limitString(os.path.splitext(os.path.basename(featExtent))[0],60)),
                                                "FID_{}".format(uf.management.limitString(os.path.splitext(os.path.basename(buffWW))[0],60)),
                                                "CONFIDENCE"]) as cursor:
                        for row in cursor:
                            if row[0] == -1:
                                cursor.deleteRow()
                            if (row[0] == 1 and row[1] == -1):
                                row[2] = "INFERRED"
                                cursor.updateRow(row)
                            if (row[0] == 1 and row[1] == 1):
                                row[2] = "CONFIDENT"
                                cursor.updateRow(row)
                        del row, cursor
                else:
                    gwlPoints = arcpy.management.SelectLayerByAttribute(
                        in_layer_or_view=xsecPoints,
                        selection_type="NEW_SELECTION",
                        where_clause="{0} >= timestamp '{1}-01-01 00:00:00' And {0} <= timestamp '{2}-12-31 00:00:00'".format(newConstDateField,year1,year2),
                        invert_where_clause=None
                    )
                    buffWW = os.path.join(scratchDir, os.path.basename(xsecPoints) + "_{}_buff_{}_{}".format(
                        arcpy.GetParameterAsText(13).replace(" ", ""),year1,year2))
                    arcpy.analysis.Buffer(gwlPoints, buffWW, "{}".format(arcpy.GetParameterAsText(13)), "FULL", "ROUND",
                                          "ALL", None, "PLANAR")
                    unionWW = os.path.join(scratchDir, os.path.basename(xsecPoints) + "_{}_Union_AllYears".format(
                        arcpy.GetParameterAsText(13).replace(" ", "")))
                    inFeatures = [featExtent, buffWW]
                    arcpy.analysis.Union(inFeatures, unionWW, "ONLY_FID", None, "GAPS")
                    confidenceZone = os.path.join(scratchDir, os.path.basename(raster) + "_ConZone")
                    arcpy.management.CopyFeatures(unionWW, confidenceZone)
                    arcpy.management.AddField(
                        in_table=confidenceZone,
                        field_name="CONFIDENCE",
                        field_type="TEXT",
                        field_length="255",
                        field_is_nullable="NULLABLE",
                        field_is_required="NON_REQUIRED"
                    )
                    with arcpy.da.UpdateCursor(confidenceZone,
                                               ["FID_{}".format(uf.management.limitString(
                                                   os.path.splitext(os.path.basename(featExtent))[0], 60)),
                                                "FID_{}".format(uf.management.limitString(
                                                    os.path.splitext(os.path.basename(buffWW))[0], 60)),
                                                "CONFIDENCE"]) as cursor:
                        for row in cursor:
                            if row[0] == -1:
                                cursor.deleteRow()
                            if (row[0] == 1 and row[1] == -1):
                                row[2] = "INFERRED"
                                cursor.updateRow(row)
                            if (row[0] == 1 and row[1] == 1):
                                row[2] = "CONFIDENT"
                                cursor.updateRow(row)
                        del row, cursor
                segProfile = XSEC_SegmentProfiles.segmentProfiles(
                    xsecLine=lines,
                    xsec=xsec,
                    ve=arcpy.GetParameterAsText(14),
                    raster=raster,
                    elev_units=arcpy.GetParameterAsText(8),
                    polygon=confidenceZone,
                    outGDB=arcpy.GetParameterAsText(16)
                )
                # Now, to clean up the database for the next cross-section or other steps...
                uf.management.AddMsgAndPrint(" - Cleaning default geodatabse...")
                arcpy.management.Delete(
                    [os.path.join(scratchDir, "XSEC_{}_zm".format(os.path.splitext(os.path.basename(lines))[0], xsec)),
                     os.path.join(scratchDir, "XSEC_{}_z".format(os.path.splitext(os.path.basename(lines))[0], xsec)),
                     buffWW,unionWW,confidenceZone,featExtent])
                arcpy.management.DeleteField(lines, ["ROUTEID",
                                                     "{}_{}_ID".format(os.path.splitext(os.path.basename(lines))[0], xsec)])
                xsecMap = prj.listMaps("XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")))[0]
                xsecMap.addDataFromPath(segProfile)

                gwlLayer = xsecMap.listLayers(os.path.splitext(os.path.basename(segProfile))[0])[0]

                # Grids symbology...
                symGWL = gwlLayer.symbology
                symGWL.updateRenderer("UniqueValueRenderer")
                gwlLayer.symbology = symGWL

                symGWL.renderer.fields = ["CONFIDENCE"]
                symGWL.renderer.removeValues({"CONFIDENCE": ["CONFIDENT", "INFERRED"]})
                gwlLayer.symbology = symGWL
                symGWL.renderer.addValues({"Confidence of Profile": ["CONFIDENT", "INFERRED"]})
                gwlLayer.symbology = symGWL
                for group in symGWL.renderer.groups:
                    for item in group.items:
                        if item.values[0][0] == "CONFIDENT":
                            item.symbol.outlineColor = {'RGB': [0, 197, 255, 100]}
                            item.symbol.outlineWidth = 1
                            item.label = "Confident Surface"
                            gwlLayer.symbology = symGWL
                        elif item.values[0][0] == "INFERRED":
                            item.symbol.applySymbolFromGallery('Dashed 6:6')
                            item.symbol.outlineColor = {'RGB': [0, 197, 255, 100]}
                            item.symbol.outlineWidth = 1
                            item.label = "Inferred Surface"
                            gwlLayer.symbology = symGWL
                prj.save()
                uf.management.AddMsgAndPrint("PLease make sure to change color symbology for different groundwater intervals.")
                uf.management.AddMsgAndPrint("-----------------------------")
    if arcpy.GetParameterAsText(10) == "":
        uf.management.AddMsgAndPrint("NO BEDROCK SURFACE PROFILE...")
    else:
        uf.management.AddMsgAndPrint("BEGIN BEDROCK SURFACE PROFILE...")
        for xsec in allValues:
            uf.management.AddMsgAndPrint("PROCESSING {}...".format(xsec))
            if bdrkDepthField in [f.name for f in arcpy.ListFields(updateBhPoint)]:
                uf.management.AddMsgAndPrint(" - Producing confidence polygon for bedrock surface...")
                featExtent = os.path.join(scratchDir,
                                          "RasterExtent_{}".format(os.path.splitext(os.path.basename(arcpy.GetParameterAsText(10)))[0]))
                arcpy.ddd.RasterDomain(arcpy.GetParameterAsText(10), featExtent, "POLYGON")
                bdrkPoints = arcpy.management.SelectLayerByAttribute(
                    in_layer_or_view=xsecPoints,
                    selection_type="NEW_SELECTION",
                    where_clause="{} > 0".format(bdrkDepthField),
                    invert_where_clause=None
                )
                buffWW = os.path.join(scratchDir, os.path.basename(xsecPoints) + "_{}_buff_BDRK".format(arcpy.GetParameterAsText(13).replace(" ", "")))
                arcpy.analysis.Buffer(bdrkPoints, buffWW, "{}".format(arcpy.GetParameterAsText(13)), "FULL", "ROUND",
                                      "ALL", None, "PLANAR")
                unionWW = os.path.join(scratchDir, os.path.basename(xsecPoints) + "_{}_Union_BDRK".format(
                    arcpy.GetParameterAsText(13).replace(" ", "")))
                inFeatures = [featExtent, buffWW]
                arcpy.analysis.Union(inFeatures, unionWW, "ONLY_FID", None, "GAPS")
                confidenceZone = os.path.join(scratchDir, os.path.basename(raster) + "_ConZone")
                arcpy.management.CopyFeatures(unionWW, confidenceZone)
                arcpy.management.AddField(
                    in_table=confidenceZone,
                    field_name="CONFIDENCE",
                    field_type="TEXT",
                    field_length="255",
                    field_is_nullable="NULLABLE",
                    field_is_required="NON_REQUIRED"
                )
                with arcpy.da.UpdateCursor(confidenceZone,
                                           ["FID_{}".format(uf.management.limitString(
                                               os.path.splitext(os.path.basename(featExtent))[0], 60)),
                                               "FID_{}".format(uf.management.limitString(
                                                   os.path.splitext(os.path.basename(buffWW))[0], 60)),
                                               "CONFIDENCE"]) as cursor:
                    for row in cursor:
                        if row[0] == -1:
                            cursor.deleteRow()
                        if (row[0] == 1 and row[1] == -1):
                            row[2] = "INFERRED"
                            cursor.updateRow(row)
                        if (row[0] == 1 and row[1] == 1):
                            row[2] = "CONFIDENT"
                            cursor.updateRow(row)
                    del row, cursor
                bdrkProfile = XSEC_SegmentProfiles.segmentProfiles(
                    xsecLine=lines,
                    xsec=xsec,
                    ve=arcpy.GetParameterAsText(14),
                    raster=arcpy.GetParameterAsText(10),
                    elev_units=arcpy.GetParameterAsText(8),
                    polygon=confidenceZone,
                    outGDB=arcpy.GetParameterAsText(16)
                )
                # Now, to clean up the database for the next cross-section or other steps...
                uf.management.AddMsgAndPrint(" - Cleaning default geodatabse...")
                arcpy.management.Delete(
                    [os.path.join(scratchDir, "XSEC_{}_zm".format(os.path.splitext(os.path.basename(lines))[0], xsec)),
                     os.path.join(scratchDir, "XSEC_{}_z".format(os.path.splitext(os.path.basename(lines))[0], xsec)),
                     buffWW, unionWW, confidenceZone,featExtent])
            else:
                bdrkProfile = XSEC_Profiles.profileViews(
                    xsecLine=lines,
                    xsecName=xsec,
                    raster=arcpy.GetParameterAsText(10),
                    ve=arcpy.GetParameterAsText(14),
                    elev_units=arcpy.GetParameterAsText(8),
                    outGDB=arcpy.GetParameterAsText(16)
                )
                # Now, to clean up the database for the next cross-section or other steps...
                uf.management.AddMsgAndPrint(" - Cleaning default geodatabse...")
                arcpy.management.Delete(
                    [os.path.join(scratchDir, "XSEC_{}_zm_{}".format(xsec,os.path.splitext(os.path.basename(lines))[0])),
                     os.path.join(scratchDir, "XSEC_{}_z".format(xsec))])
            arcpy.management.DeleteField(lines, ["ROUTEID",
                                                 "{}_{}_ID".format(os.path.splitext(os.path.basename(lines))[0], xsec)])
            xsecMap = prj.listMaps("XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")))[0]
            xsecMap.addDataFromPath(bdrkProfile)

            bdrkLayer = xsecMap.listLayers(os.path.splitext(os.path.basename(bdrkProfile))[0])[0]

            if bdrkDepthField in [f.name for f in arcpy.ListFields(updateBhPoint)]:
                # Bedrock symbology...
                symBDRK = bdrkLayer.symbology
                symBDRK.updateRenderer("UniqueValueRenderer")
                bdrkLayer.symbology = symBDRK

                symBDRK.renderer.fields = ["CONFIDENCE"]
                symBDRK.renderer.removeValues({"CONFIDENCE": ["CONFIDENT", "INFERRED"]})
                bdrkLayer.symbology = symBDRK
                symBDRK.renderer.addValues({"Confidence of Profile": ["CONFIDENT", "INFERRED"]})
                bdrkLayer.symbology = symBDRK
                for group in symBDRK.renderer.groups:
                    for item in group.items:
                        if item.values[0][0] == "CONFIDENT":
                            item.symbol.outlineColor = {'RGB': [0, 0, 0, 100]}
                            item.symbol.outlineWidth = 1
                            item.label = "Confident Surface"
                            bdrkLayer.symbology = symBDRK
                        elif item.values[0][0] == "INFERRED":
                            item.symbol.applySymbolFromGallery('Dashed 6:6')
                            item.symbol.outlineColor = {'RGB': [0, 0, 0, 100]}
                            item.symbol.outlineWidth = 1
                            item.label = "Inferred Surface"
                            bdrkLayer.symbology = symBDRK
            else:
                symBDRK = bdrkLayer.symbology
                if symBDRK.renderer.type == "UniqueValueRenderer":
                    symBDRK.updateRenderer("SimpleRenderer")
                symBDRK.renderer.symbol.outlineColor = {"RGB": [0, 0, 0, 100]}
                symBDRK.renderer.symbol.outlineWidth = 1
                bdrkLayer.symbology = symBDRK
            prj.save()
            uf.management.AddMsgAndPrint("-----------------------------")
    if arcpy.GetParameterAsText(11) == "":
        uf.management.AddMsgAndPrint("NO EXTRA SURFACE PROFILES...")
    else:
        uf.management.AddMsgAndPrint("BEGIN EXTRA SURFACE PROFILE(S)...")
        for xsec in allValues:
            uf.management.AddMsgAndPrint("PROCESSING {}...".format(xsec))
            for rasterSurf in arcpy.GetParameterAsText(11).split(";"):
                uf.management.AddMsgAndPrint(" - Processing {}...".format(rasterSurf))
                profile_view = XSEC_Profiles.profileViews(
                    xsecLine=lines,
                    xsecName=xsec,
                    raster=rasterSurf,
                    ve=arcpy.GetParameterAsText(14),
                    elev_units=arcpy.GetParameterAsText(8),
                    outGDB=arcpy.GetParameterAsText(16)
                )
                # Now, to clean up the database for the next cross-section or other steps...
                uf.management.AddMsgAndPrint(" - Cleaning default geodatabse...")
                arcpy.management.Delete(
                    [os.path.join(scratchDir, "XSEC_{}_zm".format(os.path.splitext(os.path.basename(lines))[0], xsec)),
                     os.path.join(scratchDir, "XSEC_{}_z".format(os.path.splitext(os.path.basename(lines))[0], xsec))])
                arcpy.management.DeleteField(lines, ["ROUTEID",
                                                     "{}_{}_ID".format(os.path.splitext(os.path.basename(lines))[0], xsec)])
                xsecMap = prj.listMaps("XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")))[0]
                xsecMap.addDataFromPath(profile_view)
                uf.management.AddMsgAndPrint("-----------------------------")
    uf.management.AddMsgAndPrint("-----------------------------")
    uf.management.AddMsgAndPrint("BEGIN GRID-LINE PROFILE...")
    for xsec in allValues:
        uf.management.AddMsgAndPrint("PROCESSING {}...".format(xsec))
        tempPoints = os.path.join(scratchDir, "TempBH_Points")
        xsecLine = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=lines,
            selection_type="NEW_SELECTION",
            where_clause="XSEC = '{}'".format(xsec),
            invert_where_clause=None)
        well_near = arcpy.management.SelectLayerByLocation(
            in_layer=updateBhPoint,
            overlap_type="WITHIN_A_DISTANCE",
            select_features=xsecLine,
            search_distance=arcpy.GetParameterAsText(13)
        )
        arcpy.management.CopyFeatures(well_near, tempPoints)
        arcpy.management.SelectLayerByAttribute(lines, "CLEAR_SELECTION")
        arcpy.management.SelectLayerByAttribute(arcpy.GetParameterAsText(2), "CLEAR_SELECTION")

        depthElev = []
        topElev = []
        with arcpy.da.SearchCursor(tempPoints, [newElevField, "WELL_DEPTH"]) as cursor:
            for row in cursor:
                depthElev.append(float(row[0]) - float(row[1]))
                topElev.append(float(row[0]))
            del row, cursor
        surfElev_Max = max(topElev)
        depthElev_Max = min(depthElev)

        gridOption = arcpy.ValueTable(4)
        gridOption.loadFromString(arcpy.GetParameterAsText(15))
        for i in range(0, gridOption.rowCount):
            yInt = gridOption.getValue(i, 0)
            yUnits = gridOption.getValue(i, 1)
            xInt = gridOption.getValue(i, 2)
            xUnits = gridOption.getValue(i, 3)
            uf.management.AddMsgAndPrint(
                " - Distance Units: {} {}\n - Elevation Units: {} {}".format(xInt, xUnits, yInt,
                                                                               yUnits))

            frame, labels = XSEC_GridLines.gridProfile(
                xsecLine=lines,
                xsecName=xsec,
                elevation=arcpy.GetParameterAsText(8),
                surfRaster=arcpy.GetParameterAsText(1),
                bdrkRaster=arcpy.GetParameterAsText(10),
                maxBH_elev=surfElev_Max,
                maxDepthElev=depthElev_Max,
                ve=arcpy.GetParameterAsText(14),
                elev_units=yUnits,
                dist_units=xUnits,
                elev_int=yInt,
                dist_int=xInt,
                outGDB=arcpy.GetParameterAsText(16)
            )
            # Now, to clean up the database for the next cross-section or other steps...
            uf.management.AddMsgAndPrint(" - Cleaning default geodatabse...")
            arcpy.management.Delete(
                [os.path.join(scratchDir, "XSEC_{}_zm_{}".format(xsec, os.path.splitext(os.path.basename(lines))[0])),
                 os.path.join(scratchDir, "XSEC_{}_z".format(xsec))])
            arcpy.management.DeleteField(lines, ["ROUTEID",
                                                 "{}_{}_ID".format(os.path.splitext(os.path.basename(lines))[0], xsec)])
            xsecMap = prj.listMaps("XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")))[0]
            xsecMap.addDataFromPath(frame)
            xsecMap.addDataFromPath(labels)

            # We can add some symbology to this as well...
            uf.management.AddMsgAndPrint(" - Formatting grid line labels...")
            gridLayer = xsecMap.listLayers(os.path.splitext(os.path.basename(frame))[0])[0]
            labelLayer = xsecMap.listLayers(os.path.splitext(os.path.basename(labels))[0])[0]

            symLabels = labelLayer.symbology
            symGrids = gridLayer.symbology

            # Labels symbology...
            symLabels.renderer.symbol.color = {'RGB': [0, 0, 0, 0]}
            symLabels.renderer.symbol.outlineColor = {'RGB': [0, 0, 0, 0]}
            symLabels.renderer.symbol.outlineWidth = 2
            labelLayer.symbology = symLabels
            prj.save()

            # Grids symbology...
            symGrids.updateRenderer("UniqueValueRenderer")
            gridLayer.symbology = symGrids

            symGrids.renderer.fields = ["TYPE"]
            symGrids.renderer.removeValues({"TYPE": ["FRAME", "DISTANCE MARK", "ELEVATION MARK"]})
            gridLayer.symbology = symGrids
            symGrids.renderer.addValues({"Type": ["FRAME", "DISTANCE MARK", "ELEVATION MARK"]})
            gridLayer.symbology = symGrids
            for group in symGrids.renderer.groups:
                for item in group.items:
                    if item.values[0][0] == "FRAME":
                        item.symbol.outlineColor = {'RGB': [0, 0, 0, 100]}
                        item.symbol.outlineWidth = 2
                        item.label = "Border Frame"
                        gridLayer.symbology = symGrids
                    elif item.values[0][0] == "DISTANCE MARK":
                        item.symbol.outlineColor = {'RGB': [178, 178, 178, 100]}
                        item.symbol.outlineWidth = 0.5
                        item.label = "Grid Lines"
                        gridLayer.symbology = symGrids
                    elif item.values[0][0] == "ELEVATION MARK":
                        item.symbol.outlineColor = {'RGB': [178, 178, 178, 100]}
                        item.symbol.outlineWidth = 0.5
                        item.label = "Grid Lines"
                        gridLayer.symbology = symGrids
            prj.save()

            try:
                cimObject = labelLayer.getDefinition("V3")
                lblClasses = cimObject.labelClasses
                # elevLblClass = arcpy.cim.CreateCIMObjectFromClassName("CIMLabelClass","V3")
                # elevLblClass.name = "Elevation"
                # elevLblClass.visibility = True
                # cimObject.labelClasses.append(elevLblClass)
                # labelLayer.setDefinition(cimObject)

                for lblClass in lblClasses:
                    if lblClass.name == "Class 1":
                        lblClass.name = "Distance"
                        nlc_index = cimObject.labelClasses.index(lblClass)
                        newClass = cimObject.labelClasses.copy()[nlc_index]
                        cimObject.labelClasses.append(newClass)
                        labelLayer.setDefinition(cimObject)
                        break

                cimObject = labelLayer.getDefinition("V3")
                lblClasses = cimObject.labelClasses
                for lblClass in lblClasses:
                    if lblClass.name == "Distance":
                        nlc_index = cimObject.labelClasses.index(lblClass)
                        if nlc_index != 0:
                            lblClass.name = "Elevation"
                            labelLayer.setDefinition(cimObject)

                # Place the labels correctly...
                lblClassDist_2 = cimObject.labelClasses[0]
                lblClassDist_2.maplexLabelPlacementProperties.pointPlacementMethod = "SouthOfPoint"
                lblClassDist_2.maplexLabelPlacementProperties.rotationProperties.enable = True
                lblClassDist_2.maplexLabelPlacementProperties.rotationProperties.additionalAngle = -45
                lblClassDist_2.maplexLabelPlacementProperties.primaryOffset = 10.0
                labelLayer.setDefinition(cimObject)

                lblClassElev_2 = cimObject.labelClasses[1]
                lblClassElev_2.maplexLabelPlacementProperties.pointPlacementMethod = "WestOfPoint"
                lblClassElev_2.maplexLabelPlacementProperties.primaryOffset = 10.0
                labelLayer.setDefinition(cimObject)

                labelLayer.showLabels = True

                if labelLayer.supports("SHOWLABELS"):
                    lblClassDist = labelLayer.listLabelClasses()[0]
                    lblClassDist.expressionEngine = "Arcade"
                    lblClassDist.expression = '"<FNT name = {}>" + $feature.LABEL + "</FNT>"'.format(
                        "'Times New Roman'")
                    lblClassDist.SQLQuery = "TYPE = 'DISTANCE MARK'"

                    lblClassElev = labelLayer.listLabelClasses()[1]
                    lblClassElev.expressionEngine = "Arcade"
                    lblClassElev.expression = '"<FNT name = {}>" + $feature.LABEL + "</FNT>"'.format(
                        "'Times New Roman'")
                    lblClassElev.SQLQuery = "TYPE = 'ELEVATION MARK'"
                    lblClassElev.visible = True
                else:
                    pass
                prj.save()
            except Exception as e:
                uf.management.AddMsgAndPrint(
                    "Could not complete labels and symbology.\nError Message: {}.\nPassing to final steps...".format(e),
                    1)
                pass

            extentLyr = xsecMap.listLayers(os.path.splitext(os.path.basename(labels))[0])[0]
            xsecMap.defaultCamera.setExtent(arcpy.Describe(extentLyr).extent)
            prj.save()
        uf.management.AddMsgAndPrint("-----------------------------")
        arcpy.management.Delete(tempPoints)
        depthElev.clear()
        topElev.clear()
    uf.management.AddMsgAndPrint(
        '***FINISHED CREATING CROSS-SECTION DATASETS UTILIZING THE SCHEMA DETAILED BY THE MICHIGAN GEOLOGICAL SURVEY***')
    uf.management.AddMsgAndPrint(" - Final cleaning of default geodatabse...")
    if demSR.name == linesSR.name:
        arcpy.management.Delete([updateBhPoint,updateIntTable,routeWells,xsecInterval,xsecPoints])
    else:
        arcpy.management.Delete([updateBhPoint, updateIntTable, routeWells, xsecInterval, xsecPoints, newLines])