import os
import configparser

### configuration
config_folder = r'configurations/configuration_bcda/config/'         ## folder with config files to analyze
filename = 'create_table_scripts.sql'   ## output filename
schema = 'RAW_DATA'                     ## schema to build
convert_date_types = True               ## whether or not to analyze column_names to identifiy dates and datetimes
stage = '@bcda_stage/'        ## name of the stage in which transformed fhir is located






### Script
# Function to format the table name based on the file name
def format_table_name(file_name):
    if file_name.startswith("config_"):
        file_name = file_name[7:]
    return file_name.replace('.ini', '').replace('.', '_')

# Function to determine the data type of a column
def get_data_type(column_name, date_types):
    if date_types:
        if column_name.endswith("date"):
            return "date"
        elif column_name.endswith("datetime") or column_name.endswith("time"):
            return "timestamp"
    return "varchar"

# Function to create a COPY INTO statement
def create_copy_statement(table_name, stage, schema):
    split_parts = table_name.split('_', 1)
    if len(split_parts) == 1:
        split_parts.append("[^_]+")
    else:
        split_parts[1] = ".*_" + split_parts[1] + ".*"
    # pattern = f"'{split}_[^.]+\\.csv'"  # Regex pattern for matching file names
    pattern = f"'.*{split_parts[0]}_{split_parts[1]}'"

    return f"""
-- COPY INTO statement for {table_name}
COPY INTO {schema + '.' if schema else ''}{table_name}
FROM {stage}
PATTERN = {pattern}
FILE_FORMAT = hg_csvs;
"""

# Function to create a SELECT statement
def create_select_statement(table_name, schema):
    return f"""
-- SELECT statement for {table_name}
SELECT * FROM {schema + '.' if schema else ''}{table_name};
"""

def process_ini_files(input_dir, output_file, schema=None, date_types=False, stage=None):
    all_copies = ''
    all_selects = ''

    # Open the output file
    with open(output_file, 'w') as output:
        # Loop through each file in the input directory
        for file in os.listdir(input_dir):
            if file.endswith(".ini"):
                # Reinitialize configparser for each file
                config = configparser.ConfigParser()
                config.read(os.path.join(input_dir, file))

                # Check if 'Struct' section exists
                if 'Struct' in config:
                    table_name = format_table_name(file)
                    columns = config['Struct']

                    # Construct the CREATE TABLE statement
                    create_statement = f"CREATE OR REPLACE TABLE {'.'.join([schema, table_name]) if schema else table_name} (\n"
                    create_statement += ",\n".join([f"  {col} {get_data_type(col, date_types)}" for col in columns])
                    create_statement += "\n);\n"

                    # Write to output file
                    output.write(create_statement)

                    # Write COPY INTO statement if stage is provided
                    output.write("\n/*\n")
                    if stage:
                        copy_statement = create_copy_statement(table_name, stage, schema)
                        all_copies += copy_statement + "\n"
                        all_copies += copy_statement + "\n"
                        output.write( copy_statement )

                    # Write SELECT statement
                    select_statement = create_select_statement(table_name, schema)
                    all_selects += select_statement + "\n"
                    output.write( select_statement + "\n*/\n\n")

        # Write all COPY INTO and SELECT statements at the end of the file
        output.write("/*\n")
        if stage:
            output.write("-- COPY STATEMENTS\n" + all_copies + "\n")
        output.write("-- SELECT STATEMENTS\n" + all_selects)
        output.write("*/")

process_ini_files(config_folder, filename, schema, convert_date_types, stage)
