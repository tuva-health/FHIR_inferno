import json
import os
import configparser
from collections import defaultdict, Counter



# Configuration
folder_path = r'../bcda_synthetic/input_fhir'  # folder path with files to analyze
keyword = 'coverage' # Replace with the keyword of filenames to process, usually the resource type
anchor_path = ''  # Replace with your root path or leave as empty string for the root of the JSON
# ignore_list = ['procedure','diagnosis','supportingInfo','benefitBalance.0.financial','item.0.adjudication', 'item.0.extension', 'extension', 'careTeam']#['extension', 'activity','contained']  # Replace with paths to ignore
ignore_list = []
inputFormat = 'ndjson'




##### script

def get_sub_object(obj, path):
    for part in path.split('.'):
        if part.isdigit():
            part = int(part)
        try:
            obj = obj[part]
        except (TypeError, KeyError, IndexError):
            return None
    return obj

def get_all_paths(json_obj, current_path='', all_paths=defaultdict(list), ignore_paths=set(), max_array_counts=defaultdict(int)):
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

def analyze_one_file(root_obj,root_paths,anchor_paths,ignore_set,anchor_path,max_root_array_counts,max_anchor_array_counts):
    paths, max_counts = get_all_paths(root_obj, all_paths=defaultdict(list),
                                      ignore_paths=ignore_set.union([anchor_path]),
                                      max_array_counts=max_root_array_counts)
    for path, values in paths.items():
        for value in values:
            root_paths[path][value] += 1
    for path, count in max_counts.items():
        max_root_array_counts[path] = max(max_root_array_counts[path], count)

    if anchor_path:
        anchor_obj = get_sub_object(root_obj, anchor_path)
        # Check if the root data is a list and process accordingly
        if isinstance(anchor_obj, list):
            for item in anchor_obj:
                paths, max_counts = get_all_paths(item, all_paths=None, ignore_paths=ignore_set,
                                                  max_array_counts=max_anchor_array_counts)
                for path, values in paths.items():
                    for value in values:
                        anchor_paths[path][value] += 1
                for path, count in max_counts.items():
                    max_anchor_array_counts[path] = max(max_anchor_array_counts[path], count)
        else:
            paths, max_counts = get_all_paths(anchor_obj, all_paths=defaultdict(list), ignore_paths=ignore_set,
                                              max_array_counts=max_anchor_array_counts)
            for path, values in paths.items():
                for value in values:
                    anchor_paths[path][value] += 1
            for path, count in max_counts.items():
                max_anchor_array_counts[path] = max(max_anchor_array_counts[path], count)
    return root_paths, anchor_paths, max_root_array_counts, max_anchor_array_counts


def analyze_json_files(folder_path, keyword, anchor_path='', ignore_list=None, inputFormat='json'):
    # ct = 0
    if ignore_list is None:
        ignore_list = []
    ignore_set = set(ignore_list)
    root_paths = defaultdict(Counter)
    anchor_paths = defaultdict(Counter)
    max_root_array_counts = defaultdict(int)
    max_anchor_array_counts = defaultdict(int)

    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith('.' + inputFormat) and keyword in filename:
                with open(os.path.join(root, filename), 'r') as file:
                    if inputFormat == 'json':
                        root_obj = json.load(file)
                        root_paths, anchor_paths, max_root_array_counts, max_anchor_array_counts = analyze_one_file(
                            root_obj, root_paths, anchor_paths, ignore_set, anchor_path, max_root_array_counts,
                            max_anchor_array_counts)
                    elif inputFormat == 'ndjson':
                        for line in file:
                            # ct += 1
                            # print(ct)

                            root_obj = json.loads(line)
                            root_paths, anchor_paths, max_root_array_counts, max_anchor_array_counts = analyze_one_file(
                                root_obj, root_paths, anchor_paths, ignore_set, anchor_path, max_root_array_counts,
                                max_anchor_array_counts)

    ini_filename = f'config_{keyword}.ini'
    hashmap_filename = f'hashmaps\\{keyword}_hashmap.json'
    if anchor_path:
        ini_filename = f'config_{keyword}_{anchor_path}.ini'
        hashmap_filename = f'hashmaps\\{keyword}_{anchor_path}_hashmap.json'
    return root_paths,anchor_paths, max_root_array_counts,max_anchor_array_counts, ini_filename, hashmap_filename





root_result,anchor_result, max_root_array_counts,max_anchor_array_counts, ini_filename, hashmap_filename = analyze_json_files(folder_path, keyword, anchor_path, ignore_list,inputFormat)

print(f"\n--{ini_filename}")
print(f"Number of root items: {len(root_result)}")
if anchor_path:
    print(f"Number of anchor items: {len(anchor_result)}")


# Print max array counts
print("\n--Max array counts:")

if anchor_path:
    for path, count in max_anchor_array_counts.items():
        if count > 0:
            print(f"{anchor_path}.[*].{path}: {count}")
else:
    for path, count in max_root_array_counts.items():
        if count > 0:
            print(f"{path}: {count}")

hash_obj = {"root": root_result}
if anchor_path:
    hash_obj["anchor"] = anchor_result



# Write the hashmap JSON file
# with open(hashmap_filename, 'w') as f:
#     json.dump(hash_obj, f, indent=4)

# Prepare and write the INI file
config = configparser.ConfigParser()
config['GenConfig'] = {
    'outputPath': f"{keyword}.csv",
    'inputFormat': inputFormat,
    'writeMode': 'append'
}
if anchor_path:
    config['GenConfig']['anchor'] = anchor_path
    config['Struct'] = {path.replace('.', '_'): 'Anchor:'+path for path in anchor_result if path}
    config['anchor_paths'] = {path.replace('.', '_'): 'Anchor:'+path for path in anchor_result if path}
else:
    config['Struct'] = {path.replace('.', '_'): path for path in root_result if path}

config['root_paths'] = {path.replace('.', '_'): path for path in root_result if path}

if ignore_list:
    # Exclude empty strings from ignore_list
    config['ignore_paths'] = {path.replace('.', '_'): path for path in ignore_list if path}

config['Struct']['filename'] = 'Filename:'
config['Struct']['processed_datetime'] = 'GetDate:'
with open(ini_filename, 'w') as configfile:
    config.write(configfile)


# Write all the paths to a file
# with open(f'paths_{keyword}.txt', 'w') as file:
#     for path in result.keys():
#         file.write(path + '\n')