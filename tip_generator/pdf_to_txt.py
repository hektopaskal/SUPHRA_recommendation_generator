import os
from pathlib import Path
from getpaper.parse import try_parse_paper, PDFParser
from langchain_community.document_loaders import PDFMinerLoader
from pdf2image import convert_from_path
import pytesseract

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

# Main function to process all PDF files
def process_pdfs(input_folder, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Iterate over all PDF files in the input folder
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".pdf"):
            pdf_file_path = os.path.join(input_folder, file_name)
            output_txt_path = os.path.join(
                output_folder, file_name.replace(".pdf", ""), file_name.replace(".pdf", ".txt"))

            print(f"Processing {pdf_file_path}...")

            # Step 1: Attempt to parse using the getpaper module
            parse_try = try_parse_paper(
                paper=Path(pdf_file_path),
                folder=Path(output_folder),
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
            print(parse_try)

            # Step 2: Check if the parsed text is empty or garbled
            if is_empty(output_txt_path):
                print(f"NO text detacted in {file_name}, falling back to OCR...")
                # Step 3: Use OCR as a fallback
                ocr_fallback(pdf_file_path, output_txt_path)

            print(
                f"Finished processing {file_name}. Saved to {output_txt_path}.\n")


# Set input and output folder paths
input_folder = "data/papers_pdf"
output_folder = "data/output/papers_txt"

# Run the PDF processing function
process_pdfs(input_folder, output_folder)
