import os
import configparser

## Config
ini_filepath = r'config_files'   ## Folder path where config files are
output_filepath = r'models'  ## Folder path where select files will be written
schema = 'raw_data'              ## Schema
add_qualify =  True              ## If true, will add a qualify statement that will get the latest version of each file, to get a unique record if an update happened and the same item was processed again










# Function to format the table name based on the file name
def format_table_name(file_name):
    if file_name.startswith("config_"):
        file_name = file_name[7:]
    return file_name.replace('.ini', '').replace('.', '_')

# Function to determine the data type of a column
def get_data_type(column_name, date_types):
    if date_types:
        if column_name.endswith("datetime") or column_name.endswith("time") or column_name.endswith("processed_date"):
            return "timestamp"
        elif column_name.endswith("date"):
            return "date"
    return "varchar"

# Function to create a SELECT statement
def create_select_statement(table_name, schema, columns,add_qualify=False):
    column_list = ",\n    ".join(columns.keys())
    table_reference = f"{{{{source('{schema}', '{table_name.lower()}') }}}}"
    return_string =  f"""
-- SELECT statement for {table_name}
SELECT \n    {column_list} \nFROM {table_reference} x
"""
    if add_qualify:
        return_string += f"\nQUALIFY rank() over(partition by filename order by processed_date desc) = 1"
    return return_string

def process_ini_files(input_dir, output_dir, schema=None, add_qualify=False):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

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

                # Write SELECT statement
                select_statement = create_select_statement(table_name, schema, columns,add_qualify)

                # Write to individual output file
                output_file_path = os.path.join(output_dir, f"stage__{table_name}.sql")
                with open(output_file_path.lower(), 'w') as output_file:
                    output_file.write(select_statement)

# Example usage
process_ini_files(r'C:\Users\forre\PycharmProjects\HG_connector\modules\lambda\config', r'selects', 'raw', True)
