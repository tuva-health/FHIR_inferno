# FHIR Inferno
FHIR Inferno is a python library designed to parse json objects, so that they can be loaded to a warehouse or database for further processing or analysis.  The library was designed for simplicity, and may not handle all advanced use cases.

#### Prerequisites
 - Python 3.x
 - External libraries:
   - csv output mode: None
   - parquet output mode: pandas, pyarrow
   - return mode: pandas
   - 
### Usage
The library contains a parse method that parses through a .ndjson file containing multiple fhir objects or a json file, and either writes the content to a csv, parquet file, or returns a data frame to the caller.
The parse method can also compare the columns that were present in the FHIR object against known columns, and write any new columns to a separate file for further consideration.


    import parseFhir
    
    parseFhir.parse(configPath=r'config/config_Patient.ini', inputPath='FHIR_Input/Patient_0001.json',outputPath='FHIR_output/Patient_0001.csv')


The parseFhir method streams .ndjson files one line at a time, so large input files can be handled without needing to commit the entire file to memory.

You can also use the utility script to execute the parse function via CLI.

    python utils/run_parser.py --config config/your_config.ini --input data/your_input.json --output output.csv


## Configuration
The path to the config file must be passed to the parse method via a `configPath` parameter.  There are a number of general configurations that can be passed to the method or set in the config file in the `[GenConfig] section.

| Configuration | Definition                                                                                                                   | required                                     | defualt  |
|---------------|------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------|----------|
| inputPath     | Path of the input file                                                                                                       | yes                                          | none     |
| outputPath    | Path of the output csv file                                                                                                  | yes for csv/parquet mode, no for return mode | none     |
| missingPath   | If optionally set, function will write any unknown or new json paths in fhir objects to theis file                           | no                                           | none     |
| inputFormat   | `json` or `ndjson`, depending on the input format. Currently, ndjson only supports csv output                                | no                                           | `json`   |
| outputFormat  | `csv` or `parquet` to write to **outputPath**, or `return` to return a data fram to the caller                               | no                                           | `return` |
| writeMode     | Determines if parseFHIR will overwrite the output file, or append to the output file.  Only applicable for csv output format | no                                           | `append` |

The ini file will have at minimumm two sections: `[GenConfig]` , which defines the input and output files as well as some file-level options, and a `[Struct]` section, which defines the structure of the csv including the columns in the output, as well as the path(s) to that data in the fhir object.
Optionally it can have a `[root_paths]` section, `[anchor_paths]` section, and `[ignore_paths]` section, which will determine the currently known paths for comparison, if the user wants to report the presence of any unknown or new paths (see missingPaths config description below).  

    [GenConfig]
    inputPath = patients.ndjson
    outputPath = outputpatient.csv
    
    [Struct]
    patient_id = identifier.ArrCond:use|usual.value
    name = name.ArrNotHave:period,end.ArrJoin:given
           name.ArrNotHave:period,end.family
    data_source = Hard:SynFhir

We provide scripts that help build the configs by analyzing batches of FHIR objects. See the [helper scripts readme](./helper_scripts/readme.md) for more info.


### Config Section: `[GenConfig]` - General Configuration
First section of the ini file, defining object level configurations. Example:

    [GenConfig]
    inputPath = vitalsign.ndjson
    outputPath = outputvitalsign.csv
    inputFormat = ndjson
    outputFormat = csv
    anchor = component.ArrCond:code,text|Diastolic blood pressure.valueQuantity
    writeMode = append

All general configuration configs (other than configPath) can be set in either the parameters passed to the function or the GenConfig section.
In addition, an `anchor` can optionally be set in the [GenConfig] section, which will point to an array in the FHIR object that will act as the root.  More details below.  

#### inputPath and outputPath
The relative or global paths to input and output files. Path must be to a file, no wildcards for input are available at this time.

outputFile is not required for outputFormat = return.  If in csv outputFormat, and write writeMode, the output file will contain a header row defined by the keys in the `[Struct]` configuraiton section.  
CSVs will be fully quoted.


    [GenConfig]
    inputPath = vitalsign.ndjson
    outputPath = outputvitalsign.csv

#### inputFormat and outputFormat
inputFormat can be ndjson or json. If ndjson inputFormat is set, the input path must point to a well-formed .ndjson file. Ndjson, or "newline delimeted json," is a format that allows for a series of json objects in one file.  The format specifications are the same as json, except that new lines are not  allowed in internal whitespace within the json object; instead, newlines are used to separate json object in the one file. Other internal whitespace such as tab and space are fine.

outputFormat can be csv, parquet, or return.  If outputFormat = return, the function will return a dataFrame.  If outputFormat = csv or parqut, the function will return None and will write the data to the outputPath.

For inputFormat = ndjson, only outputFormat = csv is supported.  

Different outputFormats have different dependencies:
 - outputFormat = csv: there are no external libraries required.  
 - outputFormat = parquet: pandas and pyarrow must be installed.
 - outputFormat = return: pandas must be installed.



#### Anchor
If no anchor is supplied the output will include one row per FHIR object in the input, and all paths in the Struct section must be relative to the root of the fhir object.

If an anchor is supplied, the output will include one row for every object found at that path.  If the path points to an array, the output will include 0..n rows per input fhir object (one per objects found in the array at that path), e.g. `anchor = diagnosis` will output one row for every diagnosis found in the FHIR object, or no rows if there is no diagnosis array or if it is empty.  If the anchor points to a value, it will output one row per FHIR object assuming that the path to the object exists, e.g. a config `Anchor = component.ArrCond:code,text|Systolic blood pressure.valueQuantity` will output one row per fhir object, only if the object contains a component with a text of "Systolic blood pressure" and if that object contains a valueQuantity value.

If an anchor is defined, paths relative to the root object can be defined in the `[Struct]` section like normal, or paths that start with `Anchor` will be evaluated relative to the current iteration of the anchor path.  The following will output as many rows as there are `diagnosis` objects found in that array,and will output the patient_id (found in the parent object) and the code (found in the disgnosis array) 
    
    [GenConfig]
    inputPath = encounters.ndjson
    outputPath = outputcondition.csv
    anchor = diagnosis
    
    [Struct]
    patient_id = subject.LTrim:reference|8
    code = Anchor:condition.code.coding.0.code

#### WriteMode
Only relevant for outputMode = `csv`. The default behavior is `append`, which will write only the data to the file, and will append to an existing file.
`write`  will overwrite the file found at outputPath, and will also include a header row with the column names.

#### Missing Paths
If you want to be notified if any new columns come in that you were not aware of previously, you can set a missingPaths.  If set, any new paths will be written to a csv at that location.

To tell the parser which paths are already known, a `root_paths` or `anchor_paths` section must be filled out, and optionally an `ignore_paths` section can be filled out as well. 
More details on the structure of those configurations below.

### Config Section: `[Struct]` - Structure of the output
The Struct section defines the output.  Each key in the strut section will be a new column in the output csv.  The values should be a dot notated json path to the data in the fhir object. Integers can be used to hardcode specific iterations in an array.  If multiple fhir values should be concatenated into one column in the csv, they can be concatenated by notating multiple lines with separate paths.  To hardcode an empty column, give the Key but no value.

    [Struct]
    patient_id = identifier.0.value
    name = name.0.ArrJoin:given
           name.0.family
    gender = gender
    ethnicity = 
    data_source = Hard:SynFhir

There are a number of Methods that can be used to format values, choose particular iterations of an array, join values of an array, or perform other logic needed to extract the desired data

| Method Name | Operates on | Description                                                                                                                                                    | num parameters |
|-------------|-------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| ArrCond     | Array       | Array conditional: finds the first iteration of the array that meets the given condition                                                                       | 2              |
| ArrNotHave  | Array       | Array Not Having: finds the first iteration of the array that doesn't have the specified key                                                                   | 1              |
| ArrJoin     | Value Array | Array Join: Joins all values of the array and returns the concatenated list                                                                                    | 1              |
| Left        | value       | Left: takes the first x characters of a given value                                                                                                            | 2              |
| LTrim       | value       | Left Trim: removes the first x characters of a given value                                                                                                     | 2              |
| IfEx        | value       | If Exists: returns one value if the key exists, otherwise returns another value                                                                                | 3              |
| IfEq        | value       | If Equals: returns one value if the given key's value equals the value specified, otherwise returns another value                                              | 4              |
| TimeForm    | value       | Timestamp Format: converts timestamps in the YYYY-MM-DDThh:mm:ss+zz:zz format expected by fhir, to the YYYY-MM-DD hh:mm:ss format required to load to redshift | 1              |
| Hard        | nothing     | Hardcodes a specific value in the given column                                                                                                                 | 1              |
| Filename    | nothing     | Returns the name of the file passed to the function                                                                                                            | 0              |
| GetDate     | nothing     | Returns the time the file was processed                                                                                                                        | 0              |


### Config Sections: `[root_paths]`, `[anchor_paths]`, and `[ignore_paths]` identifying new or unknown json paths
If you want to know if any new paths are present in future json files, or if the structure of the FHIR objects change at all over time, you can set a missingPath parameter as a filepath where that information will be written as a csv.

You can define all known paths in a `[root_paths]` section if there is no anchor, or an `[anchor_paths]` section if an anchor is set.  
All columns can be defined as the values in the same dot notated json path format as the `[Struct]` section.  You can also optionally build an `[ignore_paths]` section;
any path you place in this section **and all of its children** will be ignored in the missingPaths comparison.

If the missingPaths parameter is set, in addition to the normal processing, the parse function will:
 - extract all of the json paths from the inputFile object(s)
 - identify any that are not present in the root_paths or anchor_paths section, depending on if an anchor is set in GenConfig
 - also ignore any remaining paths that are in, or are children of paths in the optional ignore_paths section
 - write any remaining paths to a csv at missingPaths

This can be helpful if you are trying to extract all of the information from the FHIR objects and do the processing in a warehouse or database, or if you want to make sure you're not missing anything if the format of the FHIR objects changes over time.

Helper functions, like [analyzeJson](./helper_scripts/analyzeJson.py) can build these sections out for you by analyzing batches of json files and building configs from all of the paths found.
See the [helper scripts readme](./helper_scripts/readme.md) for more info.

The output will have three columns: the filepath, the anchor that was being processed, and the path that was found that was not in the configuration.

#### General Setup: `[Struct]` Keys in config are columns in output
For every desired column in the output, add a key in the `[Struct]` section with the name of the desired column.  The value of any column that should be populated with FHIR data should be the dot notated Json path of the value. 

The FhirConnector will produce a header row for each key in struct, and then add data from each fire object to the output for any columns with valid paths.  A key with no path will produce an empty column

For example, this `[Struct]` section:

    patient_id = identifier.value
    ethnicity = 
    birth_date = birthDate

combined with this input file:

    { "identifier" : { "type" : "mrn", "value" : "123" }, "name" : "Jim Halpert", "birthDate" : "1985-01-02" }
    { "identifier" : { "type" : "mrn", "value" : "456" }, "name" : "Michael Bluth", "birthDate" : "1972-03-04" }
    { "identifier" : { "type" : "mrn", "value" : "789" }, "name" : "Leslie Knope", "birthDate" : "1980-05-06" }

will produce this csv:
    
    "patient_id","ethnicity","birth_date"
    "123","","1985-01-02"
    "456","","1972-03-04"
    "789","","1980-05-06"

#### General Setup: Dot notated json paths
The paths to the fhir data can be defined using dot notated json paths.  From the root or anchor, every child objet's key must be listed, separated by a `.`

Specific objects in an array can be referenced by their 0 based index.
    
    e.g. given this json object:
    { "patient: { "identifier" : { "type" : "mrn", "value" : "123" } } , "results" : [ { "sequence" : 1 , "test" : "glucose" , "result" : "100 mg/dL"} , { "sequence" : 1 , "test" : "calcuim" , "result" : "9.0 mg/dL"} ] }
    
    #the data can be extracted like so:
    [Struct]
    patient_id = patient.identifier.value
    first_test = results.0.test
    first_test_result = results.0.result
    second_test = results.1.test
    second_test_result = results.1.result

#### General Setup: concatenating multiple fhir paths to one field
If multiple json values should be concatenated into one column, their respective paths can be put on new lines in the config file.  They will be space separated.
    
    # this will concatenate all of the given names, the famiy name, and the suffix into one "name" field
    name = name.0.ArrJoin:given
           name.0.family
           name.0.suffix

#### Method `ArrCond:` Array Conditional

| Method syntax | `ArrCond:param1&#124;param2` |
|---------------|------------------------------|
| Operates On:  | Array                        |
| Param 1:      | path/key to evaluate         |
| Param 2:      | value to compare             |

