from litellm import completion
from litellm.exceptions import APIError
from pathlib import Path
from dotenv import load_dotenv

from open_txt import line_breaker
import os
import json

load_dotenv()

def summarize_paper(input_folder: Path, output_folder: Path, modelname: str, instruction_file: Path):
    for folder in os.listdir(input_folder):
        # get input text (paper)
        paper_file_name = str(Path(folder)) + ".txt"
        paper_file_path = os.path.join(input_folder, folder, paper_file_name)

        try:
            with Path(paper_file_path).open(encoding='utf-8', errors='replace') as f:
                input_text = f.read()
        except FileNotFoundError:
            print(f"Input file not found: {paper_file_path}")
        except Exception as e:
            print(f"An error occured while trying to read the input file: {e}")

        try:
            with Path(instruction_file).open(encoding='utf-8', errors='replace') as f:
                instruction_text = f.read()
        except FileNotFoundError:
            print(f"Instruction file not found: {paper_file_path}")
        except Exception as e:
            print(
                f"An error occured while trying to read the instruction file: {e}")

        # completion
        try:
            print(f"Processing {folder}...")
            response = completion(
                model=modelname,
                messages=[
                    {'role': 'system', 'content': instruction_text},
                    {'role': 'user', 'content': f'Here is your text to analyse: {input_text}'}
                ]
            )
        except KeyError as e:
            print(f"Keyerror: {e}")
            return "An keyerror occured while processing the completion for summarization."
        except APIError as e:
            print(f"API error: {e}")
            return "There was an issue with the API request."
        except Exception as e:
            print(f"Unexpected error: {e}")
            return "An unexpected error occured."

        # create output files
        output_path = os.path.join(output_folder, folder.replace(".txt", ""))
        os.makedirs(output_path, exist_ok=True)
        with open(f"{output_path}/{folder}.txt", "w") as f:
            f.write(line_breaker(response.choices[0].message.content))
        print(f"Summary saved at {output_path}\n")


summarize_paper(
    input_folder="data/output/papers_txt",
    output_folder="data/output/summaries",
    modelname="groq/llama-3.1-70b-versatile",
    instruction_file="data/instructions/text_sum_inst_2.txt"
)
