import os
from pathlib import Path
from dotenv import load_dotenv

from getpaper.parse import try_parse_paper, PDFParser
from langchain_community.document_loaders import PDFMinerLoader

from pdf2image import convert_from_path
import pytesseract

from semanticscholar import SemanticScholar

import typer
from typing import Optional, List

from litellm import completion
from litellm.exceptions import APIError

# Load environment variables from .env file
load_dotenv()

app = typer.Typer()

# extract DOI of a paper converted to txt file

def get_doi(file_path: str) -> str:
    """
    Extract the DOI from a scientific paper.
    """
    try:
        with open(Path(file_path), 'r', encoding='utf-8', errors='replace') as f:
            input_text = f.read()
        response = completion(
            model="gpt-4o-mini",
            messages=[
                {'role': 'system',
                 'content': "You are analyzing scientific papers. Read the text and extract the DOI of the paper. Your output should either be the DOI (e.g. 10.1000/182) and nothing else or 'DOI_not_found' if the DOI is not available in the text."},
                {'role': 'user', 'content': f'Analyze the following text and find its DOI: {input_text}'}
            ],
            temperature=0.0,
            top_p=0.0
        )
        doi = response.choices[0].message.content
        print(f"DOI: {doi}")
        return doi
    except FileNotFoundError as e:
        raise e(f"File not found: {e}")
    except APIError as e:
        raise e(f"API error occured: {e}")
    except Exception as e:
        raise e(f"Unexpected error occured: {e}")

# True, if .txt-file is empty.Empty text usually indicates image-based-PDF
def is_empty(txt_file_path):
    try:
        with open(txt_file_path, "r") as file:
            if file.read().strip() == "":
                return True
            else:
                return False
    except FileNotFoundError:
        print(f"File not found: {txt_file_path}")
        return False
    except Exception as e:
        print(f"An error occured: {e}")
        return False

# Function to extract text using tesseract OCR


def ocr_fallback(pdf_file_path: Path, txt_file_path: Path):
    ocr_text = ""
    pages = convert_from_path(pdf_file_path)  # pdf2image
    for i, page in enumerate(pages):
        # Perform OCR on each page image
        ocr_text += pytesseract.image_to_string(page) + "\n"
    # Step 4: Save the extracted text to the output folder
    with open(txt_file_path, 'w', encoding='utf-8') as output_file:  # utf-16/32????
        output_file.write(ocr_text)

# Takes a single PDF file and converts it into a txt file


def convert_pdf(input_file: str, output_dir: str, num_pages: Optional[int] = None) -> str:
    """
    Process a single PDF file and save the result in the output directory.
    Returns the path to the converted file.
    """
    input_path = Path(input_file)
    output_path = Path(output_dir)

    # Create the output folder if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    file_name = input_path.name
    file_stem = input_path.stem  # Get the filename without extension
    
    # Check if the output file already exists
    output_txt_path = output_path / file_stem / f"{file_stem}.txt"
    if output_txt_path.exists():
        print(f"Skipping {file_name}: Output file already exists.")
        return str(output_txt_path)

    # Ensure the parent directory of the output file exists
    output_txt_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Processing {input_file}...")

    # Step 1: Attempt to parse using the getpaper module
    try_parse_paper(
        paper=input_path,
        folder=output_path,
        parser=PDFParser.pdf_miner,
        recreate_parent=False,
        cleaning=True,
        subfolder=False,
        mode="single",
        strategy="auto",
        pdf_infer_table_structure=True,
        include_page_breaks=False
    )

    # Step 2: Check if the parsed text is empty or garbled
    if is_empty(output_txt_path):
        print(f"No text detected in {file_name}, falling back to OCR...")
        # Step 3: Use OCR as a fallback
        ocr_fallback(input_file, output_txt_path)

    print(f"Finished processing {file_name}.")
    return str(output_txt_path)

@app.command()
def convert_pdf_command(
    input_file: str = typer.Argument(..., help="Path to the input PDF file"),
    output_dir: str = typer.Argument(..., help="Output directory for processed file"),
    num_pages: Optional[int] = typer.Option(
        None, "--num-pages", "-n", help="Number of pages to process (default: all)")
) -> str:
    """
    CLI command to process a single PDF file and save the result in the output directory.
    Returns the path to the converted file.
    """
    return convert_pdf(input_file, output_dir, num_pages)

# Takes a folder containing PDF files and converts into txt files


@app.command()
def convert_pdfs(
    input_dir: str = typer.Argument(...,
                                    help="Input directory containing PDF files"),
    output_dir: str = typer.Argument(...,
                                     help="Output directory for processed files"),
    num_pages: Optional[int] = typer.Option(
        None, "--num-pages", "-n", help="Number of pages to process (default: all)"),
    files: Optional[List[str]] = typer.Option(
        None, "--files", "-f", help="Specific PDF files to process")
):
    """
    Process PDF files from the input directory and save results in the output directory.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    # Create the output folder if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Iterate over all PDF files in the input folder
    for file_name in os.listdir(input_dir):
        if file_name.endswith(".pdf"):
            pdf_file_path = os.path.join(input_dir, file_name)
            output_txt_path = os.path.join(
                output_dir, file_name.replace(".pdf", ""), file_name.replace(".pdf", ".txt"))

            print(f"Processing {pdf_file_path}...")

            # Step 1: Attempt to parse using the getpaper module
            parse_try = try_parse_paper(
                paper=Path(pdf_file_path),
                folder=Path(output_dir),
                # You can choose different parsers: py_mu_pdf, unstructured, pdf_miner, etc.
                parser=PDFParser.pdf_miner,
                recreate_parent=False,  # Whether to recreate parent folders
                cleaning=True,  # Whether to clean the PDF content
                subfolder=False,
                mode="single",  # Mode (specific to 'unstructured')
                strategy="auto",  # Strategy (specific to 'unstructured')
                pdf_infer_table_structure=True,  # If you want to infer table structure
                include_page_breaks=False  # Include page breaks
            )

            # Step 2: Check if the parsed text is empty or garbled
            if is_empty(output_txt_path):
                print(
                    f"No text detacted in {file_name}, falling back to OCR...")
                # Step 3: Use OCR as a fallback
                ocr_fallback(pdf_file_path, output_txt_path)

            print(
                f"Finished processing {file_name}. Saved to {output_txt_path}.\n")

# New subcommand to search for papers using Semanticscholar


@app.command()
def search_papers_test(
    query: str = typer.Argument(..., help="Search query for papers"),
    limit: int = typer.Option(
        10, "--limit", "-l", help="Number of results to return")
):
    """
    Search for papers using Semanticscholar and display the results.
    """
    # Get the API key from environment variable
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

    if not api_key:
        typer.secho(
            "Warning: SEMANTIC_SCHOLAR_API_KEY not found in environment variables or .env file.", fg=typer.colors.YELLOW)
        typer.secho(
            "Please set the SEMANTIC_SCHOLAR_API_KEY in your .env file or environment variables.", fg=typer.colors.YELLOW)
        return

    # Initialize SemanticScholar with the API key
    sch = SemanticScholar(api_key=api_key)
    results = sch.search_paper(query, limit=limit)

    print(f"Search results for: '{query}'\n")
    for i, paper in enumerate(results, 1):
        print(f"{i}. Title: {paper.title}")
        print(
            f"   Authors: {', '.join(author.name for author in paper.authors)}")
        print(f"   Year: {paper.year}")
        print(
            f"   Abstract: {paper.abstract[:200]}..." if paper.abstract else "   Abstract: N/A")
        print(f"   URL: {paper.url}\n")

# run typer app
if __name__ == "__main__":
    app()