ArrCond will return the first object in the array it finds that meets the given criteria, where the value at key/path param1 = param2. If the array is empty or if none of the object in the array meet the criteria, it will return None which will get translated to a blank string in the CSV.

If the key to evaluate is not at the root level of the array object, param1 can be a path, however `.` must be translated to `,` so they are not evaluated as actual steps in the full json path.
If the value to compare contains `.` they must be translated to `,` so they are not interpreted as steps in the json path.  It is assumed that commas are not in the values being compared.

    # returns the value of "code" of the first object of the "coding" array that has a system of "http://loinc.org"
    # i.e. gets the loinc code, irrespective of the presence of additional coding  
    loinc = code.coding.ArrCond:system|http://loinc,org.code
    
    # returns the "text" of the reference range that has a "type.text" of "Normal Range" 
    # i.e. gets the normal range of the reference range object, if it exists
    reference_range = referenceRange.ArrCond:type,text|Normal Range.text

#### Method `ArrNotHave:` Array Not Having

| Method syntax | `ArrNotHave:param1`   |
|---------------|-----------------------|
| Operates On:  | Array                 |
| Param 1:      | path/key to evaluate  |


ArrNotHave will return the first object in the array that does not have the key/value specified, or returns none if the array is empty or if all objects contain the given path

If the key to evaluate is not at the root level of the array object, param1 can be a path, however `.` must be translated to `,` so they are not evaluated as actual steps in the full json path.

    # returns value of "family" of the first object in the address array that doesn't have a "period.end" value
    # i.e. returns the active last name, even if historical names are included
    name.ArrNotHave:period,end.family

