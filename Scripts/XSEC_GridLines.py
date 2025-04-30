# *****************************************************
# *****************************************************
# XSEC_GridLines.py
# Version: 1.2
# Date: 7/9/2024
# Last Modified Date: 4/30/2025
# Original Author: Matthew Bell, Michigan Geological Survey, matthew.e.bell@wmich.edu
# Description: Command python code to create and place gridded profiles onto a cross-sectional view.
# *****************************************************
# *****************************************************

import arcpy
import os
import numpy as np
import threading
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
version = "XSEC_Gridlines.py, Version 1.2.2"
url = "https://raw.githubusercontent.com/MichiganGeologicalSurvey/Michigan-Geological-Survey-Cross-Section-Tools/refs/heads/Master/Scripts/XSEC_Gridlines.py"
uf.management.githubVersion(
    vString=version,
    rawurl=url
)
uf.management.AddMsgAndPrint("-----------------------------")

def gridProfile(xsecLine,xsecName,elevation,surfRaster,bdrkRaster,maxBH_elev,maxDepthElev,ve,elev_units,dist_units,elev_int,dist_int,outGDB):
    zm_lineSURF,offsetSURF,id_checkField_SURF = uf.xsec.zmLine_Generation(
        lineFeature=xsecLine,
        XSEC_NAME=xsecName,
        defaultGDB=scratchDir,
        raster_surface=surfRaster
    )
    if bdrkRaster == "":
        pass
    else:
        zm_lineBDRK, offsetBDRK, id_checkField_BDRK = uf.xsec.zmLine_Generation(
            lineFeature=xsecLine,
            XSEC_NAME=xsecName,
            defaultGDB=scratchDir,
            raster_surface=bdrkRaster
        )
    topoDesc = arcpy.Describe(zm_lineSURF)
    if bdrkRaster != "":
        bdrkDesc = arcpy.Describe(zm_lineBDRK)
    Xmin = 0
    Xmax = topoDesc.extent.MMax
    if elevation == "Feet":
        if bdrkRaster == "":
            Ymin = (float(maxDepthElev) * 0.3048) * float(ve)
        else:
            Ymin = min(float(maxDepthElev) * 0.3048 * float(ve),float(bdrkDesc.extent.ZMin)* 0.3048 * float(ve))
        Ymax = max(float(maxBH_elev) * 0.3048 * float(ve),float(topoDesc.extent.ZMax) * 0.3048 * float(ve))
    if elevation == "Meters":
        if bdrkRaster == "":
            Ymin = float(maxDepthElev) * float(ve)
        else:
            Ymin = min(float(maxDepthElev) * float(ve),float(bdrkDesc.extent.ZMin) * float(ve))
        Ymax = max(float(maxBH_elev) * float(ve), float(topoDesc.extent.ZMax) * float(ve))
    nameID_Frame = 1
    while True:
        frameName = "XSEC_{}_{}x_Frame_{}_v{}".format(xsecName.replace("-", "_").replace(" ", "_"), ve, elev_units, nameID_Frame)
        framePath = os.path.join(outGDB, "XSEC_{}".format(xsecName.replace("-", "_").replace(" ", "_")), frameName)
        if arcpy.Exists(framePath):
            nameID_Frame = nameID_Frame + 1
        else:
            break
    arcpy.management.CreateFeatureclass(
        out_path=os.path.join(outGDB, "XSEC_{}".format(xsecName.replace("-", "_").replace(" ", "_"))),
        out_name=frameName,
        geometry_type="POLYLINE",
        spatial_reference=unknown
    )
    arcpy.management.AddField(framePath,"TYPE","TEXT",field_length=100)
    arcpy.management.AddField(framePath, "LABEL", "TEXT", field_length=100)
    outRows = arcpy.da.InsertCursor(framePath,["TYPE","LABEL","SHAPE@"])

    nameID_Labels = 1
    while True:
        labelName = "XSEC_{}_{}x_Labels_{}_v{}".format(xsecName.replace("-", "_").replace(" ", "_"), ve, elev_units,
                                                      nameID_Labels)
        labelPath = os.path.join(outGDB, "XSEC_{}".format(xsecName.replace("-", "_").replace(" ", "_")), labelName)
        if arcpy.Exists(labelPath):
            nameID_Labels = nameID_Labels + 1
        else:
            break
    arcpy.management.CreateFeatureclass(
        out_path=os.path.join(outGDB, "XSEC_{}".format(xsecName.replace("-", "_").replace(" ", "_"))),
        out_name=labelName,
        geometry_type="POINT",
        spatial_reference=unknown
    )
    arcpy.management.AddField(labelPath, "TYPE", "TEXT", field_length=100)
    arcpy.management.AddField(labelPath, "LABEL", "TEXT", field_length=100)
    labelRows = arcpy.da.InsertCursor(labelPath, ["TYPE", "LABEL", "SHAPE@"])

    # Now we begin to set up the frame and labels...
    if elev_units == "Meters":
        yBot = uf.xsec.round2int(
            x=(Ymin/float(ve)),
            base=float(elev_int)
        )
        if int(Ymin/float(ve)) < yBot:
            newYmin = (yBot * float(ve)) - (int(elev_int)*float(ve))
        else:
            newYmin = yBot * float(ve)
    if elev_units == "Feet":
        yBot = uf.xsec.round2int(
            x=(Ymin / float(ve))/0.3048,
            base=float(elev_int)
        )
        if int((Ymin / float(ve))/0.3048) < yBot:
            newYmin = (yBot * 0.3048 * float(ve)) - (int(elev_int) * 0.3048 * float(ve))
        else:
            newYmin = yBot * float(ve) * 0.3048

    # Now we need to define the minimum and maximum elevation and distance tick marks.
    # Elevation first...
    elevList = []
    if elev_units == "Meters":
        elevTickMin = uf.xsec.round2int(
            x=newYmin//float(ve),
            base=float(elev_int)
        )
        elevTickMax = uf.xsec.round2int(
            x=Ymax // float(ve),
            base=float(elev_int)
        )
        if (elevTickMax * float(ve)) < Ymax:
            newElevTickMax = elevTickMax + int(elev_int)
            newYmax = (elevTickMax * float(ve)) + (float(elev_int) * float(ve))
            elevList = np.arange(elevTickMin, newElevTickMax + 1, float(elev_int))
        else:
            newElevTickMax = elevTickMax
            newYmax = (elevTickMax * float(ve))
            elevList = np.arange(elevTickMin, newElevTickMax + 1, float(elev_int))
    elif elev_units == "Feet":
        elevTickMin = uf.xsec.round2int(
            x=(newYmin // float(ve))/0.3048,
            base=float(elev_int)
        )
        elevTickMax = uf.xsec.round2int(
            x=(Ymax // float(ve))/0.3048,
            base=float(elev_int)
        )
        if (elevTickMax * 0.3048 * float(ve)) < Ymax:
            newElevTickMax = elevTickMax + int(elev_int)
            newYmax = (elevTickMax * 0.3048 * float(ve)) + (float(elev_int) * 0.3048 * float(ve))
            elevList = np.arange(elevTickMin, newElevTickMax + 1, float(elev_int))
        else:
            newElevTickMax = elevTickMax
            newYmax = (elevTickMax * 0.3048 * float(ve))
            elevList = np.arange(elevTickMin, newElevTickMax + 1, float(elev_int))


    # Distance now...
    distList = []
    if dist_units == "Meters":
        distTickMin = uf.xsec.round2int(
            x=Xmin,
            base=float(dist_int)
        )
        distTickMax = uf.xsec.round2int(
            x=Xmax,
            base=float(dist_int)
        )
        if distTickMax > Xmax:
            newDistTickMax = distTickMax - float(dist_int)
            distList = np.arange(distTickMin, newDistTickMax + 1, float(dist_int))
        elif distTickMax < Xmax:
            newDistTickMax = distTickMax
            distList = np.arange(distTickMin, newDistTickMax + 1, float(dist_int))
        elif distTickMax == Xmax:
            newDistTickMax = distTickMax
            distList = np.arange(distTickMin, newDistTickMax + 1, float(dist_int))
    elif dist_units == "Kilometers":
        distTickMin = uf.xsec.round2int(
            x=Xmin/1000,
            base=float(dist_int)
        )
        distTickMax = uf.xsec.round2int(
            x=Xmax/1000,
            base=float(dist_int)
        )
        if distTickMax > (Xmax/1000):
            newDistTickMax = distTickMax - float(dist_int)
            distList = np.arange(distTickMin, newDistTickMax + 1, float(dist_int))
        elif distTickMax < (Xmax/1000):
            newDistTickMax = distTickMax
            distList = np.arange(distTickMin, newDistTickMax + 1, float(dist_int))
        elif distTickMax == (Xmax/1000):
            newDistTickMax = distTickMax
            distList = np.arange(distTickMin, newDistTickMax + 1, float(dist_int))
    elif dist_units == "Feet":
        distTickMin = uf.xsec.round2int(
            x=Xmin/0.3048,
            base=float(dist_int)
        )
        distTickMax = uf.xsec.round2int(
            x=Xmax/0.3048,
            base=float(dist_int)
        )
        if distTickMax > (Xmax/0.3048):
            newDistTickMax = distTickMax - float(dist_int)
            distList = np.arange(distTickMin, newDistTickMax + 1, float(dist_int))
        elif distTickMax < (Xmax/0.3048):
            newDistTickMax = distTickMax
            distList = np.arange(distTickMin, newDistTickMax + 1, float(dist_int))
        elif distTickMax == (Xmax/0.3048):
            newDistTickMax = distTickMax
            distList = np.arange(distTickMin, newDistTickMax + 1, float(dist_int))
    elif dist_units == "Miles":
        distTickMin = uf.xsec.round2int(
            x=(Xmin//0.3048)/5280,
            base=float(dist_int)
        )
        distTickMax = uf.xsec.round2int(
            x=(Xmax//0.3048)/5280,
            base=float(dist_int)
        )
        if distTickMax > ((Xmax/0.3048)/5280):
            newDistTickMax = distTickMax - float(dist_int)
            distList = np.arange(distTickMin, newDistTickMax + 1, float(dist_int))
        elif distTickMax < ((Xmax/0.3048)/5280):
            newDistTickMax = distTickMax
            distList = np.arange(distTickMin, newDistTickMax + 1, float(dist_int))
        elif distTickMax == ((Xmax/0.3048)/5280):
            newDistTickMax = distTickMax
            distList = np.arange(distTickMin, newDistTickMax + 1, float(dist_int))

    # Now that we have the lists of points in the area, let's build the tick marks...
    # Elevation...
    for y in elevList:
        if elev_units == "Feet":
            yVE = y * 0.3048 *float(ve)
        elif elev_units == "Meters":
            yVE = y * float(ve)
        leftpnt = (Xmin, yVE)
        rightpnt = (Xmax,yVE)
        outRows.insertRow(["ELEVATION MARK",str(y),[leftpnt,rightpnt]])

    # Distance...
    for x in distList:
        if dist_units == "Meters":
            distpnt1 = (x, newYmin)
            distpnt2 = (x, newYmax)
        elif dist_units == "Kilometers":
            distpnt1 = (x * 1000, newYmin)
            distpnt2 = (x * 1000, newYmax)
        elif dist_units == "Feet":
            distpnt1 = (x * 0.3048, newYmin)
            distpnt2 = (x * 0.3048, newYmax)
        elif dist_units == "Miles":
            distpnt1 = ((x * 5280) * 0.3048, newYmin)
            distpnt2 = ((x * 5280) * 0.3048, newYmax)
        outRows.insertRow(["DISTANCE MARK",str(x),[distpnt1,distpnt2]])

    # Setting up the frame border...
    array = []
    array.append((Xmin, newYmax))
    array.append((Xmin, newYmin))
    array.append((Xmax, newYmin))
    array.append((Xmax, newYmax))
    array.append((Xmin, newYmax))
    outRows.insertRow(["FRAME","",array])

    del outRows

    # Now we need to build the label points feature class using the same parameters as the frame.
    # Elevation...
    for y in elevList:
        if elev_units == "Feet":
            yVE = y * 0.3048 * float(ve)
        elif elev_units == "Meters":
            yVE = y * float(ve)
        elevPnt = [Xmin,yVE]
        labelRows.insertRow(["ELEVATION MARK",str(int(y)),elevPnt])

    # Distance...
    for x in distList:
        if dist_units == "Meters":
            distPnt = [x,newYmin]
        elif dist_units == "Kilometers":
            distPnt = [x * 1000,newYmin]
        elif dist_units == "Feet":
            distPnt = [x * 0.3048,newYmin]
        elif dist_units == "Miles":
            distPnt = [(x * 5280) * 0.3048, newYmin]
        labelRows.insertRow(["DISTANCE MARK",str(int(x)),distPnt])

    return framePath, labelPath

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

    # Now we can implement the grids...
    for xsec in allValues:
        extentGrid = arcpy.ValueTable(2)
        extentGrid.loadFromString(arcpy.GetParameterAsText(3))
        for i in range(0,extentGrid.rowCount):
            elevMax = extentGrid.getValue(0,0)
            elevMin = extentGrid.getValue(0,1)
        elevTop = elevMax
        elevBot = elevMin
        gridOption = arcpy.ValueTable(4)
        gridOption.loadFromString(arcpy.GetParameterAsText(5))
        for i in range(0,gridOption.rowCount):
            uf.management.AddMsgAndPrint("PROCESSING {}...".format(xsec))
            yInt = gridOption.getValue(i,0)
            yUnits = gridOption.getValue(i,1)
            xInt = gridOption.getValue(i, 2)
            xUnits = gridOption.getValue(i, 3)
            uf.management.AddMsgAndPrint(
                " ** Distance Units: {} {}\n ** Elevation Units: {} {}".format(xInt, xUnits, yInt,
                                                                               yUnits))

            frame, labels = gridProfile(
                xsecLine=lines,
                xsecName=xsec,
                elevation=arcpy.GetParameterAsText(1),
                surfRaster=arcpy.GetParameterAsText(2),
                bdrkRaster="",
                maxBH_elev=elevTop,
                maxDepthElev=elevBot,
                ve=arcpy.GetParameterAsText(4),
                elev_units=yUnits,
                dist_units=xUnits,
                elev_int=yInt,
                dist_int=xInt,
                outGDB=arcpy.GetParameterAsText(6)
            )
            # Now, to clean up the database for the next cross-section or other steps...
            uf.management.AddMsgAndPrint("Cleaning default geodatabse...")
            arcpy.management.Delete(
                [os.path.join(scratchDir, "XSEC_{}_zm_{}".format(xsec,os.path.splitext(os.path.basename(lines))[0])),
                 os.path.join(scratchDir, "XSEC_{}_z".format(xsec))])
            arcpy.management.DeleteField(lines, ["ROUTEID",
                                                 "{}_{}_ID".format(os.path.splitext(os.path.basename(lines))[0], xsec)])
            xsecMap = prj.listMaps("XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")))[0]
            xsecMap.addDataFromPath(frame)
            xsecMap.addDataFromPath(labels)

            # We can add some symbology to this as well...
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
                uf.management.AddMsgAndPrint("Could not complete labels and symbology.\nError Message: {}.\nPassing to final steps...".format(e),1)
                pass

            extentLyr = xsecMap.listLayers(os.path.splitext(os.path.basename(labels))[0])[0]
            xsecMap.defaultCamera.setExtent(arcpy.Describe(extentLyr).extent)
            prj.save()
            uf.management.AddMsgAndPrint("-----------------------------")