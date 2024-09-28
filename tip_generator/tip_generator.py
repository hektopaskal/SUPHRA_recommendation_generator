from litellm import completion
from litellm.exceptions import APIError
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

import typer
from typing import Optional, List
from semanticscholar import SemanticScholar  # Add this import

import os
import json

from tip_generator import generate_recommendations
from pdf_to_txt import convert_pdf


load_dotenv()

dois = []
output_dir = Path("output")
input_dir = Path("input")

app = typer.Typer()


@app.command
def pdf_to_tips(
    input_dir: str = typer.Argument(...,
                                    help="Directory to read the PDFs from"),
    output_dir: str = typer.Argument(...,
                                     help="Directory to save the generated tips"),
    modelname: Optional[str] = typer.Option(
        "groq/llama-3.1-70b-versatile", help="Model to use for tip generation"),
    generator_instructions: Optional[str] = typer.Option(
        "", help="Instructions for tip generating model (Path to txt file)"),
    sch_api_key: Optional[str] = typer.Option(
        None, help="Semantic Scholar API key")
):
    """
    Generates recommendations from given PDF files.
    """
    input_path = Path(input_dir).resolve().absolute()
    output_path = Path(output_dir).resolve().absolute()

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    convert_pdf(input_dir, output_dir)

    generate_recommendations(input_dir, modelname, generator_instructions)

    for pdf in input_path:
        convert_pdf(Path(pdf, output_path))
        # TODO: get_meta_data()
        meta_data = {
            "pdf": [{
                #"tip": str,
                #"information": str,
                #"category": str,
                #"goal": str,
                #"focus": str,
                #"activity_type": str,
                #"daytime": str,
                #"weekday": str,
                "source": str,
                "author's": str,
                "publication_title": str,
                "year": int,
                "citation_count": int,  # + influentialCitationCount ??
                # if paper has been released recently authors_total_citation_count could be more informative than citation_count
                "authors_total_citation_count": int,
                "source_retracted": bool,
                "journal": str,
                "validation": bool  # is flagged by validation model as valid or invalid
                # journal quality data from paperQA2
            }]
        }
        # TODO: tip_generator -> recom.json -> recom.json with meta data


@app.command
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
