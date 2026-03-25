# *****************************************************
# *****************************************************
# XSEC_SegmentProfiles.py
# Version: 1.2
# Date: 7/9/2024
# Last Modified Date: 3/25/2026
# Original Author: Matthew Bell, Michigan Geological Survey, matthew.e.bell@wmich.edu
# Description: Command python code to create and place profiles onto a cross-sectional view and segment the profiles based on a polygon of the user's choosing.
# *****************************************************
# *****************************************************

# Bedrock based on confidence of surface
# Bedrock based on geologic units
# Surface profile based on geologic units
# Groundwater profile based on confidence of surface

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
version = "XSEC_SegmentProfiles.py, Version 1.2.7"
url = "https://raw.githubusercontent.com/MichiganGeologicalSurvey/Michigan-Geological-Survey-Cross-Section-Tool/refs/heads/Master/Scripts/XSEC_SegmentProfiles.py"
uf.management.githubVersion(
    vString=version,
    rawurl=url
)
uf.management.AddMsgAndPrint("-----------------------------")

def segmentProfiles(xsecLine,xsec,ve,raster,elev_units,polygon,outGDB):
    zm_line, offset = uf.xsec.zmLine_Generation(
        lineFeature=xsecLine,
        XSEC_NAME=xsec,
        defaultGDB=scratchDir,
        raster_surface=raster
    )
    eventsTable = os.path.join(scratchDir,"{}_polyEvents_{}".format(os.path.splitext(os.path.basename(raster))[0],xsec))
    uf.management.testAndDelete(eventsTable)
    conProps = "rkey LINE FromM ToM"
    arcpy.lr.LocateFeaturesAlongRoutes(
        in_features=polygon,
        in_routes=zm_line,
        route_id_field="XSEC",
        radius_or_tolerance="#",
        out_table=eventsTable,
        out_event_properties=conProps,
        route_locations="FIRST",
        distance_field="NO_DISTANCE",
        zero_length_events="NO_ZERO"
    )
    locatedEvents = os.path.join(scratchDir,"{}_located_{}".format(os.path.splitext(os.path.basename(raster))[0],xsec))
    locatedEvents_sort = os.path.join(scratchDir,"{}_sorted_{}".format(os.path.splitext(os.path.basename(raster))[0], xsec))
    arcpy.management.Sort(in_dataset=eventsTable, out_dataset=locatedEvents_sort,
                          sort_field=[["FromM", "ASCENDING"]])
    uf.xsec.placeEvents(
        inRoutes=zm_line,
        idRteFld="XSEC",
        eventTable=locatedEvents_sort,
        eventRteFld="rkey",
        fromVar="FromM",
        toVar="ToM",
        eventLay=locatedEvents,
        wellid_fld="WELLID"
    )
    nameID = 1
    while True:
        profileName = "XSEC_{}_{}_{}x_v{}".format(
            xsec.replace("-", "_").replace(" ", "_"),
            os.path.splitext(os.path.basename(polygon))[0],
            ve,
            nameID)
        profilePath = os.path.join(outGDB, "XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")), profileName)
        if arcpy.Exists(profilePath):
            nameID = nameID + 1
        else:
            break
    arcpy.management.CreateFeatureclass(
        os.path.join(outGDB, "XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_"))),
        profileName, "POLYLINE", locatedEvents, spatial_reference=unknown
    )
    uf.xsec.plan2side(
        zm_line=locatedEvents,
        ve=ve,
        profile=profilePath,
        id_field="rkey",
        elev_units=elev_units,
        XSEC_NAME=xsec,
        adjustDist=offset
    )
    arcpy.management.Delete([locatedEvents,locatedEvents_sort,eventsTable])
    return profilePath

