import json
import csv
from pathlib import Path
import typer
import pandas as pd

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
        rec = [rec_set["recommendation_set"][0][v] for v in rec_set["recommendation_set"][0]]
        src = [recs["meta_data"][v] for v in recs["meta_data"]]

        output_df.loc[len(output_df)] = rec + src 
    print(f"dict_to_df: {output_df}")
    return output_df

# TODO hardcode the converter field by field so that it matches the data base fields

    

def flatten_meta_data(meta_data):
    meta_data_flat = {}
    for key, value in meta_data.items():
        if key == "authors":
            # When the number of authors of a paper is more than one, the format of authors meta data is difficult to handle. See SemSchol api output (meta_data) to understand why the following is done.
            authors_dict = [json.loads(a.replace("'", '"')) for a in value]
            meta_data_flat["Authors(PaperCount, CitationCount)"] = []
            for a in authors_dict:
                meta_data_flat["Authors(PaperCount, CitationCount)"].append(
                    f"{authors_dict[authors_dict.index(a)]['name']}({authors_dict[authors_dict.index(a)]['paperCount']}, {authors_dict[authors_dict.index(a)]['citationCount']})")
            meta_data_flat["Authors(PaperCount, CitationCount)"] = "; ".join(meta_data_flat['Authors(PaperCount, CitationCount)'])
        elif key == "authors.citationCount" or key  == "authors.name" or key == "authors.paperCount":
            pass
        # similar to authors...
        elif key == "publicationVenue" and not value == None:
            meta_data_flat[key] = json.loads(str(meta_data[key].replace("'", '"')))['name']
        elif key == "tldr" and not value == None:
            meta_data_flat[key] = json.loads(str(meta_data[key].replace("'", '"')))['text']
        # List to String
        elif isinstance(value, list):
            meta_data_flat[key] = ", ".join(value)
        else:
            meta_data_flat[key] = value
        
    return meta_data_flat


def append_json_to_csv(json_file, csv_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    recommendations = [set['recommendation_set'][0] for set in data['output']]
    meta_data = data['meta_data']

    # Flatten meta_data for CSV columns
    meta_data_flat = flatten_meta_data(meta_data)

    # Prepare CSV columns
    columns = [
        'Tip', 'Information', 'Category', 'Goal', 'Focus', 'Activity_type',
        'Daytime', 'Weekday', 'Validity_Flag', 'Weather', 'Concerns'
    ] + list(meta_data_flat.keys())

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
                **meta_data_flat
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