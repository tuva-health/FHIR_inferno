import os
import configparser

### configuration
config_folder = r'configurations/configuration_Metriport/'  
filename = 'create_table_scripts.sql'   
schema = 'raw_data'                     # PostgreSQL schemas are typically lowercase
convert_date_types = True              

# Function to format the table name based on the file name
def format_table_name(file_name):
    if file_name.startswith("config_"):
        file_name = file_name[7:]
    return file_name.replace('.ini', '').replace('.', '_').lower()  # PostgreSQL prefers lowercase

# Function to determine the data type of a column
def get_data_type(column_name, date_types):
    if date_types:
        if column_name.endswith("date"):
            return "DATE"
        elif column_name.endswith("datetime") or column_name.endswith("time"):
            return "TIMESTAMP"
    return "STRING"  # Changed from TEXT to STRING for Snowflake

# Function to create a COPY statement for PostgreSQL
def create_copy_statement(table_name, schema):
    return f"""
-- COPY INTO statement for {table_name}
COPY INTO {schema}.{table_name}
FROM '@your_stage/{table_name}.csv'
FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1);
"""

# Function to create a SELECT statement
def create_select_statement(table_name, schema):
    return f"""
-- SELECT statement for {table_name}
SELECT * FROM {schema}.{table_name};
"""

def process_ini_files(input_dir, output_file, schema=None, date_types=False):
    all_copies = ''
    all_selects = ''

    # Create schema if it doesn't exist
    schema_creation = f"CREATE SCHEMA IF NOT EXISTS {schema};\n\n"

    with open(output_file, 'w') as output:
        output.write(schema_creation)
        
        for file in os.listdir(input_dir):
            if file.endswith(".ini"):
                config = configparser.ConfigParser()
                config.read(os.path.join(input_dir, file))

                if 'Struct' in config:
                    table_name = format_table_name(file)
                    columns = config['Struct']

                    # Construct the CREATE TABLE statement
                    create_statement = f"CREATE TABLE IF NOT EXISTS {schema}.{table_name} (\n"
                    create_statement += ",\n".join([f"    {col.lower()} {get_data_type(col, date_types)}" for col in columns])
                    create_statement += "\n);\n"

                    # Write to output file
                    output.write(create_statement)

                    # Write COPY statement
                    output.write("\n/*\n")
                    copy_statement = create_copy_statement(table_name, schema)
                    all_copies += copy_statement + "\n"
                    output.write(copy_statement)

                    # Write SELECT statement
                    select_statement = create_select_statement(table_name, schema)
                    all_selects += select_statement + "\n"
                    output.write(select_statement + "\n*/\n\n")

        # Write all COPY and SELECT statements at the end of the file
        output.write("/*\n")
        output.write("-- COPY STATEMENTS\n" + all_copies + "\n")
        output.write("-- SELECT STATEMENTS\n" + all_selects)
        output.write("*/")

# Remove the stage parameter since it's not needed for PostgreSQL
process_ini_files(config_folder, filename, schema, convert_date_types)
