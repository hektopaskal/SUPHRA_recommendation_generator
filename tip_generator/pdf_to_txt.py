import os
from pathlib import Path
from getpaper.parse import try_parse_paper, PDFParser
from langchain_community.document_loaders import PDFMinerLoader
from pdf2image import convert_from_path
import pytesseract
import typer
from typing import Optional, List
from semanticscholar import SemanticScholar  # Add this import
from dotenv import load_dotenv  # Add this import

# Load environment variables from .env file
load_dotenv()

app = typer.Typer()
#pytesseract.pytesseract.tesseract_cmd="C:/Program Files/Tesseract-OCR/tesseract.exe"

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

def ocr_fallback(pdf_file_path, txt_file_path):
    ocr_text = ""
    pages = convert_from_path(pdf_file_path)  # pdf2image
    for i, page in enumerate(pages):
        # Perform OCR on each page image
        ocr_text += pytesseract.image_to_string(page) + "\n"
    # Step 4: Save the extracted text to the output folder
    with open(txt_file_path, 'w', encoding='utf-8') as output_file:                   #utf-16/32????
        output_file.write(ocr_text)

# Takes a single PDF file and converts it into a txt file
def convert_pdf(
    input_file: str = typer.Argument(..., help="Path to the input PDF file"),
    output_dir: str = typer.Argument(..., help="Output directory for processed file"),
    num_pages: Optional[int] = typer.Option(None, "--num-pages", "-n", help="Number of pages to process (default: all)")
):
    """
    Process a single PDF file and save the result in the output directory.
    """
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_name = os.path.basename(input_file)
    output_txt_path = os.path.join(
        output_dir, file_name.replace(".pdf", ""), file_name.replace(".pdf", ".txt"))

    print(f"Processing {input_file}...")

    # Step 1: Attempt to parse using the getpaper module
    parse_try = try_parse_paper(
        paper=Path(input_file),
        folder=Path(output_dir),
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

    print(f"Finished processing {file_name}. Saved to {output_txt_path}.")

# Takes a folder containing PDF files and converts into txt files
@app.command()
def convert_pdfs(
    input_dir: str = typer.Argument(..., help="Input directory containing PDF files"),
    output_dir: str = typer.Argument(..., help="Output directory for processed files"),
    num_pages: Optional[int] = typer.Option(None, "--num-pages", "-n", help="Number of pages to process (default: all)"),
    files: Optional[List[str]] = typer.Option(None, "--files", "-f", help="Specific PDF files to process")
):
    """
    Process PDF files from the input directory and save results in the output directory.
    """
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
                print(f"No text detacted in {file_name}, falling back to OCR...")
                # Step 3: Use OCR as a fallback
                ocr_fallback(pdf_file_path, output_txt_path)

            print(
                f"Finished processing {file_name}. Saved to {output_txt_path}.\n")

# New subcommand to search for papers using Semanticscholar
@app.command()
def search_papers(
    query: str = typer.Argument(..., help="Search query for papers"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results to return")
):
    """
    Search for papers using Semanticscholar and display the results.
    """
    # Get the API key from environment variable
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    
    if not api_key:
        typer.secho("Warning: SEMANTIC_SCHOLAR_API_KEY not found in environment variables or .env file.", fg=typer.colors.YELLOW)
        typer.secho("Please set the SEMANTIC_SCHOLAR_API_KEY in your .env file or environment variables.", fg=typer.colors.YELLOW)
        return

    # Initialize SemanticScholar with the API key
    sch = SemanticScholar(api_key=api_key)
    results = sch.search_paper(query, limit=limit)

    print(f"Search results for: '{query}'\n")
    for i, paper in enumerate(results, 1):
        print(f"{i}. Title: {paper.title}")
        print(f"   Authors: {', '.join(author.name for author in paper.authors)}")
        print(f"   Year: {paper.year}")
        print(f"   Abstract: {paper.abstract[:200]}..." if paper.abstract else "   Abstract: N/A")
        print(f"   URL: {paper.url}\n")

if __name__ == "__main__":
    app()
