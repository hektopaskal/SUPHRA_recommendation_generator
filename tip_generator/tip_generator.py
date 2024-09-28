from litellm import completion
from litellm.exceptions import APIError
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

import os
import json

load_dotenv()

# format output by calling function
tools = [
    {
        "type": "function",
        "function": {
            "name": "format_output",
            "description": "A function that takes in a list of arguments related to a productivity or health recommendations and format it right",
            "parameters": {
                "type": "object",
                "properties": {
                    "list_of_recommendation_sets": {
                        "type": "array",
                        "description": "A list that contains each tip and its additional information. The list contains at least 5 tips",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tip": {
                                    "type": "string",
                                    "description": "here you are supposed to generate the concise tip that is based on the information provided in the input text; whenever it is possible give precise time indications; ensure that the tip is concrete and easy to execute for everyone who wants to improve their own productivity and health state; Ensure that the recommendation is not to vague!"
                                },
                                "information": {
                                    "type": "string",
                                    "description": "here you are supposed to introduce the user to the study briefly; tell more about this study and how the scientists attained this findings; mention the scientists/authors of the input text and embed this information within a continuous text of a maximum of 50 words; assume that the reader had never heard of the study you are talking about; embed names and annual figures in continuous text"
                                },
                                "category": {
                                    "type": "string",
                                    "description": "here you are supposed to assign your advice to categories; the following categories are possible: Health, Well-being, active reflection, work, success, happiness, focus, time, performance, fitness, and motivation"
                                },
                                "goal": {
                                    "type": "string",
                                    "description": "here you are supposed to assign goals that should be achieved when the recommendation is executed; the following goals are possible: Awareness(should be mentioned when reflecting on something), Augment(should be mentioned when improving on something), Prevent(should be mentioned when avoiding negative impact), Recover(should be mentioned when restoring personal resources)"
                                },
                                "focus": {
                                    "type": "string",
                                    "description": "here you are supposed Ssto assign a subject to your recommendation; the following subjects are possible: Work(=daily professional activities), Non-Work(=non-professional activities), Physical(=means body, biological parameters), Mental(=emotion, thinking, orientations), Social(=inter-personal relations)"
                                },
                                "activity_type": {
                                    "type": "string",
                                    "description": "here you are supposed to assign your advice to an activity type that describes the key characteristic of the activity to execute the tip; the following types are possible: Creative, Exercise, Cognitive, Relax, Social, Time Management"
                                },
                                "daytime": {
                                    "type": "string",
                                    "description": "here you are supposed to assign a daytime to your recommendation. Decide when the advice should ideally be executed; the following times are possible: Morning(tips that may influence the day ahead. e.g. mindset, motivation), Noon(tips that are relevant for the second part of the day), Evening(tips that are relevant when the day's work is done), End of the day(tips that are relevant to finish the day, e.g. conclude about the day), Not relevant(tips for which the daytime does not seem to be relevant)"
                                },
                                "weekday": {
                                    "type": "string",
                                    "description": "here you are supposed to decide for which type of days the recommendation is relevant; the following weekdays are possible: Workdays, Weekend, Public/Personal Holiday, Not relevant"
                                }
                            },
                            "required": ["tip", "information", "category", "goal", "focus", "activity_type", "daytime", "weekday"]
                        }
                    }
                }
            }
        }
    }
]


def generate_recommendations(input_folder: Path, output_folder: Path, modelname: str, instruction_file: Path):
    for folder in os.listdir(input_folder):
        # get input text (summary)
        summary_file_name = folder + ".txt"
        summary_file_path = os.path.join(input_folder, folder, summary_file_name)

        try:
            with Path(summary_file_path).open(encoding='utf-8', errors='replace') as f:
                input_text = f.read()
        except FileNotFoundError:
            print(f"Input file not found: {summary_file_path}")
        except Exception as e:
            print(f"An error occured while trying to read the input file: {e}")

        try:
            with Path(instruction_file).open(encoding='utf-8', errors='replace') as f:
                instruction_text = f.read()
        except FileNotFoundError:
            print(f"Instruction file not found: {instruction_file}")
        except Exception as e:
            print(
                f"An error occured while trying to read the instruction file: {e}")

        # completion
        try:
            print(f"Processing {summary_file_name}")
            response = completion(
                model=modelname,
                messages=[
                    {'role': 'system', 'content': instruction_text},
                    {'role': 'user', 'content': f'Create recommendations based on the information of this summary: {input_text}'}
                ],
                tools=tools,
                temperature=0.7
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

        # implement recommendation
        



        # extract completion and add to output-json as 'output'
        output = response.to_dict()
        output["instruction"] = instruction_file # to keep track of used instruction file
        output["output"] = json.loads(
            response.choices[0].message.tool_calls[0].function.arguments)

        # create output file
        output_path = os.path.join(output_folder, folder.replace(".txt", ""))
        os.makedirs(output_path, exist_ok=True)
        output_file = f"recommendations_{folder}.json"
        with open(os.path.join(output_path, output_file), "w") as json_file:
            json.dump(output, json_file, indent=4)

        print(f'File saved at {output_path} as {output_file}\n')

generate_recommendations(
    input_folder="data/output/summaries",
    output_folder="data/output/recommendations",
    modelname="groq/llama-3.1-70b-versatile",
    instruction_file="data/instructions/cgpt_instruction.txt"
)