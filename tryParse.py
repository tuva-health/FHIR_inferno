import parseFhir
import os
import json

# Define base paths
config_folder = 'configurations/configuration_Metriport/'
input_path = ''

def get_resource_type_from_config(config_file):
    """Extract the main resource type from config filename."""
    # Remove 'config_' prefix and '.ini' suffix
    name = config_file[7:-4] if config_file.startswith('config_') else config_file[:-4]
    
    # Handle special cases for nested/contained resources
    if '_' in name:
        # Return the base resource type (e.g., "MedicationStatement" from "MedicationStatement_contained")
        return name.split('_')[0]
    return name

# First, group config files by their base resource type
config_groups = {}
for config_file in os.listdir(config_folder):
    if config_file.endswith('.ini'):
        resource_type = get_resource_type_from_config(config_file)
        if resource_type not in config_groups:
            config_groups[resource_type] = []
        config_groups[resource_type].append(config_file)

# Process each resource type separately
for resource_type, config_files in config_groups.items():
    # First, filter the input file for just this resource type
    filtered_input = f'outputs/temp_{resource_type.lower()}.ndjson'
    
    with open(input_path, 'r') as infile, open(filtered_input, 'w') as outfile:
        for line in infile:
            try:
                resource = json.loads(line)
                if resource.get('resourceType') == resource_type:
                    outfile.write(line)
            except json.JSONDecodeError:
                continue

    # Now process each config file for this resource type using the filtered input
    for config_file in config_files:
        output_name = config_file.replace('config_', '').replace('.ini', '').lower()
        parseFhir.parse(
            configPath=os.path.join(config_folder, config_file),
            inputPath=filtered_input,
            inputFormat='ndjson',
            outputPath=f'outputs/{output_name}.csv',
            outputFormat='csv',
            writeMode='w'
        )
    
    # Clean up temporary file
    os.remove(filtered_input)