import json
import csv
import configparser

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
                tempVal = " ".join([str(item) for item in lnjsn[x]])
                lnjsn = tempVal
            else:
                lnjsn = ""
        elif x.startswith("ArrNotHave:"):
            x = x[11:]
            found = False
            for i in range(len(lnjsn)):
                if getJsonValue(lnjsn[i], x.replace(",", ".")) is None:
                    lnjsn = lnjsn[i]
                    found = True
                    break
            if found != True:
                return None
        elif x.startswith("ArrCond:"):
            spl = x[8:].split("|")
            found = False
            for i in range(len(lnjsn)):
                if getJsonValue(lnjsn[i], spl[0].replace(",", ".")) == spl[1].replace(
                    ",", "."
                ):
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
            if lnjsn[spl[0]] == spl[1].replace(",", "."):
                lnjsn = spl[2]
            else:
                lnjsn = spl[3]
        elif x.startswith("Left:"):
            spl = x[5:].split("|")
            if spl[0] in lnjsn:
                lnjsn = lnjsn[spl[0]]
                lnjsn = lnjsn[: int(spl[1])]
            else:
                return None
        elif x.startswith("LTrim:"):
            spl = x[6:].split("|")
            if spl[0] in lnjsn:
                lnjsn = lnjsn[spl[0]]
                lnjsn = lnjsn[int(spl[1]) :]
            else:
                return None
        elif x.startswith("TimeForm:"):
            x = x[9:]
            if x in lnjsn:
                lnjsn = lnjsn[x]
                lnjsn = lnjsn[:19].replace("T", " ")
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


def is_input_file_bundle(input_file):
    for line in input_file:
        if "Bundle" in line:
            input_file.close()
            return True
    input_file.close()
    return False


def get_fhir_resources(input_file):
    opened_file = open(input_file)
    bundle = json.load(opened_file)

    resources = []
    for resource in bundle["entry"]:
        resources.append(json.dumps(resource["resource"]))

    opened_file.close()
    return resources


def convert_json_resource_to_ndjson(resource):
    modified_resource = []
    for i, text in enumerate(resource):
        modified_resource.append(text)
        modified_resource[i] = modified_resource[i].strip()

    return {"".join(modified_resource)}


def is_csv_empty(csv_file):
    with open(csv_file, newline=""):
        csv_dict = [row for row in csv.DictReader(csv_file)]
        if len(csv_dict) != 0:
            return False
    return True


def get_fhir_resources_types_from_bundle(inputPath):
    resources = get_fhir_resources(inputPath)

    found_resources = []
    for res in resources:
        resource_type = json.loads(res)["resourceType"]
        if resource_type not in found_resources:
            found_resources.append(resource_type)

    return found_resources


def filter_resources(resource, list_of_resources):
    if resource in list_of_resources:
        return True
    else:
        return False


def get_fhir_resource_type_from_ndjson(inputPath):
    resource_type = ""
    with open(inputPath, "r") as input_path:
        for line in input_path:
            if resource_type == "":
                resource_type = json.loads(line)["resourceType"]
    return resource_type


def get_config_options(config):
    header = []
    paths = []
    if config.has_option("GenConfig", "anchor"):
        anchor = config["GenConfig"]["anchor"]
    else:
        anchor = False
    if config.has_option("GenConfig", "WriteMode"):
        if config["GenConfig"]["WriteMode"] == "append":
            write_mode = "a"
    else:
        write_mode = "w"

    for key in config["Struct"]:
        header.append(key)
        paths.append(config["Struct"][key])

    return (write_mode, anchor, header, paths, len(header))


