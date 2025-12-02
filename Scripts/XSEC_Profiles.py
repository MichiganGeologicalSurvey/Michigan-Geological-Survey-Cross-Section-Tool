# *****************************************************
# *****************************************************
# XSEC_Profiles.py
# Version: 1.2
# Date: 7/9/2024
# Last Modified Date: 12/2/2025
# Original Author: Matthew Bell, Michigan Geological Survey, matthew.e.bell@wmich.edu
# Description: Command python code to create and place profiles onto a cross-sectional view.
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
version = "XSEC_Profiles.py, Version 1.2.6"
url = "https://raw.githubusercontent.com/MichiganGeologicalSurvey/Michigan-Geological-Survey-Cross-Section-Tool/refs/heads/Master/Scripts/XSEC_Profiles.py"
uf.management.githubVersion(
    vString=version,
    rawurl=url
)
uf.management.AddMsgAndPrint("-----------------------------")

def profileViews(xsecLine,xsecName,raster,ve,elev_units,outGDB):
    zm_line,offset,id_checkField = uf.xsec.zmLine_Generation(
        lineFeature=xsecLine,
        XSEC_NAME=xsecName,
        defaultGDB=scratchDir,
        raster_surface=raster
    )
    nameID = 1
    while True:
        profileName = "XSEC_{}_{}_{}x_v{}".format(
            xsecName.replace("-", "_").replace(" ", "_"),
            os.path.splitext(os.path.basename(raster))[0],
            ve,
            nameID)
        profilePath = os.path.join(outGDB, "XSEC_{}".format(xsecName.replace("-", "_").replace(" ", "_")), profileName)
        if arcpy.Exists(profilePath):
            nameID = nameID +1
        else:
            break
    arcpy.management.CreateFeatureclass(
        os.path.join(outGDB,"XSEC_{}".format(xsecName.replace("-", "_").replace(" ", "_"))),
        profileName,"POLYLINE",zm_line,spatial_reference=unknown
    )
    uf.xsec.plan2side(
        zm_line=zm_line,
        ve=ve,
        profile=profilePath,
        id_field=id_checkField,
        elev_units=elev_units,
        XSEC_NAME=xsecName
    )
    return profilePath

if __name__ == "__main__":
    uf.management.AddMsgAndPrint(" -- Pre-Cross-Section Checks -- ")
    lines1 = arcpy.GetParameterAsText(0)
    allValues = uf.management.unique_values(table=lines1,field="XSEC")
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
    rasterList = arcpy.GetParameterAsText(1).split(";")
    for xsec in allValues:
        uf.management.AddMsgAndPrint("PROCESSING {}...".format(xsec))
        for raster in rasterList:
            uf.management.AddMsgAndPrint(" - Processing {}...".format(raster))
            surfRaster = uf.xsec.rasterProject_GeoProj(
                surfRaster=raster,
                lines=lines1,
                scratchDir=scratchDir
            )
            allValues = uf.management.unique_values(table=lines1, field="XSEC")
            demSR = arcpy.Describe(surfRaster).spatialReference
            linesSR = arcpy.Describe(lines1).spatialReference
            if demSR.name == linesSR.name:
                lines = lines1
            else:
                newLines = os.path.join(scratchDir, "XSEC_Lines_Projection")
                arcpy.management.Project(lines1, newLines, demSR)
                lines = newLines
            profile_view = profileViews(
                xsecLine=lines,
                xsecName=xsec,
                raster=surfRaster,
                ve=arcpy.GetParameterAsText(3),
                elev_units=arcpy.GetParameterAsText(2),
                outGDB=arcpy.GetParameterAsText(4)
            )
            # Now, to clean up the database for the next cross-section or other steps...
            uf.management.AddMsgAndPrint("Cleaning default geodatabse...")
            arcpy.management.Delete([os.path.join(scratchDir,"XSEC_{}_zm".format(os.path.splitext(os.path.basename(lines))[0],xsec)),
                                     os.path.join(scratchDir,"XSEC_{}_z".format(os.path.splitext(os.path.basename(lines))[0],xsec))])
            arcpy.management.DeleteField(lines,["ROUTEID","{}_{}_ID".format(os.path.splitext(os.path.basename(lines))[0],xsec)])
            xsecMap = prj.listMaps("XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")))[0]
            xsecMap.addDataFromPath(profile_view)
            uf.management.AddMsgAndPrint("-----------------------------")