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
| activity_type | desc |
| categories | desc |
| concerns | desc |
| daytime | desc |
| wekkdays | desc |
| season | desc |
| is_outdoor | desc |
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
