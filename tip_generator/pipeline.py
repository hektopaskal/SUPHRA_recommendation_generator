# python packages
import os
import json
from pathlib import Path
from dotenv import load_dotenv

import pandas as pd
# for CLI
import typer
from typing import Optional, List
# semanticscholar library (unofficial) TODO just use requests library?
from semanticscholar import SemanticScholar, Paper, SemanticScholarException

from .generate import generate_recommendations_from_file
from .pdf_extraction import convert_pdf, get_doi
from .dtypes_conversion import dict_to_df

# load environment variables
load_dotenv()
# Create a Typer app
app = typer.Typer()

path_to_instruction_file = "/data/instructions/paper_to_rec_inst.txt"
api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
dois = []

SEMANTIC_SCHOLAR_FIELDS = [
    # 'abstract',
    # 'authors',
    # 'authors.affiliations',
    # 'authors.aliases',
    # 'authors.authorId',
    # 'authors.citationCount',
    # 'authors.externalIds',
    # 'authors.hIndex',
    # 'authors.homepage',
    # 'authors.name',
    # 'authors.paperCount',
    # 'authors.url',
    'citationCount',
    # 'citationStyles',
    # 'citations',
    # 'citations.abstract',
    # 'citations.authors',
    # 'citations.citationCount',
    # 'citations.citationStyles',
    # 'citations.corpusId',
    # 'citations.externalIds',
    # 'citations.fieldsOfStudy',
    # 'citations.influentialCitationCount',
    # 'citations.isOpenAccess',
    # 'citations.journal',
    # 'citations.openAccessPdf',
    # 'citations.paperId',
    # 'citations.publicationDate',
    # 'citations.publicationTypes',
    # 'citations.publicationVenue',
    # 'citations.referenceCount',
    # 'citations.s2FieldsOfStudy',
    # 'citations.title',
    # 'citations.url',
    # 'citations.venue',
    # 'citations.year',
    # 'corpusId',
    # 'embedding',
    # 'externalIds',
    'fieldsOfStudy',
    'influentialCitationCount',
    # 'isOpenAccess',
    # 'journal',
    # 'openAccessPdf',
    # 'paperId',
    # 'publicationDate',
    'publicationTypes',
    'publicationVenue',
    # 'referenceCount',
    # 'references',
    # 'references.abstract',
    # 'references.authors',
    # 'references.citationCount',
    # 'references.citationStyles',
    # 'references.corpusId',
    # 'references.externalIds',
    # 'references.fieldsOfStudy',
    # 'references.influentialCitationCount',
    # 'references.isOpenAccess',
    # 'references.journal',
    # 'references.openAccessPdf',
    # 'references.paperId',
    # 'references.publicationDate',
    # 'references.publicationTypes',
    # 'references.publicationVenue',
    # 'references.referenceCount',
    # 'references.s2FieldsOfStudy',
    # 'references.title',
    # 'references.url',
    # 'references.venue',
    # 'references.year',
    # 's2FieldsOfStudy',
    'title',
    # 'tldr',
    'url',
    # 'venue',
    'year'
]


def scholar_paper_to_dict(paper: Paper) -> dict:
    """
    Convert a Semantic Scholar Paper object to a dictionary.
    """
    paper_dict = {
        "src_title": getattr(paper, "title"),
        #"src_reference"
        "src_pub_year": getattr(paper, "year"),
        #"src_is_journal"
        "src_pub_type": getattr(paper, "publicationTypes"),
        "src_field_of_study": getattr(paper, "fieldsOfStudy"),
        #"src_doi"
        "src_hyperlink": getattr(paper, "url"),
        "src_pub_venue": json.loads(str(getattr(paper, "publicationVenue")).replace("'", '"'))["name"],
        "src_citations": getattr(paper, "citationCount"),
        "src_cit_influential": getattr(paper, "influentialCitationCount")
    }
    return paper_dict


