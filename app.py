import os
import sys
import base64
import traceback
from pathlib import Path
from typing import Optional

import sys
from loguru import logger

from mariadb import Connection
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.orm import sessionmaker

from dash import Dash, html, dash_table, dcc, callback, Output, Input, State, dash_table
import pandas as pd
import plotly.express as px

from tip_generator.pipeline import pdf_to_tips
from tip_generator.db_operation import connect_to_db, insert_into_db


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# Initialize the app
app = Dash(__name__, external_stylesheets=external_stylesheets,
           suppress_callback_exceptions=True)
# Initialize logger
logger.remove()
logger.add(sys.stdout, level="INFO")

# Create DB connection pool
# URL that points to the database ...//username:password@host:port/database
DATABASE_URL = os.getenv("DATABASE_URL")
# Engine for connection pool
logger.info("Initializing database connection pool")
try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=False
    )
    # SessionLocal hands out a session from the pool when needed
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.error(f"Failed to initialize database connection pool: {e}")
    engine = None
    SessionLocal = None


# App layout
app.layout = [
    html.H1(children='SUPHRA Recommendation Generator',
            style={"font-weight": "bold"}),
    dcc.Tabs(
        id="views",
        value="extract_view",
        children=[
            # ###########################################################################################################
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
                # DEBUG ONLY: open example table
                html.Button('DEBUG ONLY: open table', id='debug-table-button', n_clicks=0, style={
                    "margin": "10px"
                }),
                # Div: Info
                html.Label(id="info-label", children=[])
            ],),
            # ###########################################################################################################
            # SIMILARITIES VIEW
            dcc.Tab(label="Find Similarities", id="sim_view", children=[
                html.H3("Find Similar Recommendations"),
                # Div: browser table will be inserted here
                html.Div(id="browsing-div", children=[
                    # Button: Browse Database
                    html.Button('Browse Database', id='browse-database-button', n_clicks=0, style={
                        "margin": "10px"
                    }),
                ]),
                # Div: sim table will be inserted here
                html.Div(id="sim-table-div", children=[]),
                # DEBUG ONLY: Find Similarities
                html.Button('DEBUG ONLY: search similarities', id='similarity-search-button', n_clicks=0, style={
                    "margin": "10px"
                }),
            ]),

            # ###########################################################################################################
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
                        dcc.Input(id="db-input-port", type="number", value="",
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

                    # Connect Button
                    html.Button("Connect", id="db-connect-button",
                                n_clicks=0, style={"margin-left": "20px", "margin-top": "10px"}),

                    # Display test_db_connection() result
                    html.Div(id="test-db-connection-result",
                             children=[], style={"margin-left": "20px"})
                ], style={'width': '45%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                # Test Connect Button
                html.Button("Test", id="pool-connect-button",
                            n_clicks=0, style={"margin-left": "20px", "margin-top": "10px"}),
                # Display test_pool_connection() result
                html.Div(id="test-pool-connection-result",
                         children=[], style={"margin-left": "20px"})
            ], style={'width': '45%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        ]
    ),
]

# ###########################################################################################################
# Extract View
# ###########################################################################################################


@callback(Output(component_id='table_div', component_property='children', allow_duplicate=True),
          Input(component_id='generate-button', component_property='n_clicks'),
          State("dnd-field", "contents"),
          State("dnd-field", "filename"),
          State("table_div", "children"),
          State("model-dropdown", "value"),
          prevent_initial_call=True
          )
