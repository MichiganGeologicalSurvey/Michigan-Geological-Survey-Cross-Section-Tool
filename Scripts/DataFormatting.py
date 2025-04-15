# *****************************************************
# *****************************************************
# DataFormatting.py
# Version: 1.0
# Date: 5/31/2024
# Last Modified Date: 5/31/2024
# Original Author: Matthew Bell, Michigan Geological Survey, matthew.e.bell@wmich.edu
# Description: A Python custom script to reformat Wellogic data or other datasets into a format reviewed by the Michigan Geological Survey.
# *****************************************************
# *****************************************************

import os
import arcpy
import Utility_Functions as uf
import Dictonary
import DataFormatting_PullGeology

# Establish the parameters...
# Establish coordinate system
src = arcpy.SpatialReference(102121)
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

def dataFormatting(geologyGDB, prjName, wellPoints,lithTable,accessory,username,password,prjExtent,prjDEM,reviewTable):
    uf.management.AddMsgAndPrint("Formatting lithology groups...")
    aggTable = "https://services1.arcgis.com/vFQXQuqACTPxa4Yc/arcgis/rest/services/Lithology_Aggredation_Terms/FeatureServer/0"
    textGroup = ["Coarse", "Fine", "Medium", "Fine To Coarse", "Fine To Medium", "Medium To Coarse", "Very Coarse",
                      "Very Fine",
                      "Very Fine-Coarse", "Very Fine-Fine", "Very Fine-Medium"]
    conGroup = ["Dense", "Dry", "Gummy", "Karst", "Porous", "Strips", "Cemented", "Very Hard", "Broken",
                     "Fractured", "Heaving/Quick",
                     "Stringers", "Swelling", "Water Bearing", "Weathered", "Wet/Moist", "Firm", "Hard", "Soft"]
    secGroup = ["Clayey", "Dolomitic", "Fill", "Gravely", "Organic", "Sandy", "Silty", "Stoney", "W/Boulders",
                     "W/Clay", "W/Coal",
                     "W/Cobbles", "W/Dolomite", "W/Gravel", "W/Gypsum", "W/Limestone", "W/Pyrite", "W/Sand",
                     "W/Sandstone", "W/Shale",
                     "W/Silt", "W/Stones", "Wood"]
    colorGroup = ["Black", "Black & Gray", "Black & White", "Blue", "Brown", "Cream", "Dark Gray", "Gray",
                       "Gray & White", "Green",
                       "Light Brown", "Light Gray", "Orange", "Pink", "Red", "Rust", "Tan", "Tan & Gray", "White",
                       "Yellow"]
    groupGroup = ["Alpena Ls", "Amherstburg Fm", "Antrim Shale", "Bass Island Group", "Bayport Ls",
                       "Bedford Shale",
                       "Bell Shale",
                       "Berea Ss", "Black River Group", "Bois Blanc Fm", "Burnt Bluff Group", "Cabot Head Shale",
                       "Cataract Group",
                       "Coldwater Shale", "Detroit River Group", "Dresbach Ss", "Dundee Ls", "Eau Claire Member",
                       "Ellsworth Shale",
                       "Engadine Dol", "Franconia Ss", "Freda Ss", "Garden Island Fm", "Glenwood Member",
                       "Grand Rapids Group",
                       "Grand River Fm", "Jacobsville Ss", "Jordan Ss", "Lake Superior Group", "Lodi Member",
                       "Lucas Fm",
                       "Manistique Group", "Manitoulin Dol", "Marshall Ss", "Michigammee Fm", "Michigan Fm",
                       "Mt. Simon Ss",
                       "Napolean Ss", "New Richmond Ss", "Niagara Group", "Nonesuch Shale", "Oneota Dol", "Parma Ss",
                       "Prairie Du Chien Group", "Precambrian", "Queenston Shale", "Red Beds", "Richmond Group",
                       "Rogers City Ls",
                       "Saginaw Fm", "Salina Group", "Shakopee Dol", "Squaw Bay Ls", "St. Lawrence Member",
                       "St. Peter Ss",
                       "Sylvania Ss", "Traverse Group", "Trempealeau Fm", "Trenton Group", "Utica Shale"]
    bdrkGroup = []
    clayGroup = []
    claySandGroup = []
    tillGroup = []
    topsoilGroup = []
    sandGroup = []
    gravelGroup = []
    organicsGroup = []
    sandFineGroup = []
    sandGravelGroup = []
    unkGroup = []
    with arcpy.da.SearchCursor(aggTable,[field.name for field in arcpy.ListFields(aggTable)]) as cursor:
        for row in cursor:
            if row[5] == "BDRK":
                bdrkGroup.append(row[4])
            elif row[5] == "CLAY":
                clayGroup.append(row[4])
            elif row[5] == "CLSA":
                claySandGroup.append(row[4])
            elif row[5] == "DIAM":
                tillGroup.append(row[4])
            elif row[5] == "TOPS":
                topsoilGroup.append(row[4])
            elif row[5] == "SAND":
                sandGroup.append(row[4])
            elif row[5] == "GRAV":
                gravelGroup.append(row[4])
            elif row[5] == "ORGA":
                organicsGroup.append(row[4])
            elif row[5] == "FSAN":
                sandFineGroup.append(row[4])
            elif row[5] == "SAGR":
                sandGravelGroup.append(row[4])
            elif row[5] == "UNK":
                unkGroup.append(row[4])
        del row
        del cursor
    uf.management.AddMsgAndPrint("Add applicable domains if necessary...")
    domainNames = ["Color","Consistency","Drilling","GroupNames","LithAgg","LithAquifer","PrimaryLith",
                    "SecondaryLith","Simplified","WellStatus","TestMethod","Texture","Verification","WellAquifer",
                    "WellType","CasingType","BDRK_GroupNames","Landsystem","DepthFlag","ElevationFlag","SWLFlag",
                   "LocationAQField","AQUnits","ScreenType","AQFlag","ScreenFlag"]
    desc = arcpy.Describe(geologyGDB)
    domains = desc.domains
    for domain in domains:
        if domain in domainNames:
            try:
                arcpy.management.DeleteDomain(in_workspace=geologyGDB,domain_name=domain)
            except:
                uf.management.AddMsgAndPrint("Domain in use. Passing to next step...")
                pass
    if "Color" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"Color", "Accepted color terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.colors:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"Color",code,Dictonary.colors[code])
    if "Consistency" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"Consistency", "Accepted consistency terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.consistency:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"Consistency",code,Dictonary.consistency[code])
    if "Drilling" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"Drilling", "Accepted drilling method terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.drillDict:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"Drilling",code,Dictonary.drillDict[code])
    if "BDRK_GroupNames" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"BDRK_GroupNames", "Group names for all formations found in Michigan","TEXT", "CODED")
        for code in Dictonary.formationNames:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"BDRK_GroupNames",code,Dictonary.formationNames[code])
    if "LithAquifer" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"LithAquifer", "Accepted concatenated terms for aquifer type","TEXT", "CODED")
        for code in Dictonary.lithAquifer:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"LithAquifer",code,Dictonary.lithAquifer[code])
    if "LithAgg" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"LithAgg", "Accepted aggregation lithology terms","TEXT", "CODED")
        for code in Dictonary.aggDict:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"LithAgg",code,Dictonary.aggDict[code])
    if "PrimaryLith" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"PrimaryLith", "Accepted primary lithology terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.primLithology:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"PrimaryLith",code,Dictonary.primLithology[code])
    if "SecondaryLith" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"SecondaryLith", "Accepted modifier lithology terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.lithModifer:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"SecondaryLith",code,Dictonary.lithModifer[code])
    if "Simplified" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"Simplified", "Accepted simplified lithology terms","TEXT", "CODED")
        for code in Dictonary.lithSimplified:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"Simplified",code,Dictonary.lithSimplified[code])
    if "WellStatus" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"WellStatus", "Accepted well status terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.wellStatus:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"WellStatus",code,Dictonary.wellStatus[code])
    if "TestMethod" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"TestMethod", "Accepted pump test methods terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.testMeth:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"TestMethod",code,Dictonary.testMeth[code])
    if "Texture" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"Texture", "Accepted texture/sediment size terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.texture:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"Texture",code,Dictonary.texture[code])
    if "Verification" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"Verification", "Verification of data quality","TEXT", "CODED")
        for code in Dictonary.verification:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"Verification",code,Dictonary.verification[code])
    if "WellAquifer" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"WellAquifer", "Accepted well aquifer terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.wellAquifer:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"WellAquifer",code,Dictonary.wellAquifer[code])
    if "WellType" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"WellType", "Accepted well type terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.wellTypes:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"WellType",code,Dictonary.wellTypes[code])
    if "CasingType" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"CasingType", "Accepted casing type terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.caseDict:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"CasingType",code,Dictonary.caseDict[code])
    if "Landsystem" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"Landsystem", "Accepted casing type terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.landsystems:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"Landsystem",code,Dictonary.landsystems[code])
    if "DepthFlag" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"DepthFlag", "Accepted casing type terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.flagDepth:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"DepthFlag",code,Dictonary.flagDepth[code])
    if "ElevationFlag" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"ElevationFlag", "Accepted casing type terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.flagElev:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"ElevationFlag",code,Dictonary.flagElev[code])
    if "SWLFlag" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"SWLFlag", "Accepted casing type terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.flagSWL:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"SWLFlag",code,Dictonary.flagSWL[code])
    if "AQFlag" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"AQFlag", "Accepted casing type terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.flagAQ:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"AQFlag",code,Dictonary.flagAQ[code])
    if "ScreenFlag" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"ScreenFlag", "Accepted casing type terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.flagScreen:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"ScreenFlag",code,Dictonary.flagScreen[code])
    if "LocationAQField" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"LocationAQField", "Accepted casing type terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.reclassAQ:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"LocationAQField",code,Dictonary.reclassAQ[code])
    if "AQUnits" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"AQUnits", "Accepted casing type terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.aqUnits:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"AQUnits",code,Dictonary.aqUnits[code])
    if "ScreenType" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"ScreenType", "Accepted casing type terms from Wellogic","TEXT", "CODED")
        for code in Dictonary.screenType:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"ScreenType",code,Dictonary.screenType[code])
    if "LocMethods" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"LocMethods", "Methodology for locating the well from Wellogic","TEXT", "CODED")
        for code in Dictonary.loc_methods:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"LocMethods",code,Dictonary.loc_methods[code])
    if "ElevMethods" in domains:
        pass
    else:
        arcpy.management.CreateDomain(geologyGDB,"ElevMethods", "Methodology for the elevation from Wellogic","TEXT", "CODED")
        for code in Dictonary.elev_methods:
            arcpy.management.AddCodedValueToDomain(geologyGDB,"ElevMethods",code,Dictonary.elev_methods[code])
    uf.management.AddMsgAndPrint("BEGIN FORMATTING THE LITHOLOGY TABLE PROVIDED")
    try:
        # First, we need to see if the user wants to add the extra data to the lithology table/has the ability to do so.
        if accessory == "true":
            extraLith = DataFormatting_PullGeology.extractGeologyData(
                wells=wellPoints,
                lithTable=lithTable,
                username=username,
                password=password,
                output=scratchDir
            )
            arcpy.management.AddField(
                in_table=extraLith[0],
                field_name="RELATE",
                field_type="TEXT",
                field_length=16
            )
            arcpy.management.CalculateField(
                in_table=extraLith[0],
                field="RELATE",
                expression='"{}_{}".format(!WELLID!,str(!SEQ_NUM!).rjust(3,"0"))'
            )
        else:
            pass
    except:
        uf.management.AddMsgAndPrint("ERROR 001: Could not extract accessory data")

    try:
        uf.management.AddMsgAndPrint(
            " - Create copy of {} and create new fields...".format(os.path.splitext(os.path.basename(lithTable))[0])
        )
        try:
            newLith = os.path.join(scratchDir,"Validation_" + os.path.splitext(os.path.basename(lithTable))[0].replace(" ","_"))
            uf.management.testAndDelete(newLith)
        except:
            newLith = os.path.join(scratchDir,"Validation_" + lithTable.replace(" ", "_"))
            uf.management.testAndDelete(newLith)
        uf.management.testAndDelete(newLith)
        arcpy.conversion.ExportTable(
            in_table=lithTable,
            out_table=newLith
        )
        # Now we need to add all the fields we will need before transfering them to the fiinal table.
        arcpy.management.AddField(in_table=newLith, field_name="PRIM_CONC", field_type="TEXT", field_length=255)
        arcpy.management.AddField(in_table=newLith, field_name="TEXTURE", field_type="TEXT", field_length=255)
        arcpy.management.AddField(in_table=newLith, field_name="CON", field_type="TEXT", field_length=255)
        arcpy.management.AddField(in_table=newLith, field_name="SEC_DESC", field_type="TEXT", field_length=255)
        arcpy.management.AddField(in_table=newLith, field_name="AQ", field_type="TEXT", field_length=255)
        arcpy.management.AddField(in_table=newLith, field_name="AGG", field_type="TEXT", field_length=255)
        if accessory == "true":
            arcpy.management.AddField(in_table=newLith, field_name="RELATE", field_type="TEXT", field_length=255)
            arcpy.management.AddField(in_table=newLith, field_name="THIRD_DESC", field_type="TEXT", field_length=255)
            arcpy.management.AddField(in_table=newLith, field_name="GROUP_NAME", field_type="TEXT", field_length=255)
            arcpy.management.AddField(in_table=newLith, field_name="COMMENTS", field_type="TEXT", field_length=10000)
        else:
            pass

        # Now we are going to attempt to calculate the new fields for later appending and data transformation.
        arcpy.management.CalculateField(
            in_table=newLith,
            field="AQ",
            expression='!AQTYPE! + "-" + !MAQTYPE!'
        )
        concBlock = ("""def Combo(prim,second):
            if second == " ":
                return prim + "_"
            else:
                return prim + "_" + second""")
        arcpy.management.CalculateField(
            in_table=newLith,
            field="PRIM_CONC",
            expression="Combo(!PRIM_LITH!,!LITH_MOD!)",
            code_block=concBlock
        )
        with arcpy.da.UpdateCursor(newLith,["PRIM_CONC","AGG"]) as cursor:
            for row in cursor:
                if row[0] in bdrkGroup:
                    row[1] = "BDRK"
                elif row[0] in clayGroup:
                    row[1] = "CLAY"
                elif row[0] in claySandGroup:
                    row[1] = "CLSA"
                elif row[0] in tillGroup:
                    row[1] = "DIAM"
                elif row[0] in topsoilGroup:
                    row[1] = "TOPS"
                elif row[0] in sandGroup:
                    row[1] = "SAND"
                elif row[0] in gravelGroup:
                    row[1] = "GRAV"
                elif row[0] in organicsGroup:
                    row[1] = "ORGA"
                elif row[0] in sandFineGroup:
                    row[1] = "FSAN"
                elif row[0] in sandGravelGroup:
                    row[1] = "SAGR"
                elif row[0] in unkGroup:
                    row[1] = "UNK"
                else:
                    row[1] = "UNK"
                cursor.updateRow(row)
            del row
            del cursor
        with arcpy.da.UpdateCursor(newLith, ["LITH_MOD","TEXTURE","CON","SEC_DESC"]) as cursor:
            for row in cursor:
                if row[0] in textGroup:
                    row[1] = row[0].upper()
                elif row[0] in conGroup:
                    row[2] = row[0].upper()
                elif row[0] in secGroup:
                    row[3] = row[0].upper()
                else:
                    pass
                cursor.updateRow(row)
            del row
            del cursor
        with arcpy.da.UpdateCursor(newLith, "COLOR") as cursor:
            for row in cursor:
                if row[0] in colorGroup:
                    row[0] = row[0].upper()
                else:
                    row[0] = None
                cursor.updateRow(row)
            del row
            del cursor
        if accessory == "true":
            arcpy.management.CalculateField(
                in_table=newLith,
                field="RELATE",
                expression='"{}_{}".format(!WELLID!,str(!SEQ_NUM!).rjust(3,"0"))'
            )
            arcpy.management.JoinField(
                in_data=newLith,
                in_field="RELATE",
                join_table=extraLith[0],
                join_field="RELATE",
                fields="FORMATION;GEO_COMMENTS"
            )
            with arcpy.da.UpdateCursor(newLith,["FORMATION","GEO_COMMENTS","THIRD_DESC","GROUP_NAME","COMMENTS","COLOR","TEXTURE","CON","SEC_DESC"]) as cursor:
                for row in cursor:
                    if row[1] is not None:
                        row[4] = row[1]
                    cursor.updateRow(row)
                    if row[0] in textGroup:
                        row[6] = row[0].upper()
                    elif row[0] in conGroup:
                        row[7] = row[0].upper()
                    elif row[0] in secGroup:
                        if row[8] is None:
                            row[8] = row[0].upper()
                        else:
                            row[2] = row[0].upper()
                    elif row[0] in colorGroup:
                        if row[5] == None:
                            row[5] = row[0].upper()
                        else:
                            pass
                    elif row[0] in groupGroup:
                        if row[0] == "Alpena Ls":
                            row[3] = "ALL"
                        elif row[0] == "Antrim Shale":
                            row[3] = "ANT"
                        elif row[0] == "Bass Island Group":
                            row[3] = "BIG"
                        elif row[0] == "Bayport Ls":
                            row[3] = "BAY"
                        elif row[0] == "Bedford Shale":
                            row[3] = "BED"
                        elif row[0] == "Bell Shale":
                            row[3] = "BLS"
                        elif row[0] == "Berea Ss":
                            row[3] = "BER"
                        elif row[0] == "Black River Group":
                            row[3] = "BRG"
                        elif row[0] == "Bois Blanc Fm":
                            row[3] = "BBF"
                        elif row[0] == "Burnt Bluff Group":
                            row[3] = "BBG"
                        elif row[0] == "Cabot Head Shale":
                            row[3] = "CHS"
                        elif row[0] == "Cataract Group":
                            row[3] = "CAG"
                        elif row[0] == "Coldwater Shale":
                            row[3] = "CWT"
                        elif row[0] == "Collingwood Shale":
                            row[3] = "CSM"
                        elif row[0] == "Detroit River Group":
                            row[3] = "DRG"
                        elif row[0] == "Dresbach Ss":
                            row[3] = "DSS"
                        elif row[0] == "Dundee Ls":
                            row[3] = "DDL"
                        elif row[0] == "Eau Claire Member":
                            row[3] = "ECM"
                        elif row[0] == "Ellsworth Shale":
                            row[3] = "ELL"
                        elif row[0] == "Engadine Dol":
                            row[3] = "ENG"
                        elif row[0] == "Franconia Ss":
                            row[3] = "FRS"
                        elif row[0] == "Freda Ss":
                            row[3] = "FSS"
                        elif row[0] == "Garden Island Fm":
                            row[3] = "GIF"
                        elif row[0] == "Glenwood Member":
                            row[3] = "GLM"
                        elif row[0] == "Grand Rapids Group":
                            row[3] = "GRG"
                        elif row[0] == "Grand River Fm":
                            row[3] = "GRF"
                        elif row[0] == "Jacobsville Ss":
                            row[3] = "JAC"
                        elif row[0] == "Jordan Ss":
                            row[3] = "JSS"
                        elif row[0] == "Lake Superior Group":
                            row[3] = "LSG"
                        elif row[0] == "Lodi Member":
                            row[3] = "LOD"
                        elif row[0] == "Lucas Fm":
                            row[3] = "LUF"
                        elif row[0] == "Manistique Group":
                            row[3] = "MQG"
                        elif row[0] == "Manitoulin Dol":
                            row[3] = "MND"
                        elif row[0] == "Marshall Ss":
                            row[3] = "MAR"
                        elif row[0] == "Michigammee Fm":
                            row[3] = "MGF"
                        elif row[0] == "Michigan Fm":
                            row[3] = "MIF"
                        elif row[0] == "Mt. Simon Ss":
                            row[3] = "MSS"
                        elif row[0] == "Napolean Ss":
                            row[3] = "NSS"
                        elif row[0] == "New Richmond Ss":
                            row[3] = "NRS"
                        elif row[0] == "Niagara Group":
                            row[3] = "NIA"
                        elif row[0] == "Nonesuch Shale":
                            row[3] = "NSF"
                        elif row[0] == "Oneota Dol":
                            row[3] = "OND"
                        elif row[0] == "Parma Ss":
                            row[3] = "PSS"
                        elif row[0] == "Prairie Du Chien Group":
                            row[3] = "PDC"
                        elif row[0] == "Precambrian":
                            row[3] = "PRE"
                        elif row[0] == "Queenston Shale":
                            row[3] = "QUS"
                        elif row[0] == "Red Beds":
                            row[3] = "RBD"
                        elif row[0] == "Richmond Group":
                            row[3] = "RIG"
                        elif row[0] == "Rogers City Ls":
                            row[3] = "RCL"
                        elif row[0] == "Saginaw Fm":
                            row[3] = "SAG"
                        elif row[0] == "Salina Group":
                            row[3] = "SAL"
                        elif row[0] == "Shakopee Dol":
                            row[3] = "SHD"
                        elif row[0] == "Squaw Bay Ls":
                            row[3] = "SBL"
                        elif row[0] == "St. Lawrence Member":
                            row[3] = "SLM"
                        elif row[0] == "St. Peter Ss":
                            row[3] = "SPS"
                        elif row[0] == "Sylvania Ss":
                            row[3] = "SSS"
                        elif row[0] == "Traverse Group":
                            row[3] = "TRG"
                        elif row[0] == "Trempealeau Fm":
                            row[3] = "TMP"
                        elif row[0] == "Trenton Group":
                            row[3] = "TRN"
                        elif row[0] == "Utica Shale":
                            row[3] = "USM"
                        else:
                            row[3] = None
                    else:
                        pass
                    cursor.updateRow(row)
                del row
                del cursor
            arcpy.management.DeleteField(lithTable,["FORMATION","GEO_COMMENTS"])
        else:
            pass
    except:
        uf.management.AddMsgAndPrint("ERROR 002: Failed to format old table",2)
        raise SystemError
    try:
        # Now, we need to build the new lithology table...
        try:
            finalLith = os.path.join(geologyGDB,"Co" + os.path.splitext(os.path.basename(lithTable))[0].replace(" ","_")+"_FINAL")
            uf.management.testAndDelete(finalLith)
        except:
            finalLith = os.path.join(geologyGDB, "Co" + lithTable.replace(" ","_") + "_FINAL")
        uf.management.AddMsgAndPrint("Creating final lithology table {} and appending old data from {}...".format(
            os.path.splitext(os.path.basename(finalLith))[0],os.path.splitext(os.path.basename(newLith))[0])
        )
        arcpy.management.CreateTable(geologyGDB,os.path.splitext(os.path.basename(finalLith))[0])
        arcpy.management.AddField(in_table=finalLith,field_name="WELLID",field_type="TEXT",field_length=12,
                                  field_alias="Well ID")
        arcpy.management.AddField(in_table=finalLith, field_name="SEQ_NUM", field_type="SHORT",
                                  field_alias="Sequence Number")
        arcpy.management.AddField(in_table=finalLith, field_name="PRIM_LITH", field_type="TEXT", field_length=50,
                                  field_alias="Primary Lithology", field_domain="PrimaryLith")
        arcpy.management.AddField(in_table=finalLith, field_name="LITH_MOD", field_type="TEXT", field_length=50,
                                  field_alias="Lithology Modifier", field_domain="SecondaryLith")
        arcpy.management.AddField(in_table=finalLith, field_name="DEPTH", field_type="DOUBLE",
                                  field_alias="Depth: Bottom (ft)")
        arcpy.management.AddField(in_table=finalLith, field_name="THICKNESS", field_type="DOUBLE",
                                  field_alias="Thickness of Stratum (ft)")
        arcpy.management.AddField(in_table=finalLith, field_name="AQTYPE", field_type="TEXT", field_length=1,
                                  field_alias="Aquifer Type")
        arcpy.management.AddField(in_table=finalLith, field_name="CLASS", field_type="TEXT", field_length=16,
                                  field_alias="Aquifer Classification")
        arcpy.management.AddField(in_table=finalLith, field_name="EFFECT", field_type="DOUBLE",
                                  field_alias="Modifier Effect")
        arcpy.management.AddField(in_table=finalLith, field_name="MAQTYPE", field_type="TEXT", field_length=3,
                                  field_alias="Modified Aquifer Classification")
        arcpy.management.AddField(in_table=finalLith, field_name="COLOR", field_type="TEXT", field_length=50,
                                  field_alias="Color", field_domain="Color")
        arcpy.management.AddField(in_table=finalLith, field_name="DRLLR_DESC", field_type="TEXT", field_length=1000,
                                  field_alias="Full Driller Description")
        arcpy.management.AddField(in_table=finalLith, field_name="SEDIMENT", field_type="TEXT", field_length=7,
                                  field_alias="Simplified Sediment Class",field_domain="Simplified")
        arcpy.management.AddField(in_table=finalLith, field_name="LITH_AGG", field_type="TEXT", field_length=4,
                                  field_alias="Aggregated Lithology Unit",field_domain="LithAgg")
        arcpy.management.AddField(in_table=finalLith, field_name="CAL_TEXTURE", field_type="TEXT", field_length=50,
                                  field_alias="Sediment Texture Size",field_domain="Texture")
        arcpy.management.AddField(in_table=finalLith, field_name="CALC_CONSISTENCY", field_type="TEXT", field_length=50,
                                  field_alias="Consistency",field_domain="Consistency")
        arcpy.management.AddField(in_table=finalLith, field_name="CALC_LITH_MOD_1", field_type="TEXT", field_length=50,
                                  field_alias="Lithology Modifier (Calc)",field_domain="SecondaryLith")
        arcpy.management.AddField(in_table=finalLith, field_name="CALC_LITH_MOD_2", field_type="TEXT", field_length=50,
                                  field_alias="Second Lithology Modifier (Calc)",field_domain="SecondaryLith")
        arcpy.management.AddField(in_table=finalLith, field_name="DEPTH_TOP", field_type="DOUBLE",
                                  field_alias="Depth: Top (ft)")
        arcpy.management.AddField(in_table=finalLith, field_name="AQUIFER_NAME", field_type="TEXT", field_length=12,
                                  field_alias="Concatanated Aquifer Type",field_domain="LithAquifer")
        arcpy.management.AddField(in_table=finalLith, field_name="FIRST_BDRK", field_type="TEXT", field_length=2,
                                  field_alias="First True Bedrock Encountered?",field_domain="Verification")
        arcpy.management.AddField(in_table=finalLith, field_name="BDRK_GROUP", field_type="TEXT", field_length=12,
                                  field_alias="Bedrock Group/Formation",field_domain="BDRK_GroupNames")
        arcpy.management.AddField(in_table=finalLith, field_name="GLA_GROUP", field_type="TEXT", field_length=12,
                                  field_alias="Glacial Group/Formation", field_domain="GroupNames")
        arcpy.management.AddField(in_table=finalLith, field_name="GEO_COMMENTS", field_type="TEXT", field_length=1000,
                                  field_alias="Lithology Comments")
        arcpy.management.AddField(in_table=finalLith, field_name="VERIFIED", field_type="TEXT", field_length=2,
                                  field_alias="Lithology Verified by MGS?",field_domain="Verification")
        arcpy.management.AddGlobalIDs(in_datasets=finalLith)
        simpleExpression = ("""var aggregate = $feature.LITH_AGG;
            var sediment = When(Equals(aggregate,"UNK"),"UNK",
                                Equals(aggregate,"BDRK"),"BEDROCK",
                                Equals(aggregate,"CLAY") || Equals(aggregate,"FSAN"),"FINE",
                                Equals(aggregate,"GRAV") || Equals(aggregate,"SAND") || Equals(aggregate,"SAGR"),"COARSE",
                                Equals(aggregate,"CLSA") || Equals(aggregate,"DIAM"),"MIXED",
                                Equals(aggregate,"TOPS") || Equals(aggregate,"ORGA"),"ORGANIC",
                                "UNK");
            return sediment""")
        drillerExpression = ("""var driller = [$feature.COLOR,$feature.PRIM_LITH,$feature.CAL_TEXTURE,$feature.CALC_LITH_MOD_1,$feature.CALC_LITH_MOD_2,$feature.CALC_CONSISTENCY];
            var desc = [];
            for (var i in driller) {
                if (!IsEmpty(driller[i])){
                    desc[Count(desc)] = Upper(driller[i]);
                }
            }
            return Concatenate(desc," ")""")
        arcpy.management.AddAttributeRule(
            in_table=finalLith,
            name="SimpleLith",
            type="CALCULATION",
            script_expression=simpleExpression,
            field="SEDIMENT",
            triggering_events=["INSERT","UPDATE"]
        )
        arcpy.management.AddAttributeRule(
            in_table=finalLith,
            name="DrillerDesc",
            type="CALCULATION",
            script_expression=drillerExpression,
            field="DRLLR_DESC",
            triggering_events=["INSERT", "UPDATE"]
        )
    except:
        uf.management.AddMsgAndPrint("ERROR 003: Failed to make new table with standard fields",2)
        raise SystemError
    try:
        lithMappings = ""
        lithMappings = arcpy.FieldMappings()
        lithMappings.addTable(finalLith)
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings,oldTable=newLith,oldField="WELLID",newField="WELLID",newFieldAlias="Well ID",
            newFieldType="TEXT"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="SEQ_NUM", newField="SEQ_NUM", newFieldAlias="Sequence Number",
            newFieldType="SHORT"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="PRIM_LITH", newField="PRIM_LITH", newFieldAlias="Primary Lithology",
            newFieldType="TEXT"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="DEPTH", newField="DEPTH", newFieldAlias="Depth: Bottom (ft)",
            newFieldType="DOUBLE"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="THICKNESS", newField="THICKNESS", newFieldAlias="Thickness of Stratum (ft)",
            newFieldType="DOUBLE"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="COLOR", newField="COLOR", newFieldAlias="Color",
            newFieldType="TEXT"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="AQTYPE", newField="AQTYPE", newFieldAlias="Aquifer Type",
            newFieldType="TEXT"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="CLASS", newField="CLASS", newFieldAlias="Aquifer Classification",
            newFieldType="TEXT"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="MAQTYPE", newField="MAQTYPE", newFieldAlias="Modified Aquifer Classification",
            newFieldType="TEXT"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="EFFECT", newField="EFFECT", newFieldAlias="Modifier Effect",
            newFieldType="DOUBLE"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="LITH_MOD", newField="LITH_MOD", newFieldAlias="Lithology Modifier",
            newFieldType="TEXT"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="SEC_DESC", newField="CALC_LITH_MOD_1",
            newFieldAlias="Lithology Modifier (Calc)",
            newFieldType="TEXT"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="CON", newField="CALC_CONSISTENCY", newFieldAlias="Consistency",
            newFieldType="TEXT"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="AQ", newField="AQUIFER_NAME", newFieldAlias="Aquifer Type",
            newFieldType="TEXT"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="AGG", newField="LITH_AGG", newFieldAlias="Aggregated Lithology Unit",
            newFieldType="TEXT"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=lithMappings, oldTable=newLith, oldField="TEXTURE", newField="CALC_TEXTURE", newFieldAlias="Sediment Texture Size",
            newFieldType="TEXT"
        )
        if accessory == "true":
            uf.management.appendFieldMappingInput(
                fieldMappings=lithMappings, oldTable=newLith, oldField="THIRD_DESC", newField="CALC_LITH_MOD_2", newFieldAlias="Second Lithology Modifier (Calc)",
                newFieldType="TEXT"
            )
            uf.management.appendFieldMappingInput(
                fieldMappings=lithMappings, oldTable=newLith, oldField="GROUP_NAME", newField="BDRK_GROUP", newFieldAlias="Bedrock Group/Formation",
                newFieldType="TEXT"
            )
            uf.management.appendFieldMappingInput(
                fieldMappings=lithMappings, oldTable=newLith, oldField="COMMENTS", newField="GEO_COMMENTS", newFieldAlias="Lithology Comments",
                newFieldType="TEXT"
            )
        else:
            pass
        arcpy.management.Append(newLith,finalLith,"NO_TEST",lithMappings,"")
    except:
        uf.management.AddMsgAndPrint("ERROR 004: Failed to append old data into the new table",2)
        raise SystemError
    try:
        # Now we can fill in some of the fields using the formatted data...
        uf.format.firstBDRKValue(
            bdrkTable=finalLith,
            origTable=newLith,
            relate="WELLID",
            seq="SEQ_NUM",
            primAQField="AQUIFER_NAME",
            firstBDRK="FIRST_BDRK",
            aqField="AQTYPE",
            defaultGDB=scratchDir
        )
        arcpy.management.CalculateField(
            in_table=finalLith,
            field="DEPTH_TOP",
            expression="!DEPTH! - !THICKNESS!"
        )
        arcpy.management.JoinField(
            in_data=finalLith,
            in_field="WELLID",
            join_table=reviewTable,
            join_field="WELLID",
            fields="REVIEW;PHASE"
        )
        reviewBlock = ("""def review(oldReview,phase):
                if (phase == "LV" or phase == "LA" or phase == "EL"):
                    return "N"
                else:
                    if oldReview == "Y":
                        return "Y"
                    elif oldReview == "N":
                        return "N"
                    else:
                        return "N"
                        """)
        arcpy.management.CalculateField(
            in_table=finalLith,
            field="VERIFIED",
            expression="review(!REVIEW!,!PHASE!)",
            code_block=reviewBlock
        )
        arcpy.management.DeleteField(finalLith,["REVIEW","PHASE"])
        groupBlock = ("""def groupName(group,aq):
                if group is not None:
                    return group
                else:
                    if (aq.startswith("R") or aq.startswith("U")):
                        return "UNK"
                    else:
                        return "GLA"
            """)
        arcpy.management.CalculateField(
            in_table=finalLith,
            field="GLA_GROUP",
            expression="groupName(!GLA_GROUP!,!AQUIFER_NAME!)",
            code_block=groupBlock
        )
        arcpy.management.CalculateField(
            in_table=finalLith,
            field="BDRK_GROUP",
            expression="groupName(!BDRK_GROUP!,!AQUIFER_NAME!)",
            code_block=groupBlock
        )
    except:
        uf.management.AddMsgAndPrint("ERROR 005: Failed to fill in empty fields",2)
        raise SystemError
    try:
        uf.management.AddMsgAndPrint("Finding lithologies with first bedrock unit encountered in {}...".format(os.path.splitext(os.path.basename(finalLith))[0]))
        bdrkLithTable = os.path.join(geologyGDB,os.path.splitext(os.path.basename(finalLith))[0] + "_FIRST_BDRK")
        arcpy.analysis.TableSelect(finalLith,bdrkLithTable,"FIRST_BDRK = 'Y'")
        arcpy.management.AddAttributeRule(
            in_table=bdrkLithTable,
            name="SimpleLith",
            type="CALCULATION",
            script_expression=simpleExpression,
            field="SEDIMENT",
            triggering_events=["INSERT","UPDATE"]
        )
        arcpy.management.AddAttributeRule(
            in_table=bdrkLithTable,
            name="DrillerDesc",
            type="CALCULATION",
            script_expression=drillerExpression,
            field="DRLLR_DESC",
            triggering_events=["INSERT", "UPDATE"]
        )
        uf.management.AddMsgAndPrint(" - {} contains all the bedrock lithologies, and is written to {}".format(os.path.splitext(os.path.basename(bdrkLithTable))[0],os.path.dirname(bdrkLithTable)))
    except:
        uf.management.AddMsgAndPrint("ERROR 006: Failed to export 'first bedrock' lithology table",2)
        raise SystemError
    try:
        uf.management.AddMsgAndPrint("Adding tables and cleaning geodatabase...")
        pm = prj.activeMap
        pm.addDataFromPath(finalLith)
        pm.addDataFromPath(bdrkLithTable)
        prj.save()
        #arcpy.management.Delete(newLith)
    except:
        uf.management.AddMsgAndPrint("ERROR 007: Failed to import lithology tables and/or failed to clean geodatabase",2)
        raise SystemError

    uf.management.AddMsgAndPrint("_____________________________")
    uf.management.AddMsgAndPrint("BEGIN FORMATTING THE WATER WELL POINTS FEATURE CLASS...")
    try:
        wwName = prjName + "_WW_Points"
        uf.management.AddMsgAndPrint("Extracting elevation data to {}".format(os.path.splitext(os.path.basename(wellPoints))[0]))
        if arcpy.Describe(wellPoints).spatialReference == "GCS_WGS_1984":
            try:
                eventProject = os.path.join(scratchDir,os.path.splitext("Project_"+os.path.basename(wellPoints))[0].replace(" ","_"))
                uf.management.testAndDelete(eventProject)
            except:
                eventProject = os.path.join(scratchDir,"Project_" + wellPoints.replace(" ","_"))
            uf.management.testAndDelete(eventProject)
            uf.management.AddMsgAndPrint(" - First, project to NAD 1983 Hotine projection...")
            arcpy.management.Project(
                in_dataset=wellPoints,
                out_dataset=eventProject,
                out_coor_system="",
                transform_method="WGS_1984_(ITRF00)_To_NAD_1983",
                in_coor_system="GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]",
                preserve_shape="NO_PRESERVE_SHAPE",
                max_deviation="",
                vertical="NO_VERTICAL"
            )
            arcpy.management.SelectLayerByLocation(
                in_layer=eventProject,
                overlap_type="INTERSECT",
                select_features=prjExtent,
                search_distance=None,
                selection_type="NEW_SELECTION",
                invert_spatial_relationship=""
            )
            try:
                eventExtract = os.path.join(scratchDir,"Extract_"+os.path.splitext(os.path.basename(wellPoints))[0].replace(" ", "_"))
                uf.management.testAndDelete(eventExtract)
            except:
                eventExtract = os.path.join(scratchDir,"Extract_" + wellPoints.replace(" ","_"))
            uf.management.testAndDelete(eventExtract)
            arcpy.sa.ExtractValuesToPoints(
                in_point_features=eventProject,
                in_raster=prjDEM,
                out_point_features=eventExtract
            )
        else:
            arcpy.management.SelectLayerByLocation(
                in_layer=wellPoints,
                overlap_type="INTERSECT",
                select_features=prjExtent,
                search_distance=None,
                selection_type="NEW_SELECTION",
                invert_spatial_relationship=""
            )
            try:
                eventExtract = os.path.join(scratchDir,"Extract_" + os.path.splitext(os.path.basename(wellPoints))[0].replace(" ","_"))
                uf.management.testAndDelete(eventExtract)
            except:
                eventExtract = os.path.join(scratchDir, "Extract_" + wellPoints.replace(" ", "_"))
            uf.management.testAndDelete(eventExtract)
            arcpy.sa.ExtractValuesToPoints(
                in_point_features=wellPoints,
                in_raster=prjDEM,
                out_point_features=eventExtract
            )
    except:
        uf.management.AddMsgAndPrint("ERROR 008: Failed to extract elevation values to {}".format(wellPoints),2)
        uf.management.AddMsgAndPrint("Error is likely too many locations outside of the elevation DEM",2)
        raise SystemError
    try:
        uf.management.AddMsgAndPrint(" - Prepare {} for appending to new feature class...".format(os.path.splitext(os.path.basename(eventExtract))[0]))
        with arcpy.da.UpdateCursor(eventExtract,["RASTERVALU"]) as cursor:
            for row in cursor:
                if row[0] == None:
                    cursor.deleteRow()
            del row, cursor
        arcpy.management.CalculateField(
            in_table=eventExtract,
            field="SEC_DIST_NEW",
            expression="!SEC_DIST![0]",
            expression_type="PYTHON3"
        )
        arcpy.management.CalculateField(
            in_table=eventExtract,
            field="LANDSYS",
            expression="!LANDSYS!.upper()",
            expression_type="PYTHON3"
        )
    except:
        uf.management.AddMsgAndPrint("ERROR 009: Failed to format {}".format(os.path.splitext(eventExtract))[0],2)
        raise SystemError
    try:
        uf.management.AddMsgAndPrint("Creating new feature class ({}) with appropriate fields...".format(wwName))
        arcpy.management.CreateFeatureclass(geologyGDB, wwName, "POINT", "", "DISABLED", "DISABLED", "", "", "0", "0", "0")
        finalWWPoints = os.path.join(geologyGDB, wwName)
        arcpy.management.AddField(in_table=finalWWPoints, field_name="WELLID", field_type="TEXT", field_length=12,
                                  field_alias="Well ID")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="PERMIT_NUM", field_type="TEXT", field_length=20,
                                  field_alias="Permit Number")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="COUNTY", field_type="TEXT", field_length=30,
                                  field_alias="County")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="TOWNSHIP", field_type="TEXT", field_length=50,
                                  field_alias="Township")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="TOWN", field_type="TEXT", field_length=3,
                                  field_alias="PLSS Township")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="RANGE", field_type="TEXT", field_length=3,
                                  field_alias="PLSS Range")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="SECTION", field_type="SHORT",
                                  field_alias="PLSS Section")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="WELL_ADDR", field_type="TEXT", field_length=50,
                                  field_alias="Well Address")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="WELL_CITY", field_type="TEXT", field_length=30,
                                  field_alias="Well Address: City")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="WELL_ZIP", field_type="TEXT", field_length=9,
                                  field_alias="Well Address: Zip Code")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="OWNER_NAME", field_type="TEXT", field_length=30,
                                  field_alias="Owner Name")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="WELL_DEPTH", field_type="DOUBLE",
                                  field_alias="Completion Depth (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="WELL_TYPE", field_type="TEXT", field_length=6,
                                  field_alias="Well Type", field_domain="WellType")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="TYPE_OTHER", field_type="TEXT", field_length=30,
                                  field_alias="Well Type: Other")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="WEL_STATUS", field_type="TEXT", field_length=6,
                                  field_alias="Well Status", field_domain="WellStatus")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="STATUS_OTH", field_type="TEXT", field_length=254,
                                  field_alias="Well Status: Other")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="WSSN", field_type="DOUBLE",
                                  field_alias="WSSN")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="DRILLER_ID", field_type="TEXT", field_length=10,
                                  field_alias="Driller ID")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="DRILL_METH", field_type="TEXT", field_length=6,
                                  field_alias="Drilling Method", field_domain="Drilling")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="METH_OTHER", field_type="TEXT", field_length=30,
                                  field_alias="Drilling Method: Other")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="CONST_DATE", field_type="DATE",
                                  field_alias="Completion Date")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="CASE_TYPE", field_type="TEXT", field_length=6,
                                  field_alias="Casing Type", field_domain="CasingType")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="CASE_OTHER", field_type="TEXT", field_length=30,
                                  field_alias="Casing Type: Other")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="CASE_DIA", field_type="DOUBLE",
                                  field_alias="Casing Diameter (inches)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="CASE_DEPTH", field_type="DOUBLE",
                                  field_alias="Casing Depth (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="SCREEN_FRM", field_type="DOUBLE",
                                  field_alias="Screen Top (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="SCREEN_TO", field_type="DOUBLE",
                                  field_alias="Screen Bottom (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="SWL", field_type="DOUBLE",
                                  field_alias="Static Water Level (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="FLOWING", field_type="TEXT", field_length=2,
                                  field_alias="Artesian Well?", field_domain="Verification")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="AQ_TYPE", field_type="TEXT", field_length=6,
                                  field_alias="Aquifer Type", field_domain="WellAquifer")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="TEST_DEPTH", field_type="DOUBLE",
                                  field_alias="Pump Test: Depth (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="TEST_HOURS", field_type="DOUBLE",
                                  field_alias="Pump Test: Duration (hours)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="TEST_RATE", field_type="DOUBLE",
                                  field_alias="Pump Test: Rate (GPM)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="TEST_METHD", field_type="TEXT", field_length=6,
                                  field_alias="Pump Test: Method", field_domain="TestMethod")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="TEST_OTHER", field_type="TEXT", field_length=30,
                                  field_alias="Pump Test: Method (Other)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="GROUT", field_type="TEXT", field_length=2,
                                  field_alias="Well Grouted?", field_domain="Verification")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="PMP_CPCITY", field_type="DOUBLE",
                                  field_alias="Pump Capacity (GPM)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="LATITUDE", field_type="DOUBLE",
                                  field_alias="Latitude")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="LONGITUDE", field_type="DOUBLE",
                                  field_alias="Longitude")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="METHD_COLL", field_type="TEXT", field_length=6,
                                  field_alias="Location Method of Collection", field_domain="LocMethods")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="ELEVATION", field_type="DOUBLE",
                                  field_alias="Wellogic Elevation (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="ELEV_METHD", field_type="TEXT", field_length=6,
                                  field_alias="Elevation Method of Collection",field_domain="ElevMethods")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="WITHIN_CO", field_type="TEXT", field_length=2,
                                  field_alias="Located within County?", field_domain="Verification")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="WITHIN_SEC", field_type="TEXT", field_length=2,
                                  field_alias="Located within PLSS Section?", field_domain="Verification")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="LOC_MATCH", field_type="TEXT", field_length=2,
                                  field_alias="Located within PLSS Township and Range?", field_domain="Verification")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="SEC_DIST", field_type="TEXT", field_length=2,
                                  field_alias="Located 200 ft of PLSS Section?", field_domain="Verification")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="ELEV_DEM", field_type="DOUBLE",
                                  field_alias="USGS NED 10m DEM Elevation (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="ELEV_DIF", field_type="DOUBLE",
                                  field_alias="Absolute Difference in Wellogic Elevation and DEM Elevation")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="LANDSYS", field_type="TEXT", field_length=50,
                                  field_alias="Landsystem Group", field_domain="Landsystem")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="DEPTH_FLAG", field_type="TEXT", field_length=1,
                                  field_alias="Depth Flag Warning", field_domain="DepthFlag")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="ELEV_FLAG", field_type="TEXT", field_length=1,
                                  field_alias="Elevation Flag Warning", field_domain="ElevationFlag")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="SWL_FLAG", field_type="TEXT", field_length=1,
                                  field_alias="Static Water Level Flag Warning", field_domain="SWLFlag")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="SPC_CPCITY", field_type="DOUBLE",
                                  field_alias="Specific Capacity of Well (GPM/ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="AQ_CODE", field_type="TEXT", field_length=1,
                                  field_alias="Adjusted Aquifer Code", field_domain="LocationAQField")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="ROCK_TOP", field_type="DOUBLE",
                                  field_alias="Top of Rock Depth (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="AQ_THK_1", field_type="DOUBLE",
                                  field_alias="'Confined' Summed Thickness of All Drift Strata (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="AQ_THK_2", field_type="DOUBLE",
                                  field_alias="'Unconfined' Summed Thickness of All Drift Strata (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="AQ_THK_D", field_type="DOUBLE",
                                  field_alias="Thickness of Drift Strata Above Rock Top (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="H_COND_1", field_type="DOUBLE",
                                  field_alias="'Confined' Equivalent Horizontal Hydraulic Conductivity (ft/day)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="H_COND_2", field_type="DOUBLE",
                                  field_alias="'Unconfined' Equivalent Horizontal Hydraulic Conductivity (ft/day)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="V_COND_1", field_type="DOUBLE",
                                  field_alias="'Confined' Equivalent Vertical Hydraulic Conductivity (ft/day)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="V_COND_2", field_type="DOUBLE",
                                  field_alias="'Unconfined' Equivalent Horizontal Hydraulic Conductivity (ft/day)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="TRANSMSV_1", field_type="DOUBLE",
                                  field_alias="'Confined' Equivalent Transmissivity (ft2/day)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="TRANSMSV_2", field_type="DOUBLE",
                                  field_alias="'Unconfined' Equivalent Transmissivity (ft2/day)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="B_AQ_THK", field_type="DOUBLE",
                                  field_alias="Thickness of Bedrock Strata Below Rock Top (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="B_H_COND", field_type="DOUBLE",
                                  field_alias="Bedrock Equivalent Horizontal Hydraulic Conductivity (ft/day)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="B_V_COND", field_type="DOUBLE",
                                  field_alias="Bedrock Equivalent Vertical Hydraulic Conductivity (ft/day)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="B_TRANS", field_type="DOUBLE",
                                  field_alias="Bedrock Equivalent Transmissivity (ft2/day)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="H_COND_D", field_type="DOUBLE",
                                  field_alias="Glacial Drift Equivalent Horizontal Hydraulic Conductivity (ft/day)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="V_COND_D", field_type="DOUBLE",
                                  field_alias="Glacial Drift Equivalent Vertical Hydraulic Conductivity (ft/day)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="TRANS_D", field_type="DOUBLE",
                                  field_alias="Glacial Drift Equivalent Transmissivity (ft2/day)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="AQ_FLAG", field_type="TEXT", field_length=1,
                                  field_alias="Aquifer Flag Warning", field_domain="AQFlag")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="SCRN_FLAG", field_type="TEXT", field_length=1,
                                  field_alias="Screen Flag Warning", field_domain="ScreenFlag")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="NOTES", field_type="TEXT", field_length=255,
                                  field_alias="General Notes")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="WELLCODE", field_type="TEXT", field_length=10000,
                                  field_alias="Well Code(s)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="TOPAQ", field_type="DOUBLE",
                                  field_alias="Top Aquifer Depth (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="BOTAQ", field_type="DOUBLE",
                                  field_alias="Bottom Aquifer Depth (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="WWAT_ID", field_type="TEXT", field_length=20,
                                  field_alias="WWAT ID")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="BOREH_DEPTH", field_type="DOUBLE",
                                  field_alias="Total Borehole Depth (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="MAP_UNIT", field_type="TEXT",field_length=5,
                                  field_alias="Surficial Map Unit")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="LITH_TOP", field_type="TEXT", field_length=50,
                                  field_alias="Surficial Lithology from Log",field_domain="PrimaryLith")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="AGG_LITH_TOP", field_type="TEXT", field_length=4,
                                  field_alias="Aggregated Lithology from Log")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="WELL_LABEL", field_type="TEXT", field_length=255,
                                  field_alias="Well Label")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="AQ_UNIT", field_type="TEXT", field_length=2,
                                  field_alias="Type of Aquifer Unit (Estimated)",field_domain="AQUnits")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="SCREEN_TYPE", field_type="TEXT", field_length=4,
                                  field_alias="Well Screen Type",field_domain="ScreenTypes")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="USER_DEM_ELEV", field_type="DOUBLE",
                                  field_alias="DEM Elevation (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="MGS_DEPTH_2_BDRK", field_type="DOUBLE",
                                  field_alias="Depth to Top of Bedrock (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="DEPTH_D_SUB", field_type="DOUBLE",
                                  field_alias="Drift Depth of Submergence (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="DEPTH_R_SUB", field_type="DOUBLE",
                                  field_alias="Bedrock Depth of Submergence (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="MGS_SWL_ELEV", field_type="DOUBLE",
                                  field_alias="SWL Elevation (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="MGS_BDRK_ELEV", field_type="DOUBLE",
                                  field_alias="Bedrock Elevation (ft)")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="RECORD_LINK", field_type="TEXT", field_length=10000,
                                  field_alias="EGLE PDF Link")
        arcpy.management.AddField(in_table=finalWWPoints, field_name="VERIFIED", field_type="TEXT", field_length=2,
                                  field_alias="Location Verified by MGS?", field_domain="Verification")
        arcpy.management.AssignDefaultToField(in_table=finalWWPoints, field_name="DEPTH_FLAG", default_value="0")
        arcpy.management.AssignDefaultToField(in_table=finalWWPoints, field_name="ELEV_FLAG", default_value="0")
        arcpy.management.AssignDefaultToField(in_table=finalWWPoints, field_name="SWL_FLAG", default_value="0")
        arcpy.management.AssignDefaultToField(in_table=finalWWPoints, field_name="AQ_FLAG", default_value="0")
        arcpy.management.AssignDefaultToField(in_table=finalWWPoints, field_name="SCRN_FLAG", default_value="0")
        arcpy.management.AddGlobalIDs(in_datasets=finalWWPoints)
        labelBlock = ("""var type = $feature.WELL_TYPE;
        var aq = $feature.AQ_TYPE;
        var label = When(Equals(aq,"DRIFT")&&Equals(type,"TY1PU"),"Drift: Type 1 Public Supply",
                        Equals(aq,"DRIFT")&&Equals(type,"TY2PU"),"Drift: Type 2 Public Supply",
                        Equals(aq,"DRIFT")&&Equals(type,"TY3PU"),"Drift: Type 3 Public Supply",
                        Equals(aq,"DRIFT")&&(Equals(type,"HEATP") || Equals(type,"HEATRE") || Equals(type,"HEATSU") || Equals(type,"HOSHLD") || Equals(type,"INDUS") || Equals(type,"IRRI") || Equals(type,"OTH") || Equals(type,"TESTW") || Equals(type,"UNK")),"Drift: All Other Wells",
                        Equals(aq,"ROCK")&&Equals(type,"TY1PU"),"Bedrock: Type 1 Public Supply",
                        Equals(aq,"ROCK")&&Equals(type,"TY2PU"),"Bedrock: Type 2 Public Supply",
                        Equals(aq,"ROCK")&&Equals(type,"TY3PU"),"Bedrock: Type 3 Public Supply",
                        Equals(aq,"ROCK")&&(Equals(type,"HEATP") || Equals(type,"HEATRE") || Equals(type,"HEATSU") || Equals(type,"HOSHLD") || Equals(type,"INDUS") || Equals(type,"IRRI") || Equals(type,"OTH") || Equals(type,"TESTW") || Equals(type,"UNK")),"Bedrock: All Other Wells",
                        Equals(aq,"UNK")&&Equals(type,"TY1PU"),"Unknown Aquifer: Type 1 Public Supply",
                        Equals(aq,"UNK")&&Equals(type,"TY2PU"),"Unknown Aquifer: Type 2 Public Supply",
                        Equals(aq,"UNK")&&Equals(type,"TY3PU"),"Unknown Aquifer: Type 3 Public Supply",
                        Equals(aq,"UNK")&&(Equals(type,"HEATP") || Equals(type,"HEATRE") || Equals(type,"HEATSU") || Equals(type,"HOSHLD") || Equals(type,"INDUS") || Equals(type,"IRRI") || Equals(type,"OTH") || Equals(type,"TESTW") || Equals(type,"UNK")),"Unknown Aquifer: All Other Wells","Unknown Aquifer: All Other Wells");
        return label;""")
        arcpy.management.AddAttributeRule(
            in_table=finalWWPoints,
            name="WellLabel",
            type="CALCULATION",
            script_expression=labelBlock,
            field="WELL_LABEL",
            triggering_events=["INSERT","UPDATE"]
        )
    except:
        uf.management.AddMsgAndPrint("ERROR 010: Failed to create final dataset template",2)
        raise SystemError
    try:
        uf.management.AddMsgAndPrint(" - Appending data from {} to {}...".format(os.path.splitext(os.path.basename(eventExtract))[0],os.path.splitext(os.path.basename(finalWWPoints))[0]))
        wwMappings = ""
        wwMappings = arcpy.FieldMappings()
        wwMappings.addTable(finalWWPoints)
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings,oldTable=eventExtract,oldField="RASTERVALU",newField="USER_DEM_ELEV",
            newFieldType="DOUBLE",newFieldAlias="DEM Elevation (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="ELEVATION", newField="ELEVATION",
            newFieldType="DOUBLE", newFieldAlias="Wellogic Elevation (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="WELL_DEPTH", newField="WELL_DEPTH",
            newFieldType="DOUBLE", newFieldAlias="Completion Depth (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="CONST_DATE", newField="CONST_DATE",
            newFieldType="DATE", newFieldAlias="Completion Date"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="TOWN", newField="TOWN",
            newFieldType="TEXT", newFieldAlias="PLSS Township"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="RANGE", newField="RANGE",
            newFieldType="TEXT", newFieldAlias="PLSS Range"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="SECTION", newField="SECTION",
            newFieldType="TEXT", newFieldAlias="PLSS Section"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="WELLID", newField="WELLID",
            newFieldType="TEXT", newFieldAlias="Well ID"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="PERMIT_NUM", newField="PERMIT_NUM",
            newFieldType="TEXT", newFieldAlias="Permit Number"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="COUNTY", newField="COUNTY",
            newFieldType="TEXT", newFieldAlias="County"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="TOWNSHIP", newField="TOWNSHIP",
            newFieldType="TEXT", newFieldAlias="Township"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="WELL_ADDR", newField="WELL_ADDR",
            newFieldType="TEXT", newFieldAlias="Well Address"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="WELL_CITY", newField="WELL_CITY",
            newFieldType="TEXT", newFieldAlias="Well Address: City"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="WELL_ZIP", newField="WELL_ZIP",
            newFieldType="TEXT", newFieldAlias="Well Address: Zip Code"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="OWNER_NAME", newField="OWNER_NAME",
            newFieldType="TEXT", newFieldAlias="Owner Name"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="WELL_TYPE", newField="WELL_TYPE",
            newFieldType="TEXT", newFieldAlias="Well Type"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="TYPE_OTHER", newField="TYPE_OTHER",
            newFieldType="TEXT", newFieldAlias="Well Type: Other"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="WEL_STATUS", newField="WEL_STATUS",
            newFieldType="TEXT", newFieldAlias="Well Status"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="STATUS_OTH", newField="STATUS_OTH",
            newFieldType="TEXT", newFieldAlias="Well Status: Other"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="WSSN", newField="WSSN",
            newFieldType="DOUBLE", newFieldAlias="WSSN"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="DRILLER_ID", newField="DRILLER_ID",
            newFieldType="TEXT", newFieldAlias="Driller ID"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="DRILL_METH", newField="DRILL_METH",
            newFieldType="TEXT", newFieldAlias="Drilling Method"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="METH_OTHER", newField="METH_OTHER",
            newFieldType="TEXT", newFieldAlias="Drilling Method: Other"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="CASE_TYPE", newField="CASE_TYPE",
            newFieldType="TEXT", newFieldAlias="Casing Type"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="CASE_OTHER", newField="CASE_OTHER",
            newFieldType="TEXT", newFieldAlias="Casing Type: Other"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="CASE_DIA", newField="CASE_DIA",
            newFieldType="DOUBLE", newFieldAlias="Casing Diameter (inches)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="CASE_DEPTH", newField="CASE_DEPTH",
            newFieldType="DOUBLE", newFieldAlias="Casing Depth (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="SCREEN_FRM", newField="SCREEN_FRM",
            newFieldType="DOUBLE", newFieldAlias="Screen Top (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="SCREEN_TO", newField="SCREEN_TO",
            newFieldType="DOUBLE", newFieldAlias="Screen Bottom (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="SWL", newField="SWL",
            newFieldType="DOUBLE", newFieldAlias="Static Water Level (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="FLOWING", newField="FLOWING",
            newFieldType="TEXT", newFieldAlias="Artesian Well?"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="AQ_TYPE", newField="AQ_TYPE",
            newFieldType="TEXT", newFieldAlias="Aquifer Type"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="TEST_DEPTH", newField="TEST_DEPTH",
            newFieldType="DOUBLE", newFieldAlias="Pump Test: Depth (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="TEST_HOURS", newField="TEST_HOURS",
            newFieldType="DOUBLE", newFieldAlias="Pump Test: Duration (hours)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="TEST_RATE", newField="TEST_RATE",
            newFieldType="DOUBLE", newFieldAlias="Pump Test: Rate (GPM)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="TEST_METHD", newField="TEST_METHD",
            newFieldType="TEXT", newFieldAlias="Pump Test: Method"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="TEST_OTHER", newField="TEST_OTHER",
            newFieldType="TEXT", newFieldAlias="Pump Test: Method (Other)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="GROUT", newField="GROUT",
            newFieldType="TEXT", newFieldAlias="Well Grouted?"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="PMP_CPCITY", newField="PMP_CPCITY",
            newFieldType="DOUBLE", newFieldAlias="Pump Capacity (GPM)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="LATITUDE", newField="LATITUDE",
            newFieldType="DOUBLE", newFieldAlias="Latitude"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="LONGITUDE", newField="LONGITUDE",
            newFieldType="DOUBLE", newFieldAlias="Longitude"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="METHD_COLL", newField="METHD_COLL",
            newFieldType="TEXT", newFieldAlias="Location Method of Collection"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="ELEV_METHD", newField="ELEV_METHD",
            newFieldType="TEXT", newFieldAlias="Elevation Method of Collection"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="WITHIN_CO", newField="WITHIN_CO",
            newFieldType="TEXT", newFieldAlias="Located within County?"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="WITHIN_SEC", newField="WITHIN_SEC",
            newFieldType="TEXT", newFieldAlias="Located within PLSS Section?"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="LOC_MATCH", newField="LOC_MATCH",
            newFieldType="TEXT", newFieldAlias="Located within PLSS Township and Range?"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="SEC_DIST_NEW", newField="SEC_DIST",
            newFieldType="TEXT", newFieldAlias="Located 200 ft of PLSS Section?"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="ELEV_DEM", newField="ELEV_DEM",
            newFieldType="DOUBLE", newFieldAlias="USGS NED 10m DEM Elevation (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="LANDSYS", newField="LANDSYS",
            newFieldType="TEXT", newFieldAlias="Landsystem Group"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="AQ_CODE", newField="AQ_CODE",
            newFieldType="TEXT", newFieldAlias="Adjusted Aquifer Code"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="ROCK_TOP", newField="ROCK_TOP",
            newFieldType="DOUBLE", newFieldAlias="Top of Rock Depth (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="WELLCODE", newField="WELLCODE",
            newFieldType="TEXT", newFieldAlias="Well Code(s)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="AQ_THK_1", newField="AQ_THK_1",
            newFieldType="DOUBLE", newFieldAlias="'Confined' Summed Thickness of All Drift Strata (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="AQ_THK_2", newField="AQ_THK_2",
            newFieldType="DOUBLE", newFieldAlias="'Unconfined' Summed Thickness of All Drift Strata (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="AQ_THK_D", newField="AQ_THK_D",
            newFieldType="DOUBLE", newFieldAlias="Thickness of Drift Strata Above Rock Top (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="H_COND_1", newField="H_COND_1",
            newFieldType="DOUBLE", newFieldAlias="'Confined' Equivalent Horizontal Hydraulic Conductivity (ft/day)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="H_COND_2", newField="H_COND_2",
            newFieldType="DOUBLE", newFieldAlias="'Unconfined' Equivalent Horizontal Hydraulic Conductivity (ft/day)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="V_COND_1", newField="V_COND_1",
            newFieldType="DOUBLE", newFieldAlias="'Confined' Equivalent Vertical Hydraulic Conductivity (ft/day)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="V_COND_2", newField="V_COND_2",
            newFieldType="DOUBLE", newFieldAlias="'Unconfined' Equivalent Vertical Hydraulic Conductivity (ft/day)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="TRANSMSV_1", newField="TRANSMSV_1",
            newFieldType="DOUBLE", newFieldAlias="'Confined' Equivalent Transmissivity (ft2/day)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="TRANSMSV_2", newField="TRANSMSV_2",
            newFieldType="DOUBLE", newFieldAlias="'Unconfined' Equivalent Transmissivity (ft2/day)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="B_AQ_THK", newField="B_AQ_THK",
            newFieldType="DOUBLE", newFieldAlias="Thickness of Bedrock Strata Below Rock Top (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="B_H_COND", newField="B_H_COND",
            newFieldType="DOUBLE", newFieldAlias="Bedrock Equivalent Horizontal Hydraulic Conductivity (ft/day)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="B_V_COND", newField="B_V_COND",
            newFieldType="DOUBLE", newFieldAlias="Bedrock Equivalent Vertical Hydraulic Conductivity (ft/day)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="B_TRANS", newField="B_TRANS",
            newFieldType="DOUBLE", newFieldAlias="Bedrock Equivalent Transmissivity (ft2/day)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="H_COND_D", newField="H_COND_D",
            newFieldType="DOUBLE", newFieldAlias="Glacial Drift Equivalent Horizontal Hydraulic Conductivity (ft/day)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="V_COND_D", newField="V_COND_D",
            newFieldType="DOUBLE", newFieldAlias="Glacial Drift Equivalent Vertical Hydraulic Conductivity (ft/day)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="TRANS_D", newField="TRANS_D",
            newFieldType="DOUBLE", newFieldAlias="Glacial Drift Equivalent Transmissivity (ft2/day)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="NOTES", newField="NOTES",
            newFieldType="TEXT", newFieldAlias="General Notes"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="TOPAQ", newField="TOPAQ",
            newFieldType="DOUBLE", newFieldAlias="Top Aquifer Depth (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="BOTAQ", newField="BOTAQ",
            newFieldType="DOUBLE", newFieldAlias="Bottom Aquifer Depth (ft)"
        )
        uf.management.appendFieldMappingInput(
            fieldMappings=wwMappings, oldTable=eventExtract, oldField="WWAT_ID", newField="WWAT_ID",
            newFieldType="TEXT", newFieldAlias="WWAT ID"
        )
        arcpy.management.Append(eventExtract,finalWWPoints,"NO_TEST",wwMappings,"")
    except:
        uf.management.AddMsgAndPrint("ERROR 011: Failed to append {} to {}".format(os.path.splitext(os.path.basename(eventExtract))[0],os.path.splitext(os.path.basename(finalWWPoints))[0]),2)
        raise SystemError
    try:
        uf.management.AddMsgAndPrint("Formatting the empty fields in {}...".format(os.path.splitext(os.path.basename(finalWWPoints))[0]))
        maxDepthTable = os.path.join(scratchDir,"{}_MaxDepth".format(prjName))
        firstLithTable = os.path.join(scratchDir,"{}_FirstLith".format(prjName))
        arcpy.analysis.Statistics(
            in_table=finalLith,
            out_table=maxDepthTable,
            statistics_fields=[["DEPTH","MAX"]],
            case_field="WELLID"
        )
        arcpy.conversion.ExportTable(
            in_table=finalLith,
            out_table=firstLithTable,
            where_clause="SEQ_NUM = 1"
        )
        arcpy.management.JoinField(
            in_data=finalWWPoints,
            in_field="WELLID",
            join_table=bdrkLithTable,
            join_field="WELLID",
            fields="DEPTH_TOP"
        )
        arcpy.management.JoinField(
            in_data=finalWWPoints,
            in_field="WELLID",
            join_table=firstLithTable,
            join_field="WELLID",
            fields="PRIM_LITH;LITH_AGG"
        )
        arcpy.management.JoinField(
            in_data=finalWWPoints,
            in_field="WELLID",
            join_table=maxDepthTable,
            join_field="WELLID",
            fields="MAX_DEPTH"
        )
        arcpy.management.CalculateField(
            in_table=finalWWPoints,
            field="MGS_DEPTH_2_BDRK",
            expression="!DEPTH_TOP!"
        )
        arcpy.management.CalculateField(
            in_table=finalWWPoints,
            field="LITH_TOP",
            expression="!PRIM_LITH!"
        )
        #arcpy.management.CalculateField(
        #    in_table=finalWWPoints,
        #    field="AGG_LITH_TOP",
        #    expression="!LITH_AGG!"
        #)
        boreDepth = ("""def boreDepth(bore,compl):
                if bore is None:
                    return compl
                else:
                    return bore
                """)
        arcpy.management.CalculateField(
            in_table=finalWWPoints,
            field="BOREH_DEPTH",
            expression="boreDepth(!MAX_DEPTH!,!WELL_DEPTH!)",
            code_block=boreDepth
        )
        wellAQBlock = ("""def aq(scrn_top,scrn_bottom,bdrk):
            if bdrk is None:
                if scrn_top > 0 and scrn_bottom > 0:
                    return "DRIFT"
                else:
                    return "UNK"
            else:
                if (scrn_top == 0 and scrn_bottom == 0 and bdrk != 0):
                    return "ROCK"
                if (scrn_bottom >= bdrk and bdrk !=0):
                    return "ROCK"
                if scrn_bottom <= bdrk:
                    return "DRIFT"
                else:
                    return "UNK"
            """)
        arcpy.management.CalculateField(
            in_table=finalWWPoints,
            field="AQ_TYPE",
            expression="aq(!SCREEN_FRM!,!SCREEN_TO!,!MGS_DEPTH_2_BDRK!)",
            code_block=wellAQBlock
        )
        arcpy.management.CalculateField(
            in_table=finalWWPoints,
            field="DEPTH_D_SUB",
            expression="driftSub(!AQ_TYPE!,!SCREEN_FRM!,!SCREEN_TO!,!SWL!)",
            expression_type="PYTHON3",
            code_block="""def driftSub(aqField,screen_top,screen_bot,swl):
            if aqField == "R":
                return None
            else:
                midScreen = (screen_bot - screen_top)/2
                return swl - midScreen"""
        )
        with arcpy.da.UpdateCursor(finalWWPoints, ["SCREEN_TYPE","AQ_TYPE","SCREEN_FRM","SCREEN_TO"]) as cursor:
            for row in cursor:
                if (row[1] == "ROCK" and (row[2] == 0 and row[3] == 0)):
                    row[0] = "R_US"
                elif (row[1] == "ROCK" and (row[2] != 0 and row[3] != 0)):
                    row[0] = "R_S"
                elif (row[1] == "DRIFT" and (row[2] == 0 and row[3] == 0)):
                    row[0] = "D_US"
                elif (row[1] == "DRIFT" and (row[2] != 0 and row[3] != 0)):
                    row[0] = "D_S"
                elif (row[1] == "UNK" and (row[2] == 0 and row[3] == 0)):
                    row[0] = "U_US"
                elif (row[1] == "UNK" and (row[2] != 0 and row[3] != 0)):
                    row[0] = "U_S"
                else:
                    row[0] = None
                cursor.updateRow(row)
            del row
            del cursor
        arcpy.management.CalculateField(
            in_table=finalWWPoints,
            field="MGS_BDRK_ELEV",
            expression="!USER_DEM_ELEV! - !MGS_DEPTH_2_BDRK!"
        )
        arcpy.management.CalculateField(
            in_table=finalWWPoints,
            field="MGS_SWL_ELEV",
            expression="!USER_DEM_ELEV! - !SWL!"
        )
        arcpy.management.CalculateField(
            in_table=finalWWPoints,
            field="RECORD_LINK",
            expression='"https://www.egle.state.mi.us/wellogic/ReportProxy.aspx/?/WELLOGIC/WELLOGIC/user_Well%20Record&rs:Command=Render&rs:Format=PDF&wellLogID=" + $feature.WELLID',
            expression_type="ARCADE"
        )
        arcpy.management.JoinField(
            in_data=finalWWPoints,
            in_field="WELLID",
            join_table=reviewTable,
            join_field="WELLID",
            fields="REVIEW"
        )
        locRevBlock = ("""def review(oldReview):
            if oldReview == "Y":
                return "Y"
            elif oldReview == "N":
                return "N"
            else:
                return "N"
        """)
        arcpy.management.CalculateField(
            in_table=finalWWPoints,
            field="VERIFIED",
            expression="review(!REVIEW!)",
            code_block=locRevBlock
        )
        arcpy.management.DeleteField(finalWWPoints,["DEPTH_TOP","MAX_DEPTH_BOT","REVIEW","PRIM_LITH","LITH_AGG"])
    except:
        uf.management.AddMsgAndPrint("ERROR 012: Failed to format the new points table",2)
        raise SystemError
    try:
        pm.addDataFromPath(finalWWPoints)
        prj.save()
        try:
            uf.symbols.wwSymbol(map=pm, feature=finalWWPoints)
            csm = prj.listMaps("03_Layout Map - Cross Section")[0]
            mm = prj.listMaps("02_Layout Map - Main")[0]
            mm.addDataFromPath(finalWWPoints)
            csm.addDataFromPath(finalWWPoints)
            prj.save()
            uf.symbols.wwSymbol(map=mm,feature=finalWWPoints)
            uf.symbols.wwSymbol(map=csm, feature=finalWWPoints)
        except:
            uf.management.AddMsgAndPrint("Maps do not exist or is not supported. Passing to next step...")
            pass
    except:
        uf.management.AddMsgAndPrint("ERROR 013: Failed to add data into the respective maps",2)
        raise SystemError
    try:
        uf.management.AddMsgAndPrint(" - Creating copy of {} for generating groundwater surfaces...".format(os.path.splitext(os.path.basename(finalWWPoints))[0]))
        orig_count = arcpy.management.GetCount(finalWWPoints)
        uf.management.AddMsgAndPrint(" * Orginal water wells feature class has {} records.".format(orig_count))
        gwlName = wwName + "_GWL_USABLE"
        gwlWW = os.path.join(geologyGDB,gwlName)
        uf.management.testAndDelete(gwlWW)
        arcpy.management.CopyFeatures(finalWWPoints,gwlWW)
        arcpy.management.CalculateField(in_table=gwlWW,
                                        field="WELL_LABEL",
                                        expression=labelBlock,
                                        expression_type="ARCADE")

        # Update the GWL Table
        with arcpy.da.UpdateCursor(gwlWW, "VERIFIED") as cursor:
            for row in cursor:
                if row[0] == "Y":
                    pass
                else:
                    cursor.deleteRow()
            del row, cursor
        arcpy.AddMessage('  Filtering anomalous SWL values (greater than 999)...')
        with arcpy.da.UpdateCursor(gwlWW, ["SWL", "FLOWING", "WELLID"]) as cursor:
            for row in cursor:
                if row[0] > 998:
                    row[0] = None
                    cursor.updateRow(row)
                if (row[0] == 0 and row[1] == "Y"):
                    arcpy.AddWarning('      {} has an 0 swl and is flowing. Please review for validity...'.format(row[2]))
                del row
            del cursor
        swlCodeBlock = (
            """def finalSWL(swl,elev):
                    if (swl == None):
                        pass
                    else:
                        return elev-swl""")
        arcpy.management.CalculateField(in_table=gwlWW,
                                        field="MGS_SWL_ELEV",
                                        expression="finalSWL(!SWL!,!USER_DEM_ELEV!)",
                                        code_block=swlCodeBlock)
        gwlcopy_count = arcpy.management.GetCount(gwlWW)
        arcpy.AddMessage(" * Groundwater copy of water points has {} records.".format(gwlcopy_count))
    except:
        uf.management.AddMsgAndPrint("ERROR 014: Failed to copy {} for groundwater analysis".format(os.path.splitext(os.path.basename(finalWWPoints))[0]),2)
        raise SystemError
    try:
        uf.management.AddMsgAndPrint("Adding tables and cleaning scratch geodatabase...")
        pm.addDataFromPath(gwlWW)
        prj.save()
        try:
            uf.symbols.wwSymbol(map=pm,feature=gwlWW)
        except:
            pass
        if arcpy.Describe(wellPoints).spatialReference == "GCS_WGS_1984":
            arcpy.management.Delete(eventProject)
        arcpy.management.Delete([eventExtract,firstLithTable,maxDepthTable,newLith])
    except:
        uf.management.AddMsgAndPrint("ERROR 015: Failed to add tables and clean geodatabase for water well points",2)
        raise SystemError
    return finalLith,finalWWPoints

if __name__ == "__main__":
    lith,wwPoints = dataFormatting(
        geologyGDB=arcpy.GetParameterAsText(0),
        prjName=arcpy.GetParameterAsText(1),
        wellPoints=arcpy.GetParameterAsText(2),
        lithTable=arcpy.GetParameterAsText(3),
        accessory=arcpy.GetParameterAsText(4),
        username=arcpy.GetParameterAsText(5),
        password=arcpy.GetParameterAsText(6),
        prjExtent=arcpy.GetParameterAsText(7),
        prjDEM=arcpy.GetParameterAsText(8),
        reviewTable="https://services1.arcgis.com/vFQXQuqACTPxa4Yc/arcgis/rest/services/ReviewTable/FeatureServer/0"
    )