from litellm import completion
from litellm.exceptions import APIError
from pathlib import Path
from dotenv import load_dotenv
import json

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
                                "short_desc": {
                                    "type": "string",
                                    "description": "generate the concise tip that is based on the information provided in the input text; whenever it is possible give precise time indications; ensure that the tip is concrete and easy to execute for everyone who wants to improve their own productivity and health state; Ensure that the recommendation is not to vague!"
                                },
                                "long_desc": {
                                    "type": "string",
                                    "description": "introduce the user to the study briefly and assume that the user is not aware of the study. Therefore, use indefinite pronouns and say 'a study...' instead of 'the study...'; tell more about the study and how the scientists attained this findings; mention the scientists/authors of the input text and embed this information within a continuous text of a maximum of 50 words; embed names and annual figures in continuous text"
                                },
                                "goal": {
                                    "type": "string",
                                    "description": "assign goals that should be achieved when the recommendation is executed. the following goals are possible: augment(should be mentioned when improving on something), prevent(should be mentioned when avoiding negative impact), recover(should be mentioned when restoring personal resources), maintain(Preserving current levels of performance, well-being, or resources to ensure stability and consistency)"
                                },
                                "activity_type": {
                                    "type": "string",
                                    "description": "assign your advice to an activity type that describes the key characteristic of the activity to execute the tip. the following types are possible: Creative, Exercise, Cognitive, Relax, Social, Time Management"
                                },
                                "categories": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "assign your advice to categories. the following categories are possible: work, success, productivity, performance, focus, time management, happiness, mental, active reflection, awareness, well-being, health, fitness, social"
                                },
                                "concerns": {
                                    "type": "array",
                                    "items": {"type": "string"},
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
                                "daytime": {
                                    "type": "string",
                                    "description": "assign a daytime that is ideal for the execution of the tip. The following times are possible: morning(tips that may influence the day ahead. e.g. mindset, motivation), noon(tips that are relevant for the second part of the day), evening(tips that are relevant when the day's work is done), end of day(tips that are relevant to finish the day, e.g. conclude about the day), any(if it doesnt matter)"
                                },
                                "weekdays": {
                                    "type": "string",
                                    "description": "decide for which type of days the recommendation is relevant; the following weekdays are possible: workdays, weekend, week start, end of workweek, public holiday, , any(if it doesnt matter)"
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
                            "required": ["short_desc", "long_desc", "goal", "activity_type", "categories", "concerns", "daytime", "weekdays", "seasons", "is_outdoor", "is_basic", "is_advanced", "gender"]
                        }
                    }
                }
            }
        }
    }
]


def generate_recommendations_from_file(input_text: str, modelname: str, instruction_file: str):
    try:
        with Path(instruction_file).absolute().resolve().open(encoding='utf-8', errors='replace') as f:
            instruction_text = f.read()
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {e}")
    except PermissionError as e:
        raise PermissionError(f"Permission for instruction denied: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error occured: {e}")

    # completion
    try:
        print("Processing input text...")
        response = completion(
            model=modelname,
            messages=[
                {'role': 'system', 'content': instruction_text},
                {'role': 'user', 'content': f'Create recommendations based on the information of this summary: {input_text}'}
            ],
            tools=tools,
            temperature=0.5
        )
    except KeyError as e:
        raise KeyError(f"Keyerror: {e}")
    except APIError as e:
        raise APIError(f"API error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")

    # extract completion and create output dictionary
    output = response.to_dict()
    # to keep track of used instruction file
    output["instruction"] = Path(instruction_file).stem
    output["output"] = [json.loads(c.function.arguments)
                        for c in response.choices[0].message.tool_calls]

    print("Recommendation generated successfully.")
    return output
