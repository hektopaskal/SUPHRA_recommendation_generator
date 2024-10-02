import json
import csv
from pathlib import Path
import pandas as pd
import typer

def flatten_meta_data(meta_data):
    meta_data_flat = {}
    for key, value in meta_data.items():
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            try:
                value = [json.loads(item.replace("'", "\"")) for item in value]
            except json.JSONDecodeError:
                pass  # If parsing fails, keep the original list of strings

        if isinstance(value, list):
            if key == 'authors':
                meta_data_flat[key] = [author['name'] for author in value if 'name' in author]
            elif key == 'publicationVenue':
                meta_data_flat[key] = [venue['name'] for venue in value if 'name' in venue]
            elif key == 'tldr':
                meta_data_flat[key] = [tldr['text'] for tldr in value if 'text' in tldr]
            else:
                meta_data_flat[key] = value
        else:
            meta_data_flat[key] = value
    return meta_data_flat

def append_json_to_csv(json_file, csv_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    recommendations = data['output']['list_of_recommendation_sets']
    meta_data = data['meta_data']
    
    # Flatten meta_data for CSV columns
    meta_data_flat = flatten_meta_data(meta_data)
    
    # Prepare CSV columns
    columns = [
        'Tip', 'Information', 'Category', 'Goal', 'Focus', 'Activity_type', 
        'Daytime', 'Weekday', 'Validity_Flag'
    ] + list(meta_data_flat.keys())
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        
        # Write header only if the file is empty
        if csvfile.tell() == 0:
            writer.writeheader()
        
        for rec in recommendations:
            # Ensure keys match the fieldnames exactly
            row = {
                'Tip': rec.get('tip'),
                'Information': rec.get('information'),
                'Category': rec.get('category'),
                'Goal': rec.get('goal'),
                'Focus': rec.get('focus'),
                'Activity_type': rec.get('activity_type'),
                'Daytime': rec.get('daytime'),
                'Weekday': rec.get('weekday'),
                'Validity_Flag': rec.get('validity_flag'),
                **meta_data_flat
            }
            writer.writerow(row)

def merge_json_to_csv(folder_path):
    # Create the output CSV file path
    output_csv_path = Path(folder_path) / 'merged_data.csv'
    
    # Initialize the CSV file with headers from the first JSON file
    first_json_file = next(Path(folder_path).rglob('*/**/*.json'))
    append_json_to_csv(first_json_file, output_csv_path)
    
    # Iterate through each JSON file in the subfolders
    for file_path in Path(folder_path).rglob('*/**/*.json'):
        append_json_to_csv(file_path, output_csv_path)

def command_append_json_to_csv(json_file: str, csv_file: str):
    """
    CLI function to append JSON data to a CSV file.
    
    Args:
        json_file (str): Path to the JSON file.
        csv_file (str): Path to the CSV file.
    """
    append_json_to_csv(json_file, csv_file)

if __name__ == "__main__":
    typer.run(cli_append_json_to_csv)
merge_json_to_csv("C:/Users/Nutzer/Desktop/pdf_to_tip_output")
