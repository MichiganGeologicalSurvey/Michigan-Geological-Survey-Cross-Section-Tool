# *****************************************************
# *****************************************************
# DataFormatting_PullGeology.py
# Version: 1.0
# Date: 5/31/2024
# Last Modified Date: 5/31/2024
# Original Author: Matthew Bell, Michigan Geological Survey, matthew.e.bell@wmich.edu
# Description: A Python script to extract extra data from Wellogic for hidden third lithology column and geology field
# comments.
# *****************************************************
# *****************************************************

def extractGeologyData(wells,lithTable,username,password,output):
    import os
    import time
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
    from openpyxl import Workbook
    import pandas as pd
    import arcpy
    from Utility_Functions import management
    # First, let us create the final Excel sheet that will contain all the information. We can transfer this to ArcGIS
    # Pro once it is all organized.
    try:
        wb = Workbook()
        wb["Sheet"].title = "GeologyData"
        sh1 = wb.active
        title = [["WELLID","SEQ_NUM","COLOR","LITH_PRIM","SEC_LITH","FORMATION","THICKNESS","DEPTH","GEO_COMMENTS"]]
        for i in title:
            sh1.append(i)
        outputLocation = os.path.join(os.path.dirname(output),"{}.xlsx".format(os.path.splitext(os.path.basename(wells))[0]))
        wb.save(outputLocation)
        wellids = management.unique_values(wells,"WELLID")
    except:
        management.AddMsgAndPrint("ERROR 001: Failed to setup workbook",2)
        raise SystemError
    time.sleep(2)
    try:
        op = webdriver.firefox.options.Options()
        op.add_arguement("--headless")
        driver = webdriver.Firefox(options=op,firefox_binary=FirefoxBinary())
        # We need to be logged in to Wellogic in order to pull the data from the geology section.
        driver.get('https://www.egle.state.mi.us/wellogic/Login.aspx')
        userElement = driver.find_element(By.ID, "ctl00_ContentPlaceholderMain_UserLogin_UserName")
        passElement = driver.find_element(By.ID, "ctl00_ContentPlaceholderMain_UserLogin_Password")
        signElement = driver.find_element(By.XPATH,
                                          "/html/body/form/div[3]/div[2]/div[2]/div[1]/div[2]/table/tbody/tr/td/div[4]/input")
        userElement.send_keys(username)
        passElement.send_keys(password)
        signElement.click()
        management.AddMsgAndPrint("Logged in to: {}".format(username))
    except:
        management.AddMsgAndPrint("ERROR 002: Failed to log in to Wellogic",2)
        raise SystemError
    arcpy.SetProgressor("step","Downloading data for wells...",0,len(wellids))
    for wellid in wellids:
        # Try to connect to the website and pull the geology data into a text string...
        driver.get('https://www.egle.state.mi.us/wellogic/waterwell.aspx?wellid={}#fragment-2'.format(wellid))
        time.sleep(3)
        df1 = pd.read_excel(outputLocation,sheet_name="GeologyData")
        arcpy.SetProgressorLabel("Gathering data for: {}".format(wellid))
        try:
            try:
                arcpy.management.MakeTableView(
                    in_table=lithTable,
                    out_view="WellLithologies",
                    where_clause="WELLID = '{}'".format(wellid)
                )
                rows = arcpy.management.GetCount("WellLithologies")[0]
            except:
                management.AddMsgAndPrint("ERROR 003: Could not select data",2)
                raise SystemError
            seq = 1
            try:
                for r in range(2, int(rows) + 2):
                    color = driver.find_element(By.XPATH,
                                                '//*[@id="ctl00_ContentPlaceholderMain_GeologyUC_GeologyDataList"]/tbody/tr[{0}]/td[2]'.format(
                                                    str(r))).text
                    primLith = driver.find_element(By.XPATH,
                                                   '//*[@id="ctl00_ContentPlaceholderMain_GeologyUC_GeologyDataList"]/tbody/tr[{0}]/td[3]'.format(
                                                       str(r))).text
                    secLith = driver.find_element(By.XPATH,
                                                  '//*[@id="ctl00_ContentPlaceholderMain_GeologyUC_GeologyDataList"]/tbody/tr[{0}]/td[4]'.format(
                                                      str(r))).text
                    thirdLith = driver.find_element(By.XPATH,
                                                    '//*[@id="ctl00_ContentPlaceholderMain_GeologyUC_GeologyDataList"]/tbody/tr[{0}]/td[5]'.format(
                                                        str(r))).text
                    thick = driver.find_element(By.XPATH,
                                                '//*[@id="ctl00_ContentPlaceholderMain_GeologyUC_GeologyDataList"]/tbody/tr[{0}]/td[6]'.format(
                                                    str(r))).text
                    depth = driver.find_element(By.XPATH,
                                                '//*[@id="ctl00_ContentPlaceholderMain_GeologyUC_GeologyDataList"]/tbody/tr[{0}]/td[7]'.format(
                                                    str(r))).text
                    if primLith == "See Comments":
                        geoComment = driver.find_element(By.XPATH,
                                                         '/html/body/form/div[3]/div[2]/div[3]/div[2]/div[4]/div/div[2]/textarea').text
                    else:
                        geoComment = ""
                    sh1.append([wellid, seq, color, primLith, secLith, thirdLith, float(thick), float(depth), geoComment])
                    seq = seq + 1
            except:
                management.AddMsgAndPrint("Warning: Could not extract the data for {}".format(wellid),1)
            wb.save(outputLocation)
            arcpy.management.Delete("WellLithologies")
            arcpy.SetProgressorPosition()
        except:
            management.AddMsgAndPrint("ERROR 004: Could not retrieve data")
            raise SystemError
    driver.quit()
    arcGeoTable = os.path.join(output,"{}_EXTRA_GEO".format(os.path.splitext(os.path.basename(wells))[0]))
    management.testAndDelete(arcGeoTable)
    arcpy.conversion.ExcelToTable(
        Input_Excel_File=outputLocation,
        Output_Table=arcGeoTable
    )
    return arcGeoTable