def update_output_table(n_clicks, contents, filenames, claim, model):
    """
    Funct: Button: Generate
    """
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
            output_path = Path("data/temp")
            # Create the output folder regarding the pdf file
            output_path = output_path / filename
            # output_path = os.path.join(Path("data/temp"), filename)
            with open(output_path, "wb") as f:
                f.write(file_data)

    # Generate recommendations
    path_to_instruction_file = "data/instructions/paper_to_rec_inst.txt"
    df = pdf_to_tips(
        input_dir="data/temp",
        output_dir="data/temp",
        generator_instructions=path_to_instruction_file,
        modelname=model,
    )
    # if claim == []:
    table = dash_table.DataTable(
        id='table',
        # "records" transforms into dictionary where each dictionary corresponds to a row
        data=df.to_dict("records"),
        columns=[{'id': i, 'name': i} for i in df.columns],
        style_table={'overflowX': 'auto'},  # enables horizontal scrolling
        style_cell={'textAlign': 'left'},
        editable=True,
        sort_action="native",
        sort_mode="multi",
        row_selectable="multi",
        row_deletable=True,
        selected_rows=[],
    )

    return table


@callback(Output("table", "data"),
          Output("table", "selected_rows"),
          Output("info-label", "children"),
          Input("apply-button", "n_clicks"),
          State("table", "selected_rows"),
          State("table", "data"),
          State("db-input-table", "value"),
          prevent_initial_call=True,)
def apply_to_db(n_clicks, selection, all_rows, table):
    """
    Funct: Button: Apply to DB
    TODO: Keep recs in UI if upload to DB fails ! IMPORTANT !
    """
    # Check if database connection is available
    if SessionLocal is None:
        return all_rows, selection, ["Database connection not available!"]
        
    # seperate selected rows
    sel_rows = pd.DataFrame()
    updated_rows = pd.DataFrame()

    # iterate over rows and differentiate between selected and unselected rows
    for i, row in enumerate(all_rows):
        if i not in selection:
            updated_rows = pd.concat(
                [updated_rows, pd.DataFrame([all_rows[i]])], ignore_index=True)
        else:
            sel_rows = pd.concat(
                [sel_rows, pd.DataFrame([all_rows[i]])], ignore_index=True)

    # try to insert via pool
    try:
        insert_into_db(
            recommendations=sel_rows
        )
    # this exception is only raised when the entered table cannot be found (see insert_into_db from tip_generator.db_operation)
    except Exception as e:
        # TODO keep selection after exception
        logger.error(f"Error while uploading to the database: {e}")
        logger.error(traceback.format_exc())
        return all_rows, selection, ["Table not found!"]

    return updated_rows.to_dict("records"), [], ["Successfully inserted data!"]


# Open previously generated table for debugging


@callback(Output(component_id='table_div', component_property='children', allow_duplicate=True),
          Input("debug-table-button", "n_clicks"),
          prevent_initial_call=True)
def open_debug_table(n_clicks):
    df = pd.read_csv("data/archive/complete run/merged_data.csv")
    table = dash_table.DataTable(
        id='table',
        # "records" transforms into dictionary where each dictionary corresponds to a row
        data=df.to_dict("records"),
        columns=[{'id': i, 'name': i} for i in df.columns],
        style_table={'overflowX': 'auto'},  # enables horizontal scrolling
        style_cell={'textAlign': 'left'},
        editable=True,
        sort_action="native",
        sort_mode="multi",
        row_selectable="multi",
        row_deletable=True,
        selected_rows=[],
    )
    return table

# ###########################################################################################################
    # Similarities View
# ###########################################################################################################


@callback(Output("browsing-div", "children"),
          Input("browse-database-button", "n_clicks"),
          prevent_initial_call=True)
def browse_database(n_clicks):
    """
    Funct: Button: Browse Database
    """
    if SessionLocal is None:
        return html.Div("Database connection not available!")
        
    session = SessionLocal()
    try:
        result = session.execute(
            text("SELECT * FROM recommendation")).fetchall()
        df = pd.DataFrame(result)
        table = dash_table.DataTable(
            id='browsing-table',
            data=df.to_dict("records"),
            columns=[{'id': i, 'name': i} for i in df.columns],
            style_table={'overflowX': 'auto'},  # enables horizontal scrolling
            style_cell={'textAlign': 'left'},
            editable=True,
            sort_action="native",
            sort_mode="multi",
            row_selectable="multi",
            row_deletable=True,
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=10,
        )
        return table
    except Exception as e:
        return f"Error while browsing database: {e}"
    finally:
        session.close()


