# *****************************************************
# *****************************************************
# XSEC_GammaRay.py
# Version: 1.2
# Date: 7/9/2024
# Last Modified Date: 12/2/2025
# Original Author: Matthew Bell, Michigan Geological Survey, matthew.e.bell@wmich.edu
# Description: Command python code to create and project gamma ray data from wells onto a cross-sectional view.
# *****************************************************
# *****************************************************

import arcpy
import os
import Utility_Functions as uf
import pandas as pd

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
version = "XSEC_GammaRay.py, Version 1.2.6"
url = "https://raw.githubusercontent.com/MichiganGeologicalSurvey/Michigan-Geological-Survey-Cross-Section-Tool/refs/heads/Master/Scripts/XSEC_GammaRay.py"
uf.management.githubVersion(
    vString=version,
    rawurl=url
)
uf.management.AddMsgAndPrint("-----------------------------")

def gammaRay(lineFeature,xsec,surfDEM,elev_units,elev_field,well_points,wellid,wellidField,lasFile,buff,depthUnits,runAvg,ve,he,outGDB):
    zm_line, offset, id_checkField = uf.xsec.zmLine_Generation(
        lineFeature=lineFeature,
        XSEC_NAME=xsec,
        defaultGDB=scratchDir,
        raster_surface=surfDEM
    )
    uf.management.AddMsgAndPrint(" - Generating table from Excel file...")
    df = pd.read_excel(lasFile)
    df = df.sort_values(by=["DEPTH"])
    df = df[df["DATA"] > -998]
    df = df.reset_index(drop=True)
    df.insert(0, "WELLID", wellid, True)
    if runAvg != 0:
        df["AVG{}_DATA".format(runAvg)] = df["DATA"].rolling(window=int(runAvg), min_periods=2, center=True).mean()
        viewField = "AVG{}_DATA".format(runAvg)
    else:
        viewField = "DATA"
    wellidnew = wellid.replace(" ", "_").replace("-", "_")
    df.to_csv(os.path.join(os.path.dirname(scratchDir), "GammaRay_Table_{}.csv".format(os.path.splitext(os.path.basename(lasFile))[0].replace("-","_").replace(" ","_"))), index=False)
    gammaRayTable = os.path.join(scratchDir,"GammaRay_Table_{}".format(os.path.splitext(os.path.basename(lasFile))[0].replace("-","_").replace(" ","_")))
    arcpy.conversion.TableToTable(
        in_rows=os.path.join(os.path.dirname(scratchDir), "GammaRay_Table_{}.csv".format(os.path.splitext(os.path.basename(lasFile))[0].replace("-","_").replace(" ","_"))),
        out_path=scratchDir,
        out_name="GammaRay_Table_{}".format(os.path.splitext(os.path.basename(lasFile))[0].replace("-","_").replace(" ","_"))
    )
    #gammaRayTable = uf.xsec.gammaRayDisplay_Table(
    #    las=lasFile,
    #    defaultGDB=scratchDir,
    #    wellid=wellid,
    #    depthUnits=depthUnits
    #)
    with arcpy.da.UpdateCursor(gammaRayTable,[viewField,"DEPTH"]) as cursor:
        for row in cursor:
            if row[0] < -998:
                cursor.deleteRow()
        del row, cursor
    with arcpy.da.UpdateCursor(gammaRayTable,[viewField,"DEPTH"]) as cursor:
        for row in cursor:
            if depthUnits != elev_units:
                if elev_units == "Feet":
                    row[1] = row[1] / 0.3048
                elif elev_units == "Meters":
                    row[1] = row[1] * 0.3048
                cursor.updateRow(row)
        del row, cursor
    with arcpy.da.SearchCursor(gammaRayTable,[viewField,"DEPTH"]) as cursor:
        countvalues = []
        depthvalues = []
        for row in cursor:
            countvalues.append(row[0])
            depthvalues.append(row[1])
        maxDepth = max(depthvalues)
        del row, cursor
    well_near = arcpy.management.SelectLayerByLocation(
        in_layer=well_points,
        overlap_type="WITHIN_A_DISTANCE",
        select_features=zm_line,
        search_distance=buff
    )
    zWells = "XSEC_{}_zWells".format(xsec)
    arcpy.management.CopyFeatures(well_near, zWells)
    zField = elev_field

    arcpy.management.SelectLayerByAttribute(well_points, "CLEAR_SELECTION")
    rProps = "rkey POINT M fmp"
    eventTableWells = uf.xsec.locateEvents_Table(
        pts=zWells,
        XSEC_NAME=xsec,
        defaultGDB=scratchDir,
        route_line=zm_line,
        checkField=id_checkField,
        sel_dist=buff,
        event_props=rProps
    )
    eventLayerWells = "XSEC_{}_Events".format(xsec)
    arcpy.lr.MakeRouteEventLayer(zm_line, id_checkField, eventTableWells, rProps, eventLayerWells, "#", "#",
                                 "ANGLE_FIELD", "TANGENT")
    locPoints = os.path.join(scratchDir, "XSEC_{}_wellsLocated".format(xsec))
    arcpy.management.CopyFeatures(eventLayerWells, locPoints)
    arcpy.management.AddField(locPoints, "DistFromSection", "DOUBLE")
    arcpy.management.AddField(locPoints, "LocalXSEC_Azimuth", "DOUBLE")
    arcpy.management.AddField(locPoints, "GAMMA_DEPTH", "DOUBLE")
    with arcpy.da.UpdateCursor(locPoints,[wellidField,"GAMMA_DEPTH"]) as cursor:
        for rowM in cursor:
            if rowM[0] == wellid:
                rowM[1] = maxDepth
                cursor.updateRow(rowM)
            else:
                pass
        del cursor
    bhLine = uf.xsec.boreholes(
        locatedPoints=locPoints,
        XSEC_NAME=xsec,
        defaultGDB=scratchDir,
        elev_field=zField,
        depth_field="GAMMA_DEPTH",
        elev_units=elev_units,
        ve=ve
    )
    nameID = 1
    while True:
        gammaRaySName = "XSEC_{}_GammaStick_{}_{}vx_{}hx_v{}".format(xsec.replace("-", "_").replace(" ", "_"), wellid.replace("-","").replace(" ","").replace(".",""),ve,he, nameID)
        gammaLogStick = os.path.join(outGDB, "XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")), gammaRaySName)
        if arcpy.Exists(gammaLogStick):
            nameID = nameID + 1
        else:
            break
    arcpy.management.CopyFeatures(bhLine, gammaLogStick)
    profilenameID = 1
    while True:
        gammaRayPName = "XSEC_{}_GammaProfile_{}_{}vx_{}hx_v{}".format(xsec.replace("-", "_").replace(" ", "_"), wellid.replace("-","").replace(" ","").replace(".",""),ve,he, nameID)
        gammaLogProfile = os.path.join(outGDB, "XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")), gammaRayPName)
        if arcpy.Exists(gammaLogProfile):
            profilenameID = profilenameID + 1
        else:
            break
    arcpy.management.CreateFeatureclass(
        os.path.join(outGDB, "XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_"))),
        gammaRayPName, "POLYLINE", locPoints, "DISABLED", "SAME_AS_TEMPLATE")
    uf.management.AddMsgAndPrint(" - Placing gamma ray log for {}".format(wellid))
    lf = arcpy.ListFields(locPoints)
    flds = [f.name for f in lf if f.type != "Geometry"]
    flds.append("SHAPE@")

    tRows = arcpy.da.SearchCursor(locPoints, flds)
    gRows = arcpy.da.SearchCursor(gammaRayTable,[viewField,"DEPTH"])
    cur = arcpy.da.InsertCursor(gammaLogProfile, flds)
    oidName = [f.name for f in lf if f.type == "OID"][0]
    oid_i = tRows.fields.index(oidName)
    elevID = tRows.fields.index(elev_field)

    for data in tRows:
        if data[tRows.fields.index(wellidField)] == wellid:
            topElev = data[elevID]
            mRoute = data[tRows.fields.index("M")]
            gammaArray = []
            for row in gRows:
                X = (float(row[0]) * float(he)) + mRoute
                if elev_units == "Meters":
                    Y = (float(topElev) - float(row[1])) * float(ve)
                if elev_units == "Feet":
                    Y = ((float(topElev) - float(row[1])) * 0.3048) * float(ve)
                gammaArray.append((X, Y))
            #uf.management.AddMsgAndPrint("{}".format(gammaArray))
            vals = list(data).copy()
            vals[tRows.fields.index("SHAPE@")] = gammaArray
            try:
                cur.insertRow(vals)
                gammaArray.clear()
            except Exception as e:
                uf.management.AddMsgAndPrint(
                    "Could not create feature from objectid {} in {}".format(row[oid_i], locPoints), 1)
                uf.management.AddMsgAndPrint(e)

    return gammaLogStick,gammaLogProfile

