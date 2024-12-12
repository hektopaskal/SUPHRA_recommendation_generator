from litellm import completion
from litellm.exceptions import APIError
from pathlib import Path
from dotenv import load_dotenv, dotenv_values
import sys
import json
import ast

load_dotenv()

# format output by calling function
tools = [
    {
        "type": "function",
        "function": {
            "name": "format_output",
            "description": "A function that formats a recommendation and their additional information properly",
            "parameters": {
                "type": "object",
                "properties": {
                    "recommendation_set": {
                        "type": "array",
                        "description": "A set that contains a recommendation and all additional information.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tip": {
                                    "type": "string",
                                    "description": "here you are supposed to generate the concise tip that is based on the information provided in the input text; whenever it is possible give precise time indications; ensure that the tip is concrete and easy to execute for everyone who wants to improve their own productivity and health state; Ensure that the recommendation is not to vague!"
                                },
                                "information": {
                                    "type": "string",
                                    "description": "here you are supposed to introduce the user to the study briefly; tell more about the study and how the scientists attained this findings; mention the scientists/authors of the input text and embed this information within a continuous text of a maximum of 50 words; assume that the reader had never heard of the study you are talking about; embed names and annual figures in continuous text"
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
                                    "description": "here you are supposed to assign a subject to your recommendation; the following subjects are possible: Work(=daily professional activities), Non-Work(=non-professional activities), Physical(=means body, biological parameters), Mental(=emotion, thinking, orientations), Social(=inter-personal relations)"
                                },
                                "activity_type": {
                                    "type": "string",
                                    "description": "here you are supposed to assign your advice to an activity type that describes the key characteristic of the activity to execute the tip; the following types are possible: Creative, Exercise, Cognitive, Relax, Social, Time Management"
                                },
                                "daytime": {
                                    "type": "string",
                                    "description": "here you are supposed to assign a daytime to your recommendation. Decide when the advice should ideally be executed. The following times are possible: Morning(tips that may influence the day ahead. e.g. mindset, motivation), Noon(tips that are relevant for the second part of the day), Evening(tips that are relevant when the day's work is done), End of the day(tips that are relevant to finish the day, e.g. conclude about the day), Not relevant(tips for which the daytime does not seem to be relevant)"
                                },
                                "weekday": {
                                    "type": "string",
                                    "description": "here you are supposed to decide for which type of days the recommendation is relevant; the following weekdays are possible: Workdays, Weekend, Public/Personal Holiday, Not relevant"
                                },
                                "weather": {
                                    "type": "string",
                                    "description": "here you are supposed to assign one or more weather situations that are ideal for execution of the tip. The following weather situations are possible: Sunny(ideal for outdoor activity), Overcast(suitable for less intense outdoor tasks or reflective activities), Rainy(best for indoor-focused tasks)"
                                },
                                "concerns": {
                                    "type": "string",
                                    "description": "here you are supposed to assign one or more concerns for which the tip could be helpful. The following concerns are possible: Time Management, Self-Discipline(staying focused and avoiding distractions), Procrastination, Goal-Setting(Defining Goals and tracking progress toward them), Work-Life Balance, Stress Management, Self-Motivation(finding internal motivation to work on tasks), Workspace Management(e.g. noise, lightning, comfort), Sleep Quality, Mindset"
                                },
                                "season": {
                                    "description": ""
                                }
                            },
                            "required": ["tip", "information", "category", "goal", "focus", "activity_type", "daytime", "weekday", "weather", "concerns"]
                        }
                    }
                }
            }
        }
    }
]

