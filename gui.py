import os
import base64
from pathlib import Path

from dash import Dash, html, dash_table, dcc, callback, Output, Input, State, dash_table
import pandas as pd
import plotly.express as px

from tip_generator.pipeline import pdf_to_tips
from tip_generator.db_operation import test_connection

# Incorporate data
# df = pd.read_csv('merged_data.csv')


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# Initialize the app
app = Dash(__name__, external_stylesheets=external_stylesheets)

# App layout
app.layout = [
    html.H1(children='SUPHRA Recommendation Generator',
            style={"font-weight": "bold"}),
    dcc.Tabs(
        id="tab",
        value="extract_view",
        children=[
            # EXTRACT VIEW
            dcc.Tab(label="Extract", id="extract_view", children=[
                # DnD field for file upload
                dcc.Upload(
                    id='dnd-field',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '90%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    # Allow multiple files to be uploaded
                    multiple=True
                ),
                # Dropdown: model selection
                dcc.Dropdown(["gpt-4o-mini", "groq/llama_3.1_versataile"], 'gpt-4o-mini', id='model-dropdown', style={
                    "width": "40vw",
                }),
                # Button: Generate!
                html.Button('Generate Recommendations', id='generate-button', n_clicks=0, style={
                    "margin": "10px"
                }),
                # Div: table will be inserted here
                html.Div(id="table_div", children=[]),
                # Button: Apply
                html.Button('Apply to Database', id='apply-button', n_clicks=0, style={
                    "margin": "10px"
                }),
            ],),
            # SIMILARITIES VIEW
            dcc.Tab(label="Find Similarities", id="sim_view", children=[
                
                html.Div(dcc.Input(id='input-on-submit-text', type='text'))
            ]),
            # DATABASE VIEW
            dcc.Tab(label="Connect to DB", children=[
                html.Div([
                    html.H3("Database Connection Settings",
                            style={"margin-bottom": "15px"}),

                    # User Input
                    html.Div([
                        html.Label("User:"),
                        dcc.Input(id="db-input-user", type="text",
                                  placeholder="Enter username", style={"width": "100%"}),
                    ], style={"margin-left": "20px", "margin-bottom": "10px", "width": "30vw"}),

                    # Password Input
                    html.Div([
                        html.Label("Password:"),
                        dcc.Input(id="db-input-password", type="password",
                                  placeholder="Enter password", style={"width": "100%"}),
                    ], style={"margin-left": "20px", "margin-bottom": "10px", "width": "30vw"}),

                    # Host Input
                    html.Div([
                        html.Label("Host:"),
                        dcc.Input(id="db-input-host", type="text",
                                  placeholder="Enter host (e.g., localhost)", style={"width": "100%"}),
                    ], style={"margin-left": "20px", "margin-bottom": "10px", "width": "30vw"}),

                    # Port Input
                    html.Div([
                        html.Label("Port:"),
                        dcc.Input(id="db-input-port", type="number",
                                  placeholder="Enter port (e.g., 3306)", style={"width": "100%"}),
                    ], style={"margin-left": "20px", "margin-bottom": "10px", "width": "30vw"}),

                    # Database Input
                    html.Div([
                        html.Label("Database:"),
                        dcc.Input(id="db-input-database", type="text",
                                  placeholder="Enter database name", style={"width": "100%"}),
                    ], style={"margin-left": "20px", "margin-bottom": "10px", "width": "30vw"}),

                    # Table Input
                    html.Div([
                        html.Label("Table:"),
                        dcc.Input(id="db-input-table", type="text",
                                  placeholder="Enter table name", style={"width": "100%"}),
                    ], style={"margin-left": "20px", "margin-bottom": "10px", "width": "30vw"}),

                    # Submit Button
                    html.Button("Submit and Test Connection", id="db-connect-button",
                                n_clicks=0, style={"margin-top": "10px"}),

                    # Display test_db_connection() result
                    html.Div(id="test-db-connection-result", children=[])
                ])
            ]),
        ],
    ),
]

# Funct: Button: Generate
@callback(Output(component_id='table_div', component_property='children', allow_duplicate=True),
          Input(component_id='generate-button', component_property='n_clicks'),
          State("dnd-field", "contents"),
          State("dnd-field", "filename"),
          State("table_div", "children"),
          State("model-dropdown", "value"),
          prevent_initial_call=True
          )
def update_output_table(n_clicks, contents, filenames, claim, model):
    if not contents or not filenames:
        return html.Div("No files uploaded.")  # Handle no files uploaded

    # Ensure contents and filenames are lists
    if not isinstance(contents, list):
        contents = [contents]
        filenames = [filenames]

    # Store uploaded files in work directory
    for content, filename in zip(contents, filenames):
        if filename.endswith(".pdf"):  # Ensure only PDFs are saved
            # Decode the Base64 content
            content_type, content_string = content.split(",")
            file_data = base64.b64decode(content_string)

            # Save the file to the output directory
            output_path = os.path.join(Path(
                "C:/Users/Nutzer/iCloudDrive/_Longevity/py_plotly_test/tip_generator_rep/data/archive"), filename)
            with open(output_path, "wb") as f:
                f.write(file_data)

        # Generate recommendations
        path_to_instruction_file = "data/instructions/paper_to_rec_inst.txt"
        df = pdf_to_tips(
            input_dir="C:/Users/Nutzer/iCloudDrive/_Longevity/py_plotly_test/tip_generator_rep/data/archive",
            output_dir="C:/Users/Nutzer/iCloudDrive/_Longevity/py_plotly_test/tip_generator_rep/data/archive",
            generator_instructions=path_to_instruction_file,
            modelname=model,
        )
    if claim == []:
        table = dash_table.DataTable(
            id='table',
            # "records" transforms into dictionary where each dictionary corresponds to a row
            data=df.to_dict("records"),
            columns=[{'id': i, 'name': i} for i in df.columns],
            style_table={'overflowX': 'auto'},  # enables horizontal scrolling
            editable=True,
            sort_action="native",
            sort_mode="multi",
            row_selectable="multi",
            row_deletable=True,
            selected_columns=[],
            selected_rows=[],
        )
    return table

# Funct: Button: Test DB-Connection
@callback(Output("test-db-connection-result", "children"),
          Input("db-connect-button", "n_clicks"),
          State("db-input-user", "value"),
          State("db-input-password", "value"),
          State("db-input-host", "value"),
          State("db-input-port", "value"),
          State("db-input-database", "value"),
          State("db-input-table", "value"),
          prevent_initial_call=True)
def test_db_conn_button(n_clicks, user, password, host, port, database, table):
    login = {
            "user" : user,
            "password" : password,
            "host" : host,
            "port" : int(port) if not port == "" else 0,
            "database" : database,
            "table" : table         
        }
    if test_connection(login):
        return "True"
    else:
        return "False"

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
