import json
import boto3
import configparser
from collections import defaultdict, Counter




## s3 path to be analyzed
s3_path = 's3://my-FHIR-bucket/FHIR/'
## resource type list to build: an array of sets wtih three members: the keyword for the config to be built, the anchor, and a list of any ignore_paths
resource_type_list = [
    ('AllergyIntolerance', '', []),
    ('CarePlan', '', ['activity', 'contained']),
    ('CarePlan', 'activity', []),
    ('CarePlan', 'contained', []),
    ('Coverage', '', []),
    ('DocumentReference', '', []),
    ('FamilyMemberHistory', '', ['condition']),
    ('FamilyMemberHistory', 'condition', []),
    ('Immunization', '', ['contained']),
    ('Immunization', 'contained', []),
    ('Observation', '', ['contained', 'extension', 'hasMember']),
    ('Observation', 'contained', []),
    ('Observation', 'extension', []),
    ('Observation', 'hasMember', []),
    ('Organization', '', [])
]





##### Script

def get_sub_object(obj, path):
    for part in path.split('.'):
        if part.isdigit():
            part = int(part)
        try:
            obj = obj[part]
        except (TypeError, KeyError, IndexError):
            return None
    return obj


def get_all_paths(json_obj, current_path='', all_paths=defaultdict(list), ignore_paths=set(),max_array_counts=defaultdict(int)):
    if all_paths is None:
        all_paths = defaultdict(list)
    if ignore_paths is None:
        ignore_paths=set()
    if max_array_counts is None:
        max_array_counts = defaultdict(int)
    if isinstance(json_obj, dict):
        for k, v in json_obj.items():
            new_path = f"{current_path}.{k}" if current_path else k
            if new_path not in ignore_paths:
                get_all_paths(v, new_path, all_paths, ignore_paths, max_array_counts)
    elif isinstance(json_obj, list):
        max_array_counts[current_path] = max(max_array_counts[current_path], len(json_obj))
        for idx, item in enumerate(json_obj):
            get_all_paths(item, f"{current_path}.{idx}", all_paths, ignore_paths, max_array_counts)
    else:
        all_paths[current_path].append(json_obj)
    return all_paths, max_array_counts


def analyze_json_files(s3_path, resource_type_list, hashmap_analysis=False):
    # Connect to S3
    s3 = boto3.resource('s3')
    bucket_name, prefix = parse_s3_path(s3_path)  # Define a function to extract bucket name and prefix from s3_path

    # Initialize data structures
    results = {}

    for resource_type, anchor_path, ignore_list in resource_type_list:
        results[(resource_type, anchor_path)] = {
            'root_paths': defaultdict(Counter),
            'anchor_paths': defaultdict(Counter),
            'max_root_array_counts': defaultdict(int),
            'max_anchor_array_counts': defaultdict(int)
        }

    # Process files in S3 bucket
    paginator = s3.meta.client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for obj in page['Contents']:
            file_key = obj['Key']
            for resource_type, anchor_path, ignore_list in resource_type_list:
                if resource_type in file_key:
                    file_obj = s3.Object(bucket_name, file_key)
                    file_content = file_obj.get()['Body'].read()
                    root_obj = json.loads(file_content)

                    ignore_set = set(ignore_list)
                    if anchor_path:
                        anchor_obj = get_sub_object(root_obj, anchor_path)
                        if isinstance(anchor_obj, list):
                            for item in anchor_obj:
                                paths, max_counts = get_all_paths(item, all_paths=None, ignore_paths=ignore_set,
                                                                  max_array_counts=
                                                                  results[(resource_type, anchor_path)][
                                                                      'max_anchor_array_counts'])
                                for path, values in paths.items():
                                    for value in values:
                                        results[(resource_type, anchor_path)]['anchor_paths'][path][value] += 1
                        else:
                            paths, max_counts = get_all_paths(anchor_obj, all_paths=defaultdict(list),
                                                              ignore_paths=ignore_set,
                                                              max_array_counts=results[(resource_type, anchor_path)][
                                                                  'max_anchor_array_counts'])
                            for path, values in paths.items():
                                if hashmap_analysis:
                                    for value in values:
                                        results[(resource_type, anchor_path)]['anchor_paths'][path][value] += 1
                                else:
                                    results[(resource_type, anchor_path)]['anchor_paths'][path]['__count__'] += len(values)
                    else:
                        paths, max_counts = get_all_paths(root_obj, all_paths=defaultdict(list), ignore_paths=ignore_set.union({anchor_path}), max_array_counts=results[(resource_type, anchor_path)]['max_root_array_counts'])
                        for path, values in paths.items():
                            if hashmap_analysis:
                                for value in values:
                                    results[(resource_type, anchor_path)]['root_paths'][path][value] += 1
                            else:
                                results[(resource_type, anchor_path)]['root_paths'][path]['__count__'] += len(values)

    # Output INI files and optional hashmap analysis
    for (resource_type, anchor_path), data in results.items():
        # Generate filenames based on resource type and anchor path
        ini_filename = f'config_{resource_type}_{anchor_path}.ini' if anchor_path else f'config_{resource_type}.ini'
        hashmap_filename = f'hashmaps/{resource_type}_{anchor_path}_hashmap.json' if anchor_path else f'hashmaps/{resource_type}_hashmap.json'

        # Prepare and write the INI file
        config = configparser.ConfigParser()
        config['GenConfig'] = {
            'inputPath': f"{resource_type}.json",
            'outputPath': f"{resource_type}.csv",
            'parseMode': 'json',
            'WriteMode': 'append'
        }

        if anchor_path:
            config['GenConfig']['anchor'] = anchor_path
            config['Struct'] = {path.replace('.', '_'): 'Anchor:' + path for path in data['anchor_paths'].keys()}
            config['anchor_paths'] = {path: path for path in data['anchor_paths'].keys()}
        else:
            config['Struct'] = {path.replace('.', '_'): path for path in data['root_paths'].keys()}

        config['root_paths'] = {path.replace('.', '_'): path for path in data['root_paths'].keys()}

        # Ignore paths are assumed to be the same for all items with the same resource type and anchor path
        ignore_list = next((ignore for res_type, anchor, ignore in resource_type_list if
                            res_type == resource_type and anchor == anchor_path), [])
        if ignore_list:
            config['ignore_paths'] = {path: path for path in ignore_list}

        # Write the INI file
        with open(ini_filename, 'w') as configfile:
            config.write(configfile)

        # Write the hashmap JSON file

        hash_obj = {
            "root": data['root_paths'],
            "max_root_array_counts": data['max_root_array_counts']
        }
        if anchor_path:
            hash_obj["anchor"] = data['anchor_paths']
            hash_obj["max_anchor_array_counts"] = data['max_anchor_array_counts']

        with open(hashmap_filename, 'w') as f:
            json.dump(hash_obj, f, indent=4)

def parse_s3_path(s3_path):
    if s3_path.startswith('s3://'):
        s3_path = s3_path[5:]

    parts = s3_path.split('/', 1)
    bucket_name = parts[0]
    prefix = parts[1] if len(parts) > 1 else ''

    return bucket_name, prefix




analyze_json_files(s3_path, resource_type_list, hashmap_analysis=False)