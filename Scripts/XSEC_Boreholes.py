# *****************************************************
# *****************************************************
# XSEC_Boreholes.py
# Version: 1.2
# Date: 7/9/2024
# Last Modified Date: 6/10/2025
# Original Author: Matthew Bell, Michigan Geological Survey, matthew.e.bell@wmich.edu
# Description: Command python code to create and place borehole sticks onto a cross-sectional view.
# *****************************************************
# *****************************************************

import arcpy
import os
import Utility_Functions as uf

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
version = "XSEC_Boreholes.py, Version 1.2.3"
url = "https://raw.githubusercontent.com/MichiganGeologicalSurvey/Michigan-Geological-Survey-Cross-Section-Tools/refs/heads/Master/Scripts/XSEC_Boreholes.py"
uf.management.githubVersion(
    vString=version,
    rawurl=url
)
uf.management.AddMsgAndPrint("-----------------------------")

def boreholeSticks(lineFeature,xsec,surfDEM,elev_units,elev_field,well_points,buff,ve,outGDB,stickType):
    # We will determine which points are within the user defined area
    # Initially, we will need to create the route to place the points.
    zm_line, offset, id_checkField = uf.xsec.zmLine_Generation(
        lineFeature=lineFeature,
        XSEC_NAME=xsec,
        defaultGDB=scratchDir,
        raster_surface=surfDEM
    )
    well_near = arcpy.management.SelectLayerByLocation(
        in_layer=well_points,
        overlap_type="WITHIN_A_DISTANCE",
        select_features=zm_line,
        search_distance=buff
    )
    zWells = "XSEC_{}_zWells".format(xsec)
    if elev_field == "":
        arcpy.ddd.InterpolateShape(surfDEM,well_near,zWells)
        arcpy.management.AddField(zWells,"zDEM","DOUBLE")
        try:
            arcpy.management.CalculateField(zWells,"zDEM","!SHAPE.FIRSTPOINT.Z!","PYTHON3")
        except:
            arcpy.management.CalculateField(zWells, "zDEM", 0, "PYTHON3")
        zField = "zDEM"
    else:
        arcpy.management.CopyFeatures(well_near,zWells)
        zField = elev_field
    arcpy.management.SelectLayerByAttribute(well_points,"CLEAR_SELECTION")
    rProps = "rkey POINT M fmp"
    eventTableWells = uf.xsec.locateEvents_Table(
        pts=zWells,
        rasterDEM=surfDEM,
        XSEC_NAME=xsec,
        defaultGDB=scratchDir,
        route_line=zm_line,
        checkField=id_checkField,
        sel_dist=buff,
        event_props=rProps,
        z_type="Z"
    )
    eventLayerWells = "XSEC_{}_Events".format(xsec)
    arcpy.lr.MakeRouteEventLayer(zm_line, id_checkField, eventTableWells, rProps, eventLayerWells, "#", "#",
                                 "ANGLE_FIELD", "TANGENT")
    locPoints = os.path.join(scratchDir, "XSEC_{}_wellsLocated".format(xsec))
    arcpy.management.CopyFeatures(eventLayerWells, locPoints)
    arcpy.management.AddField(locPoints, "DistFromSection", "DOUBLE")
    arcpy.management.AddField(locPoints, "LocalXSEC_Azimuth", "DOUBLE")
    bhLines = uf.xsec.boreholes(
        locatedPoints=locPoints,
        XSEC_NAME=xsec,
        defaultGDB=scratchDir,
        elev_field=zField,
        depth_field="WELL_DEPTH",
        elev_units=elev_units,
        ve=ve
    )
    nameID = 1
    while True:
        bhName = "XSEC_{}_bhStick_{}x_v{}".format(xsec.replace("-", "_").replace(" ", "_"),ve, nameID)
        bhStick = os.path.join(outGDB, "XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")),bhName)
        if arcpy.Exists(bhStick):
            nameID = nameID + 1
        else:
            break
    if stickType == "Polygon":
        arcpy.analysis.Buffer(bhLines, bhStick, "10 Unknown", "FULL", "FLAT", "NONE", None, "PLANAR")
        arcpy.management.DeleteField(bhStick, ["BUFF_DIST", "ORIG_FID"])
    else:
        arcpy.management.CopyFeatures(bhLines,bhStick)
    arcpy.management.Delete([eventTableWells])
    return bhStick,bhLines

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
        outFDS = os.path.join(arcpy.GetParameterAsText(9),FDSname)
        if not arcpy.Exists(outFDS):
            arcpy.management.CreateFeatureDataset(arcpy.GetParameterAsText(9),FDSname,unknown)
    try:
        updateBhPoint = os.path.join(scratchDir, "{}_BH_MGS".format(
            os.path.splitext(os.path.basename(arcpy.GetParameterAsText(2)))[0]))
        uf.management.testAndDelete(updateBhPoint)
    except:
        updateBhPoint = os.path.join(scratchDir, "{}_BH_MGS".format(arcpy.GetParameterAsText(2).replace(" ","_")))

    uf.management.AddMsgAndPrint(" - Extracting elevation measurements from DEM...")
    featExtent = os.path.join(scratchDir, "RasterArea_{}".format(
        os.path.splitext(os.path.basename(arcpy.GetParameterAsText(1)))[0]))
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
        uf.management.AddMsgAndPrint(
            "Too many locations outside the raster boundary (Limit: 10). Please review the wells and select only the records inside the defined DEM.",
            2)
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
    arcpy.management.DeleteField(updateBhPoint,["RASTERVALU"])
    if arcpy.GetParameterAsText(3) == "true":
        bhFields = arcpy.ValueTable(3)
        bhFields.loadFromString(arcpy.GetParameterAsText(4))
        idField = bhFields.getValue(0,0)
        depthField = bhFields.getValue(0,1)
        elevField = bhFields.getValue(0,2)

        arcpy.management.CopyFeatures(arcpy.GetParameterAsText(2),updateBhPoint)
        arcpy.management.AlterField(
            in_table=updateBhPoint,
            field=idField,
            new_field_name="WELLID"
        )
        arcpy.management.AlterField(
            in_table=updateBhPoint,
            field=depthField,
            new_field_name="WELL_DEPTH"
        )
        if elevField == "":
            newElevField = ""
        else:
            newElevField = elevField
    else:
        newElevField = "DEM_ELEV"
    wellIds = []
    with arcpy.da.SearchCursor(updateBhPoint, ["WELLID"]) as cursor:
        for row in cursor:
            wellIds.append(row[0])
        del row, cursor
    routeLiths = arcpy.management.SelectLayerByAttribute(
        in_layer_or_view=updateBhPoint,
        selection_type="ADD_TO_SELECTION",
        where_clause="WELLID IN {}".format(wellIds).replace("[", "(").replace("]", ")"),
        invert_where_clause=None)
    for xsec in allValues:
        uf.management.AddMsgAndPrint("PROCESSING {}...".format(xsec))
        finalBorehole,bhLines = boreholeSticks(
            lineFeature=lines,
            xsec=xsec,
            surfDEM=arcpy.GetParameterAsText(1),
            elev_units=arcpy.GetParameterAsText(5),
            elev_field=newElevField,
            well_points=routeLiths,
            buff=arcpy.GetParameterAsText(6),
            ve=arcpy.GetParameterAsText(7),
            outGDB=arcpy.GetParameterAsText(9),
            stickType=arcpy.GetParameterAsText(8)
        )
        # Now, to clean up the database for the next cross-section or other steps...
        uf.management.AddMsgAndPrint("Cleaning default geodatabse...")
        arcpy.management.Delete(
            [os.path.join(scratchDir, "XSEC_{}_zm_{}".format(xsec,os.path.splitext(os.path.basename(lines))[0])),
             os.path.join(scratchDir, "XSEC_{}_z".format(xsec)),
             os.path.join(scratchDir, "XSEC_{}_wellsLocated".format(xsec)),
             os.path.join(scratchDir, "XSEC_{}_bhLines".format(xsec)),
             os.path.join(scratchDir, "XSEC_{}_zWells".format(xsec)),
             bhLines])
        arcpy.management.DeleteField(lines,
                                     ["ROUTEID", "{}_{}_ID".format(os.path.splitext(os.path.basename(lines))[0], xsec)])
        xsecMap = prj.listMaps("XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")))[0]
        xsecMap.addDataFromPath(finalBorehole)
        uf.management.AddMsgAndPrint("-----------------------------")