if __name__ == "__main__":
    lines = arcpy.GetParameterAsText(0)
    allValues = uf.management.unique_values(table=lines,field="XSEC")
    surfRaster = uf.xsec.rasterProject_GeoProj(
        surfRaster=arcpy.GetParameterAsText(2),
        lines=lines,
        scratchDir=scratchDir
    )
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
        outFDS = os.path.join(arcpy.GetParameterAsText(10),FDSname)
        if not arcpy.Exists(outFDS):
            arcpy.management.CreateFeatureDataset(arcpy.GetParameterAsText(10),FDSname,unknown)
    wells = arcpy.GetParameterAsText(3)
    wellidField = arcpy.GetParameterAsText(4)
    gammaData = arcpy.ValueTable(5)
    gammaData.loadFromString(arcpy.GetParameterAsText(6))
    for xsec in allValues:
        uf.management.AddMsgAndPrint("PROCESSING {}...".format(xsec))
        for i in range(0,gammaData.rowCount):
            wellid = gammaData.getValue(i,0)
            lasFile = gammaData.getValue(i,1)
            depthUnits = gammaData.getValue(i,2)
            runAvg_Question = gammaData.getValue(i,3)
            runAvg = gammaData.getValue(i,4)
            uf.management.AddMsgAndPrint(" - Processing {}...".format(wellid))
            if (runAvg_Question == "false" or runAvg_Question == ""):
                newRun = 0
            else:
                newRun = runAvg
            wellFeature = os.path.join(scratchDir,"{}_GAMMA_POINT".format(wellid.replace("-","_").replace(" ","")))
            arcpy.conversion.ExportFeatures(
                in_features=wells,
                out_features=wellFeature,
                where_clause="{} = '{}'".format(wellidField,wellid),
                use_field_alias_as_name="NOT_USE_ALIAS",
                sort_field=None
            )
            gammaStick, gammaRayPlot = gammaRay(
                lineFeature=lines,
                xsec=xsec,
                surfDEM=surfRaster,
                elev_units=arcpy.GetParameterAsText(1),
                elev_field=arcpy.GetParameterAsText(5),
                well_points=wellFeature,
                wellid=wellid,
                wellidField=wellidField,
                lasFile=lasFile,
                buff=arcpy.GetParameterAsText(7),
                depthUnits=depthUnits,
                ve=arcpy.GetParameterAsText(8),
                he=arcpy.GetParameterAsText(9),
                outGDB=arcpy.GetParameterAsText(10),
                runAvg=newRun
            )
            # Now, to clean up the database for the next cross-section or other steps...
            uf.management.AddMsgAndPrint("Cleaning default geodatabse...")
            arcpy.management.Delete(
                [os.path.join(scratchDir, "XSEC_{}_zm".format(os.path.splitext(os.path.basename(lines))[0], xsec)),
                 os.path.join(scratchDir, "XSEC_{}_z".format(os.path.splitext(os.path.basename(lines))[0], xsec)),
                 wellFeature])
            arcpy.management.DeleteField(lines,
                                         ["ROUTEID",
                                          "{}_{}_ID".format(os.path.splitext(os.path.basename(lines))[0], xsec)])
            xsecMap = prj.listMaps("XSEC_{}".format(xsec.replace("-", "_").replace(" ", "_")))[0]
            if float(arcpy.management.GetCount(gammaStick)[0]) == 0:
                uf.management.AddMsgAndPrint(
                    "**{} did not intersect line {}. Deleting feature class...".format(wellid,xsec))
                arcpy.management.Delete([gammaStick,gammaRayPlot])
            else:
                xsecMap.addDataFromPath(gammaStick)
                xsecMap.addDataFromPath(gammaRayPlot)
            uf.management.AddMsgAndPrint("-----------------------------")