def get_csv_outputs(inputPath, config_paths, resources=None):
    found_resources = []
    output = []
    parsed_paths = []

    # if not given resources, this is ndjson
    if resources == None:
        config = configparser.ConfigParser()
        config.read(config_paths)
        outputPath = f"{get_fhir_resource_type_from_ndjson(inputPath)}.csv"
        write_mode, anchor, header, paths, leng = get_config_options(config)

        thisRow = [""] * leng
        csv_file = open(outputPath, write_mode, newline="")
        csv_writer = csv.writer(
            csv_file, delimiter=",", escapechar="\\", quoting=csv.QUOTE_ALL
        )

        if write_mode == "w":
            csv_writer.writerow(header)

        output.append(
            {
                "resource": open(inputPath),
                "inputPath": inputPath,
                "thisRow": thisRow,
                "leng": leng,
                "csv_writer": csv_writer,
                "paths": paths,
                "anchor": anchor,
            }
        )
    else:
        for res in resources:
            resource_type = json.loads(res)["resourceType"]
            if resource_type not in found_resources:
                # find which configPath is the right one
                found_resources.append(resource_type)

        for i, path in enumerate(config_paths):
            parsed_paths.append(found_resources[i])
            config = configparser.ConfigParser()
            config.read(path)

            write_mode, anchor, header, paths, leng = get_config_options(config)

            thisRow = [""] * leng

            if config.has_option("GenConfig", "resourceType"):
                matched_fhir_resources = [
                    res
                    for res in resources
                    if json.loads(res)["resourceType"] == found_resources[i]
                ]
                if len(matched_fhir_resources) == 0:
                    print(
                        f"Warning: no resources found for {found_resources[i]} resource"
                    )
                    continue
                outputPath = f"{found_resources[i]}.csv"
                csv_file = open(outputPath, write_mode, newline="")
                csv_writer = csv.writer(
                    csv_file,
                    delimiter=",",
                    escapechar="\\",
                    quoting=csv.QUOTE_ALL,
                )

                if write_mode == "w":
                    csv_writer.writerow(header)
                    write_mode = "a"

                for matched_resource in matched_fhir_resources:
                    output.append(
                        {
                            "resource": matched_resource,
                            "inputPath": inputPath,
                            "thisRow": thisRow,
                            "leng": leng,
                            "csv_writer": csv_writer,
                            "paths": paths,
                            "anchor": anchor,
                        }
                    )
            else:
                print(f"Error: resourceType key for {path} missing!")
                exit()

        # check to see if any resources were missed
        missed_resources = []
        for res in get_fhir_resources_types_from_bundle(inputPath):
            if not filter_resources(res, parsed_paths):
                missed_resources.append(res)

        if len(missed_resources) > 0:
            m_out = ", ".join(map(str, missed_resources))
            print(
                f"Warning: the following resources were found but not parsed: {m_out}"
            )

    return output


def parse_resource(
    input_resource, input_path, row, config_length, csv_writer, paths, anchor
):

    newInput = []
    if ".json" in input_path:
        newInput = convert_json_resource_to_ndjson(input_resource)
    else:
        newInput = input_resource

    for jsntxt in newInput:
        try:
            jsndict = json.loads(jsntxt)
            if anchor == False:
                for i in range(config_length):
                    row[i] = combineValues(jsndict, paths[i])
                csv_writer.writerow(row)
            else:
                anchorArray = getJsonValue(jsndict, anchor)
                if anchorArray is not None and isinstance(anchorArray, list):
                    for z in anchorArray:
                        for i in range(config_length):
                            if paths[i][:7] == "Anchor:":
                                row[i] = combineValues(z, paths[i][7:])
                            else:
                                row[i] = combineValues(jsndict, paths[i])
                        csv_writer.writerow(row)
                elif anchorArray is not None:
                    for i in range(config_length):
                        if paths[i][:7] == "Anchor:":
                            row[i] = combineValues(anchorArray, paths[i][7:])
                        else:
                            row[i] = combineValues(jsndict, paths[i])
                    csv_writer.writerow(row)
        except:
            badfile = open("badfile.csv", "a")
            badfile.write(jsntxt)

    if ".json" not in input_path:
        input_resource.close()


####### Main #######
def parse(inputPath, config_paths):
    bundle = is_input_file_bundle(open(inputPath))
    # if this is a bundle, process the file and extract the FHIR resources
    if bundle:
        resources = get_fhir_resources(inputPath)
        prepared_outputs = get_csv_outputs(inputPath, config_paths, resources)
        for output in prepared_outputs:
            parse_resource(
                output["resource"],
                inputPath,
                output["thisRow"],
                output["leng"],
                output["csv_writer"],
                output["paths"],
                output["anchor"],
            )
    else:
        output = get_csv_outputs(inputPath, config_paths)[0]
        parse_resource(
            output["resource"],
            inputPath,
            output["thisRow"],
            output["leng"],
            output["csv_writer"],
            output["paths"],
            output["anchor"],
        )
