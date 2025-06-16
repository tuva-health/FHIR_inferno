#!/usr/bin/env python3

import argparse
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parseFhir import parse

def main():
    parser = argparse.ArgumentParser(description="Run the FHIR parser.")
    parser.add_argument("--config", required=True, help="Path to .ini config file")
    parser.add_argument("--input", help="Override input path (optional)")
    parser.add_argument("--output", help="Override output path (optional)")
    parser.add_argument("--missing", help="Path for writing missing paths (optional)")
    parser.add_argument("--format", help="Output format: csv, parquet, return (optional)")
    parser.add_argument("--input-format", help="Input format: json, ndjson (optional)")
    parser.add_argument("--mode", help="Write mode: write or append (optional)")

    args = parser.parse_args()

    parse(
        configPath=args.config,
        inputPath=args.input,
        outputPath=args.output,
        missingPath=args.missing,
        outputFormat=args.format,
        inputFormat=args.input_format,
        writeMode=args.mode
    )


if __name__ == "__main__":
    main()
