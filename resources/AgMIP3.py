# -*- coding: utf-8 -*-
"""
Created on Wed Oct  2 09:49:13 2019

@author: Dominique van der Mensbrugghe
"""

import csv
import os
from datetime import date
import argparse
import pandas
import numpy as np

perm = [0, 1, 2, 3, 4, 5, 6]
nFields = 7
# initializing the titles and rows list
csvfields = []
rows = []
rowclean = ['0','1','2','3','4',0,'6',0.0]
nCols    = len(rowclean)
fields = ['Model','Scenario','Region','Variable','Item','Year','Unit','Value']
nDrop = 0
Drop  = []
nDupl = 0
strQuote = '"'
delimiter = ','

"""Define the command line arguments"""
parser = argparse.ArgumentParser(description="Parse a contributed AgMIP result file")
parser.add_argument("--modelName", help="The name of the model with submitted results")
parser.add_argument("-f", "--fieldHeader", help="Use -f to output a field header line, default is no header line",
                    action="store_true")
parser.add_argument("-v", "--verbose", help="Use -v to output diagnostic information",
                    action="store_true")

def Usage(ifQuit):

    """ Function that prints out the usage of this script"""
    """ If the argument is set to True, the function will also cause the script to abort"""
    print("\n")
    parser.print_help()
    print("\n"*2)
    print("Example: AgMIP3 [-f] [--modelName=ModelName]")
    print("\n")
    if ifQuit:
        quit()

""" Start of main script """

# Parse the arguments

args = parser.parse_args()
if(args.verbose):
    ifVerbose = True
else:
    ifVerbose = False

if ifVerbose:
    print(args)
    print("<<",args.modelName,">>")

if(args.modelName == None):
    fileName = "EPPA.opt"
else:
    fileName = args.modelName + ".opt"
if ifVerbose:
    print(fileName)

if(args.fieldHeader):
    ifHeader = True
else:
    ifHeader = False

# Get the options

with open(fileName,"r+") as inFile:
    for inputline in inFile:
        if inputline.strip().lower() == "model:":
            model = inFile.readline().strip()
        elif inputline.strip().lower() == "folder:":
            folder = inFile.readline().strip()
        elif inputline.strip().lower() == "filename:":
            filename = inFile.readline().strip()
        elif inputline.strip().lower() == "skip:":
            skip = int(inFile.readline())
        elif inputline.strip().lower() == "year column:":
            year = int(inFile.readline())-1
        elif inputline.strip().lower() == "value column:":
            value = int(inFile.readline())-1
        elif inputline.strip().lower() == "unit column:":
            unit = int(inFile.readline())-1
        elif inputline.strip().lower() == "delimiter:":
            delimiter = inFile.readline().strip()
        elif inputline.strip().lower()[:7] == "concord":
            for i in range(0,nFields):
                perm[i] = int(inFile.readline())-1
        elif inputline.strip().lower() == "drop scenarios:":
            nDrop = int(inFile.readline())
            for i in range(0,nDrop):
                Drop.append('"' + inFile.readline().rstrip() + '"')

if ifVerbose:
    print("Model: ", model)
    print("Folder: ", folder)
    print("Filename: ", filename)
    print("Skip: ", skip)
    print("Ifheader: ", ifHeader)
    print("Year col: ", year)
    print("Val col: ", value)
    print("Delimiter: <", delimiter,">", len(delimiter))
    for i in range(0,nFields):
        print(perm[i])
    for i in range(0,nDrop):
        print(Drop[i])

os.chdir(folder)
outFile  = filename + date.today().strftime("%d%b%Y").upper() + ".csv"

# print(outFile)

#   Define validation function

def ifValid(value, validSet):
    n = len(validSet)
    for i in range(0,n):
        if value.strip().lower() == validSet[i].lower():
            return True
    return False

