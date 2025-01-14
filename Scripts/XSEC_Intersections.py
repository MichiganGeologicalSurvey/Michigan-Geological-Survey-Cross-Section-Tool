# *****************************************************
# *****************************************************
# XSEC_Intersections.py
# Version: 1.0
# Date: 7/9/2024
# Last Modified Date: 7/9/2024
# Original Author: Matthew Bell, Michigan Geological Survey, matthew.e.bell@wmich.edu
# Description: Command python code to create and place intersected points of interest onto a cross-sectional view.
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
uf.management.AddMsgAndPrint("-----------------------------")

def intersectingPoints(lineFeature,selectDist,otherFeatures,xsec,surfDEM,elev_units,ve,outGDB):
    # We will determine which points intersect the cross-section lines.
    # Initially, we will need to create the route to place the points.
    intersectedFeatures = []
    zm_line,offset,id_checkField = uf.xsec.zmLine_Generation(
        lineFeature=lineFeature,
        XSEC_NAME=xsec,
        defaultGDB=scratchDir,
        raster_surface=surfDEM
    )
    # First, let's figure out which cross-sections intersect each other.
    xsecIntersect = os.path.join(scratchDir,"XSEC_Intersect")
    arcpy.analysis.PairwiseIntersect(
        in_features=[lineFeature],
        out_feature_class=xsecIntersect,
        join_attributes="ALL",
        cluster_tolerance=None,
        output_type="POINT"
    )
    featuresList = []
    if otherFeatures == "":
        pass
    else:
        for feature in otherFeatures.split(";"):
            xsecFeatureInt = os.path.join(scratchDir,"XSEC_Intersect_{}".format(os.path.splitext(os.path.basename(feature))[0]))
            if arcpy.Describe(feature).shapeType == "Polyline":
                pointsIntersect = os.path.join(scratchDir, "IntersectionsPOINT")
                arcpy.analysis.PairwiseIntersect(
                    in_features=[lineFeature,feature],
                    out_feature_class=pointsIntersect,
                    join_attributes="ALL",
                    cluster_tolerance=None,
                    output_type="POINT"
                )
                arcpy.management.MultipartToSinglepart(
                    in_features=pointsIntersect,
                    out_feature_class=xsecFeatureInt
                )
                featuresList.append(xsecFeatureInt)
                arcpy.management.Delete(pointsIntersect)
            elif arcpy.Describe(feature).shapeType == "Polygon":
                linesIntersect = os.path.join(scratchDir,"IntersectionsLINE")
                pointsIntersect = os.path.join(scratchDir, "IntersectionsPOINT")
                arcpy.management.FeatureToLine(
                    in_features=feature,
                    out_feature_class=linesIntersect,
                    cluster_tolerance=None,
                    attributes="ATTRIBUTES"
                )
                arcpy.analysis.PairwiseIntersect(
                    in_features=[lineFeature, linesIntersect],
                    out_feature_class=pointsIntersect,
                    join_attributes="ALL",
                    cluster_tolerance=None,
                    output_type="POINT"
                )
                arcpy.management.MultipartToSinglepart(
                    in_features=pointsIntersect,
                    out_feature_class=xsecFeatureInt
                )
                featuresList.append(xsecFeatureInt)
                arcpy.management.Delete([linesIntersect,pointsIntersect])
            elif arcpy.Describe(feature).shapeType == "Point":
                selectPoints = arcpy.management.SelectLayerByLocation(
                    in_layer=feature,
                    overlap_type="WITHIN_A_DISTANCE",
                    select_features=lineFeature,
                    search_distance=selectDist,
                    selection_type="NEW_SELECTION",
                    invert_spatial_relationship="NOT_INVERT"
                )
                arcpy.management.CopyFeatures(selectPoints,xsecFeatureInt)
                arcpy.management.AddField(
                    in_table=xsecFeatureInt,
                    field_name="XSEC",
                    field_type="TEXT",
                    field_length=255
                )
                arcpy.management.CalculateField(
                    in_table=xsecFeatureInt,
                    field="XSEC",
                    expression="'{}'".format(xsec)
                )
                featuresList.append(xsecFeatureInt)
                arcpy.management.SelectLayerByAttribute(feature,"CLEAR_SELECTION")
    # Since we only care about the cross-section names, we do not need the direction field or the FID field. We can
    # delete those fields.
    arcpy.management.DeleteField(
        in_table=xsecIntersect,
        drop_field=["DIRECTIONS"]
    )
    xsecOnLine = arcpy.management.SelectLayerByAttribute(
        in_layer_or_view=xsecIntersect,
        selection_type="NEW_SELECTION",
        where_clause="XSEC <> '{}'".format(xsec)
    )
    zXsecLines = os.path.join(scratchDir,"XSEC_{}_zXSEC".format(xsec))
    arcpy.ddd.InterpolateShape(surfDEM,xsecOnLine,zXsecLines)
    arcpy.management.AddField(zXsecLines,"zDEM","DOUBLE")
    arcpy.management.CalculateField(zXsecLines,"zDEM","!SHAPE.FIRSTPOINT.Z!","PYTHON3")
    zField = "zDEM"
    arcpy.management.SelectLayerByAttribute(zXsecLines,"CLEAR_SELECTION")

    rProps = "rkey POINT M fmp"
    eventTableXSEC = uf.xsec.locateEvents_Table(
        pts=zXsecLines,
        rasterDEM=surfDEM,
        XSEC_NAME=xsec,
        defaultGDB=scratchDir,
        route_line=zm_line,
        checkField=id_checkField,
        sel_dist="1 Meters",
        event_props=rProps,
        z_type="Z"
    )
    eventLayerXSEC = "XSEC_{}_Events".format(xsec)
    arcpy.lr.MakeRouteEventLayer(zm_line,id_checkField,eventTableXSEC,rProps,eventLayerXSEC,"#","#","ANGLE_FIELD","TANGENT")
    locPoints = os.path.join(scratchDir,"XSEC_{}_surfLocated".format(xsec))
    arcpy.management.CopyFeatures(eventLayerXSEC,locPoints)
    arcpy.management.AddField(locPoints, "DistFromSection", "DOUBLE")
    arcpy.management.AddField(locPoints, "LocalXSEC_Azimuth", "DOUBLE")

    surfMarkedPoints = uf.xsec.surfPoints(
        locatedPoints=locPoints,
        XSEC_NAME=xsec,
        defaultGDB=outGDB,
        elev_field=zField,
        elev_units=elev_units,
        ve=ve
    )
    intersectedFeatures.append(surfMarkedPoints)
    if otherFeatures == "":
        pass
    else:
        for feature in featuresList:
            arcpy.management.DeleteField(
                in_table=feature,
                drop_field=["DIRECTIONS"]
            )
            xsecOnLine = arcpy.management.SelectLayerByAttribute(
                in_layer_or_view=feature,
                selection_type="NEW_SELECTION",
                where_clause="XSEC = '{}'".format(xsec)
            )
            zXsecLines = os.path.join(scratchDir, "XSEC_{}_z{}".format(xsec,os.path.splitext(os.path.basename(feature))[0]))
            arcpy.ddd.InterpolateShape(surfDEM, xsecOnLine, zXsecLines)
            arcpy.management.AddField(zXsecLines, "zDEM", "DOUBLE")
            arcpy.management.CalculateField(zXsecLines, "zDEM", "!SHAPE.FIRSTPOINT.Z!", "PYTHON3")
            zField = "zDEM"
            arcpy.management.SelectLayerByAttribute(zXsecLines, "CLEAR_SELECTION")

            rProps = "rkey POINT M fmp"
            eventTableXSEC = uf.xsec.locateEvents_Table(
                pts=zXsecLines,
                rasterDEM=surfDEM,
                XSEC_NAME=xsec,
                defaultGDB=scratchDir,
                route_line=zm_line,
                checkField=id_checkField,
                sel_dist=selectDist,
                event_props=rProps,
                z_type="Z"
            )
            eventLayerXSEC = "XSEC_{}_Events_{}".format(xsec,os.path.splitext(os.path.basename(feature))[0])
            arcpy.lr.MakeRouteEventLayer(zm_line, id_checkField, eventTableXSEC, rProps, eventLayerXSEC, "#", "#",
                                         "ANGLE_FIELD", "TANGENT")
            locPoints = os.path.join(scratchDir, "XSEC_{}_{}".format(xsec,os.path.splitext(os.path.basename(feature))[0]))
            arcpy.management.CopyFeatures(eventLayerXSEC, locPoints)
            arcpy.management.AddField(locPoints, "DistFromSection", "DOUBLE")
            arcpy.management.AddField(locPoints, "LocalXSEC_Azimuth", "DOUBLE")

            featureSurfIntersect = uf.xsec.surfPoints(
                locatedPoints=locPoints,
                XSEC_NAME=xsec,
                defaultGDB=outGDB,
                elev_field=zField,
                elev_units=elev_units,
                ve=ve
            )
            if float(arcpy.management.GetCount(featureSurfIntersect)[0]) == 0:
                uf.management.AddMsgAndPrint(
                    "**No features intersected line for {}. Deleting feature class...".format(os.path.splitext(os.path.basename(featureSurfIntersect))[0]))
                arcpy.management.Delete(featureSurfIntersect)
            else:
                intersectedFeatures.append(featureSurfIntersect)
        arcpy.management.Delete(featuresList)
    return intersectedFeatures

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
        outFDS = os.path.join(arcpy.GetParameterAsText(6),FDSname)
        if not arcpy.Exists(outFDS):
            arcpy.management.CreateFeatureDataset(arcpy.GetParameterAsText(6),FDSname,unknown)
    for xsec in allValues:
        uf.management.AddMsgAndPrint("PROCESSING {}...".format(xsec))
        surfMarkers = intersectingPoints(
            lineFeature=lines,
            selectDist=arcpy.GetParameterAsText(1),
            otherFeatures=arcpy.GetParameterAsText(2),
            xsec=xsec,
            surfDEM=arcpy.GetParameterAsText(3),
            elev_units=arcpy.GetParameterAsText(4),
            ve=arcpy.GetParameterAsText(5),
            outGDB=arcpy.GetParameterAsText(6)
        )
        # Now, to clean up the database for the next cross-section or other steps...
        uf.management.AddMsgAndPrint("Cleaning default geodatabse...")
        arcpy.management.Delete(
            [os.path.join(scratchDir,"XSEC_{}_zm".format(xsec)),os.path.join(scratchDir, "XSEC_{}_z".format( xsec)),
             os.path.join(scratchDir,"XSEC_{}_surfLocated".format(xsec)),"XSEC_{}_Events".format(xsec),
             os.path.join(scratchDir,"XSEC_{}_zXSEC".format(xsec)),
             os.path.join(scratchDir,"XSEC_{}_locEvents".format(xsec)),os.path.join(scratchDir,"XSEC_Intersect")])
        arcpy.management.DeleteField(lines,
                                     ["ROUTEID", "{}_{}_ID".format(os.path.splitext(os.path.basename(lines))[0], xsec)])
        xsecMap = prj.listMaps("XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")))[0]
        for feature in surfMarkers:
            xsecMap.addDataFromPath(feature)
        uf.management.AddMsgAndPrint("-----------------------------")