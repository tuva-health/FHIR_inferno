import json
import sys
import csv
import configparser
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s: %(levelname)s - %(message)s'
)


##### functions #####
def is_integer(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()


def getJsonValue(lnjsn, ln):
    retVal = ""
    for x in ln.split("."):
        if x.startswith("ArrJoin:"):
            x = x[8:]
            if x in lnjsn:
                tempVal = ' '.join([str(item) for item in lnjsn[x]])
                lnjsn = tempVal
            else:
                lnjsn = ""
        elif x.startswith("ArrNotHave:"):
            x = x[11:]
            found = False
            for i in range(len(lnjsn)):
                if getJsonValue(lnjsn[i], x.replace(",",".")) is None:
                    lnjsn = lnjsn[i]
                    found = True
                    break
            if found != True:
                return None
        elif x.startswith("ArrCond:"):
            spl = x[8:].split("|")
            found = False
            for i in range(len(lnjsn)):
                if getJsonValue(lnjsn[i], spl[0].replace(",",".")
                                ) == spl[1].replace(",","."):
                    lnjsn = lnjsn[i]
                    found = True
                    break
            if found != True:
                return None
        elif x.startswith("Hard:"):
            lnjsn = x[5:]
        elif x.startswith("IfEx:"):
            spl = x[5:].split("|")
            if spl[0] in lnjsn:
                lnjsn = spl[1]
            else:
                lnjsn = spl[2]
        elif x.startswith("IfEq:"):
            spl = x[5:].split("|")
            if lnjsn[spl[0]] == spl[1].replace(",","."):
                lnjsn = spl[2]
            else:
                lnjsn = spl[3]
        elif x.startswith("Left:"):
            spl = x[5:].split("|")
            if spl[0] in lnjsn:
                lnjsn = lnjsn[spl[0]]
                lnjsn = lnjsn[:int(spl[1])]
            else:
                return None
        elif x.startswith("LTrim:"):
            spl = x[6:].split("|")
            if spl[0] in lnjsn:
                lnjsn = lnjsn[spl[0]]
                lnjsn = lnjsn[int(spl[1]):]
            else:
                return None
        elif x.startswith("TimeForm:"):
            x = x[9:]
            if x in lnjsn:
                lnjsn = lnjsn[x]
                lnjsn = lnjsn[:19].replace("T"," ")
            else:
                return None
        elif x in lnjsn:
            lnjsn = lnjsn[x]
        elif is_integer(x):
            if int(x) < len(lnjsn):
                lnjsn = lnjsn[int(x)]
            else:
                lnjsn = ""
                break
        else:
            return None
    return lnjsn


def combineValues(jsn, path):
    retVal = ""
    for ln in path.splitlines():
        retVal = (retVal + " " + str(getJsonValue(jsn, ln) or "")).strip()
    return retVal


####### Main #######
def parse(configpath):
    logging.info('Started parsing "%s"', configpath)
    config = configparser.ConfigParser()

    config.read(configpath)
    inputPath = config['GenConfig']['inputPath']
    outputPath = config['GenConfig']['outputPath']
    if config.has_option('GenConfig', 'anchor'):
        anchor = config['GenConfig']['anchor']
    else:
        anchor = False
    if config.has_option('GenConfig', 'WriteMode'):
        if config['GenConfig']['WriteMode'] == 'append':
            writemode = "a"
    else:
        writemode = "w"

    header = []
    paths = []
    leng = 0
    row_count = 0

    for key in config['Struct']:
        header.append(key)
        paths.append(config['Struct'][key])
        leng = leng + 1

    thisRow = [""]*leng
    csvfile = open(outputPath, writemode, newline='')
    csvwriter = csv.writer(csvfile,
                           delimiter=',',
                           escapechar='\\',
                           quoting=csv.QUOTE_ALL
                           )
    if writemode == "w":
        csvwriter.writerow(header)

    badfile = open('badfile.csv', 'a')

    with open(inputPath) as inputFile:
        for jsntxt in inputFile:
            try:
                jsndict = json.loads(jsntxt)
            except:
                badfile.write(jsntxt)
                logging.exception('Issue with input file "%s", see badfile.csv',
                                  configpath
                                  )
            if anchor == False:
                for i in range(leng):
                    thisRow[i] = combineValues(jsndict, paths[i])
                csvwriter.writerow(thisRow)
                row_count = row_count + 1
            else:
                anchorArray = getJsonValue(jsndict, anchor)
                if anchorArray is not None and isinstance(anchorArray, list):
                    for z in anchorArray:
                        for i in range(leng):
                            if paths[i][:7] == 'Anchor:':
                                thisRow[i] = combineValues(z, paths[i][7:])
                            else:
                                thisRow[i] = combineValues(jsndict, paths[i])
                        csvwriter.writerow(thisRow)
                        row_count = row_count + 1
                elif anchorArray is not None:
                    for i in range(leng):
                        if paths[i][:7] == 'Anchor:':
                            thisRow[i] = combineValues(anchorArray,
                                                       paths[i][7:]
                                                       )
                        else:
                            thisRow[i] = combineValues(jsndict, paths[i])
                    csvwriter.writerow(thisRow)
                    row_count = row_count + 1

    csvfile.close()
    logging.info('Finished parsing "%s", %s rows written',
                 configpath,
                 str(row_count)
                 )
