# *****************************************************
# *****************************************************
# Utility_Functions.py
# Version: 1.2.7
# Date: 5/30/2024
# Last Modified Date: 3/25/2026
# Original Author: Matthew Bell, Michigan Geological Survey, matthew.e.bell@wmich.edu
# Description: A utility functions python file to store generic definitions and functions related to other main software scripts.
# *****************************************************
# *****************************************************

import os, sys
import arcpy
import pandas as pd
import requests

debug = False

# Generic functions and definitions for all scripts
class management:
    def testAndDelete(fc):
        if arcpy.Exists(fc):
            arcpy.management.Delete(fc)

    def checkExtensions(self) -> object:
        # Check for the Spatial Analyst Extension
        try:
            if arcpy.CheckExtension("Spatial") == "Available":
                arcpy.CheckOutExtension("Spatial")
            else:
                raise "LicenseError"
            if arcpy.CheckExtension("3D") == "Available":
                arcpy.CheckOutExtension("3D")
            else:
                raise "LicenseError"
            if arcpy.CheckExtension("LocationReferencing") == "Available":
                arcpy.CheckOutExtension("LocationReferencing")
            else:
                raise "LicenseError"
        except "LicenseError":
            arcpy.AddMessage("One or more extensions are unavailable (Spatial Analyst, 3D Analyst, Location Referencing)")
            raise SystemError

    def AddMsgAndPrint(msg,severity=0):
        # Adds message (in case this is run as a tool) and also prints the message to the screen (standard output)
        print(msg)

        # Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
        try:
            for string in msg.split("\n"):
                # Add appropriate geoprocessing message:
                if severity == 0:
                    arcpy.AddMessage(string)
                elif severity == 1:
                    arcpy.AddWarning(string)
                elif severity == 2:
                    arcpy.AddError(string)
        except:
            pass

    def appendFieldMappingInput(fieldMappings,oldTable,oldField,newField,newFieldAlias,newFieldType):
        # Add the input field for the given field name
        fieldMap = arcpy.FieldMap()
        fieldMap.addInputField(oldTable,oldField)
        name = fieldMap.outputField
        name.name, name.aliasName,name.type = newField,newFieldAlias,newFieldType
        fieldMap.outputField = name
        # Add output field to field mapping objects
        fieldMappings.addFieldMap(fieldMap)

    def limitString(string,limit):
        if len(string) > limit:
            return string[0:limit]
        else:
            return string

    def removeBasemaps(map):
        try:
            basenameLayer = map.listLayers("World Topographic Map")[0]
            hillLayer = map.listLayers("World Hillshade")[0]
            map.removeLayer(basenameLayer)
            map.removeLayer(hillLayer)
        except:
            arcpy.AddMessage("**Basemap already removed. Passing map...")
            pass

    def unique_values(table,field):
        with arcpy.da.SearchCursor(table,field) as cursor:
            return sorted({row[0] for row in cursor})
        del row, cursor

    def githubVersion(vString,rawurl):
        # Let us check for the latest version of the toolbox.
        try:
            page = requests.get(rawurl)
            raw = page.text
            if vString in raw:
                pass
                arcpy.AddMessage(f"This version of the tool is up to date: {vString}")
            else:
                repourl = "https://github.com/MichiganGeologicalSurvey/Michigan-Geological-Survey-Cross-Section-Tool/releases"
                arcpy.AddWarning(f"WARNING: You are using an outdated version of the tool\nPlease download the latest version from {repourl}")
        except:
            arcpy.AddWarning("Could not verify version of tool in GitHub.")

# Definitions related to project creation tool and data reformatting tool...
class format:
    def firstBDRKValue(bdrkTable, origTable, relate, seq, primAQField, firstBDRK, aqField,defaultGDB):
        # Definition function to determine the first bedrock unit observed within a lithology log.

        # Note: This may tag units that are not true bedrock surfaces (i.e. the driller did not use the appropriate term
        # for a lithology description). Generally, this accelerates the process, but make note to review the bedrock
        # contacts.

        # First, we need to determine the minimum and maximum sequence numbers for each type of unit (bedrock, glacial
        # drift, and unknown). This will tell us if the driller has labeled the try bedrock contact.
        statTable = os.path.join(defaultGDB,os.path.splitext(os.path.basename(origTable))[0] + "_stats")
        caseFields = relate + ";" + aqField
        arcpy.analysis.Statistics(
            in_table=origTable,
            out_table=statTable,
            statistics_fields="{0} MIN;{0} MAX".format(seq),
            case_field=caseFields
        )

        # Now that we have the statistics, we need to get the maximum and minimum values for each type of unit into
        # separate tables. This way we can have them as single rows per well to see if the bedrock and glacial units are
        # placed correctly in sequence.

        arcpy.analysis.SplitByAttributes(
            Input_Table=statTable,
            Target_Workspace=defaultGDB,
            Split_Fields=aqField
        )
        bdrkStatsTable = os.path.join(defaultGDB,"R")
        drftStatsTable = os.path.join(defaultGDB,"D")
        nrcdStatsTable = os.path.join(defaultGDB,"U")

        # Let us now prepare the created tables to join to the main table to determine the true bedrock contact.
        # First, let's alter the fields for the bedrock table...
        arcpy.management.AlterField(
            in_table=bdrkStatsTable,
            field="MAX_{}".format(seq),
            new_field_name="MAX_BDRK",
            field_length=8,
            field_is_nullable="NULLABLE",
            clear_field_alias="CLEAR_ALIAS"
        )
        arcpy.management.AlterField(
            in_table=bdrkStatsTable,
            field="MIN_{}".format(seq),
            new_field_name="MIN_BDRK",
            field_length=8,
            field_is_nullable="NULLABLE",
            clear_field_alias="CLEAR_ALIAS"
        )
        # Second, let's alter the fields for the drift table...
        arcpy.management.AlterField(
            in_table=drftStatsTable,
            field="MAX_{}".format(seq),
            new_field_name="MAX_DRFT",
            field_length=8,
            field_is_nullable="NULLABLE",
            clear_field_alias="CLEAR_ALIAS"
        )
        arcpy.management.AlterField(
            in_table=drftStatsTable,
            field="MIN_{}".format(seq),
            new_field_name="MIN_DRFT",
            field_length=8,
            field_is_nullable="NULLABLE",
            clear_field_alias="CLEAR_ALIAS"
        )

        # Now, let's join the two tables to the final lithology table...
        arcpy.management.JoinField(
            in_data=bdrkTable,
            in_field=relate,
            join_table=bdrkStatsTable,
            join_field=relate,
            fields="MIN_BDRK;MAX_BDRK",
            fm_option="NOT_USE_FM",
            field_mapping=None
        )
        arcpy.management.JoinField(
            in_data=bdrkTable,
            in_field=relate,
            join_table=drftStatsTable,
            join_field=relate,
            fields="MIN_DRFT;MAX_DRFT",
            fm_option="NOT_USE_FM",
            field_mapping=None
        )

        # Finally, we can make the necessary steps to figure out if a unit is the true bedrock unit.

        # If the sequence number of a unit is the same as the minimum value calculated previously, that unit will be
        # assigned as the first bedrock unit.
        with arcpy.da.UpdateCursor(bdrkTable,[seq,primAQField,"MIN_BDRK","MAX_BDRK","MIN_DRFT","MAX_DRFT",firstBDRK]) as cursor:
            for row in cursor:
                if row[1].startswith("R"):
                    if row[5] is not None:
                        if (row[2] == row[0] and row[2] > row[5]):
                            # If the minimum sequence is the same as the current sequence number and the minimum bedrock
                            # sequence is greater than the maximum drift sequence (meaning max drift is on top of the
                            # minimum bedrock sequence), the unit is assumed to be the first bedrock contact.
                            row[6] = "Y"
                        elif (row[5]+1 == row[0] and row[3] <= row[4]):
                            # If the unit below the maximum drift sequence is the same as the current sequence number and
                            # the maximum bedrock sequence is less than or equal to the minimum drift sequence, then the
                            # unit is assumed to be the first bedrock contact.
                            row[6] = "Y"
                        else:
                            row[6] = "N"
                    if row[5] is None:
                        # This assumes there was no drift sequence found in the lithology log (drilled only in bedrock
                        # units)
                        if row[2] == row[0]:
                            # If the minimum bedrock sequence is the same as the current sequence, then the unit is
                            # assumed to be the first bedrock contact.
                            row[6] = "Y"
                        else:
                            row[6] = "N"
                else:
                    # If the unit is not a bedrock unit, we do not care about it for the bedrock contact. We simply label
                    # as "NA" or "Not Applicable".
                    row[6] = "NA"
                cursor.updateRow(row)
            del row
            del cursor
        arcpy.management.DeleteField(bdrkTable,["{}_1".format(seq),"MIN_BDRK","MAX_BDRK","MIN_DRFT","MAX_DRFT"])
        arcpy.management.Delete([statTable,bdrkStatsTable,drftStatsTable,nrcdStatsTable])

    def createGWLraster(points,outraster,boundary,map,swl_elev):
        if int(arcpy.management.GetCount(points)[0]) < 10:
            arcpy.AddMessage(" ** Not enough datapoints for the given time period. (At least 10 points needed) \nSkipping time interval...")
            pass
        else:
            with arcpy.EnvManager(mask=boundary):
                out_raster = arcpy.sa.Idw(
                    in_point_features=points,
                    z_field=swl_elev,
                    cell_size=10,
                    power=2,
                    search_radius="VARIABLE 12",
                    in_barrier_polyline_features=None
                )
            out_raster.save(outraster)
            prj = arcpy.mp.ArcGISProject("CURRENT")
            map.addDataFromPath(outraster)
            prj.save()
        arcpy.management.SelectLayerByAttribute(points,"CLEAR_SELECTION")

    def createBDRKraster(points,outraster,boundary,map,bdrk_elev):
        if int(arcpy.management.GetCount(points)[0]) < 10:
            arcpy.AddMessage(" ** Not enough datapoints for the given time period. (At least 10 points needed) \nSkipping time interval...")
            pass
        else:
            with arcpy.EnvManager(mask=boundary):
                arcpy.ga.EmpiricalBayesianKriging(
                    in_features=points,
                    z_field=bdrk_elev,
                    cell_size=10,
                    output_type="PREDICTION",
                    out_raster=outraster
                )
            prj = arcpy.mp.ArcGISProject("CURRENT")
            map.addDataFromPath(outraster)
            prj.save()
        arcpy.management.SelectLayerByAttribute(points, "CLEAR_SELECTION")
    def find_header_row(file_path):
        with open(file_path, "r") as file:
            for idx, line in enumerate(file):
                if line.startswith("~A"):
                    return idx
        return None