new_tools = [
    {
        "type": "function",
        "function": {
            "name": "format_output",
            "description": "A function that formats a recommendation and their additional information properly",
            "parameters": {
                "type": "object",
                "properties": {
                    "recommendation_set": {
                        "type": "array",
                        "description": "A set that contains a recommendation and all additional information.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tip": {
                                    "type": "string",
                                    "description": "generate the concise tip that is based on the information provided in the input text; whenever it is possible give precise time indications; ensure that the tip is concrete and easy to execute for everyone who wants to improve their own productivity and health state; Ensure that the recommendation is not to vague!"
                                },
                                "information": {
                                    "type": "string",
                                    "description": "introduce the user to the study briefly and assume that the user is not aware of the study. Therefore, use indefinite pronouns and say 'a study...' instead of 'the study...'; tell more about the study and how the scientists attained this findings; mention the scientists/authors of the input text and embed this information within a continuous text of a maximum of 50 words; embed names and annual figures in continuous text"
                                },
                                "category": {
                                    "type": "string",
                                    "description": "assign your advice to categories. the following categories are possible: work, success, productivity, performance, focus, time management, happiness, mental, active reflection, awareness, well-being, health, fitness, social"
                                },
                                "goal": {
                                    "type": "string",
                                    "description": "assign goals that should be achieved when the recommendation is executed. the following goals are possible: augment(should be mentioned when improving on something), prevent(should be mentioned when avoiding negative impact), recover(should be mentioned when restoring personal resources), maintain(Preserving current levels of performance, well-being, or resources to ensure stability and consistency)"
                                },
                                "activity_type": {
                                    "type": "string",
                                    "description": "assign your advice to an activity type that describes the key characteristic of the activity to execute the tip. the following types are possible: Creative, Exercise, Cognitive, Relax, Social, Time Management"
                                },
                                "daytime": {
                                    "type": "string",
                                    "description": "assign a daytime that is ideal for the execution of the tip. The following times are possible: morning(tips that may influence the day ahead. e.g. mindset, motivation), noon(tips that are relevant for the second part of the day), evening(tips that are relevant when the day's work is done), end of day(tips that are relevant to finish the day, e.g. conclude about the day), any(if it doesnt matter)"
                                },
                                "weekday": {
                                    "type": "string",
                                    "description": "decide for which type of days the recommendation is relevant; the following weekdays are possible: workdays, weekend, week start, end of workweek, public holiday, , any(if it doesnt matter)"
                                },
                                "weather": {
                                    "type": "string",
                                    "description": "assign one or more weather situations that are ideal for execution of the tip. The following weather situations are possible: 'sunny' (if tip suggests outdoor activity), 'overcast' (suitable for less intense outdoor tasks or reflective activities), 'rainy' (if tip suggests indoor-focused tasks), 'any' (if it doesnt matter)"
                                },
                                "concerns": {
                                    "type": "string",
                                    "description": """assign one concern for which the tip could be helpful. The following concerns are possible: 
                                    goal-setting(Defining Goals and tracking progress toward them), self-motivation(finding internal motivation to work on tasks), 
                                    self-direction(Taking initiative and making independent decisions to guide your work and priorities), 
                                    self-discipline(maintaining consistent effort and control over impulses to achieve tasks and goals), 
                                    focus(concentrating on tasks while minimizing distractions and interruptions), 
                                    mindeset(Developing attitudes and beliefs that support resilience and growth), 
                                    time management(organizing and allocating time effectively to complete tasks and meet deadlines),
                                    procrastination(overcoming delays andavoidance in starting and completing tasks), 
                                    stress management(coping with and reducing stess to maintain productivity and well-being)
                                    mental-health(promoting emotional and psychological well-being to support overall performance)
                                    work-life balance(balancing professional and personal responsibilities for a fulfilling lifestyle),
                                    sleep quality(improving the quality and consistency of sleep to enhance energy and focus)"""
                                },
                                "season": {
                                    "type": "string",
                                    "description": "assign one or more season types that are ideal for execution of the tip. The following seasons are possible: any, spring, summer, autumn, winter, holiday season(starting in late November and lasting until the begin of January), summer vacation"
                                },
                                "is_outdoor": {
                                    "type": "boolean",
                                    "description": "Give 'TRUE' when tip is most probably executed outdoors or 'FALSE', if it can be executed indoors"
                                },
                                "is_basic": {
                                    "type": "boolean",
                                    "description": "Give 'TRUE', if the tip is executable for users with low health literacy (e.g. do sports 1-2 times per week) This however will be irrelevant for more savvy users. Otherwise: 'FALSE'"
                                },
                                "is_advanced": {
                                    "type": "boolean",
                                    "description": "Give 'TRUE', if the tip adressed to users with high health literacy (e.g. how to optimize cardio training) This however will be irrelevant for users with low health literacy. Otherwise: 'FALSE'"
                                },
                                "gender": {
                                    "type": "string",
                                    "description": "Assign the gender for which the tip is specifically relevant. Possible values: any, male, female(e.g. regarding menstrual cycle or menopause)"
                                }
                            },
                            "required": ["tip", "information", "category", "goal", "activity_type", "daytime", "weekday", "weather", "concerns", "season", "is_outdoor", "is_basic", "is_advanced", "gender"]
                        }
                    }
                }
            }
        }
    }
]

"""def generate_recommendations_from_folder(input_folder: Path, output_folder: Path, modelname: str, instruction_file: Path):
    for folder in os.listdir(input_folder):
        # get input text (summary)
        summary_file_name = folder + ".txt"
        summary_file_path = os.path.join(
            input_folder, folder, summary_file_name)

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
        # to keep track of used instruction file
        output["instruction"] = instruction_file.stem
        '''
        output["output"] = json.loads(
            response.choices[0].message.tool_calls[0].function.arguments)
        '''
        output["output"] = [json.loads(c.function.arguments)
                            for c in response.choices[0].message.tool_calls]

        # create output file
        output_path = os.path.join(output_folder, folder.replace(".txt", ""))
        os.makedirs(output_path, exist_ok=True)
        output_file = f"recommendations_{folder}.json"
        with open(os.path.join(output_path, output_file), "w") as json_file:
            json.dump(output, json_file, indent=4)

        print(f'File saved at {output_path} as {output_file}\n')"""


def generate_recommendations_from_file(input_text: str, modelname: str, instruction_file: str):
    try:
        with Path(instruction_file).absolute().resolve().open(encoding='utf-8', errors='replace') as f:
            instruction_text = f.read()
    except FileNotFoundError:
        print(f"Instruction file not found: {instruction_file}")
    except PermissionError:
        print(f"Permission for instructions file denied: {instruction_file}") 
    except Exception as e:
        print(
            f"An error occurred while trying to read the instruction file: {e}")
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
            tools=new_tools,
            temperature=0.5
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
    # to keep track of used instruction file
    output["instruction"] = Path(instruction_file).stem
    output["output"] = [json.loads(c.function.arguments)
                        for c in response.choices[0].message.tool_calls]

    print("Recommendation generated successfully.")
    return output
