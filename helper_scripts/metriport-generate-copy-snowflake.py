import os

output_dir = '/Users/ramilgaripov/Desktop/metriport/inferno/fhir-inferno/outputs'
db="TEST_TUVA"
stage="my_test_stage"
schema = 'RAW_DATA'

output_filename="scratch-copy-commands.sql"
# First create the SQL file with all COPY commands
with open(output_filename, 'w') as f:
    # Add COPY commands for each CSV file
    for csv_file in os.listdir(output_dir):
        if csv_file.endswith('.csv'):
            table_name = csv_file.replace('.csv', '')
            f.write(f"COPY INTO {db}.{schema}.{table_name.upper()}\n")
            f.write(f"FROM '@{stage}/{table_name}.csv'\n")
            f.write("FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY='\"' SKIP_HEADER=1)\n")
            f.write("ON_ERROR = 'CONTINUE';\n\n")


print("Generated files:")
print(f"{output_filename} - Contains all COPY statements")
print("\nBefore loading data, make sure to:")
print("1. Create a stage for each table")
print("2. Upload the CSV files to their respective stages")
print("3. Install SnowSQL CLI")