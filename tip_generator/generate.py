from litellm import completion
from litellm.exceptions import APIError
from pathlib import Path
from dotenv import load_dotenv, dotenv_values
import os
import json
import ast

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
                        "description": "A list that contains each tip and its additional information. This list contains as many recommendations as you can create based only on the provided information.",
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


def generate_recommendations_from_folder(input_folder: Path, output_folder: Path, modelname: str, instruction_file: Path):
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
                tools=tools
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
        # extract completion and add to output-json as 'output'
        output = response.to_dict()
        output["instruction"] = instruction_file.stem # to keep track of used instruction file
        output["output"] = json.loads(
            response.choices[0].message.tool_calls[0].function.arguments)

        # create output file
        output_path = os.path.join(output_folder, folder.replace(".txt", ""))
        os.makedirs(output_path, exist_ok=True)
        output_file = f"recommendations_{folder}.json"
        with open(os.path.join(output_path, output_file), "w") as json_file:
            json.dump(output, json_file, indent=4)

        print(f'File saved at {output_path} as {output_file}\n')


def generate_recommendations_from_file(input_text: str, modelname: str, instruction_file: str):
    try:
        with Path(instruction_file).absolute().resolve().open(encoding='utf-8', errors='replace') as f:
            instruction_text = f.read()
    except FileNotFoundError:
        print(f"Instruction file not found: {instruction_file}")
        return None
    except Exception as e:
        print(f"An error occurred while trying to read the instruction file: {e}")
        return None

    # completion
    try:
        print("Processing input text...")
        response = completion(
            model=modelname,
            messages=[
                {'role': 'system', 'content': instruction_text},
                {'role': 'user', 'content': f'Create recommendations based on the information of this summary: {input_text}'}
            ],
            tools=tools
        )
    except KeyError as e:
        print(f"Keyerror: {e}")
        return None
    except APIError as e:
        print(f"API error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    
    # extract completion and create output dictionary
    output = response.to_dict()
    output["instruction"] = Path(instruction_file).stem # to keep track of used instruction file
    output["output"] = json.loads(
        response.choices[0].message.tool_calls[0].function.arguments)

    print("Recommendation generated successfully.")
    return output

#!!! Instructions can still be None TODO
def validate_recommendations(paper_path: str = None, paper_text: str = None, recommendations_path: str = None, recommendations_data: dict = None, modelname: str = None)->list[bool]:
    # Read the source paper
    if paper_path:
        try:
            with open(paper_path, 'r', encoding='utf-8', errors="replace") as f:
                source_paper = f.read()
        except FileNotFoundError:
            print(f"Source paper file not found: {paper_path}")
            return None
        except Exception as e:
            print(f"An error occurred while reading the source paper: {e}")
            return None
    elif paper_text:
        source_paper = paper_text
    else:
        print("Invalid paper input. Must provide either a file path or the paper text.")
        return None

    # Read the recommendation data
    if recommendations_path:
        try:
            with open(recommendations_path, 'r', encoding='utf-8') as f:
                recommendations_data = json.load(f)
        except FileNotFoundError:
            print(f"Recommendations file not found: {recommendations_path}")
            return None
        except json.JSONDecodeError:
            print(f"Invalid JSON in recommendations file: {recommendations_path}")
            return None
        except Exception as e:
            print(f"An error occurred while reading the recommendations file: {e}")
            return None
    elif recommendations_data:
        recommendations_data = recommendations_data
    else:
        print("Invalid recommendations input. Must provide either a file path or a dictionary.")
        return None

    recommendations_list = []
    for rec in recommendations_data["output"]["list_of_recommendation_sets"]:
        recommendations_list.append({"tip": rec["tip"], "information": rec["information"]})

    try:
        response = completion(
            model=modelname,
            messages=[
                {'role': 'system', 'content': f"""
                You will receive an informational scientific text that you have to analyze. 
                Your task is to determine if the following recommendations are valid based on the information provided in the scientific paper.
                These are the mentioned recommendations, each accompanied by a small explanation:
                         {recommendations_list}
                Decide whether the scientific paper justifies the claim of the recommendation or not.
                For each recommendation - information -pair:

                - Output "True" if the information sufficiently justifies the recommendation.
                - Output "False" if the information does not sufficiently justify the recommendation.

                Do not repeat the recommendation in your output.
                The output should be a list of boolean values (True/False) in the same order as the input recommendations(example output: "[True, False]"). 
                """},
                {'role': 'user', 'content': f"Here is the scientific paper: {source_paper}"}
            ],
            temperature=0.0,
            top_p=0.0
        )
        validation_result = [bool(value) for value in ast.literal_eval(response.choices[0].message.content)]

        print("Validity note: ", validation_result)  # Print the LLM response
    except APIError as api_error:
        print(f"An API error occurred during validation: {api_error}")
        print(f"Error details: {api_error.response.text if hasattr(api_error, 'response') else 'No additional details'}")
        return None
    except KeyError as key_error:
        print(f"A key error occurred during validation: {key_error}")
        print(f"This might be due to an unexpected response structure.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during validation: {e}")
        print(f"Error type: {type(e).__name__}")
        return None

    for rec in recommendations_data["output"]["list_of_recommendation_sets"]:
        rec["validity_flag"] = validation_result[recommendations_data["output"]["list_of_recommendation_sets"].index(rec)]

    return validation_result  # Return the validation result


    