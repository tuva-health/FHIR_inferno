## Helper scripts

These helper scripts simplify and automate some of the setup and administration of FHIR inferno.

Use cases and setups can vary greatly, and you may need to tweak these files to fit your needs.

#### analyzeJson.py

This script will read through a batch of FHIR files in a folder, filter for a specific resource type by filename, collect all of the paths, and build a well formatted configuration file.
It can be run with an anchor as well.
It also outputs the max count of every array, so you can determine if you want to build more tables from the same fhir objects at that array using an anchor.

See the [fhir processing guide](https://www.example.com/fhir_processing_guide) for more information

#### analyzeJson_aws.py

Similar to analyzejson.py, but it reads from an aws bucket rather than a local disk, and
it bulk build config files for multiple resources and anchors at once. It does not report max array counts.

#### create_table_create_csv.py

This script reads through your config files in a folder, and creates `create table` statements for every table, and builds (but comments out)
statements to copy into the tables and select from the tables for validation. The copy into statements are built to load csv files.
It is designed to build statements loading to snowflake from s3 and may need to be tweaked to accomodate other warehouses or
cloud storage providers.

#### create_table_create_parquet.py

Similar to create_table_create.py, but designed to load parquet files from s3 rather than csv.

### create_select_parquet.py

Reads through configuration files in a folder, and creates select statements from each config, and writes them to their own file.
A great way to build staging models for a dbt project.
