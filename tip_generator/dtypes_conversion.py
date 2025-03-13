import json
import csv
from pathlib import Path
import typer
import pandas as pd

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
    return output_df