# - Symbology definitions for project creation tool and data formatting tool...
class symbols:
    def DEMSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrDEM = map.listLayers(os.path.splitext(os.path.basename(feature))[0])[0]
        symDEM = lyrDEM.symbology
        if hasattr(symDEM,"colorizer"):
            if symDEM.colorizer.type == "RasterStretchColorizer":
                symDEM.colorizer.stretchType = "PercentClip"
                symDEM.colorizer.minPercent = 1.0
                symDEM.colorizer.maxPercent = 1.0
                cr = prj.listColorRamps("Prediction")[0]
                symDEM.colorizer.colorRamp = cr
                symDEM.colorizer.minLabel = "Minimum: {} ft".format(symDEM.colorizer.minLabel)
                symDEM.colorizer.maxLabel = "Maximum: {} ft".format(symDEM.colorizer.maxLabel)
                lyrDEM.symbology = symDEM
            if lyrDEM.supports("TRANSPARENCY"):
                lyrDEM.transparency = 50

    def contoursSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        field_names = [f.name for f in arcpy.ListFields(feature)]
        try:
            lyrContours = map.listLayers(os.path.splitext(os.path.basename(feature))[0])[0]
            symContours = lyrContours.symbology
            if hasattr(symContours,"renderer"):
                if symContours.renderer.type == "SimpleRenderer":
                    symContours.updateRenderer("UniqueValueRenderer")
                    symContours.renderer.fields = [field_names[5]]
                    lyrContours.symbology = symContours
                    groups = symContours.renderer.groups
                    if groups:
                        groups[0].heading = "Contour Type"
                    symContours.groups = groups
                    for group in symContours.renderer.groups:
                        for item in group.items:
                            if item.values[0][0] == "INDEX":
                                item.symbol.applySymbolFromGallery("Contour, Topographic, Index")
                                item.label = "Index Contours"
                                lyrContours.symbology = symContours
                            else:
                                item.symbol.applySymbolFromGallery("Contour, Topographic, Intermediate")
                                item.symbol.color = {"RGB":[115,76,0,100]}
                                item.label = "Intermediate Contours"
                                lyrContours.symbology = symContours
            prj.save()
        except:
            # There is a weird bug where the contours will sometimes become classified, and sometimes it will not. This
            # could be the case if there are too many contours to use this method, but this catches the glitch to allow
            # the script to continue as normal. Symbology is not a huge priority at the moment.
            arcpy.AddWarning(" ** Feature {} does not support Unique Value Classification.\nCould be too many features to "
                             "symbologize. Passing symbology...".format(os.path.splitext(os.path.basename(feature))[0]))
            pass

    def lakesSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrLake = map.listLayers(os.path.splitext(os.path.basename(feature))[0])[0]
        symLake = lyrLake.symbology
        if symLake.renderer.type == "UniqueValueRenderer":
            symLake.updateRenderer("SimpleRenderer")
        symLake.renderer.symbol.applySymbolFromGallery("Water (area)",1)
        lyrLake.symbology = symLake
        prj.save()

    def riverSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrRiver = map.listLayers(os.path.splitext(os.path.basename(feature))[0])[0]
        symRiver = lyrRiver.symbology
        if symRiver.renderer.type == "UniqueValueRenderer":
            symRiver.updateRenderer("SimpleRenderer")
        symRiver.renderer.symbol.outlineColor = {"RGB":[10,147,252,100]}
        symRiver.renderer.symbol.outlineWidth = 1
        lyrRiver.symbology = symRiver
        prj.save()

    def roadSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        try:
            lyrRoad = map.listLayers(os.path.splitext(os.path.basename(feature))[0])[0]
            symRoad = lyrRoad.symbology
            symRoad.updateRenderer("UniqueValueRenderer")
            lyrRoad.symbology = symRoad

            symRoad.renderer.fields = ["TNMFRC"]
            groups = symRoad.renderer.groups
            if groups:
                groups[0].heading = "Functional Road Classification"
            symRoad.groups = groups
            for group in symRoad.renderer.groups:
                for item in group.items:
                    if item.values[0][0] == "1":
                        item.symbol.color = {"RGB":[0, 92, 230, 100]}
                        item.symbol.outlineWidth = 2
                        item.label = "Controlled-access Highway"
                        lyrRoad.symbology = symRoad
                    elif item.values[0][0] == "2":
                        item.symbol.color = {"RGB": [230, 0, 0, 100]}
                        item.symbol.outlineWidth = 1.5
                        item.label = "Secondary Highway or Major Connecting Road"
                        lyrRoad.symbology = symRoad
                    elif item.values[0][0] == "3":
                        item.symbol.color = {"RGB": [169, 0, 230, 100]}
                        item.symbol.outlineWidth = 1.5
                        item.label = "Local Connecting Road"
                        lyrRoad.symbology = symRoad
                    elif item.values[0][0] == "4":
                        item.symbol.color = {"RGB": [0, 0, 0, 100]}
                        item.symbol.outlineWidth = 1.0
                        item.label = "Local Road"
                        lyrRoad.symbology = symRoad
                    elif item.values[0][0] == "5":
                        item.symbol.color = {"RGB": [56, 168, 0, 100]}
                        item.symbol.outlineWidth = 1.5
                        item.label = "Ramp"
                        lyrRoad.symbology = symRoad
                    elif item.values[0][0] == "6":
                        item.symbol.applySymbolFromGallery('Dashed 4:4')
                        item.symbol.color = {"RGB": [255, 170, 0, 100]}
                        item.symbol.outlineWidth = 1.0
                        item.label = "4WD Road"
                        lyrRoad.symbology = symRoad
                    elif item.values[0][0] == "7":
                        item.symbol.applySymbolFromGallery('Ferry')
                        item.symbol.outlineWidth = 1.0
                        item.label = "Ferry Route"
                        lyrRoad.symbology = symRoad
                    elif item.values[0][0] == "8":
                        item.symbol.applySymbolFromGallery('Dashed 4:4')
                        item.symbol.color = {"RGB": [0, 0, 0, 100]}
                        item.symbol.outlineWidth = 1
                        item.label = "Tunnel"
                        lyrRoad.symbology = symRoad
                    elif item.values[0][0] == "9":
                        item.symbol.applySymbolFromGallery('Line with 1 Marker')
                        item.symbol.color = {"RGB": [0, 0, 0, 100]}
                        item.symbol.outlineWidth = 1
                        item.label = "Closed Road"
                        lyrRoad.symbology = symRoad
                    elif item.values[0][0] == "99":
                        item.symbol.color = {"RGB": [204,204,204,100]}
                        item.symbol.outlineWidth = 1
                        item.label = "Unknown Road"
                        lyrRoad.symbology = symRoad
            prj.save()
        except:
            arcpy.AddWarning(" ** Feature {} does not support Unique Value Classification.\nPassing symbology...".format(
                os.path.splitext(os.path.basename(feature))[0]))
            pass

    def railSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrRail = map.listLayers(os.path.splitext(os.path.basename(feature))[0])[0]
        symRail = lyrRail.symbology
        if symRail.renderer.type == "UniqueValueRenderer":
            symRail.updateRenderer("SimpleRenderer")
        symRail.renderer.symbol.applySymbolFromGallery('Railroad')
        symRail.renderer.symbol.color = {'RGB': [0, 0, 0, 100]}
        lyrRail.symbology = symRail
        prj.save()

    def schoolSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrSchool = map.listLayers(os.path.splitext(os.path.basename(feature))[0])[0]
        symSchool = lyrSchool.symbology
        if symSchool.renderer.type == "UniqueValueRenderer":
            symSchool.updateRenderer("SimpleRenderer")
        symSchool.renderer.symbol.applySymbolFromGallery('School', 1)
        symSchool.renderer.symbol.color = {'RGB': [0, 92, 230, 100]}
        lyrSchool.symbology = symSchool
        prj.save()

    def collegeSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrCollege = map.listLayers(os.path.splitext(os.path.basename(feature))[0])[0]
        symCollege = lyrCollege.symbology
        if symCollege.renderer.type == "UniqueValueRenderer":
            symCollege.updateRenderer("SimpleRenderer")
        symCollege.renderer.symbol.applySymbolFromGallery('School', 1)
        lyrCollege.symbology = symCollege
        prj.save()

    def locSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrLoc = map.listLayers(os.path.splitext(os.path.basename(feature))[0])[0]
        symLoc = lyrLoc.symbology
        symLoc.renderer.symbol.applySymbolFromGallery('Star 3')
        symLoc.renderer.symbol.color = {'RGB': [255, 255, 0, 100]}
        symLoc.renderer.symbol.size = 15
        lyrLoc.symbology = symLoc
        prj.save()

    def sectionSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrSection = map.listLayers(feature)[0]
        symSection = lyrSection.symbology
        symSection.renderer.symbol.color = {'RGB': [255, 255, 255, 0]}
        symSection.renderer.symbol.outlineColor = {'RGB': [255, 0, 0, 100]}
        symSection.renderer.symbol.outlineWidth = 0.7
        lyrSection.symbology = symSection
        prj.save()

    def townSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrTown = map.listLayers(feature)[0]
        symTown = lyrTown.symbology
        symTown.renderer.symbol.applySymbolFromGallery('Dashed Black Outline (1pt)')
        symTown.renderer.symbol.outlineWidth = 2
        lyrTown.symbology = symTown
        prj.save()

    def plsstownSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrTown = map.listLayers(feature)[0]
        symTown = lyrTown.symbology
        symTown.renderer.symbol.color = {'RGB': [255, 255, 255, 0]}
        symTown.renderer.symbol.outlineColor = {'RGB': [130, 130, 130, 100]}
        symTown.renderer.symbol.outlineWidth = 1.5
        lyrTown.symbology = symTown
        prj.save()

    def stateCSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrStateC = map.listLayers(feature)[0]
        symStateC = lyrStateC.symbology
        symStateC.renderer.symbol.color = {'RGB': [255, 255, 255, 0]}
        symStateC.renderer.symbol.outlineColor = {'RGB': [230, 0, 169, 100]}
        symStateC.renderer.symbol.outlineWidth = 2.5
        lyrStateC.symbology = symStateC
        prj.save()

    def countySymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrCounty = map.listLayers(feature)[0]
        symCounty = lyrCounty.symbology
        symCounty.renderer.symbol.color = {'RGB': [255, 255, 255, 0]}
        symCounty.renderer.symbol.outlineColor = {'RGB': [0, 0, 0, 100]}
        symCounty.renderer.symbol.outlineWidth = 1.5
        lyrCounty.symbology = symCounty
        prj.save()

    def xsecSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrXSec = map.listLayers(os.path.splitext(os.path.basename(feature))[0])[0]
        symXSec = lyrXSec.symbology
        symXSec.renderer.symbol.outlineColor = {'RGB': [255, 255, 255, 100]}
        symXSec.renderer.symbol.outlineWidth = 2.5
        lyrXSec.symbology = symXSec
        prj.save()

    def mile2Symbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyr2Mile = map.listLayers(os.path.splitext(os.path.basename(feature))[0])[0]
        sym2Mile = lyr2Mile.symbology
        sym2Mile.renderer.symbol.applySymbolFromGallery('Black Outline (1pt)')
        sym2Mile.renderer.symbol.color = {'RGB': [255, 255, 255, 0]}
        sym2Mile.renderer.symbol.outlineColor = {'RGB': [168, 0, 0, 100]}
        sym2Mile.renderer.symbol.outlineWidth = 2
        lyr2Mile.symbology = sym2Mile
        prj.save()

    def mile5Symbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyr5Mile = map.listLayers(os.path.splitext(os.path.basename(feature))[0])[0]
        sym5Mile = lyr5Mile.symbology
        sym5Mile.renderer.symbol.applySymbolFromGallery('Black Outline (1pt)')
        sym5Mile.renderer.symbol.color = {'RGB': [255, 255, 255, 0]}
        sym5Mile.renderer.symbol.outlineColor = {'RGB': [0, 92, 230, 100]}
        sym5Mile.renderer.symbol.outlineWidth = 2
        lyr5Mile.symbology = sym5Mile
        prj.save()

    def extentSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrExtent = map.listLayers(os.path.splitext(os.path.basename(feature))[0])[0]
        symExtent = lyrExtent.symbology
        symExtent.renderer.symbol.applySymbolFromGallery('Black Outline (1pt)')
        symExtent.renderer.symbol.color = {'RGB': [255, 255, 255, 0]}
        symExtent.renderer.symbol.outlineColor = {'RGB': [168, 0, 0, 100]}
        symExtent.renderer.symbol.outlineWidth = 2
        lyrExtent.symbology = symExtent
        prj.save()

    def wwSymbol(map,feature):
        prj = arcpy.mp.ArcGISProject("CURRENT")
        lyrWW = map.listLayers(os.path.splitext(os.path.basename(feature))[0])[0]
        symWW = lyrWW.symbology
        symWW.updateRenderer('UniqueValueRenderer')
        lyrWW.symbology = symWW
        symWW.renderer.fields = ['well_label']
        symWW.renderer.removeValues({"well_label": ["Drift: Type 1 Public Supply", "Drift: Type 2 Public Supply", "Drift: Type 3 Public Supply",
                                                    "Drift: All Other Wells",
                                                    "Bedrock: Type 1 Public Supply", "Bedrock: Type 2 Public Supply", "Bedrock: Type 3 Public Supply",
                                                    "Bedrock: All Other Wells",
                                                    "Unknown Aquifer: Type 1 Public Supply",
                                                    "Unknown Aquifer: Type 2 Public Supply", "Unknown Aquifer: Type 3 Public Supply",
                                                    "Unknown Aquifer: All Other Wells"]})
        lyrWW.symbology = symWW
        symWW.renderer.addValues({"Aquifer Type: Well Usage": symWW.renderer.listMissingValues()[0].items})
        lyrWW.symbology = symWW
        for group in symWW.renderer.groups:
            for item in group.items:
                if item.values[0][0] == "Drift: Type 1 Public Supply":
                    item.symbol.applySymbolFromGallery('Star 3')
                    item.symbol.color = {'RGB': [76, 230, 0, 100]}
                    item.symbol.size = 13
                    lyrWW.symbology = symWW
                elif item.values[0][0] == "Drift: Type 2 Public Supply":
                    item.symbol.applySymbolFromGallery('Diamond 4')
                    item.symbol.color = {'RGB': [76, 230, 0, 100]}
                    item.symbol.outlineWidth = 1
                    item.symbol.size = 13
                    lyrWW.symbology = symWW
                elif item.values[0][0] == "Drift: Type 3 Public Supply":
                    item.symbol.applySymbolFromGallery('Triangle 3')
                    item.symbol.color = {'RGB': [76, 230, 0, 100]}
                    item.symbol.outlineWidth = 1
                    item.symbol.size = 8
                    lyrWW.symbology = symWW
                elif item.values[0][0] == "Drift: All Other Wells":
                    item.symbol.color = {'RGB': [76, 230, 0, 100]}
                    item.symbol.size = 3
                    item.symbol.outlineWidth = 0
                    lyrWW.symbology = symWW
                elif item.values[0][0] == "Bedrock: Type 1 Public Supply":
                    item.symbol.applySymbolFromGallery('Star 3')
                    item.symbol.color = {'RGB': [230, 0, 0, 100]}
                    item.symbol.size = 13
                    lyrWW.symbology = symWW
                elif item.values[0][0] == "Bedrock: Type 2 Public Supply":
                    item.symbol.applySymbolFromGallery('Diamond 4')
                    item.symbol.outlineWidth = 1
                    item.symbol.size = 13
                    item.symbol.color = {'RGB': [230, 0, 0, 100]}
                    lyrWW.symbology = symWW
                elif item.values[0][0] == "Bedrock: Type 3 Public Supply":
                    item.symbol.applySymbolFromGallery('Triangle 3')
                    item.symbol.outlineWidth = 1
                    item.symbol.size = 8
                    item.symbol.color = {'RGB': [230, 0, 0, 100]}
                    lyrWW.symbology = symWW
                elif item.values[0][0] == "Bedrock: All Other Wells":
                    item.symbol.color = {'RGB': [230, 0, 0, 100]}
                    item.symbol.size = 3
                    item.symbol.outlineWidth = 0
                    lyrWW.symbology = symWW
                if item.values[0][0] == "Unknown Aquifer: Type 1 Public Supply":
                    item.symbol.applySymbolFromGallery('Star 3')
                    item.symbol.color = {'RGB': [115, 178, 255, 100]}
                    item.symbol.size = 13
                    lyrWW.symbology = symWW
                elif item.values[0][0] == "Unknown Aquifer: Type 2 Public Supply":
                    item.symbol.applySymbolFromGallery('Diamond 4')
                    item.symbol.color = {'RGB': [115, 178, 255, 100]}
                    item.symbol.outlineWidth = 1
                    item.symbol.size = 13
                    lyrWW.symbology = symWW
                elif item.values[0][0] == "Unknown Aquifer: Type 3 Public Supply":
                    item.symbol.applySymbolFromGallery('Triangle 3')
                    item.symbol.color = {'RGB': [115, 178, 255, 100]}
                    item.symbol.outlineWidth = 1
                    item.symbol.size = 8
                    lyrWW.symbology = symWW
                elif item.values[0][0] == "Unknown Aquifer: All Other Wells":
                    item.symbol.color = {'RGB': [115, 178, 255, 100]}
                    item.symbol.size = 3
                    item.symbol.outlineWidth = 0
                    lyrWW.symbology = symWW
        prj.save()