#### Method `ArrJoin:` Array Join

| Method syntax | `ArrJoin:param1`          |
|---------------|---------------------------|
| Operates On:  | Array of Values           |
| Param 1:      | key of array to concanate |

ArrJoin will only work on an array of values, not on an array of objects.  ArrJoin will concatenate all of the values in the array together (space separated) and return them to a single column.

    # returns concatenation of all values found in the "name.given" array
    # i.e. concatenates firstname, middlename, and any other names included  
    address = name.ArrNotHave:period,end.ArrJoin:given

#### Method `Hard:` Hard code a value

| Method syntax | `Hard:param1`     |
|---------------|-------------------|
| Operates On:  | Nothing           |
| Param 1:      | Value to Hardcode |

`Hard:` does not reference the input object, but rather hardcodes the same value in the output csv for every row.

    # Hard codes "icd-10-pcs"
    procedure_code_type = Hard:icd-10-pcs


#### Method `Left:` returns the first n characters 

| Method syntax | `Left:param1&#124;param2`    |
|---------------|------------------------------|
| Operates On:  | Value                        |
| Param 1:      | Key to take substring of     |
| Param 2:      | Number of characters to take |


takes param2 characters of the value of param1 key

    # gets the first 10 characters of the "order.authoredOn" field
    # i.e. gets the date from a field containing a datetime 
    request_date = order.Left:authoredOn|10

