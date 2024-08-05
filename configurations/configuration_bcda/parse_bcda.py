import os
import parseFhir

config_dir = r'configurations\configuration_bcda\config'
input_dir = r'test'
output_dir = r'testout'
configs = ["Patient", "Coverage", "ExplanationOfBenefit"]


def main():
    for input_filename in os.listdir(input_dir):
        input_filepath = os.path.join(input_dir, input_filename)

        # print (input_filepath)
        # Only process files
        if not os.path.isfile(input_filepath):
            continue

        for key in configs:
            if key in input_filename:
                for config_filename in os.listdir(config_dir):

                    # print(config_filepath)
                    # Only process ini files that contain the key
                    if config_filename.endswith('.ini') and key in config_filename:
                        config_filepath = os.path.join(config_dir, config_filename)
                        # print(key)
                        # print(config_filename[config_filename.find(key)+len(key):config_filename.rfind('.')])
                        subKey = config_filename[config_filename.find(key)+len(key):config_filename.rfind('.')]

                        # print(f"Processing {input_filename} with {config_filename}")
                        try:
                            parseFhir.parse(
                                configPath=config_filepath,
                                inputPath=input_filepath,
                                outputPath=os.path.join(output_dir, f"{os.path.splitext(input_filename)[0]}_{key}{subKey}.csv"),
                                outputFormat = 'csv' )

                        except Exception as e:
                            print(f"Error processing {input_filename} with {config_filename}: {e}")


if __name__ == "__main__":
    main()