@callback(
    Output("sim-table-div", "children"),
    Input("similarity-search-button", "n_clicks"),
    State("browsing-table", "derived_virtual_data"),
    State("browsing-table", "derived_virtual_selected_rows"),
    prevent_initial_call=True
)
def search_similarities(n_clicks, rows, selection):
    """
    Funct: Button: Search Similarities
    """
    if SessionLocal is None:
        return html.Div("Database connection not available!")
        
    if not selection:
        return html.Div("No rows selected.")
    else:
        # get actual rows as DataFrame (considering sorting and filtering)
        data = pd.DataFrame(rows)
        # get indices (or more likely ids) of selected rows (considering sorting and filtering)
        selected_df = data.iloc[selection]
        # db-id of selected row (corresponds to vector id)
        v_id = selected_df["id"].tolist()[0] 
        logger.info(f"Selected rows: {selected_df['id'].tolist()[0]}")
        
        try:
            session = SessionLocal()
            # get 3 most similar recommendations from database (euclidean distance)
            result = session.execute(text("SELECT id FROM emb_ada002 ORDER BY VEC_DISTANCE_EUCLIDEAN(emb, (SELECT emb FROM emb_ada002 WHERE id = :v_id)) LIMIT 3;"), [{"v_id": str(v_id)}])
            # get result as list
            result = [r[0] for r in result.fetchall()]
            # get recommendations from db
            stmt = text("SELECT * FROM recommendation WHERE id IN :ids").bindparams(bindparam("ids", expanding=True))

            result = session.execute(stmt, {"ids": result}).fetchall()
            df = pd.DataFrame(result)
            table = dash_table.DataTable(
                id='sim-table',
                data=df.to_dict("records"),
                columns=[{'id': i, 'name': i} for i in df.columns],
                style_table={'overflowX': 'auto'},  # enables horizontal scrolling
                style_cell={'textAlign': 'left'},
                editable=True,
                sort_action="native",
                sort_mode="multi",
                row_selectable="multi",
                row_deletable=True,
                selected_rows=[],
                page_action="native",
                page_current=0,
                page_size=10,
            )
            return table
        except Exception as e:
            #print(traceback.format_exc())
            logger.error(f"Error while searching similarities: {e}")
            return html.Div("Error while searching similarities.", e)
        finally:
            session.close()



# ###########################################################################################################
    # Database View
# ###########################################################################################################

@callback(Output("test-pool-connection-result", "children"),
          Input("pool-connect-button", "n_clicks"),
          prevent_initial_call=True)
def test_db_connection(n_clicks):
    """
    Funct: Button: Test Pool-Connection
    """
    if SessionLocal is None:
        return "Database connection not available!"
        
    session = SessionLocal()
    try:
        result = session.execute(
            text("SELECT COUNT(*) FROM recommendation")).fetchone()
        return f"Pool connection successful: {result}"
    except Exception as e:
        return f"Pool connection failed: {e}"
    finally:
        session.close()


# Run the app
def start_gui():
    logger.info("Starting GUI")
    try:
        # Get host from environment or use default - FORCE 0.0.0.0 for Docker
        host = "0.0.0.0"  # Always use 0.0.0.0 in Docker
        logger.info(f"Using host: {host}")
        
        
        # Run server with absolute minimum configuration
        app.run_server(
            host=host,
            port=8050,
            debug=False,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())

# Remove the threading and test code - simplify main block
if __name__ == '__main__':
    try:
        # Just call start_gui directly - no threading
        start_gui()
    except Exception as e:
        logger.error(f"Error starting the application: {e}")
        logger.error(traceback.format_exc())
