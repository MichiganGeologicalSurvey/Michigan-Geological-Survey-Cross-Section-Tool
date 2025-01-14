# *****************************************************
# *****************************************************
# ProjectCreation.py
# Version: 2.0
# Date: 7/26/2024
# Last Modified Date: 7/26/2024
# Original Author: Matthew Bell, Michigan Geological Survey, matthew.e.bell@wmich.edu
# Description: A Python custom script to reformat Wellogic data or other datasets into a format reviewed by the
# Michigan Geological Survey. This also formats data into a project-specific area.
# *****************************************************
# *****************************************************

import os
import arcpy
import io
import zipfile
import requests
import datetime
import Utility_Functions as uf
import Dictonary
import DataFormatting
import GWL_RasterCreation

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

def projectCreation(projectName,projectLoc,state,standard_no,siteData,dem,customRange):
    uf.management.AddMsgAndPrint("_____________________________")
    uf.management.AddMsgAndPrint("BEGIN CREATING THE WORKSPACE WITH THE APPROPRIATE DATASETS...")
    uf.management.AddMsgAndPrint(" - Adding in the required geodatabases for the project...")
    arcpy.management.CreateFileGDB(projectLoc,projectName,"CURRENT")
    cultureGDB = os.path.join(projectLoc,projectName + ".gdb")
    arcpy.management.CreateFeatureDataset(cultureGDB,"Culture",src)

    arcpy.management.CreateFileGDB(projectLoc,projectName + "_Geology","CURRENT")
    geologyGDB = os.path.join(projectLoc,projectName + "_Geology.gdb")

    arcpy.management.CreateFileGDB(projectLoc,"Scratch","CURRENT")
    arcpy.management.CreateFileGDB(projectLoc,"Rasters","CURRENT")
    arcpy.management.CreateFileGDB(projectLoc,"001_CrossSectionFiles","CURRENT")

    domainNames = ["QGEOLOGY","ROADS","DIRECTIONS","Verification"]
    desc = arcpy.Describe(geologyGDB)
    domains = desc.domains
    for domain in domains:
        if domain in domainNames:
            try:
                arcpy.management.DeleteDomain(in_workspace=geologyGDB,domain_name=domain)
            except:
                uf.management.AddMsgAndPrint("Domain in use. Passing to next step...")
                pass
    if "QGEOLOGY" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB, "QGEOLOGY", "Names of Quaternary surficial geology units based off of the Farrand & Bell (1987) surficial map", "TEXT",
                                      "CODED")
        for code in Dictonary.qGeology:
            arcpy.management.AddCodedValueToDomain(geologyGDB, "QGEOLOGY", code, Dictonary.qGeology[code])
    if "ROADS" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"ROADS", "Segment names for designated NFC road classifications","TEXT", "CODED")
        for code in Dictonary.roadCodes:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"ROADS",code,Dictonary.roadCodes[code])
    if "DIRECTIONS" in domains:
        pass
    else:
        arcpy.management.CreateDomain(cultureGDB,"DIRECTIONS", "Accepted direction orientations for cross-section lines","TEXT", "CODED")
        for code in Dictonary.directions:
            arcpy.management.AddCodedValueToDomain(cultureGDB,"DIRECTIONS",code,Dictonary.directions[code])
    if "Verification" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"Verification", "Verification of data quality","TEXT", "CODED")
        for code in Dictonary.verification:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"Verification",code,Dictonary.verification[code])

    uf.management.AddMsgAndPrint(" - Adding in the required folders for the project...")
    arcpy.management.CreateFolder(projectLoc, "Scratch")
    arcpy.management.CreateFolder(projectLoc, "PDF_Documents")
    arcpy.management.CreateFolder(projectLoc, "WaterWells")
    arcpy.management.CreateFolder(projectLoc, "StateWide_Files")
    statewideLoc = os.path.join(projectLoc, "StateWide_Files")

    # Now we get to download and extract all the datasets we would need for a project...
    # All data is provided by the USGS mapping service. This can apply to any state.
    uf.management.AddMsgAndPrint(" - Downloading and extracting state-wide datasets...")
    stateAbbrev = Dictonary.stateAbbr.get(state,None)
    govUnitsURL = "https://prd-tnm.s3.amazonaws.com/StagedProducts/GovtUnit/GDB/GOVTUNIT_{}_State_GDB.zip".format(state.replace(" ","_"))
    transURL = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Tran/GDB/TRAN_{}_State_GDB.zip".format(state.replace(" ","_"))
    hydroURL = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/State/GDB/NHD_H_{}_State_GDB.zip".format(state.replace(" ","_"))
    schoolsURL = "https://carto.nationalmap.gov/arcgis/rest/services/structures/MapServer/58"
    collegesURL = "https://carto.nationalmap.gov/arcgis/rest/services/structures/MapServer/56"
    qGeologyURL = "https://gisagocss.state.mi.us/arcgis/rest/services/OpenData/geology/MapServer/5"
    bdrkGeologyURL = "https://gisagocss.state.mi.us/arcgis/rest/services/OpenData/geology/MapServer/0"

    req1 = requests.get(govUnitsURL)
    unzip1 = zipfile.ZipFile(io.BytesIO(req1.content))
    unzip1.extractall(statewideLoc)

    req2 = requests.get(transURL)
    unzip2 = zipfile.ZipFile(io.BytesIO(req2.content))
    unzip2.extractall(statewideLoc)

    req3 = requests.get(hydroURL)
    unzip3 = zipfile.ZipFile(io.BytesIO(req3.content))
    unzip3.extractall(statewideLoc)

    arcpy.conversion.ExportFeatures(
        in_features=schoolsURL,
        out_features=os.path.join(statewideLoc,"Schools.shp"),
        where_clause="STATE = '{}'".format(stateAbbrev)
    )
    arcpy.conversion.ExportFeatures(
        in_features=collegesURL,
        out_features=os.path.join(statewideLoc,"Colleges.shp"),
        where_clause="STATE = '{}'".format(stateAbbrev)
    )
    if state == "Michigan":
        onlineBedrock = "https://gisagocss.state.mi.us/arcgis/rest/services/OpenData/geology/MapServer/0"
        onlineQuaternary = "https://gisagocss.state.mi.us/arcgis/rest/services/OpenData/geology/MapServer/5"
        arcpy.conversion.ExportFeatures(
            in_features=onlineBedrock,
            out_features=os.path.join(statewideLoc, "Bedrock_Geology.shp")
        )
        arcpy.conversion.ExportFeatures(
            in_features=onlineQuaternary,
            out_features=os.path.join(statewideLoc, "Quaternary_Geology_Map.shp")
        )

    arcpy.management.CreateFeatureclass(
        cultureGDB, "Location", "POINT", None, "DISABLED", "DISABLED",
        'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]];-400 -400 1111948722.22222;-100000 10000;-100000 10000;8.98315284119521E-09;0.001;0.001;IsHighPrecision',
        '', 0, 0, 0, '')
    outLocation = os.path.join(cultureGDB,"Location")
    arcpy.management.AddField(outLocation, "NAME", "TEXT", "", "", "1000", "", "NULLABLE", "NON_REQUIRED", "")
    for i in range(0,siteData.rowCount):
        siteName = siteData.getValue(i,0)
        siteLat = siteData.getValue(i,1)
        siteLong = siteData.getValue(i,2)

        uf.management.AddMsgAndPrint(" * Placing {} at ({}, {}) * ".format(siteName,siteLat,siteLong))
        siteCoords = [siteLong,siteLat]
        x = siteCoords[0]
        y = siteCoords[1]
        point_obj = arcpy.Point(x,y)
        point_obj.X = x
        point_obj.Y = y
        row = [siteName, point_obj]
        with arcpy.da.InsertCursor(outLocation, ["NAME", "SHAPE@"]) as cursor:
            cursor.insertRow(row)
            del cursor
    siteLoc = os.path.join(cultureGDB,"POI_Location")
    arcpy.management.Project(outLocation, siteLoc, src, "WGS_1984_(ITRF00)_To_NAD_1983", 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]', "NO_PRESERVE_SHAPE", None, "NO_VERTICAL")

    uf.management.AddMsgAndPrint(" - Creating the cross-section feature class...")
    arcpy.management.CreateFeatureclass(cultureGDB, "XSEC_Lines", "POLYLINE", None, "DISABLED", "DISABLED", src)
    # Add the appropriate fields for the name and the direction
    outXSEC = os.path.join(cultureGDB, "XSEC_Lines")
    arcpy.management.AddField(outXSEC, "XSEC", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.management.AddField(outXSEC, "DIRECTION", "TEXT", "", "", "5", "", "NULLABLE", "NON_REQUIRED", "")
    # Adding the domain signature for the DIRECTION field
    arcpy.management.AssignDomainToField(outXSEC, "DIRECTION", "DIRECTIONS")

    uf.management.AddMsgAndPrint(" - Determining if multiple rasters are given...")
    rasterName = projectName + "_DEM_ft_FULLEXTENT"
    fullDEM = os.path.join(os.path.join(projectLoc,"Rasters.gdb"),rasterName)
    if 1 < dem.rowCount:
        uf.management.AddMsgAndPrint("   - Mosaic multiple DEM files together...")
        for i in range(0,dem.rowCount):
            demRaster = dem.getValue(i,0)
            elevUnits = dem.getValue(i,1)
            demfeet = os.path.join(scratchDir, os.path.splitext(os.path.basename(demRaster))[0] + "_feet")
            if elevUnits == "Meters":
                outputRaster = arcpy.Raster(demRaster)/0.3048
                outputRaster.save(demfeet)
            if elevUnits == "Feet":
                arcpy.management.CopyRaster(demRaster,demfeet)
        areaDEM = projectName + "_ProjectArea"
        demList = arcpy.ListRasters()
        mosListDEM = ";".join(demList)
        arcpy.management.MosaicToNewRaster(mosListDEM,os.path.join(projectLoc,"Rasters.gdb"),areaDEM,src,"32_BIT_FLOAT",None,1,"LAST","FIRST")
        mosDEM = os.path.join(os.path.join(projectLoc,"Rasters.gdb"),areaDEM)
        arcpy.management.CopyRaster(mosDEM,fullDEM)
        arcpy.management.Delete([mosDEM,mosListDEM])
    else:
        uf.management.AddMsgAndPrint("   - One DEM file given. Copying current DEM...")
        demRaster = dem.getValue(0,0)
        elevUnits = dem.getValue(0,1)
        if elevUnits == "Meters":
            demfeet = os.path.join(scratchDir, os.path.splitext(os.path.basename(demRaster))[0] + "_feet")
            outputRaster = arcpy.Raster(demRaster) / 0.3048
            outputRaster.save(demfeet)
            arcpy.management.CopyRaster(demfeet,fullDEM)
            arcpy.management.Delete(demfeet)
        if elevUnits == "Feet":
            arcpy.management.CopyRaster(demRaster,fullDEM)

    uf.management.AddMsgAndPrint(" - Creating the boundary(s)...")
    if standard_no == "2-5 Mile Project":
        buff2Mile = os.path.join(cultureGDB,"BuffZone_2mile")
        arcpy.analysis.Buffer(
            in_features=siteLoc,
            out_feature_class=buff2Mile,
            buffer_distance_or_field="2 Miles",
            dissolve_option="ALL"
        )
        buff5Mile = os.path.join(cultureGDB, "BuffZone_5mile")
        arcpy.analysis.Buffer(
            in_features=siteLoc,
            out_feature_class=buff5Mile,
            buffer_distance_or_field="5 Miles",
            dissolve_option="ALL"
        )
    if standard_no == "User-Defined Project Area":
        featExtent = os.path.join(cultureGDB,"DEM_Extent")
        arcpy.ddd.RasterDomain(fullDEM,featExtent,"POLYGON")
        buff2Mile = os.path.join(cultureGDB, "BuffZone_2mile")
        arcpy.analysis.Buffer(
            in_features=siteLoc,
            out_feature_class=buff2Mile,
            buffer_distance_or_field="2 Miles",
            dissolve_option="ALL"
        )

    uf.management.AddMsgAndPrint(" - Creating project-area topographic datasets...")
    prjDEM = os.path.join(os.path.join(projectLoc,"Rasters.gdb"),projectName + "_DEM_ft")
    if standard_no == "2-5 Mile Project":
        extractRaster = arcpy.sa.ExtractByMask(fullDEM,buff5Mile)
        extractRaster.save(prjDEM)
    if standard_no == "User-Defined Project Area":
        arcpy.management.CopyRaster(fullDEM,prjDEM)
    uf.management.AddMsgAndPrint("   - Creating hillshade raster of {}...".format(os.path.splitext(os.path.basename(prjDEM))[0]))
    hillName = os.path.join(os.path.join(projectLoc,"Rasters.gdb"),"HILLSHADE")
    arcpy.ddd.HillShade(prjDEM,hillName,315,45,"NO_SHADOWS",1)

    uf.management.AddMsgAndPrint("   - Creating 10 feet contours of {}...".format(os.path.splitext(os.path.basename(prjDEM))[0]))
    contourLines = os.path.join(os.path.join(projectLoc,"Rasters.gdb"),os.path.splitext(os.path.basename(prjDEM))[0] + "_10ft_contours")
    arcpy.sa.Contour(prjDEM,contourLines,10)
    arcpy.management.AddField(contourLines, "CONTOUR_TYPE", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    with arcpy.da.UpdateCursor(contourLines, ["Contour", "CONTOUR_TYPE"]) as cursor:
        for row in cursor:
            if float(row[0] / 50).is_integer():
                row[1] = "INDEX"
            else:
                row[1] = "INTERMEDIATE"
            cursor.updateRow(row)
        del row, cursor
    uf.management.AddMsgAndPrint("   - Creating 20 feet contours of {}...".format(os.path.splitext(os.path.basename(prjDEM))[0]))
    contourLines20 = os.path.join(os.path.join(projectLoc, "Rasters.gdb"),os.path.splitext(os.path.basename(prjDEM))[0] + "_20ft_contours")
    arcpy.sa.Contour(prjDEM, contourLines20, 10)
    arcpy.management.AddField(contourLines20, "CONTOUR_TYPE", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
    with arcpy.da.UpdateCursor(contourLines20, ["Contour", "CONTOUR_TYPE"]) as cursor:
        for row in cursor:
            if float(row[0] / 100).is_integer():
                row[1] = "INDEX"
            else:
                row[1] = "INTERMEDIATE"
            cursor.updateRow(row)
        del row, cursor

    uf.management.AddMsgAndPrint(" - Defining features to project area from StateWide_Files folder...")
    cultureDataset = os.path.join(cultureGDB,"Culture")
    govUnits_statewideLoc = os.path.join(statewideLoc,"GOVTUNIT_{}_State_GDB.gdb".format(state.replace(" ","_")),"GovernmentUnits")
    hydro_statewideLoc = os.path.join(statewideLoc,"NHD_H_{}_State_GDB.gdb".format(state.replace(" ","_")),"Hydrography")
    trans_statewideLoc = os.path.join(statewideLoc,"TRAN_{}_State_GDB.gdb".format(state.replace(" ","_")),"Transportation")

    uf.management.AddMsgAndPrint("   - Clipping appropriate features...")
    roadNames = os.path.join(cultureDataset, projectName + "_Roads")
    lakeNames = os.path.join(cultureDataset, projectName + "_Lakes")
    riverNames = os.path.join(cultureDataset, projectName + "_Rivers")
    schoolNames = os.path.join(cultureDataset, projectName + "_Schools")
    collegeNames = os.path.join(cultureDataset, projectName + "_Colleges")
    railNames = os.path.join(cultureDataset, projectName + "_Railroads")
    if state == "Michigan":
        qGeology = os.path.join(geologyGDB, projectName + "_qGeology")
        bdrkGeology = os.path.join(geologyGDB, projectName + "_bdrkGeology")
    if standard_no == "2-5 Mile Project":
        arcpy.analysis.Clip(os.path.join(trans_statewideLoc,"Trans_RoadSegment"), buff5Mile, roadNames,"")
        arcpy.analysis.Clip(os.path.join(trans_statewideLoc, "Trans_RailFeature"), buff5Mile, railNames, "")
        arcpy.analysis.Clip(os.path.join(hydro_statewideLoc, "NHDFlowline"), buff5Mile, riverNames, "")
        arcpy.analysis.Clip(os.path.join(hydro_statewideLoc, "NHDWaterbody"), buff5Mile, lakeNames, "")
        arcpy.analysis.Clip(schoolsURL, buff5Mile, schoolNames, "")
        arcpy.analysis.Clip(collegesURL, buff5Mile, collegeNames, "")
        if state == "Michigan":
            arcpy.analysis.Clip(qGeologyURL, buff5Mile, qGeology, "")
            arcpy.analysis.Clip(bdrkGeologyURL, buff5Mile, bdrkGeology, "")
        else:
            pass
    if standard_no == "User-Defined Project Area":
        arcpy.analysis.Clip(os.path.join(trans_statewideLoc, "Trans_RoadSegment"), featExtent, roadNames, "")
        arcpy.analysis.Clip(os.path.join(trans_statewideLoc, "Trans_RailFeature"), featExtent, railNames, "")
        arcpy.analysis.Clip(os.path.join(hydro_statewideLoc, "NHDFlowline"), featExtent, riverNames, "")
        arcpy.analysis.Clip(os.path.join(hydro_statewideLoc, "NHDWaterbody"), featExtent, lakeNames, "")
        arcpy.analysis.Clip(schoolsURL, featExtent, schoolNames, "")
        arcpy.analysis.Clip(collegesURL, featExtent, collegeNames, "")
        if state == "Michigan":
            arcpy.analysis.Clip(qGeologyURL, featExtent, qGeology, "")
            arcpy.analysis.Clip(bdrkGeologyURL, featExtent, bdrkGeology, "")
        else:
            pass
    uf.management.AddMsgAndPrint("   - Selecting appropriate features...")
    countyName = projectName + "_Counties"
    townName = projectName + "_TownshipCities"
    townCounties = projectName + "Township_InCounties"
    plssTownName = projectName + "_PLSS_Townships"
    plssSectionName = projectName + "_PLSS_Sections"
    if standard_no == "2-5 Mile Project":
        selectCounties = arcpy.management.SelectLayerByLocation(
            os.path.join(govUnits_statewideLoc,"GU_CountyOrEquivalent"),
            "INTERSECT",
            buff5Mile
        )
        arcpy.conversion.FeatureClassToFeatureClass(selectCounties,cultureDataset,countyName,"","","")
        selectTown = arcpy.management.SelectLayerByLocation(
            os.path.join(govUnits_statewideLoc, "GU_MinorCivilDivision"),
            "INTERSECT",
            buff5Mile
        )
        arcpy.conversion.FeatureClassToFeatureClass(selectTown, cultureDataset, townName, "", "", "")
        selectTownCounties = arcpy.management.SelectLayerByLocation(
            os.path.join(govUnits_statewideLoc, "GU_MinorCivilDivision"),
            "HAVE_THEIR_CENTER_IN",
            os.path.join(cultureDataset,countyName)
        )
        arcpy.conversion.FeatureClassToFeatureClass(selectTownCounties, cultureDataset, townCounties, "", "", "")
        if int(arcpy.management.GetCount(os.path.join(govUnits_statewideLoc, "GU_PLSSTownship"))[0]) > 0:
            arcpy.conversion.FeatureClassToFeatureClass(selectTownCounties, cultureDataset, townCounties, "", "", "")
            selectPLSSTown= arcpy.management.SelectLayerByLocation(
                os.path.join(govUnits_statewideLoc, "GU_PLSSTownship"),
                "HAVE_THEIR_CENTER_IN",
                os.path.join(cultureDataset, townName)
            )
            arcpy.conversion.FeatureClassToFeatureClass(selectPLSSTown, cultureDataset, plssTownName, "", "", "")
            selectPLSSSection = arcpy.management.SelectLayerByLocation(
                os.path.join(govUnits_statewideLoc, "GU_PLSSFirstDivision"),
                "HAVE_THEIR_CENTER_IN",
                os.path.join(cultureDataset, plssTownName)
            )
            arcpy.conversion.FeatureClassToFeatureClass(selectPLSSSection, cultureDataset, plssSectionName, "", "", "")
    if standard_no == "User-Defined Project Area":
        selectCounties = arcpy.management.SelectLayerByLocation(
            os.path.join(govUnits_statewideLoc, "GU_CountyOrEquivalent"),
            "INTERSECT",
            featExtent
        )
        arcpy.conversion.FeatureClassToFeatureClass(selectCounties, cultureDataset, countyName, "", "", "")
        selectTown = arcpy.management.SelectLayerByLocation(
            os.path.join(govUnits_statewideLoc, "GU_MinorCivilDivision"),
            "INTERSECT",
            featExtent
        )
        arcpy.conversion.FeatureClassToFeatureClass(selectTown, cultureDataset, townName, "", "", "")
        selectTownCounties = arcpy.management.SelectLayerByLocation(
            os.path.join(govUnits_statewideLoc, "GU_MinorCivilDivision"),
            "HAVE_THEIR_CENTER_IN",
            os.path.join(cultureDataset, countyName)
        )
        arcpy.conversion.FeatureClassToFeatureClass(selectTownCounties, cultureDataset, townCounties, "", "", "")
        if int(arcpy.management.GetCount(os.path.join(govUnits_statewideLoc, "GU_PLSSTownship"))[0]) > 0:
            arcpy.conversion.FeatureClassToFeatureClass(selectTownCounties, cultureDataset, townCounties, "", "", "")
            selectPLSSTown = arcpy.management.SelectLayerByLocation(
                os.path.join(govUnits_statewideLoc, "GU_PLSSTownship"),
                "HAVE_THEIR_CENTER_IN",
                os.path.join(cultureDataset, townName)
            )
            arcpy.conversion.FeatureClassToFeatureClass(selectPLSSTown, cultureDataset, plssTownName, "", "", "")
            selectPLSSSection = arcpy.management.SelectLayerByLocation(
                os.path.join(govUnits_statewideLoc, "GU_PLSSFirstDivision"),
                "HAVE_THEIR_CENTER_IN",
                os.path.join(cultureDataset, plssTownName)
            )
            arcpy.conversion.FeatureClassToFeatureClass(selectPLSSSection, cultureDataset, plssSectionName, "", "", "")

    if state == "Michigan":
        uf.management.AddMsgAndPrint(" - Downloading and extracting Wellogic data...")
        wwUP_url = "https://gisagocss.state.mi.us/arcgis/rest/services/OpenData/public_health/MapServer/4"
        wwN_LP_url = "https://gisagocss.state.mi.us/arcgis/rest/services/OpenData/public_health/MapServer/5"
        wwWC_LP_url = "https://gisagocss.state.mi.us/arcgis/rest/services/OpenData/public_health/MapServer/6"
        wwSW_LP_url = "https://gisagocss.state.mi.us/arcgis/rest/services/OpenData/public_health/MapServer/7"
        wwEC_LP_url = "https://gisagocss.state.mi.us/arcgis/rest/services/OpenData/public_health/MapServer/8"
        wwSC_SE_LP_url = "https://gisagocss.state.mi.us/arcgis/rest/services/OpenData/public_health/MapServer/9"
        wwLithUrl = "https://gisp.mcgi.state.mi.us/arcgis/rest/services/DEQ/DW_Wells/MapServer/9"

        wwUP_export = os.path.join(scratchDir,"UP_Export")
        wwN_LP_export = os.path.join(scratchDir,"N_LP_Export")
        wwWC_LP_export = os.path.join(scratchDir,"WC_LP_Export")
        wwSW_LP_export = os.path.join(scratchDir,"SW_LP_Export")
        wwEC_LP_export = os.path.join(scratchDir,"EC_LP_Export")
        wwSC_SE_LP_export = os.path.join(scratchDir,"SC_SE_LP_Export")
        wwPoints_export = os.path.join(os.path.join(projectLoc,"WaterWells"),projectName + "_WellPoints.shp")
        wwLith_export = os.path.join(os.path.join(projectLoc,"WaterWells"),projectName + "_lithTable.dbf")

        countyList = []
        with arcpy.da.SearchCursor(os.path.join(cultureDataset, countyName), ["county_name"]) as cursor:
            for row in cursor:
                countyList.append(row[0])
            del row, cursor
        countyCodes_wells = [Dictonary.wellId_county.get(item,item) for item in countyList]
        wwUP_select = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=wwUP_url,
            selection_type="NEW_SELECTION",
            where_clause="COUNTY IN {}".format(countyList).replace("[", "(").replace("]", ")"),
            invert_where_clause=None
        )
        wwN_LP_select = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=wwN_LP_url,
            selection_type="NEW_SELECTION",
            where_clause="COUNTY IN {}".format(countyList).replace("[", "(").replace("]", ")"),
            invert_where_clause=None
        )
        wwWC_LP_select = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=wwWC_LP_url,
            selection_type="NEW_SELECTION",
            where_clause="COUNTY IN {}".format(countyList).replace("[", "(").replace("]", ")"),
            invert_where_clause=None
        )
        wwSW_LP_select = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=wwSW_LP_url,
            selection_type="NEW_SELECTION",
            where_clause="COUNTY IN {}".format(countyList).replace("[", "(").replace("]", ")"),
            invert_where_clause=None
        )
        wwEC_LP_select = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=wwEC_LP_url,
            selection_type="NEW_SELECTION",
            where_clause="COUNTY IN {}".format(countyList).replace("[", "(").replace("]", ")"),
            invert_where_clause=None
        )
        wwSC_SE_LP_select = arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=wwSC_SE_LP_url,
            selection_type="NEW_SELECTION",
            where_clause="COUNTY IN {}".format(countyList).replace("[", "(").replace("]", ")"),
            invert_where_clause=None
        )
        arcpy.management.Merge(
            inputs=[wwUP_select,wwN_LP_select,wwWC_LP_select,wwSW_LP_select,wwEC_LP_select,wwSC_SE_LP_select],
            output=wwPoints_export
        )
        lithFiles = []
        for codes in countyCodes_wells:
            lithTemp = os.path.join(scratchDir,"LithTable_{}".format(codes))
            wwLith_select = arcpy.management.SelectLayerByAttribute(
                in_layer_or_view=wwLithUrl,
                selection_type="NEW_SELECTION",
                where_clause="WELLID LIKE '{}%'".format(codes),
                invert_where_clause=None
            )
            arcpy.management.CopyRows(
                in_rows=wwLith_select,
                out_table=lithTemp
            )
            lithFiles.append(lithTemp)
        arcpy.management.Merge(
            inputs=lithFiles,
            output=wwLith_export)
        arcpy.management.Delete(lithFiles)
    uf.management.AddMsgAndPrint("*** {} FOLDERS, GEODATABASES, AND FILES HAVE BEEN CREATED AND IS READY FOR USE***".format(projectName))

    # Now we will begin formatting the map views in the project file
    uf.management.AddMsgAndPrint("_____________________________")
    uf.management.AddMsgAndPrint("BEGIN CREATING THE MAPS AND SYMBOLIZING FEATURES...")
    uf.management.AddMsgAndPrint(" - Creating maps and adding datasets to new maps...")
    mapList = ["02_Layout Map - Main","03_Layout Map - Cross-Section","04_County Context","05_State Context"]
    for m in mapList:
        if m in prj.listMaps():
            pass
        else:
            prj.createMap(m)
    pm = prj.activeMap
    if standard_no == "2-5 Mile Project":
        pmLayers = [hillName,prjDEM,contourLines,riverNames,lakeNames,roadNames,railNames,schoolNames,collegeNames,
                    os.path.join(cultureDataset,plssSectionName),os.path.join(cultureDataset,plssTownName),
                    os.path.join(cultureDataset,townName),os.path.join(cultureDataset,countyName),outXSEC,buff2Mile,
                    buff5Mile,siteLoc]
        for feats in pmLayers:
            pm.addDataFromPath(feats)
        extentLyr = pm.listLayers(os.path.splitext(os.path.basename(buff5Mile))[0])[0]
    if standard_no == "User-Defined Project Area":
        pmLayers = [hillName, prjDEM, contourLines, riverNames,lakeNames, roadNames, railNames, schoolNames,
                    collegeNames,
                    os.path.join(cultureDataset, plssSectionName), os.path.join(cultureDataset, plssTownName),
                    os.path.join(cultureDataset, townName), os.path.join(cultureDataset, countyName), outXSEC,
                    buff2Mile,featExtent, siteLoc]
        for feats in pmLayers:
            pm.addDataFromPath(feats)
        extentLyr = pm.listLayers(os.path.splitext(os.path.basename(featExtent))[0])[0]
    uf.management.removeBasemaps(pm)
    pm.defaultCamera.setExtent(arcpy.Describe(extentLyr).extent)

    sm = prj.listMaps("05_State Context")[0]
    smLayers = [os.path.join(govUnits_statewideLoc, "GU_CountyOrEquivalent"),os.path.join(cultureDataset, countyName)]
    for feats in smLayers:
        sm.addDataFromPath(feats)
    uf.management.removeBasemaps(sm)

    cm = prj.listMaps("04_County Context")[0]
    cmLayers = [os.path.join(cultureDataset,townCounties),os.path.join(cultureDataset,countyName),siteLoc]
    for feats in cmLayers:
        cm.addDataFromPath(feats)
    uf.management.removeBasemaps(cm)

    mm = prj.listMaps("02_Layout Map - Main")[0]
    if standard_no == "2-5 Mile Project":
        mmLayers = [hillName,prjDEM,contourLines,riverNames,lakeNames,roadNames,railNames,schoolNames,collegeNames,
                    os.path.join(cultureDataset,plssSectionName),os.path.join(cultureDataset,plssTownName),
                    os.path.join(cultureDataset,townName),os.path.join(cultureDataset,countyName),outXSEC,buff2Mile,
                    buff5Mile,siteLoc]
    if standard_no == "User-Defined Project Area":
        mmLayers = [hillName, prjDEM, contourLines, riverNames,lakeNames, roadNames, railNames, schoolNames,
                    collegeNames,
                    os.path.join(cultureDataset, plssSectionName), os.path.join(cultureDataset, plssTownName),
                    os.path.join(cultureDataset, townName), os.path.join(cultureDataset, countyName), outXSEC,
                    buff2Mile,featExtent, siteLoc]
    for feats in mmLayers:
        mm.addDataFromPath(feats)
    uf.management.removeBasemaps(mm)

    csm = prj.listMaps("03_Layout Map - Cross-Section")[0]
    csmLayers = [hillName,prjDEM,contourLines,lakeNames,riverNames,roadNames,railNames,buff2Mile,outXSEC,siteLoc]
    for feats in csmLayers:
        csm.addDataFromPath(feats)
    uf.management.removeBasemaps(csm)

    uf.management.AddMsgAndPrint(" - Formatting datasets in maps...")
    uf.management.AddMsgAndPrint("   - Processing Map...")
    uf.symbols.DEMSymbol(map=pm, feature=prjDEM)
    uf.symbols.roadSymbol(map=pm,feature=roadNames)
    uf.symbols.contoursSymbol(map=pm, feature=contourLines)
    uf.symbols.riverSymbol(map=pm, feature=riverNames)
    uf.symbols.lakesSymbol(map=pm, feature=lakeNames)
    uf.symbols.schoolSymbol(map=pm, feature=schoolNames)
    uf.symbols.collegeSymbol(map=pm, feature=collegeNames)
    uf.symbols.railSymbol(map=pm, feature=railNames)
    uf.symbols.sectionSymbol(map=pm, feature=plssSectionName)
    uf.symbols.townSymbol(map=pm, feature=townName)
    uf.symbols.plsstownSymbol(map=pm, feature=plssTownName)
    uf.symbols.countySymbol(map=pm, feature=countyName)
    uf.symbols.mile2Symbol(map=pm, feature=buff2Mile)
    uf.symbols.locSymbol(map=pm, feature=siteLoc)
    uf.symbols.xsecSymbol(map=pm, feature=outXSEC)
    if standard_no == "2-5 Mile Project":
        uf.symbols.mile5Symbol(map=pm, feature=buff5Mile)
    if standard_no == "User-Defined Project Area":
        uf.symbols.extentSymbol(map=pm, feature=featExtent)

    uf.management.AddMsgAndPrint("   - 02_Layout Map - Main...")
    uf.symbols.DEMSymbol(map=mm,feature=prjDEM)
    uf.symbols.roadSymbol(map=mm,feature=roadNames)
    uf.symbols.contoursSymbol(map=mm,feature=contourLines)
    uf.symbols.riverSymbol(map=mm,feature=riverNames)
    uf.symbols.lakesSymbol(map=mm,feature=lakeNames)
    uf.symbols.schoolSymbol(map=mm,feature=schoolNames)
    uf.symbols.collegeSymbol(map=mm,feature=collegeNames)
    uf.symbols.railSymbol(map=mm,feature=railNames)
    uf.symbols.sectionSymbol(map=mm,feature=plssSectionName)
    uf.symbols.plsstownSymbol(map=mm, feature=plssTownName)
    uf.symbols.townSymbol(map=mm,feature=townName)
    uf.symbols.countySymbol(map=mm,feature=countyName)
    uf.symbols.mile2Symbol(map=mm,feature=buff2Mile)
    uf.symbols.locSymbol(map=mm,feature=siteLoc)
    uf.symbols.xsecSymbol(map=mm,feature=outXSEC)
    if standard_no == "2-5 Mile Project":
        uf.symbols.mile5Symbol(map=mm,feature=buff5Mile)
    if standard_no == "User-Defined Project Area":
        uf.symbols.extentSymbol(map=mm,feature=featExtent)

    uf.management.AddMsgAndPrint("   - 03_Layout Map - Cross-Section...")
    uf.symbols.DEMSymbol(map=csm, feature=prjDEM)
    uf.symbols.contoursSymbol(map=csm, feature=contourLines)
    uf.symbols.locSymbol(map=csm, feature=siteLoc)
    uf.symbols.riverSymbol(map=csm, feature=riverNames)
    uf.symbols.lakesSymbol(map=csm, feature=lakeNames)
    uf.symbols.roadSymbol(map=csm,feature=roadNames)
    uf.symbols.railSymbol(map=csm, feature=railNames)
    uf.symbols.xsecSymbol(map=csm, feature=outXSEC)
    uf.symbols.mile2Symbol(map=csm, feature=buff2Mile)

    uf.management.AddMsgAndPrint("   - 04_County Context...")
    uf.symbols.townSymbol(map=cm,feature=townCounties)
    uf.symbols.countySymbol(map=cm,feature=countyName)
    uf.symbols.locSymbol(map=cm,feature=siteLoc)

    uf.management.AddMsgAndPrint("   - 05_State Context...")
    uf.symbols.stateCSymbol(map=sm,feature=countyName)
    uf.symbols.countySymbol(map=sm,feature="GU_CountyOrEquivalent")
    uf.management.AddMsgAndPrint("*** ALL MAPS AND DATASETS FOR {} HAVE BEEN CREATED AND IS READY FOR USE***".format(projectName))

    # Now we move on to creating the datasets needed for Michigan. This involves reformatting and extracting
    # information for the water well points, lithologies, and generating groundwater rasters and bedrock surface
    # rasters.
    if state == "Michigan":
        uf.management.AddMsgAndPrint("_____________________________")
        uf.management.AddMsgAndPrint("BEGIN FORMATTING WELLOGIC DATA...")
        if standard_no == "2-5 Mile Project":
            lith,wwPoints = DataFormatting.dataFormatting(
                geologyGDB=geologyGDB,
                prjName=projectName,
                wellPoints=wwPoints_export,
                lithTable=wwLith_export,
                accessory="false",
                username="",
                password="",
                prjExtent=buff5Mile,
                prjDEM=prjDEM,
                reviewTable="https://services1.arcgis.com/vFQXQuqACTPxa4Yc/arcgis/rest/services/ReviewTable/FeatureServer/0"
            )
            uf.management.AddMsgAndPrint("_____________________________")
            uf.management.AddMsgAndPrint("BEGIN GENERATING GROUNDWATER SURFACES...")
            gwlUsable = os.path.join(geologyGDB, os.path.splitext(os.path.basename(wwPoints))[0] + "_GWL_USABLE")
            GWL_RasterCreation.gwlRasterCreation(
                wellType="All Wells",
                wwPoints=gwlUsable,
                wwPoints_aq="AQ_TYPE",
                wwPoints_swlElev="MGS_SWL_ELEV",
                wwPoints_constDate="CONST_DATE",
                dateRange=customRange,
                boundary=buff5Mile,
                rasterGDB=os.path.join(projectLoc,"Rasters.gdb")
            )
            uf.management.AddMsgAndPrint("_____________________________")
            uf.management.AddMsgAndPrint("BEGIN GENERATING BEDROCK SURFACE...")
            bdrkRaster = os.path.join(os.path.join(projectLoc,"Rasters.gdb"),os.path.splitext(os.path.basename(wwPoints))[0] + "_BDRK_SURFACE")
            bdrkPoints = arcpy.management.SelectLayerByAttribute(
                in_layer_or_view=gwlUsable,
                selection_type="NEW_SELECTION",
                where_clause="MGS_DEPTH_2_BDRK IS NOT NULL",
                invert_where_clause=None
            )
            uf.format.createBDRKraster(
                points=bdrkPoints,
                outraster=bdrkRaster,
                boundary=buff5Mile,
                map=pm,
                bdrk_elev="MGS_BDRK_ELEV"
            )
        if standard_no == "User-Defined Project Area":
            lith, wwPoints = DataFormatting.dataFormatting(
                geologyGDB=geologyGDB,
                prjName=projectName,
                wellPoints=wwPoints_export,
                lithTable=wwLith_export,
                accessory="false",
                username="",
                password="",
                prjExtent=featExtent,
                prjDEM=prjDEM,
                reviewTable="https://services1.arcgis.com/vFQXQuqACTPxa4Yc/arcgis/rest/services/ReviewTable/FeatureServer/0"
            )
            uf.management.AddMsgAndPrint("_____________________________")
            uf.management.AddMsgAndPrint("BEGIN GENERATING GROUNDWATER SURFACES...")
            gwlUsable = os.path.join(geologyGDB,os.path.splitext(os.path.basename(wwPoints))[0] + "_GWL_USABLE")
            GWL_RasterCreation.gwlRasterCreation(
                wellType="All Wells",
                wwPoints=gwlUsable,
                wwPoints_aq="AQ_TYPE",
                wwPoints_swlElev="MGS_SWL_ELEV",
                wwPoints_constDate="CONST_DATE",
                dateRange=customRange,
                boundary=featExtent,
                rasterGDB=os.path.join(projectLoc, "Rasters.gdb")
            )
            uf.management.AddMsgAndPrint("_____________________________")
            uf.management.AddMsgAndPrint("BEGIN GENERATING BEDROCK SURFACE...")
            bdrkRaster = os.path.join(os.path.join(projectLoc, "Rasters.gdb"),os.path.splitext(os.path.basename(wwPoints))[0] + "_BDRK_SURFACE")
            bdrkPoints = arcpy.management.SelectLayerByAttribute(
                in_layer_or_view=gwlUsable,
                selection_type="NEW_SELECTION",
                where_clause="MGS_DEPTH_2_BDRK IS NOT NULL",
                invert_where_clause=None
            )
            uf.format.createBDRKraster(
                points=bdrkPoints,
                outraster=bdrkRaster,
                boundary=featExtent,
                map=pm,
                bdrk_elev="MGS_BDRK_ELEV"
            )

