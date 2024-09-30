from litellm import completion
from litellm.exceptions import APIError
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

import typer
from typing import Optional, List
from semanticscholar import SemanticScholar, Paper  # Add this import

import os
import json

from generate import generate_recommendations_from_file
from pdf_to_txt import convert_pdf, get_doi


load_dotenv()

path_to_instruction_file = "py_tip_generator\data\instructions/paper_to_rec_inst.txt"

dois = []
output_dir = Path("output")
input_dir = Path("input")

app = typer.Typer()

SEMANTIC_SCHOLAR_FIELDS = [
    #'abstract',
    'authors',
    #'authors.affiliations',
    #'authors.aliases',
    #'authors.authorId',
    'authors.citationCount',
    #'authors.externalIds',
    #'authors.hIndex',
    #'authors.homepage',
    'authors.name',
    'authors.paperCount',
    #'authors.url',
    'citationCount',
    #'citationStyles',
    'citations',
    #'citations.abstract',
    #'citations.authors',
    #'citations.citationCount',
    #'citations.citationStyles',
    #'citations.corpusId',
    #'citations.externalIds',
    #'citations.fieldsOfStudy',
    #'citations.influentialCitationCount',
    #'citations.isOpenAccess',
    #'citations.journal',
    #'citations.openAccessPdf',
    #'citations.paperId',
    #'citations.publicationDate',
    #'citations.publicationTypes',
    #'citations.publicationVenue',
    #'citations.referenceCount',
    #'citations.s2FieldsOfStudy',
    #'citations.title',
    #'citations.url',
    #'citations.venue',
    #'citations.year',
    #'corpusId',
    #'embedding',
    #'externalIds',
    'fieldsOfStudy',
    'influentialCitationCount',
    #'isOpenAccess',
    'journal',
    'openAccessPdf',
    #'paperId',
    'publicationDate',
    'publicationTypes',
    'publicationVenue',
    'referenceCount',
    'references',
    #'references.abstract',
    #'references.authors',
    #'references.citationCount',
    #'references.citationStyles',
    #'references.corpusId',
    #'references.externalIds',
    #'references.fieldsOfStudy',
    #'references.influentialCitationCount',
    #'references.isOpenAccess',
    #'references.journal',
    #'references.openAccessPdf',
    #'references.paperId',
    #'references.publicationDate',
    #'references.publicationTypes',
    #'references.publicationVenue',
    #'references.referenceCount',
    #'references.s2FieldsOfStudy',
    #'references.title',
    #'references.url',
    #'references.venue',
    #'references.year',
    #'s2FieldsOfStudy',
    'title',
    'tldr',
    'url',
    'venue',
    'year'
]

api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')

def paper_to_dict(paper: Paper) -> dict:
    """
    Convert a Semantic Scholar Paper object to a dictionary.
    """
    paper_dict = {}
    for field in SEMANTIC_SCHOLAR_FIELDS:
        value = getattr(paper, field, None)
        if isinstance(value, (str, int, float, bool, type(None))):
            paper_dict[field] = value
        elif isinstance(value, list):
            paper_dict[field] = [item.to_dict() if hasattr(item, 'to_dict') else str(item) for item in value]
        elif hasattr(value, 'to_dict'):
            paper_dict[field] = value.to_dict()
        else:
            paper_dict[field] = str(value)
    return paper_dict

@app.command()
def pdf_to_tips(
    input_dir: str = typer.Argument(...,
                                    help="Directory to read the PDFs from"),
    output_dir: str = typer.Argument(...,
                                     help="Directory to save the generated tips"),
    modelname: Optional[str] = typer.Option(
        "gpt-4o-mini", help="Model to use for tip generation"),
    generator_instructions: Optional[str] = typer.Option(
        path_to_instruction_file, help="Instructions for tip generating model (Path to txt file)"),
    sch_api_key: Optional[str] = typer.Option(
        None, help="Semantic Scholar API key")
):
    """
    Generates recommendations from given PDF files.
    """
    try:
        input_path = Path(input_dir).resolve().absolute()
        output_path = Path(output_dir).resolve().absolute()

        output_path.mkdir(parents=True, exist_ok=True)

        for pdf in input_path.glob('*.pdf'):
            try:
                # Convert PDF to text
                converted_pdf_path = convert_pdf(str(pdf), str(output_path))
                typer.echo(f"Converted PDF saved at {converted_pdf_path}")
                
                # Extract DOI
                doi = get_doi(converted_pdf_path)
                if not doi:
                    typer.echo(f"Warning: Could not extract DOI from {pdf.name}. Skipping this file.")
                    continue

                # Fetch metadata from Semantic Scholar
                sch = SemanticScholar(api_key=api_key)
                meta_data = sch.get_paper(doi, fields=SEMANTIC_SCHOLAR_FIELDS)

                # Convert Paper object to dictionary
                meta_data_dict = paper_to_dict(meta_data)

                # Read the converted text file
                with Path(converted_pdf_path).open(encoding="utf-8", errors="replace") as f:
                    paper_text = f.read()

                # Generate recommendations
                recommendations = generate_recommendations_from_file(
                    input_text=paper_text,
                    modelname=modelname,
                    instruction_file=generator_instructions
                )
                recommendations["meta_data"] = meta_data_dict

                # Save recommendations to JSON file
                output_json_path = Path(converted_pdf_path).with_suffix(".json")
                with output_json_path.open('w', encoding='utf-8') as json_file:
                    json.dump(recommendations, json_file, ensure_ascii=False, indent=4)
                
                typer.echo(f"Processed {pdf.name} successfully. Output saved to {output_json_path}")

            except Exception as e:
                typer.echo(f"Error processing {pdf.name}: {str(e)}")
                typer.echo(f"Error details: {type(e).__name__} at line {e.__traceback__.tb_lineno}")
                continue

        typer.echo("All PDFs processed.")

    except Exception as e:
        typer.echo(f"An error occurred: {str(e)}")
        typer.echo(f"Error details: {type(e).__name__} at line {e.__traceback__.tb_lineno}")
        raise typer.Exit(code=1)

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
        paper_file_path = input_dir / paper_file_name

        # ... existing code for processing each DOI ...

        typer.echo(f"Processed DOI: {doi}")

    typer.echo("All DOIs processed successfully!")


if __name__ == "__main__":
    app()
