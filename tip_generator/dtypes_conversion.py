import json
import csv
from pathlib import Path
import typer
import pandas as pd
import ast

# Create a Typer app
app = typer.Typer()


@app.command()
def dict_to_df(recs : dict) -> pd.DataFrame:
    # read out the keys of the first recommendation set and and set them as headers
    headers = [key for key in recs["output"][0]["recommendation_set"][0].keys()]
    #rec_headers = ["short_desc", "long_desc", "goal", "activity_type", "categories", "concerns", "daytime", "weekdays", "season", "is_outdoor", "is_basic", "is_advanced", "gender"]
    #src_headers = ["src_title", ]

    # add headers of source data
    headers = headers + [key for key in recs["meta_data"].keys()]
    output_df = pd.DataFrame(columns=headers)

    # add recommendations as body to DataFrame
    for rec_set in recs["output"]:    
        rec = [",".join(rec_set["recommendation_set"][0][v]) if isinstance(rec_set["recommendation_set"][0][v], list) else rec_set["recommendation_set"][0][v] for v in rec_set["recommendation_set"][0]]
        src = [",".join(recs["meta_data"][v]) if isinstance(recs["meta_data"][v], list) else recs["meta_data"][v] for v in recs["meta_data"]]

        output_df.loc[len(output_df)] = rec + src 

    print_output = output_df["categories"]
    print(f"dict_to_df: {print_output}")
    return output_df


def append_json_to_csv(json_file, csv_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    recommendations = [set['recommendation_set'][0] for set in data['output']]
    meta_data = data['meta_data']

    # Prepare CSV columns
    columns = [
        'Tip', 'Information', 'Category', 'Goal', 'Focus', 'Activity_type',
        'Daytime', 'Weekday', 'Validity_Flag', 'Weather', 'Concerns'
    ] + list(meta_data.keys())

    with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)

        # Write header only if the file is empty
        if csvfile.tell() == 0:
            writer.writeheader()

        for rec in recommendations:
            # Ensure keys match the fieldnames exactly
            row = {
                'short_desc': rec.get('tip'),
                'long_desc': rec.get('information'),
                'goal': rec.get('category'),
                'activity_type': rec.get('goal'),
                'categories': rec.get('focus'),
                'concerns': rec.get('activity_type'),
                'daytime': rec.get('daytime'),
                'weekdays': rec.get('weekday'),
                'season': rec.get('validity_flag'),
                'is_outdoor': rec.get('weather'),
                'is_basic': rec.get('concerns'),
                **meta_data
            }
            writer.writerow(row)


def merge_json_to_csv(folder_path: str):
    # Create the output CSV file path
    output_csv_path = Path(folder_path) / 'merged_data.csv'

    # Check for JSON files in the provided folder path
    json_files = list(Path(folder_path).rglob('*/**/*.json'))
    if not json_files:
        raise FileNotFoundError("No JSON files found in the provided folder path.")
    if output_csv_path.exists():
        print("Will append to existing CSV...")

    # Iterate through each JSON file in the subfolders
    for file_path in json_files:
        append_json_to_csv(file_path, output_csv_path)


@app.command()
def command_merge_json_to_csv(folder_path: str):
    merge_json_to_csv(folder_path)
    typer.echo("Finished.")


# run typer app
if __name__ == "__main__":
    app()