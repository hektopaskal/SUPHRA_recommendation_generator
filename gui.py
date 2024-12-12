import os
from PIL import Image
from pathlib import Path
import pandas as pd

# intern functions
from tip_generator.json_to_csv import flatten_meta_data
from tip_generator.tip_generator import pdf_to_tips
from tip_generator.db_operation import test_connection, connect_to_maria, insert_into_db

# tkinter
import tkinterdnd2 as tk2
from tkinterdnd2 import TkinterDnD
import customtkinter
from tksheet import Sheet
from tksheet import num2alpha as n2a


class NavigationFrame(customtkinter.CTkFrame):
    """Navigation Frame with buttons for switching views."""

    def __init__(self, master, app, images):
        super().__init__(master)
        self.app = app

        title_label = customtkinter.CTkLabel(self, text="  SUPHRA", image=images["uni_logo"],
                                             compound="top", font=customtkinter.CTkFont(size=15, weight="bold"))
        title_label.pack(pady=10, padx=0)

        extract_nav_button = customtkinter.CTkButton(self, corner_radius=0, height=40, border_spacing=10, text="Extract",
                                                     fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", command=lambda: self.app.show_frame("Extraction"))
        extract_nav_button.pack(pady=10, padx=10)

        simil_nav_button = customtkinter.CTkButton(self, corner_radius=0, height=40, border_spacing=10, text="Find Similarities",
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", command=lambda: self.app.show_frame("Comparison"))
        simil_nav_button.pack(pady=10, padx=10)

        db_nav_button = customtkinter.CTkButton(self, corner_radius=0, height=40, border_spacing=10, text="DB Connect",
                                                fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", command=lambda: self.app.show_frame("DBConnect"))
        db_nav_button.pack(pady=10, padx=10)

        keys_nav_button = customtkinter.CTkButton(self, corner_radius=0, height=40, border_spacing=10, text="Keys",
                                                  fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", command=lambda: self.app.show_frame("Keys"))
        keys_nav_button.pack(pady=10, padx=10)

        self.appearance_mode_menu = customtkinter.CTkOptionMenu(self, values=["Light", "Dark", "System"],
                                                                command=self.change_appearance_mode_event)
        #self.appearance_mode_menu.pack(pady=10, padx=10, side="bottom")

    def change_appearance_mode_event(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)


# =================== Recommendations Frame ====================

class RecommendationsFrame(customtkinter.CTkFrame):
    """
    Frame that contains the table of generated recommendations.
    The table is built with tksheet (v.7.2.23) module    
    """

    def __init__(self, master, recs_df):
        super().__init__(master)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # TODO dynamically split columns into recs and src
        headers : list = recs_df.columns.tolist() + ["select"]
        data = recs_df.values.tolist()

        """headers = [key for key in recommendations["output"]
                   [0]["recommendation_set"][0]] + ["select"]
        data = [[rs["recommendation_set"][0][key]
                 for key in rs["recommendation_set"][0]] for rs in recommendations["output"]]"""

        self.sheet = Sheet(
            self,
            headers=headers,
            data=data,
            theme="light blue"
        )
        self.sheet.grid(row=0, column=0, sticky="nswe")
        # auto resize columns, column minimum width set to 150 pixels
        self.sheet.set_all_cell_sizes_to_text()
        self.sheet.column_width(column=0, width=100)
        self.sheet.column_width(column=1, width=100)
        self.sheet.enable_bindings("all", "edit_index", "edit_header")

        # create dropdown boxes in the last column
        self.sheet.dropdown(
            n2a(len(headers)-1),
            values=["yes", "no", "maybe"],
        )




# =================== Source Frame ====================

class SourceFrame(customtkinter.CTkFrame):
    """
    Frame that contains the table of source data from generated recommendations.
    The table is built with tksheet (v.7.2.23) module    
    """

    def __init__(self, master, recs_df):
        super().__init__(master)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        headers = recs_df.columns.tolist()
        data = recs_df.values.tolist()

        """headers = [key for key in recommendations["meta_data"]]
        data = [[rs["recommendation_set"][0][key]
                 for key in rs["recommendation_set"][0]] for rs in recommendations["output"]]"""

        self.sheet = Sheet(
            self,
            headers=headers,
            data=data,
            theme="light blue"
        )
        self.sheet.grid(row=0, column=0, sticky="nswe")
        # auto resize columns, column minimum width set to 150 pixels
        self.sheet.set_all_cell_sizes_to_text()
        self.sheet.column_width(column=0, width=100)
        self.sheet.column_width(column=1, width=100)
        self.sheet.enable_bindings("all", "edit_index", "edit_header")

        self.select_span = self.sheet.span("select")




# =================== Extraction Frame ====================

class ExtractionFrame(customtkinter.CTkFrame):
    """
    Frame where tips can be generated from an inserted folder containing PDF files
        TODO: should be allowed to insert single PDF files; output directory problem to be solved
    DND label built with tkinterdnd2 (v.0.4.2)
    
    TODO Procedure for key handling:
        If key entries on KeysFrame are filled, try them
        Else if env variables are set, try them
        Else Error
    """

    def __init__(self, master, app, fg_color="transparent"):
        super().__init__(master, fg_color=fg_color)
        self.app = app

        # Configure grid for this frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # variable that contains target directory
        # will be changed when ondrop events occurs
        target_dir = None
        # Drag-and-drop (DND) field TODO: constant width - currently label width changes when text length differs
        # TODO: DnD field touches navigation frame on left side
        info_text_label = customtkinter.CTkLabel(
            self, text="Please insert a folder here containing the PDF files to be analyzed")
        info_text_label.grid(row=0, column=0, columnspan=2,
                             padx=10, pady=5, sticky="ew")

        self.dnd_label = customtkinter.CTkLabel(
            self, text="Drop a folder here", fg_color="steelblue", text_color=("azure1"), corner_radius=50, width=200)
        self.dnd_label.grid(row=1, column=0, rowspan=2,
                            ipady=50, pady=5, padx=10, sticky="nsew")

        # Register the drag-and-drop field
        self.dnd_label.drop_target_register(
            tk2.DND_FILES)  # Register for file drops
        self.dnd_label.dnd_bind('<<Drop>>', self.on_drop)  # Bind drop event

        # Display target directory
        self.target_dir_label = customtkinter.CTkLabel(
            # TODO 'Selected Directory:' bold
            self, text="Selected Directory: no directory selected")
        self.target_dir_label.grid(row=1, column=1, pady=5, sticky="nsew")

        # Drop-Down Menu (Combobox) for Model Selection
        self.modelname = customtkinter.CTkComboBox(self, state="readonly", values=[
                                              "gpt-4o-mini", "groq/llama_3.1_versataile"])
        self.modelname.grid(row=2, column=1, padx=20, pady=5,
                       sticky="ew")  # Centered in the grid

        # Button: 'Generate Recommendations'
        self.gen_rec_button = customtkinter.CTkButton(
            self, text="Generate Recommendations", command=self.extract_recs, state="disabled")
        self.gen_rec_button.grid(
            row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ns")

    # call generate_from_folder() from tip_generator/tip_generator.py -> dict containing recommendations and source data
    # displayed in a frame splitted up(tabview) into 'Recommendations' and 'Source Data'
    # the dict of recommendations is handed to the classes RecommendationsFrame and SourceFrame where it will be displayed when class is initialized
    def extract_recs(self):
        # recommendations = tip_generator.tip_generator.pdf_to_recs()
        if self.target_dir == None:
            raise ValueError("No directory selected.")
        path_to_instruction_file = "C:/Users/Nutzer/iCloudDrive/_Longevity/py_tip_generator/data/instructions/paper_to_rec_inst.txt"

        pdf_to_tips(
            input_dir=self.target_dir,
            output_dir=self.target_dir,
            generator_instructions=path_to_instruction_file,
            modelname=self.modelname.get()
        )
        csv_path = Path(self.target_dir) / 'merged_data.csv'
        tips_df = pd.read_csv(csv_path)

        # Tabview containing recommendations and source data
        self.tabview = customtkinter.CTkTabview(
            self, segmented_button_selected_color="steelblue4")
        self.tabview.grid(row=4, column=0, columnspan=2,
                          padx=10, pady=(10, 5), sticky="nsew")
        self.tabview.add("Recommendations")
        self.tabview.add("Source")
        self.tabview.tab("Recommendations").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Recommendations").grid_rowconfigure(0, weight=1)
        self.tabview.tab("Source").grid_columnconfigure(0, weight=1)

        self.recom_view = RecommendationsFrame(
            self.tabview.tab("Recommendations"), tips_df)
        self.recom_view.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        # Label: display status for application to database
        #   every recommendation that is selected will be applied
        #   TODO if no selection, will be disabled
        self.selection_status_label = customtkinter.CTkLabel(self, text="*number of selected recommendations* selected.",  # TODO display num of selected recs
                                                             fg_color="gray")
        self.selection_status_label.grid(
            row=5, column=1, padx=5, pady=10, sticky="sw")
        # Button: 'Apply to Data Base'
        self.apply_to_db_button = customtkinter.CTkButton(
            self, text="Apply to Data Base", fg_color="steelblue4", command=self.apply_to_db)
        self.apply_to_db_button.grid(
            row=5, column=1, padx=5, pady=(0, 10), sticky="se")
        return tips_df


    def get_selected_recs(self):
        selected_recs = pd.DataFrame(columns=self.recom_view.sheet.get_column_data()) # set column names

        for row in range(len(self.recom_view.sheet.data)):
            row_data = self.recom_view.sheet.get_row_data(row)
            if row_data[-1] == "yes": # choose row if 'select' menu is set to yes
                # convert List row_data to pd.Series and append to df; ignore_index to keep continous indexing inside df
                selected_recs = selected_recs(pd.Series(row_data), ignore_index=True)
        return selected_recs
    

    # Apply selected recommendations to DB
    # get dropdown values: YES: apply to DB; NO: delete; TODO? MAYBE: save them for later
    def apply_to_db(self):
        # get selected recommendations
        recs = self.get_selected_recs()
        # read out login information and set up DB connection
        login = self.app.frames["DBConnect"].get_login()
        connection = connect_to_maria(
            user = login["user"],
            password = login["password"],
            host = login["host"],
            port = login["port"],
            database = login["database"],
        )
        # insert selected recs into db
        insert_into_db(connection, recs)


    # DND field function
    # self.target_dir defined at the top

    def on_drop(self, event):
        '''
        Display the name of the dropped folder and set target_dir 
        '''
        if not os.path.isdir(event.data):
            self.dnd_label.configure(
                text="No folder behind path!", fg_color="red")
        else:
            pdf_found = any(file.lower().endswith('.pdf')
                            for file in os.listdir(event.data))
            if pdf_found:
                # Display the path of the dropped file
                self.dnd_label.configure(
                    text=Path(event.data).name, fg_color="green")
                self.target_dir = event.data
                self.target_dir_label.configure(
                    text=f"Selected Directory: {Path(event.data)}")
                self.gen_rec_button.configure(state="enabled")
            else:
                self.dnd_label.configure(
                    text="No PDF file in directory!", fg_color="red")


# =================== Comparison Frame ====================

class ComparisonFrame(customtkinter.CTkFrame):
    """TODO Frame where the generated recommendations can be compared to the existing ones"""

    def __init__(self, master, fg_color="transparent"):
        super().__init__(master, fg_color=fg_color)

        # Configure grid for this frame
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        label = customtkinter.CTkLabel(
            self, text="This is the Comparison Frame")
        label.grid(row=0, column=0, padx=10, pady=10)

        button = customtkinter.CTkButton(self, text="Do something")
        button.grid(row=1, column=1, padx=10, pady=10)


# =================== DB Connect Frame ====================

class DBConnectFrame(customtkinter.CTkFrame):
    """Frame where login data to maria db can be entered"""

    def __init__(self, master, fg_color="transparent"):
        super().__init__(master, fg_color=fg_color)

        """self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self.grid_rowconfigure(6, weight=1)"""

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(3, weight=1)


        label = customtkinter.CTkLabel(
            self, text="Connect to MariaDB Database")
        label.grid(row=0, column=1, columnspan=2, padx=10, pady=10)

        user_label = customtkinter.CTkLabel(self, text="User: ")
        user_label.grid(row=2, column=1, pady=3, sticky="ew")
        self.user_entry = customtkinter.CTkEntry(self)
        self.user_entry.grid(row=2, column=2, pady=3, sticky="ew")

        password_label = customtkinter.CTkLabel(self, text="Password: ")
        password_label.grid(row=3, column=1, pady=3, sticky="ew")
        self.password_entry = customtkinter.CTkEntry(self, show="*")
        self.password_entry.grid(row=3, column=2, pady=3, sticky="ew")

        host_label = customtkinter.CTkLabel(self, text="Host: ")
        host_label.grid(row=4, column=1, pady=3, sticky="ew")
        self.host_entry = customtkinter.CTkEntry(self)
        self.host_entry.grid(row=4, column=2, pady=3, sticky="ew")

        port_label = customtkinter.CTkLabel(self, text="Port: ")
        port_label.grid(row=5, column=1, pady=3, sticky="ew")
        self.port_entry = customtkinter.CTkEntry(self)
        self.port_entry.grid(row=5, column=2, pady=3, sticky="ew")

        database_label = customtkinter.CTkLabel(self, text="Database: ")
        database_label.grid(row=6, column=1, pady=3, sticky="ew")
        self.database_entry = customtkinter.CTkEntry(self)
        self.database_entry.grid(row=6, column=2, pady=3, sticky="ew")

        test_db_connection_button = customtkinter.CTkButton(self, text="Test connection", command=self.test_connection)
        test_db_connection_button.grid(row=7, column=1, columnspan=2, padx=10, pady=10)

        self.test_db_connection_label = customtkinter.CTkLabel(self, text="")
        self.test_db_connection_label.grid(row=8, column=1, columnspan=2, padx=10, pady=10)


    def test_connection(self):    
        if test_connection(
            user = self.user_entry.get(),
            password = self.password_entry.get(),
            host = self.host_entry.get(),
            port = int(self.port_entry.get()) if not self.port_entry.get() == "" else 0,
            database = self.database_entry.get(),
        ):
            self.test_db_connection_label.configure(text="Connection succeeded!")
        else:
            self.test_db_connection_label.configure(text="Connection failed!")

    def get_login(self):
        login = {
            "user" : self.user_entry.get(),
            "password" : self.password_entry.get(),
            "host" : self.host_entry.get(),
            "port" : int(self.port_entry.get()) if not self.port_entry.get() == "" else 0,
            "database" : self.database_entry.get()            
        }
        return login

# =================== Key Frame ====================

class KeysFrame(customtkinter.CTkFrame):
    """Frame where required keys can be entered"""

    def __init__(self, master, fg_color="transparent"):
        super().__init__(master, fg_color=fg_color)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(3, weight=1)


        label = customtkinter.CTkLabel(
            self, text="Enter your keys")
        label.grid(row=0, column=1, columnspan=2, padx=10, pady=10)

        openai_api_label = customtkinter.CTkLabel(self, text="OpenAI API: ")
        openai_api_label.grid(row=2, column=1, pady=3, sticky="ew")
        self.openai_api_entry = customtkinter.CTkEntry(self)
        self.openai_api_entry.grid(row=2, column=2, pady=3, sticky="ew")

        semsch_api_label = customtkinter.CTkLabel(self, text="SemanticScholar API: ")
        semsch_api_label.grid(row=3, column=1, pady=3, sticky="ew")
        self.semsch_api_entry = customtkinter.CTkEntry(self)
        self.semsch_api_entry.grid(row=3, column=2, pady=3, sticky="ew")

class App:
    """Main application class to manage frames and navigation."""

    def __init__(self, root):
        self.root = root
        self.root.title("Class-Based Frames Example")
        self.root.geometry("800x600")

        # Set appearance and theme
        # Options: "Light", "Dark", "System"
        customtkinter.set_appearance_mode("Light")
        # Options: "blue", "dark-blue", "green"
        customtkinter.set_default_color_theme("blue")
        customtkinter.set_widget_scaling(1.2)  # Set scaling factor

        # Load images
        self.images = {}
        image_path = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "images")
        self.images["uni_logo"] = customtkinter.CTkImage(Image.open(
            os.path.join(image_path, "rostock_logo.png")), size=(150, 30))

        # Configure grid layout for the root
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=0)  # Navigation column
        self.root.grid_columnconfigure(1, weight=1)  # Content column

        # Create navigation frame
        self.navigation_frame = NavigationFrame(
            self.root, self, images=self.images)
        self.navigation_frame.grid(row=0, column=0, sticky="ns")

        # Create content frames
        self.frames = {
            "Extraction": ExtractionFrame(self.root, self),
            "Comparison": ComparisonFrame(self.root),
            "DBConnect" : DBConnectFrame(self.root),
            "Keys" : KeysFrame(self.root),
        }

        # Initially display the home frame
        self.show_frame("Extraction")

    def show_frame(self, frame_name):
        """Display the requested frame and hide others."""
        for frame in self.frames.values():
            frame.grid_forget()  # Hide all frames
        self.frames[frame_name].grid(
            row=0, column=1, sticky="nsew")  # Show selected frame


def start_gui():
    root = TkinterDnD.Tk()
    app = App(root)
    root.mainloop()