# Definitions for cross-section tools...
class xsec:
    def round2int(x,base):
        return base * round(x/base)

    def getCPValue(quadrant):
        cpDict = {"Northwest":"UPPER_LEFT",
                  "Southwest":"LOWER_LEFT",
                  "Northeast":"UPPER_RIGHT",
                  "Southeast":"LOWER_RIGHT"}
        return cpDict[quadrant]

    def fieldNone(fc, field):
        try:
            with arcpy.da.SearchCursor(fc, field) as rows:
                if rows.next()[0] in [None,""]:
                    return False
                else:
                    return True
        except:
            return False

    def add_id(out_name,field_names,out_path):
        id_name = "{}_id".format(management.limitString(out_name,61))
        if not id_name in field_names:
            arcpy.management.AddField(out_path,id_name,"TEXT",field_length=50)
        letters = []
        for s in out_name:
            if s.isalpha():
                if s.isupper():
                    letters.append(s)
        pref = "".join(letters)
        return id_name, pref

    def cartesianToGeographic(angle):
        ctg = -90 - angle
        if ctg < 0:
            ctg = ctg + 360
            return ctg

    def locateEvents_Table(pts, XSEC_NAME, defaultGDB, route_line, checkField,sel_dist, event_props, is_lines=False):
        # Used to locate the points that are within the distance of the cross-section line. Can be used to locate
        # boreholes, open holes, and points of interest on or near the cross-section line.
        dupDetectField = "xDupDetect"
        arcpy.management.AddField(pts, dupDetectField, "LONG")
        eventLocTable = os.path.join(defaultGDB,"XSEC_{}_locEvents".format(XSEC_NAME))
        management.testAndDelete(eventLocTable)
        arcpy.lr.LocateFeaturesAlongRoutes(
            in_features=pts,
            in_routes=route_line,
            route_id_field=checkField,
            radius_or_tolerance=sel_dist,
            out_table=eventLocTable,
            out_event_properties=event_props
        )
        nRows = int(arcpy.management.GetCount(eventLocTable)[0])
        nPts = int(arcpy.management.GetCount(pts)[0])
        if nRows > nPts and not is_lines:
            arcpy.management.DeleteIdentical(eventLocTable,dupDetectField)
        arcpy.management.DeleteField(eventLocTable,dupDetectField)
        return eventLocTable

    def boreholes(locatedPoints,XSEC_NAME,defaultGDB,elev_field,depth_field,elev_units,ve,adjustDist):
        # Used to create the borehole sticks that is observed in the selection distance described by the user.
        bhLineNames = "XSEC_{}_bhLines".format(XSEC_NAME)
        bhSticks = os.path.join(defaultGDB,bhLineNames)
        management.testAndDelete(bhSticks)
        arcpy.management.CreateFeatureclass(
            out_path=defaultGDB,
            out_name=bhLineNames,
            geometry_type="POLYLINE",
            template=locatedPoints
        )

        lf = arcpy.ListFields(locatedPoints)
        bhFields = [f.name for f in lf if f.type != "Geometry"]
        bhFields.append("SHAPE@")

        uniq_ID, id_pref = xsec.add_id(out_name=bhLineNames,field_names=bhFields,out_path=bhSticks)

        tRows = arcpy.da.SearchCursor(locatedPoints,bhFields)
        bhFields.append(uniq_ID)
        cur = arcpy.da.InsertCursor(bhSticks,bhFields)
        oidName = [f.name for f in lf if f.type == "OID"][0]
        oid_i = tRows.fields.index(oidName)
        elevID = tRows.fields.index(elev_field)
        depthID = tRows.fields.index(depth_field)
        mField = tRows.fields.index("M")

        i = 0
        for row in tRows:
            if elev_units == "Meters":
                i = i + 1
                bhArray = []
                X = row[mField] + float(adjustDist)
                Ytop = float(row[elevID])
                Ybot = Ytop - float(row[depthID])
                bhArray.append((X, Ytop * float(ve)))
                bhArray.append((X, Ybot * float(ve)))
                vals = list(row).copy()
                print(vals)
                vals.append("")
                vals[-2] = bhArray
                csAzi = xsec.cartesianToGeographic(angle=row[tRows.fields.index("LOC_ANGLE")])
                vals[tRows.fields.index("LocalXSEC_Azimuth")] = csAzi
                vals[tRows.fields.index("DistFromSection")] = row[tRows.fields.index("Distance")]
                vals[-1] = "{}_{}".format(id_pref,i)
                try:
                    cur.insertRow(vals)
                    bhArray.clear()
                except Exception:
                    management.AddMsgAndPrint("Could not create feature from objectid {} in {}".format(row[oid_i],locatedPoints),1)
                    management.AddMsgAndPrint(Exception)
            if elev_units == "Feet":
                i = i + 1
                bhArray = []
                X = row[mField] + float(adjustDist)
                Ytop = float(row[elevID]) * 0.3048
                Ybot = Ytop - float(row[depthID]) * 0.3048
                bhArray.append((X, Ytop * float(ve)))
                bhArray.append((X, Ybot * float(ve)))
                vals = list(row).copy()
                vals.append("")
                vals[-2] = bhArray
                csAzi = xsec.cartesianToGeographic(angle=row[tRows.fields.index("LOC_ANGLE")])
                vals[tRows.fields.index("LocalXSEC_Azimuth")] = csAzi
                vals[tRows.fields.index("DistFromSection")] = row[tRows.fields.index("Distance")]
                vals[-1] = "{}_{}".format(id_pref, i)
                try:
                    cur.insertRow(vals)
                    bhArray.clear()
                except Exception:
                    management.AddMsgAndPrint("Could not create feature from objectid {} in {}".format(row[oid_i], locatedPoints), 1)
                    management.AddMsgAndPrint(f"{Exception}")
            del row
        del tRows, cur
        return bhSticks

    def surfPoints(locatedPoints,XSEC_NAME,defaultGDB,elev_field,elev_units,ve,adjustDist):
        # Used to create the borehole sticks that is observed in the selection distance described by the user.
        nameID = 1
        while True:
            surfPointsName = "{}_{}x_v{}".format(os.path.splitext(os.path.basename(locatedPoints))[0],ve, nameID)
            surfPoints = os.path.join(defaultGDB, "XSEC_{}".format(XSEC_NAME.replace("-", "_").replace(" ", "_")),
                                       surfPointsName)
            if arcpy.Exists(surfPoints):
                nameID = nameID + 1
            else:
                break
        arcpy.management.CreateFeatureclass(os.path.join(defaultGDB, "XSEC_{}".format(XSEC_NAME.replace("-", "_").replace(" ", "_"))),
                                            surfPointsName, "POINT", locatedPoints, "DISABLED","SAME_AS_TEMPLATE")

        lf = arcpy.ListFields(locatedPoints)
        surfFields = [f.name for f in lf if f.type != "Geometry"]
        surfFields.append("SHAPE@")

        uniq_ID, id_pref = xsec.add_id(out_name=surfPointsName, field_names=surfFields, out_path=surfPoints)

        tRows = arcpy.da.SearchCursor(locatedPoints, surfFields)
        surfFields.append(uniq_ID)
        cur = arcpy.da.InsertCursor(surfPoints, surfFields)
        oidName = [f.name for f in lf if f.type == "OID"][0]
        oid_i = tRows.fields.index(oidName)
        elevID = tRows.fields.index(elev_field)

        i = 1
        for row in tRows:
            if elev_units == "Meters":
                i = i + 1
                X = row[tRows.fields.index("M")] + float(adjustDist)
                Ytop = float(row[elevID])
                surfPnt = [float(X),float(Ytop* float(ve))]
                vals = list(row).copy()
                vals.append("{}_{}".format(id_pref, i))
                vals[-2] = surfPnt
                csAzi = xsec.cartesianToGeographic(angle=row[tRows.fields.index("LOC_ANGLE")])
                vals[tRows.fields.index("LocalXSEC_Azimuth")] = csAzi
                vals[tRows.fields.index("DistFromSection")] = row[tRows.fields.index("Distance")]
                try:
                    cur.insertRow(vals)
                    surfPnt.clear()
                except Exception as e:
                    management.AddMsgAndPrint(
                        "Could not create feature from objectid {} in {}\n{}".format(row[oid_i], locatedPoints, e), 1)
            if elev_units == "Feet":
                i = i + 1
                X = row[tRows.fields.index("M")] + float(adjustDist)
                Ytop = float(row[elevID]) * 0.3048
                surfPnt = [float(X),float(Ytop* float(ve))]
                vals = list(row).copy()
                vals.append("{}_{}".format(id_pref, i))
                vals[-2] = surfPnt
                csAzi = xsec.cartesianToGeographic(angle=row[tRows.fields.index("LOC_ANGLE")])
                vals[tRows.fields.index("LocalXSEC_Azimuth")] = csAzi
                vals[tRows.fields.index("DistFromSection")] = row[tRows.fields.index("Distance")]
                try:
                    cur.insertRow(vals)
                    surfPnt.clear()
                except Exception as e:
                    management.AddMsgAndPrint(
                        "Could not create feature from objectid {} in {}\n{}".format(row[oid_i], locatedPoints,e), 1)
            del row
        del tRows, cur
        return surfPoints

    def placeEvents(inRoutes, idRteFld, eventTable, eventRteFld, fromVar, toVar, eventLay,wellid_fld):
        props = "{} LINE {} {}".format(eventRteFld, fromVar, toVar)
        arcpy.lr.MakeRouteEventLayer(inRoutes, idRteFld, eventTable, props, "layer")
        arcpy.management.CopyFeatures("layer","layer2")
        arcpy.management.MakeFeatureLayer("layer2","layer3","Shape_Length <> 0")
        arcpy.management.CopyFeatures("layer3",eventLay)
        descEvent = arcpy.ListFields(eventLay)
        if wellid_fld in descEvent:
            arcpy.management.DeleteIdentical(eventLay,wellid_fld)
        else:
            pass

    def plan2side(zm_line,ve,profile,id_field,elev_units,XSEC_NAME,adjustDist):
        fldOBJ = arcpy.ListFields(zm_line)
        flds = [f.name for f in fldOBJ if f.type != "Geometry"]
        flds.append("SHAPE@")

        # Providing search cursor on "zm_line" with the field listed from "fldOBJ"
        inRows = arcpy.da.SearchCursor(zm_line, flds)
        # Extending the list of fields to include the new ID field in the output. This is now at the end of the list, with
        # an index of -1.
        flds.append(id_field)
        outRows = arcpy.da.InsertCursor(profile, flds)

        i = 0
        for row in inRows:
            if elev_units == "Meters":
                i = i + 1
                vals = list(row).copy()
                # Extend vals by one more element to make room for the ID value
                vals.append("")
                array = []
                line = row[-1]
                for pnt in line[0]:
                    X = pnt.M + float(adjustDist)
                    Y = pnt.Z
                    array.append((X,Y * float(ve)))
                vals[-2] = array
                vals[-1] = "{}_SP_{}".format(XSEC_NAME,i)
                outRows.insertRow(vals)
            if elev_units == "Feet":
                i = i + 1
                vals = list(row).copy()
                # Extend vals by one more element to make room for the ID value
                vals.append("")
                array = []
                line = row[-1]
                for pnt in line[0]:
                    X = pnt.M + float(adjustDist)
                    Y = pnt.Z * 0.3048
                    array.append((X, Y * float(ve)))
                vals[-2] = array
                vals[-1] = "{}_SP_{}".format(XSEC_NAME, i)
                outRows.insertRow(vals)
            del row
        del inRows, outRows

    def zmLine_Generation(lineFeature,XSEC_NAME,defaultGDB,raster_surface):
        # We need to be able to have a line feature that has route information as well as elevation information. This
        # function establishes both for the desired cross-section line.
        lineFields = [f.name for f in arcpy.ListFields(lineFeature)]
        if ("XSEC" in lineFields and "DIRECTION" in lineFields):
            arcpy.management.MakeFeatureLayer(lineFeature,"lineLayers")
            arcpy.management.SelectLayerByAttribute("lineLayers","NEW_SELECTION","{}='{}'".format("XSEC",XSEC_NAME))

            # Add z values
            z_line = os.path.join(defaultGDB,"XSEC_{}_z".format(XSEC_NAME))
            management.testAndDelete(z_line)
            arcpy.ddd.InterpolateShape(raster_surface,"lineLayers",z_line)
            if int(arcpy.management.GetCount(z_line)[0]) == 0:
                management.AddMsgAndPrint(f"{XSEC_NAME} does not intersect the DEM.\nRemove cross-section line or deselect from analysis.",1)
                quit()
            with arcpy.da.SearchCursor(z_line,["DIRECTION"]) as cursor:
                for row in cursor:
                    if (row[0] == "W-E" or row[0] == "NW-SE" or row[0] == "N-S"):
                        quad = "Northwest"
                        management.AddMsgAndPrint(" - Analyzing line {} from the NW quadrant...".format(XSEC_NAME))
                    elif (row[0] == "SW-NE" or row[0] == "S-N"):
                        quad = "Southwest"
                        management.AddMsgAndPrint(" - Analyzing line {} from the SW quadrant...".format(XSEC_NAME))
                    elif (row[0] == "NE-SW" or row[0] == "E-W"):
                        quad = "Northeast"
                        management.AddMsgAndPrint(" - Analyzing line {} from the NE quadrant...".format(XSEC_NAME))
                    elif row[0] == "SE-NW":
                        quad = "Southeast"
                        management.AddMsgAndPrint(" - Analyzing line {} from the SE quadrant...".format(XSEC_NAME))
                    else:
                        management.AddMsgAndPrint(f"{XSEC_NAME} does not have a directionality.\nPlease review cross-section direction field before proceeding.",1)
                        quit()
                    del row
                del cursor

            cp = xsec.getCPValue(quadrant=quad)
            tmpLine = os.path.join(defaultGDB,"tempLine")
            arcpy.lr.CreateRoutes(
                in_line_features="lineLayers",
                route_id_field="XSEC",
                out_feature_class=tmpLine,
                measure_source="LENGTH",
                coordinate_priority=cp,
                measure_factor=1
            )
            zm_line = os.path.join(defaultGDB,"XSEC_{}_zm_{}".format(XSEC_NAME,os.path.splitext(os.path.basename(raster_surface))[0]))
            management.testAndDelete(zm_line)
            if arcpy.Describe(raster_surface).spatialReference.linearUnitName == "Meter":
                arcpy.lr.CreateRoutes(
                    in_line_features=z_line,
                    route_id_field="XSEC",
                    out_feature_class=zm_line,
                    measure_source="LENGTH",
                    coordinate_priority=cp,
                    measure_factor=1
                )
            elif arcpy.Describe(raster_surface).spatialReference.linearUnitName == "Foot":
                arcpy.lr.CreateRoutes(
                    in_line_features=z_line,
                    route_id_field="XSEC",
                    out_feature_class=zm_line,
                    measure_source="LENGTH",
                    coordinate_priority=cp,
                    measure_factor=0.3048
                )
            elif arcpy.Describe(raster_surface).spatialReference.linearUnitName == "Foot_US":
                arcpy.lr.CreateRoutes(
                    in_line_features=z_line,
                    route_id_field="XSEC",
                    out_feature_class=zm_line,
                    measure_source="LENGTH",
                    coordinate_priority=cp,
                    measure_factor=0.3048006096012192
                )

            # Now, we need to make sure the line starts where it is supposed to in the cross-section view.
            # Step 1: Find the start and end points of the reference line and the zm_line...
            moveLength = 0
            with arcpy.da.SearchCursor(zm_line,["SHAPE@"]) as cursor:
                for row in cursor:
                    rastGeom = row[0]
                    startPointRoute = rastGeom.firstPoint
                    endPointRoute = rastGeom.lastPoint
                    break
                del row, cursor
            with arcpy.da.SearchCursor(tmpLine,["SHAPE@"]) as cursor:
                for row in cursor:
                    refGeom = row[0]
                    break
                del row, cursor


            # Step 2: Get the extent of the lines to see if the profile has been offset...
            if startPointRoute.M == 0:
                m_value_on_orig = refGeom.measureOnLine(startPointRoute)
                if int(m_value_on_orig) == 0:
                    pass
                else:
                    moveLength += m_value_on_orig
                #if (startPointRef.X == startPointRoute.X and startPointRef.Y == startPointRoute.Y):
                #    pass
                #else:
                #    gapX = abs(startPointRoute.X - startPointRef.X)
                #    gapY = abs(startPointRoute.Y - startPointRef.Y)
                #    gapDist = ((gapX ** 2) + (gapY ** 2)) ** 0.5
                #    moveLength += gapDist
            if endPointRoute.M == 0:
                m_value_on_origEnd = refGeom.measureOnLine(endPointRoute)
                if int(m_value_on_origEnd) == 0:
                    pass
                else:
                    moveLength += m_value_on_origEnd
                #if (endPointRef.X == endPointRoute.X and endPointRef.Y == endPointRoute.Y):
                #    pass
                #else:
                #    gapX = abs(startPointRef.X - endPointRef.X)
                #    gapY = abs(startPointRef.Y - endPointRef.Y)
                #    gapDist = ((gapX ** 2) + (gapY ** 2)) ** 0.5
                #    moveLength += gapDist
            # Clean up the dataset at this stage...
            return (zm_line,moveLength)
        else:
            management.AddMsgAndPrint("The fields 'XSEC' and/or 'DIRECTION' is not found within the cross-section lines feature class. Please add both/either field.\nAcceptable terms for 'DIRECTION' are as follows:\n'W-E', 'NW-SE', 'E-W', 'SW-NE', 'S-N', 'N-S', 'NE-SW', 'SE-NW'",2)
            raise SystemError

    def gammaRayDisplay_Table(las,defaultGDB,wellid,depthUnits):
        skipRowNumber = format.find_header_row(las)
        df2 = pd.read_table(las,delimiter="\s+", skiprows=skipRowNumber)
        lastColumn = df2.columns[-1]
        if lastColumn == "Field1":
            df2 = df2.rename(columns={"Field1": "GAMMA", "~A": "DEPTH"})
        elif lastColumn == "GAMMARAY":
            df2 = df2.rename(columns={"GAMMARAY": "Field1", "DEPT": "GAMMA","~A":"DEPTH"})
        elif lastColumn == "GR":
            if depthUnits == "Meters":
                df2 = df2.rename(columns={"GR":"Field1","COUNT":"GR","EHT":"COUNT","TCPU":"EHT","Time":"TCPU",
                                          "DEPT[M]":"Time","~A":"DEPTH"})
            elif depthUnits == "Feet":
                df2 = df2.rename(columns={"GR": "Field1", "COUNT": "GR", "EHT": "COUNT", "TCPU": "EHT", "Time": "TCPU",
                                          "DEPT[FT]": "Time", "~A": "DEPTH"})
        elif lastColumn == "DTC_GAM":
            if depthUnits == "Meters":
                df2 = df2.rename(columns = {"DTC_GAM":"Field1","GAMMA":"DTC_GAM","POSDT":"GAMMA","POSCOUNT":"POSDT",
                                            "TIME":"POSCOUNT","SPEED":"TIME","DEPT[M]":"SPEED","~A":"DEPTH"})
            elif depthUnits == "Feet":
                df2 = df2.rename(columns={"DTC_GAM": "Field1", "GAMMA": "DTC_GAM", "POSDT": "GAMMA", "POSCOUNT": "POSDT",
                                          "TIME": "POSCOUNT", "SPEED": "TIME", "DEPT[FT]": "SPEED", "~A": "DEPTH"})
        df2 = df2.sort_values(by=["DEPTH"])
        df2 = df2[df2["GAMMA"] > -998]
        df2 = df2.reset_index(drop=True)
        df2.insert(0,"WELLID",wellid,True)
        df2["AVG5_GAMMA"] = df2["GAMMA"].rolling(window=5,min_periods=2,center=True).mean()
        wellid = wellid.replace(" ","_").replace("-","_")
        df2.to_csv(os.path.join(os.path.dirname(defaultGDB), "GammaRay_Table_{}.csv".format(wellid)),index=False)
        gammaRay_table = os.path.join(defaultGDB,"GammaRay_Table_{}".format(wellid))
        management.testAndDelete(gammaRay_table)
        arcpy.conversion.TableToTable(
            in_rows=os.path.join(os.path.dirname(defaultGDB), "GammaRay_Table_{}.csv".format(wellid)),
            out_path=defaultGDB,
            out_name="GammaRay_Table_{}".format(wellid)
        )
        # Return later to incorporate auto generation of gamma ray log profile.
        # Note for later: To display the path to the file in arcpy, define the message as :f'<a href="{file_path}">Open this file</a'
        # File path = "file:///C:/path/to/your/file.text"
        return gammaRay_table

    def pointsNearLine(custom,points,raster,int_table,xsecline,searchDist,parm_bhFields,parm_intFields,scratchDir):
        management.AddMsgAndPrint("* Locating wells near cross-section line(s)...")
        # First, we need to find the wells that are located in the search radius. Once selected, we will take all
        # those Well ID values and add them to a list to grab the corresponding table intervals.
        wellIds = []
        locations = arcpy.management.SelectLayerByLocation(
            in_layer=points,
            overlap_type="WITHIN_A_DISTANCE",
            select_features=xsecline,
            search_distance=searchDist,
            selection_type="NEW_SELECTION"
        )
        if custom == "true":
            bhFieldscustom = arcpy.ValueTable(3)
            bhFieldscustom.loadFromString(parm_bhFields)
            idFieldcustom = bhFieldscustom.getValue(0, 0)
            with arcpy.da.SearchCursor(locations, [idFieldcustom]) as cursor:
                for row in cursor:
                    wellIds.append(row[0])
                del row, cursor
        else:
            with arcpy.da.SearchCursor(locations, ["WELLID"]) as cursor:
                for row in cursor:
                    wellIds.append(row[0])
                del row, cursor
        xsecPoints = os.path.join(scratchDir, "LocalPoints_BH_MGS")
        management.testAndDelete(xsecPoints)
        with arcpy.EnvManager(maintainAttachments="NOT_MAINTAIN_ATTACHEMENTS", preserveGlobalIds=True):
            arcpy.management.CopyFeatures(
                in_features=locations,
                out_feature_class=xsecPoints
            )
        arcpy.management.SelectLayerByAttribute(
            in_layer_or_view=points,
            selection_type="CLEAR_SELECTION"
        )
        if int_table is None:
            xsecInterval = None
            pass
        else:
            xsecInterval = os.path.join(scratchDir, "LocalPoints_INT_MGS")
            management.testAndDelete(xsecInterval)
            if custom == "true":
                bhFieldscustom = arcpy.ValueTable(3)
                bhFieldscustom.loadFromString(parm_bhFields)
                idFieldcustom = bhFieldscustom.getValue(0, 0)
                routeWellsInt = arcpy.management.SelectLayerByAttribute(
                    in_layer_or_view=int_table,
                    selection_type="ADD_TO_SELECTION",
                    where_clause="{} IN {}".format(idFieldcustom,wellIds).replace("[", "(").replace("]", ")"),
                    invert_where_clause=None)
            else:
                routeWellsInt = arcpy.management.SelectLayerByAttribute(
                    in_layer_or_view=int_table,
                    selection_type="ADD_TO_SELECTION",
                    where_clause="WELLID IN {}".format(wellIds).replace("[", "(").replace("]", ")"),
                    invert_where_clause=None)
            with arcpy.EnvManager(maintainAttachments="NOT_MAINTAIN_ATTACHEMENTS", preserveGlobalIds=True):
                arcpy.management.CopyRows(
                    in_rows=routeWellsInt,
                    out_table=xsecInterval
                )
            arcpy.management.SelectLayerByAttribute(int_table, "CLEAR_SELECTION")

        # Now, we will prepare the trimmed down version of the boreholes so that it is only processing the points along
        # the line
        management.AddMsgAndPrint("* Extracting elevation measurements from DEM...")
        arcpy.ddd.AddSurfaceInformation(
            in_feature_class=xsecPoints,
            in_surface=raster,
            out_property="Z",
            method="BILINEAR",
            sample_distance=None,
            z_factor=1,
            pyramid_level_resolution=0,
            noise_filtering=""
        )
        arcpy.management.AddField(
            in_table=xsecPoints,
            field_name="DEM_ELEV",
            field_type="DOUBLE",
            field_is_nullable="NULLABLE",
            field_is_required="NON_REQUIRED"
        )
        arcpy.management.CalculateField(
            in_table=xsecPoints,
            field="DEM_ELEV",
            expression='!Z!'
        )
        arcpy.management.DeleteField(xsecPoints, ["Z"])
        with arcpy.da.UpdateCursor(xsecPoints, ["DEM_ELEV"]) as cursor:
            for row in cursor:
                if row[0] is None:
                    cursor.deleteRow()
            del row, cursor
        management.AddMsgAndPrint("* Formatting and finding required fields (local copy)...")
        if custom == "true":
            bhFields = arcpy.ValueTable(3)
            bhFields.loadFromString(parm_bhFields)
            idField = bhFields.getValue(0, 0)
            depthField = bhFields.getValue(0, 1)
            elevField = bhFields.getValue(0, 2)

            newTopDepthField = None
            newBotDepthField = None

            if int_table == "":
                pass
            else:
                intervFields = arcpy.ValueTable(3)
                intervFields.loadFromString(parm_intFields)
                interIdField = intervFields.getValue(0, 0)
                topDepthField = intervFields.getValue(0, 1)
                botDepthField = intervFields.getValue(0, 2)

                with arcpy.da.UpdateCursor(xsecInterval, [botDepthField, topDepthField]) as cursor:
                    for row in cursor:
                        if (row[0] == 0 and row[1] == 0):
                            cursor.deleteRow()
                        else:
                            pass
                    del row, cursor
                try:
                    arcpy.management.AlterField(
                        in_table=xsecInterval,
                        field=interIdField,
                        new_field_name="WELLID"
                    )
                except:
                    pass
                try:
                    arcpy.management.AlterField(
                        in_table=xsecInterval,
                        field=topDepthField,
                        new_field_name="DEPTH_TOP"
                    )
                    newTopDepthField = "DEPTH_TOP"
                except:
                    pass
                try:
                    arcpy.management.AlterField(
                        in_table=xsecInterval,
                        field=botDepthField,
                        new_field_name="BOT_DEPTH"
                    )
                    newBotDepthField = "BOT_DEPTH"
                except:
                    newBotDepthField = "DEPTH"
                if "DEPTH_TOP" in [f.name for f in arcpy.ListFields(xsecInterval)]:
                    pass
                else:
                    arcpy.management.AddField(
                        in_table=xsecInterval,
                        field_name="DEPTH_TOP",
                        field_type="DOUBLE",
                        field_is_nullable="NULLABLE",
                        field_is_required="NON_REQUIRED"
                    )
                    arcpy.management.CalculateField(
                        in_table=xsecInterval,
                        field="DEPTH_TOP",
                        expression='!DEPTH! - !THICKNESS!'
                    )
                    with arcpy.da.UpdateCursor(xsecInterval, ["DEPTH", "DEPTH_TOP"]) as cursor:
                        for row in cursor:
                            if (row[0] == 0 and row[1] == 0):
                                cursor.deleteRow()
                            else:
                                pass
                        del row, cursor
            try:
                arcpy.management.AlterField(
                    in_table=xsecPoints,
                    field=idField,
                    new_field_name="WELLID"
                )
            except:
                pass
            try:
                arcpy.management.AlterField(
                    in_table=xsecPoints,
                    field=depthField,
                    new_field_name="WELL_DEPTH"
                )
            except:
                pass
            if elevField == "":
                newElevField = "DEM_ELEV"
            else:
                newElevField = elevField
        else:
            newElevField = "DEM_ELEV"
            newTopDepthField = "DEPTH_TOP"
            newBotDepthField = "DEPTH"

        return xsecPoints,xsecInterval,"WELLID",newElevField,"WELL_DEPTH",newTopDepthField,newBotDepthField

    def rasterProject_GeoProj(surfRaster,lines,scratchDir):
        rasterSR = arcpy.Describe(surfRaster).spatialReference
        if rasterSR.type == "Geographic":
            management.AddMsgAndPrint("* Raster is in a geographic coordinate system. Reprojecting to area for cross-section view...")
            with arcpy.EnvManager(
                    extent=arcpy.Describe(lines).extent):
                arcpy.management.ProjectRaster(
                    in_raster=surfRaster,
                    out_raster=os.path.join(scratchDir,"Raster_Project"),
                    out_coor_system=arcpy.SpatialReference(102100),
                    resampling_type="NEAREST",
                    cell_size="",
                    geographic_transform=None,
                    Registration_Point=None
                )
            outRaster = os.path.join(scratchDir,"Raster_Project")
        else:
            outRaster = surfRaster
            #rasterUnits = str(rasterSR.linearUnitName)
            #if rasterUnits != "Meter":
            #    management.AddMsgAndPrint("* Raster's linear units are not in meters. Reprojecting to area for cross-section view...")
            #    with arcpy.EnvManager(extent=arcpy.Describe(lines).extent):
            #        arcpy.management.ProjectRaster(
            #            in_raster=surfRaster,
            #            out_raster=os.path.join(scratchDir, "Raster_Project"),
            #            out_coor_system=arcpy.SpatialReference(102100),
            #            resampling_type="NEAREST",
            #            cell_size="",
            #            geographic_transform=None,
            #            Registration_Point=None
            #        )
            #    outRaster = os.path.join(scratchDir, "Raster_Project")
            #else:
            #    outRaster = surfRaster
        return outRaster