#### Method `Left:` returns the first n characters 

| Method syntax | `Left:param1&#124;param2`    |
|---------------|------------------------------|
| Operates On:  | Value                        |
| Param 1:      | Key to take substring of     |
| Param 2:      | Number of characters to take |


takes param2 characters of the value of param1 key

    # gets the first 10 characters of the "order.authoredOn" field
    # i.e. gets the date from a field containing a datetime 
    request_date = order.Left:authoredOn|10


#### Method `LTrim:` trims the first n characters 

| Method syntax | `LTrim:param1&#124;param2`                |
|---------------|-------------------------------------------|
| Operates On:  | Value                                     |
| Param 1:      | Key to take substring of                  |
| Param 2:      | Number of characters at the start to drop |


removes the first param2 characters of the value of param1 key and returns the result 

    # removes the first 10 characters from encounter.reference
    # i.e. given the value "encounter\12345| , removes the "encounter\" and returns "12345"
    request_date = encounter.LTrim:reference|10


#### Method `IfEx:` If value exists 

| Method syntax | `IfEx:param1&#124;param2&#124;param3`      |
|---------------|--------------------------------------------|
| Operates On:  | Value                                      |
| Param 1:      | Key/path to evaluate                       |
| Param 2:      | Value to return if key/path exists         |
| Param 3:      | Value to return if key/path does not exist |

Evaluates if the key/path in param1 exists, returns param2 if it does, otherwise returns param3

if param1 is a path, convert `.` in dot notated path to `,` so they are not evaluated as steps in the full json path

    # returns a 1 or 0, depending on if a "deceasedDateTime" key exists 
    death_flag = IfEx:deceasedDateTime|1|0



#### Method `IfEq:` If value exists 

| Method syntax | `IfEx:param1&#124;param2&#124;param3&#124;param4`        |
|---------------|----------------------------------------------------------|
| Operates On:  | Value                                                    |
| Param 1:      | Key/path to evaluate                                     |
| Param 2:      | Value to to compare to value of evaluated path at param1 |
| Param 3:      | Value to return if equal                                 |
| Param 4:      | Value to return if not equal                             |

Evaluates if the key/path in param1 equals the value in param2, returns param3 if it does, otherwise returns param4

if param1 is a path, or if param2 contains periods, convert `.` in parameters to `,` so they are not evaluated as steps in the full json path.  

    # returns "icd-10-cm" if the coding system is "http://www.cms.gov/Medicare/Coding/ICD10", otherwise returns "internal"
    code_type = code.coding.0.IfEq:system|http://www,cms,gov/Medicare/Coding/ICD10|icd-10-cm|internal




#### Method `TimeForm:` Format Time 

| Method syntax | `IfEx:param1&#124;param2&#124;param3&#124;param4` |
|---------------|---------------------------------------------------|
| Operates On:  | Value (in FHIR dateTime format)                   |
| Param 1:      | Key/path to evaluate                              |

Converts dateTimes in the `YYYY-MM-DDThh:mm:ss+zz:zz` format used by fhir to the `YYYY-MM-DD hh:mm:ss` format required to load to a datetime/timestampe (no timezone) in redshift and other dbms.  

    # Converts an effectiveDatetime to redshift input format
    # i.e. converts "2019-01-02T01:05:10.000Z" to "2019-01-02 01:05:10" 
    result_date = TimeForm:effectiveDateTime


