if __name__ == "__main__":
    uf.management.AddMsgAndPrint(" -- Pre-Cross-Section Checks -- ")
    lines1 = arcpy.GetParameterAsText(0)
    allValues = uf.management.unique_values(table=lines1, field="XSEC")
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
        outFDS = os.path.join(arcpy.GetParameterAsText(4),FDSname)
        if not arcpy.Exists(outFDS):
            arcpy.management.CreateFeatureDataset(arcpy.GetParameterAsText(4),FDSname,unknown)
    for xsec in allValues:
        uf.management.AddMsgAndPrint("PROCESSING {}...".format(xsec))
        rasterPolys = arcpy.ValueTable(2)
        rasterPolys.loadFromString(arcpy.GetParameterAsText(1))
        for i in range(0,rasterPolys.rowCount):
            raster = rasterPolys.getValue(i,0)
            polygon = rasterPolys.getValue(i,1)
            uf.management.AddMsgAndPrint(" - Processing {}: {}...".format(raster,polygon))
            surfRaster = uf.xsec.rasterProject_GeoProj(
                surfRaster=raster,
                lines=lines1,
                scratchDir=scratchDir
            )
            allValues = uf.management.unique_values(table=lines1, field="XSEC")
            demSR = arcpy.Describe(surfRaster).spatialReference
            linesSR = arcpy.Describe(lines1).spatialReference
            polySR = arcpy.Describe(polygon).spatialReference
            if demSR.linearUnitName == linesSR.linearUnitName:
                lines = lines1
            else:
                newLines = os.path.join(scratchDir, "XSEC_Lines_Projection")
                arcpy.management.Project(lines1, newLines, demSR)
                lines = newLines
            if demSR.name == polySR.name:
                copyPoly = polygon
            else:
                try:
                    projectPoly = os.path.join(scratchDir,
                                           "Local_Project_{}".format(os.path.splitext(os.path.basename(polygon))[0]))
                    uf.management.testAndDelete(projectPoly)
                except:
                    projectPoly = os.path.join(scratchDir,
                                           "Project_"+polygon.replace(" ", "_").replace("-", "_").replace("(", "").replace(")",""))
                with arcpy.EnvManager(
                        outputCoordinateSystem=demSR):
                    arcpy.management.CopyFeatures(
                        in_features=polygon,
                        out_feature_class=projectPoly,
                        config_keyword="",
                        spatial_grid_1=None,
                        spatial_grid_2=None,
                        spatial_grid_3=None
                    )
                copyPoly = projectPoly
            try:
                newPoly = os.path.join(scratchDir,"Local_{}".format(os.path.splitext(os.path.basename(polygon))[0]))
                uf.management.testAndDelete(newPoly)
            except:
                newPoly = os.path.join(scratchDir,"Local_"+polygon.replace(" ","_").replace("-","_").replace("(","").replace(")",""))
            arcpy.management.MultipartToSinglepart(
                in_features=copyPoly,
                out_feature_class=newPoly
            )
            linesIntersect = os.path.join(scratchDir, "IntersectionsLINE")
            pointsIntersect = os.path.join(scratchDir, "IntersectionsPOINT")
            xsecFeatureInt = os.path.join(scratchDir,"XSEC_Intersect_{}".format(os.path.splitext(os.path.basename(newPoly))[0]))
            arcpy.management.MakeFeatureLayer(lines, "lineLayers")
            arcpy.management.SelectLayerByAttribute("lineLayers", "NEW_SELECTION", "{}='{}'".format("XSEC", xsec))
            arcpy.management.FeatureToLine(
                in_features=newPoly,
                out_feature_class=linesIntersect,
                cluster_tolerance=None,
                attributes="ATTRIBUTES"
            )
            arcpy.analysis.PairwiseIntersect(
                in_features=["lineLayers", linesIntersect],
                out_feature_class=pointsIntersect,
                join_attributes="ALL",
                cluster_tolerance=None,
                output_type="POINT"
            )
            arcpy.management.MultipartToSinglepart(
                in_features=pointsIntersect,
                out_feature_class=xsecFeatureInt
            )
            if int(arcpy.management.GetCount(xsecFeatureInt)[0]) == 0:
                uf.management.AddMsgAndPrint("RASTER DOES NOT INTERSECT {}. PASSING TO NEXT LINE...".format(xsec))
                arcpy.management.Delete([linesIntersect,pointsIntersect,xsecFeatureInt,newPoly])
            else:
                segProfile = segmentProfiles(
                    xsecLine=lines,
                    xsec=xsec,
                    ve=arcpy.GetParameterAsText(3),
                    raster=surfRaster,
                    elev_units=arcpy.GetParameterAsText(2),
                    polygon=newPoly,
                    outGDB=arcpy.GetParameterAsText(4)
                )
                # Now, to clean up the database for the next cross-section or other steps...
                uf.management.AddMsgAndPrint("Cleaning default geodatabse...")
                arcpy.management.Delete(
                    [os.path.join(scratchDir, "XSEC_{}_zm".format(os.path.splitext(os.path.basename(lines))[0], xsec)),
                     os.path.join(scratchDir, "XSEC_{}_z".format(os.path.splitext(os.path.basename(lines))[0], xsec)),
                     newPoly,linesIntersect,pointsIntersect,xsecFeatureInt])
                xsecMap = prj.listMaps("XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")))[0]
                xsecMap.addDataFromPath(segProfile)
                uf.management.AddMsgAndPrint("-----------------------------")