# reading csv file
with open(filename+'.csv', newline='') as csvreadfile:

    print("Reading file " + folder + '/' + filename + '.csv...')

    # creating a csv reader object
    csvreader = csv.reader(csvreadfile, delimiter=delimiter)

    if skip > 0:
        for r in range(0, skip):
            line = next(csvreader)

    # extracting field names through first row
    # If skip is negative (e.g. -1), the file has no header row
    if skip >= 0:
        csvfields = next(csvreader)
    if (ifVerbose and skip >= 0):
        print('Field names are:' + ', '.join(field for field in csvfields))

    # extracting each data row one by one
    # Convert 11th column to an integer
    # Convert 12th column to a float
    # print(perm)
    nValid = 0
    for row in csvreader:
        if ifVerbose and csvreader.line_num < 5:
            print(row)
        for c in range(0, nFields):
            if ifVerbose and csvreader.line_num < 5:
                print("c =", c, ", perm[c] = ", perm[c], ", row[c] = ", row[c], ", row[perm[c]] = ", row[perm[c]])
            if c == year:
                try:
                    rowclean[c+1] = int(row[perm[c]])
                except:
                    print(row)
            elif c == value:
                if (row[perm[c]] == '#DIV/0!'):
                    rowclean[c+1] = 0
                elif (row[perm[c]] == 'N/A!'):
                    rowclean[c+1] = np.nan
                elif (row[perm[c]] == 'N/A'):
                    rowclean[c+1] = np.nan
                elif (row[perm[c]] == 'NA'):
                    rowclean[c+1] = np.nan
                elif (row[perm[c]].lower() == 'nan'):
                    rowclean[c+1] = np.nan
                else:
                    rowclean[c+1] = float(row[perm[c]])
            else:
                if perm[c] >= 0:
                    if c == unit:
                        rowclean[c+1] = strQuote + row[perm[c]].strip() + strQuote
                    elif (row[perm[c]] == 'World'):
                        rowclean[c+1] = strQuote + 'WLD' + strQuote
                    else:
                        # Quote all strings
                        rowclean[c+1] = strQuote + row[perm[c]].strip() + strQuote


        rowclean[0] = model
        ifDrop = False
        # FOR GCAM--replace scenario names
        if rowclean[1].find('_Diet') > 0:
            rowclean[1] = rowclean[1].replace("_Diet","")
        # Are we dropping this scenario?
        for i in range(0,nDrop):
            if ifVerbose and csvreader.line_num < 5:
                print(Drop[i].lower())
                print(rowclean[1].lower())
            if(Drop[i].lower() == rowclean[1].lower()):
                ifDrop = True
        if(ifDrop == False):
            rows.append(rowclean.copy())

    # get total number of rows
    print("Total no. of rows (excluding skipped): %d"%(csvreader.line_num-skip))

csvreadfile.close()

if nValid > 0:
    print("Number of invalid entries: ", nValid)
    exit(1)

#  printing first 5 rows
if ifVerbose:
    print('\nFirst 5 rows are:\n')
    for row in rows[:5]:
        # parsing each column of a row
        i=0
        for col in row:
            if i == 5:
                print("<%4d>"%col),
            elif i == 7:
                print("<%15.4f>"%col),
            else:
                print("<%10s>"%col),
            i = i + 1
    print('\n')

# Convert to a Pandas dataframe

df = pandas.DataFrame(rows)
df.columns=["Model", "Scenario", "Region", "Variable", "Item", "Year", "Unit", "Value"]

#   Get the unique scenario names and save to Excel

Scenarios=pandas.DataFrame(df["Scenario"].unique())
Scenarios.to_excel(model + "_Scenarios.xlsx", index=True)

# Reset column labels

df.columns = fields

if ifVerbose:
    print(df.head(5))

#   Let's look for duplicate rows

duplicate_row_index = df.duplicated(subset=['Model','Scenario','Region',
              'Variable','Item','Year','Unit'], keep="first")

# Get the duplicate rows

duplicate_rows = df[duplicate_row_index]

nDuplRows = len(duplicate_rows)
# print('nDuplRows = ' + str(nDuplRows))

if(nDuplRows > 0):
    # Save the duplicate rows to an Excel file in the 'model' directory
    duplicate_rows.to_excel(model + "_Duplicate_Rows.xlsx", index=True)
    duplicate_rows.to_csv(model + "_Duplicate_Rows.csv", index = False, quoting=csv.QUOTE_NONE, quotechar='"', header=False, na_rep='NA')

    # Drop the duplicate rows
    #    Not sure why the next line does not work!?
    #df = df.drop(index=duplicate_row_index) 
    df = df.drop_duplicates(subset=['Model','Scenario','Region',
              'Variable','Item','Year','Unit'], keep="first")

# Save the DF (minus the duplicate rows)

df.to_csv(outFile, index = False, quoting=csv.QUOTE_NONE, quotechar='"', header=False, na_rep='NA')
