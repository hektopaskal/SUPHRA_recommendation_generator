# SUPHRA Recommendation Generator
A tool to extract, upload, and maintain productivity and health recommendations from scientific papers. Each LLM-generated recommendation source information from [Semantic Scholar API](https://www.semanticscholar.org/product/api) will be assigned.


<img src="assets/screenshot_extraction_frame.png" width="100%" align="center"> GUI Screenshot


## 🖥️How to use with GUI
**1. Set up keys**
You can store your Keys in your environment variables or navigate to *Keys* and enter them there.

**2. Feed your papers** To hand in your PDFs to the tool, collect them in a folder and drop this folder on the drag-and-drop field. It is suggested that nothing else be stored in this folder. 

**3. Choose a model** The only model that is currently supported is OpenAIs GPT-4o-mini. Depending on requirements more models will be added. Be sure to provide the required keys for the chosen model.

**4. Generate!** Click on *Generate Recommendations* and the model will analyze what you have given to it. 

## ⌨️ How to use with CLI
...


## 📅 Output Table
| **Field** | **Describtion** |
|-----------|-----------------|
| short_desc | desc |
| long_desc | desc |
| goal | desc | 
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
