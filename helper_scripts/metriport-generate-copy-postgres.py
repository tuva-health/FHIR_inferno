import os

output_dir = '/Users/ramilgaripov/Desktop/metriport/inferno/fhir-inferno/outputs'
schema = 'RAW_DATA'

# PostgreSQL connection details
pg_host = 'localhost'
pg_port = '5432'
pg_db = 'test_tuva'
pg_user = 'admin'

# First create the SQL file with all COPY commands
with open('copy_commands.sql', 'w') as f:
    # Add COPY commands for each CSV file
    for csv_file in os.listdir(output_dir):
        if csv_file.endswith('.csv'):
            table_name = csv_file.replace('.csv', '')
            f.write(f"COPY {schema}.{table_name} FROM '{output_dir}/{csv_file}' WITH (FORMAT csv, HEADER true);\n")

# Then create a shell script to execute the SQL file
with open('load_data.sh', 'w') as f:
    f.write('#!/bin/bash\n\n')
    f.write('# Execute all COPY commands\n')
    f.write(f'psql -h {pg_host} -p {pg_port} -U {pg_user} -d {pg_db} -f copy_commands.sql\n')

# Make the script executable
os.chmod('load_data.sh', 0o755)

print("Generated files:")
print("1. copy_commands.sql - Contains all COPY statements")
print("2. load_data.sh - Shell script to execute the SQL file")
print("\nTo load the data, run:")
print("./load_data.sh") 