def pdf_to_tips(
    input_dir: str,
    output_dir: str,
    generator_instructions: str,
    modelname: str
):   
    """
    Generates recommendations from given PDF files and generates output dir with a folder for each paper containing .txt file with extracted text
    and .json file with recommendations and meta data.
    """

    input_path = Path(input_dir).resolve().absolute()
    output_path = Path(output_dir).resolve().absolute()

    output_path.mkdir(parents=True, exist_ok=True)

    merged_dfs = pd.DataFrame

    for pdf in input_path.glob('*.pdf'):
        # TODO: check whether .txt already exists
        # Convert PDF to text
        converted_pdf_path = convert_pdf(str(pdf), output_dir)
        typer.echo(f"Converted PDF saved at {converted_pdf_path}")

        # Check if the converted file exists
        if not Path(converted_pdf_path).exists():
            print(f"Error: Converted file not found at {converted_pdf_path}\n")
            continue

        # Extract DOI
        doi = get_doi(converted_pdf_path)
        if not doi:
            print(f"Warning: Not able to extract DOI from {pdf.name}. Skipping this file.\n")
            continue

        # Fetch metadata from Semantic Scholar
        sch = SemanticScholar(api_key=api_key)
        try:
            meta_data = sch.get_paper(
                doi, fields=SEMANTIC_SCHOLAR_FIELDS)
            # Convert semantic scholar object: Paper into meta_data dictionary
            meta_data_dict = scholar_paper_to_dict(meta_data)
        except SemanticScholarException as e:
            print(
                f"Semantic-Scholar-API-Error occured: {e} - Skipping this file!\n")
            continue
        except Exception as e:
            print(f"Unkown error occured: {e}")

        # Read the converted text file
        with Path(converted_pdf_path).open(encoding="utf-8", errors="replace") as f:
            paper_text = f.read()

        # Generate recommendations
        try:
            recommendations = generate_recommendations_from_file(
                input_text=paper_text,
                modelname=modelname,
                instruction_file=generator_instructions
            )
        except Exception as e:
            print(f"Generate-Function: {e}")
            break
        # merge recommendations and meta data
        recommendations["meta_data"] = meta_data_dict
        # Save recommendations in JSON format
        output_json_path = Path(
            converted_pdf_path).with_suffix(".json")
        with output_json_path.open('w', encoding='utf-8') as json_file:
            json.dump(recommendations, json_file,
                      ensure_ascii=False, indent=4)

        # return recommendations as Pandas DataFrame
        merged_dfs =pd.concat([merged_dfs, dict_to_df(recommendations)])

        print(
            f"Processed {pdf.name} successfully. Output saved to {output_json_path}\n")
    
    print("All PDFs processed.")
    # save recs_df as .csv file in output folder
    merged_dfs.to_csv(Path(output_dir, "merged_data.csv"))
    print("Created csv file.\n")

    return merged_dfs

@app.command()
def pdf_to_tips_command(
    input_dir: str = typer.Argument(...,
                                    help="Directory to read the PDFs from"),
    output_dir: str = typer.Argument(...,
                                     help="Directory to save the generated tips"),
    modelname: Optional[str] = typer.Option(
        "gpt-4o-mini", help="Model to use for tip generation"),
    generator_instructions: Optional[str] = typer.Option(
        path_to_instruction_file, help="Instructions for tip generating model (Path to txt file)"),
):
    pdf_to_tips(input_dir=input_dir, output_dir=output_dir, modelname=modelname, generator_instructions=generator_instructions)

# does not work yet!!!
@app.command()
def dois_to_tips(
    dois: List[str] = typer.Argument(..., help="List of DOIs to process"),
    output_dir: str = typer.Argument(...,
                                     help="Directory to save the generated tips"),
    semantic_scholar_api_key: Optional[str] = typer.Option(
        None, help="Semantic Scholar API key")
):
    """
    Generates tips from a list of DOIs from scientific papers.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for doi in dois:
        paper_file_name = f"{doi.replace('/', '_')}.txt"

        # ... existing code for processing each DOI ...

        typer.echo(f"Processed DOI: {doi}")

    typer.echo("All DOIs processed successfully!\n")


# run typer app
if __name__ == "__main__":
    app()