if __name__ == "__main__":
    siteTable = arcpy.ValueTable(3)
    siteTable.loadFromString(arcpy.GetParameterAsText(3))
    demTable = arcpy.ValueTable(2)
    demTable.loadFromString(arcpy.GetParameterAsText(5))
    customDatesTable = arcpy.ValueTable(2)
    customDatesTable.loadFromString(arcpy.GetParameterAsText(6))

    dateInterval = []
    for i in range(0,customDatesTable.rowCount):
        startYear = int(customDatesTable.getValue(i,0))
        endYear = int(customDatesTable.getValue(i,1))
        genDate = datetime.datetime(year=1900,month=1,day=1)
        date1 = genDate.replace(year=startYear).strftime('%Y-%m-%d %H:%M:%S')
        date2 = genDate.replace(year=endYear,month=12,day=31).strftime('%Y-%m-%d %H:%M:%S')
        dateInterval.append([date1,date2])
    projectCreation(
        projectName=arcpy.GetParameterAsText(0),
        projectLoc=arcpy.GetParameterAsText(1),
        state=arcpy.GetParameterAsText(4),
        standard_no=arcpy.GetParameterAsText(2),
        siteData=siteTable,
        dem=demTable,
        customRange=dateInterval
    )
    uf.management.AddMsgAndPrint("_____________________________")
    uf.management.AddMsgAndPrint('***FINISHED CREATING DATASETS UTILIZING THE SCHEMA DETAILED BY THE MICHIGAN GEOLOGICAL SURVEY***')
    uf.management.AddMsgAndPrint('General Disclaimer: All data present is derived from the Wellogic database.\nPlease take time to validate the datasets for validity before performing for any sort of analysis')
