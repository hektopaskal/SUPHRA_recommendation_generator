# SUPHRA Recommendation Generator
A tool to extract, upload, and maintain productivity and health recommendations from scientific papers. Each LLM-generated recommendation source information from [Semantic Scholar API](https://www.semanticscholar.org/product/api) will be assigned.


<img src="assets/screenshot_extraction_frame.png" width="100%" align="center"> GUI Screenshot


## 📖How to use
**1. Set up keys**
To generate recommendations you necessarily need to add an [OpenAi API key](https://openai.com/index/openai-api/), since OpenAi´s GPT models are the only supported models so far. A [Semantic Scholar API](https://www.semanticscholar.org/product/api) is also required for usage.
To set up your keys just fill in `.env` like it is done in [.env.template](/.env.template).

**2. Feed your papers** 
To hand in your scientific papers just select them via the drag and drop field in the 'Extraction' view. It is recommended to not upload too many papers at ones scince you will probably lose track of them. Start with 1-2 papers to see how it works.

**3. Choose a model** The only model that is currently supported is OpenAIs GPT-4o-mini. Depending on requirements more models will be added. Be sure to provide the required keys for the chosen model.

**4. Generate!** Click on *Generate Recommendations* and the model will analyze what you have given to it. 

## 📅 Output Table
| **Field** | **Describtion** |
|-----------|-----------------|
| short_desc | A short describtion of the recommended tip. |
| long_desc | A more informative version of the tip which also introduces the reader to the study from which the tip comes from. |
| goal | What should be achieved when the tip is excuded? Possible values: `augment`(should be mentioned when improving on something), `prevent`(should be mentioned when avoiding negative impact), `recover`(should be mentioned when restoring personal resources), `maintain`(Preserving current levels of performance, well-being, or resources to ensure stability and consistency) | 
| activity_type | What is the key characteric of the tip to execute the tip? Possible values: `Creative`, `Exercise`, `Cognitive`, `Relax`, `Social`, `Time Management` |
| categories | Possible values: `work`, `success`, `productivity`, `performance`, `focus`, `time management`, `happiness`, `mental`, `active reflection`, `awareness`, `well-being`, `health`, `fitness`, `social` |
| concerns | Concerns for which the tip could be helpful. Possible values: `goal-setting`(Defining Goals and tracking progress toward them), `self-motivation`(finding internal motivation to work on tasks), `self-direction`(Taking initiative and making independent decisions to guide your work and priorities), `self-discipline`(maintaining consistent effort and control over impulses to achieve tasks and goals), `focus`(concentrating on tasks while minimizing distractions and interruptions), `mindeset`(Developing attitudes and beliefs that support resilience and growth), `time management`(organizing and allocating time effectively to complete tasks and meet deadlines), `procrastination`(overcoming delays andavoidance in starting and completing tasks), `stress management`(coping with and reducing stess to maintain productivity and well-being), `mental-health`(promoting emotional and psychological well-being to support overall performance), `work-life balance`(balancing professional and personal responsibilities for a fulfilling lifestyle), `sleep quality`(improving the quality and consistency of sleep to enhance energy and focus) |
| daytime | When should the tip ideally be executed? Possible values: `morning`(tips that may influence the day ahead. e.g. mindset, motivation), `noon`(tips that are relevant for the second part of the day), `evening`(tips that are relevant when the day's work is done), `end of day`(tips that are relevant to finish the day, e.g. conclude about the day), `any`(if it doesnt matter) |
| wekkdays | For which type of days is the tip relevant? Possible values: `workdays`, `weekend`, `week start`, `end of workweek`, `public holiday`, `any`(if it doesnt matter) |
| season | In which season should the tip ideally be executed? Possible values: `any`, `spring`, `summer`, `autumn`, `winter`, `holiday season`(starting in late November and lasting until the begin of January), `summer vacation` |
| is_outdoor | Is the tip most probably executed outdoors? outdoor:`TRUE`, indoor:`FALSE`  |
| is_basic | desc |
| is_advanced | desc |
| gender | desc |
| src_title | desc |
| src_reference | desc |
| src_pub_year | desc |
| src_is_journal | desc |
| src_pub_type | desc |
| src_field_of_study | desc |
| src_doi | desc |
| src_hyperlink | desc |
| src_pub_venue | desc |
| src_citations | desc |
| src_cit_influential | desc |
| created_at | desc |
| modified_at | desc |
| risk | desc |
| is_approved | desc |

The prompt that is used for the generation is based on [this instructions text](./data/instructions/paper_to_rec_inst.txt). To keep a clear output structure function calling is used (see *tools* in [generate.py](./tip_generator/)).
