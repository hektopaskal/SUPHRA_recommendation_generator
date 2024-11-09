import os
from tkinter import *
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinterdnd2 as tk2

import pathlib
from pathlib import Path
import pandas as pd
import mariadb

from tip_generator.tip_generator import pdf_to_tips

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.option_add("*Font", ("Helvetica", 11))
        self.root.title("tip_generator")
        self.root.geometry("1000x700")

        # set ttkbootstrap theme
        self.style = tb.Style("superhero")

        # Initialize ttk.Notebook (tabbed window)
        self.notebook = tb.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        # Set up frames/tabs
        self.setup_main_frame()
        self.setup_similarity_check_frame()


        # --MAIN FRAME
    def setup_main_frame(self):
        main_frame = tb.Frame(self.notebook)
        self.notebook.add(main_frame, text="Main")
        
        # Main label and info text
        main_label = tb.Label(main_frame, text="SUPHRA Recommendation DB", font=("Helvetica", 19, "bold"), padding=10, relief="solid", borderwidth=2, bootstyle="default")
        main_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(30, 0), sticky="nw")
        info_label = tb.Label(main_frame, text="Sustainable Health and Productivity Advisory", font=("Helvetica", 12))
        info_label.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 0), sticky="nw")

        # MariaDB LabelFrame
        mariadb_labelframe = tb.LabelFrame(main_frame, text="Connection", padding=10, bootstyle="default")
        mariadb_labelframe.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="nw")
        
        # Entries for database connection
        # User
        self.user_label = tb.Label(mariadb_labelframe, text="User:")
        self.user_label.grid(row=0, column=0, pady=3, sticky="nw")
        self.user_entry = tb.Entry(mariadb_labelframe)
        self.user_entry.grid(row=0, column=1, padx=20, pady=3, sticky="nw")
        # Password
        self.password_label = tb.Label(mariadb_labelframe, text="Password:")
        self.password_label.grid(row=1, column=0, pady=3, sticky="nw")
        self.password_entry = tb.Entry(mariadb_labelframe, show="*")  # Hide password input
        self.password_entry.grid(row=1, column=1, padx=20, pady=3, sticky="nw")
        # Host
        self.host_label = tb.Label(mariadb_labelframe, text="Host:")
        self.host_label.grid(row=2, column=0, pady=3, sticky="nw")
        self.host_entry = tb.Entry(mariadb_labelframe)
        self.host_entry.grid(row=2, column=1, padx=20, pady=3, sticky="nw")
        # Port
        self.port_label = tb.Label(mariadb_labelframe, text="Port:")
        self.port_label.grid(row=3, column=0, pady=3, sticky="nw")
        self.port_entry = tb.Entry(mariadb_labelframe)
        self.port_entry.grid(row=3, column=1, padx=20, pady=3, sticky="nw")
        # Database
        self.database_label = tb.Label(mariadb_labelframe, text="Database:")
        self.database_label.grid(row=4, column=0, pady=3, sticky="nw")
        self.database_entry = tb.Entry(mariadb_labelframe)
        self.database_entry.grid(row=4, column=1, padx=20, pady=3, sticky="nw")

        # Test database connection
        # Test Button
        test_button = tb.Button(main_frame, text="Test Connection", command=self.test_connection)
        test_button.grid(row=3, column=0, padx=25, pady=10, sticky="nw")
        # Label to display connection status
        self.connection_status_label = tb.Label(main_frame, text="", font=("bold"))
        self.connection_status_label.grid(row=7, column=1, padx=20, pady=10, sticky="e")

        # DND Extract from PDF Field
        # LabelFrame
        dnd_labelframe = tb.LabelFrame(main_frame, text="Extract from PDF", padding=10)
        dnd_labelframe.grid(row=2, column=3, columnspan=2, padx=20, pady=10, sticky="nw")
        # Information text
        info_text_label = tb.Label(dnd_labelframe, text="Please insert a folder here containing the PDF files to be analyzed", font=("Helvetica", 12))
        info_text_label.grid(row=0, column=1, columnspan=2, pady=5)
        # DND Label
        self.dnd_label = tb.Label(
            dnd_labelframe, 
            text="Drag a File here!", 
            font=("Helvetica", 14), 
            bootstyle="inverse-secondary", 
            padding=(20, 40),
            width=40,
            anchor="center")
        self.dnd_label.grid(row=1, column=1, columnspan=2, pady=5)
        # Register the DND field
        self.dnd_label.drop_target_register(tk2.DND_FILES)  # Register for file drops
        self.dnd_label.dnd_bind('<<Drop>>', self.on_drop)  # Bind drop event
        # Button: Extract recommendations
        extract_tips_button = tb.Button(dnd_labelframe, text="Extract Recommendations", command=self.extract_recommendations)
        extract_tips_button.grid(row=2, column=1, padx=25, pady=10, sticky="nw")
        # Combobox: Select Model
        self.modelname = tb.Combobox(dnd_labelframe, state="readonly", values=["gpt_4o_mini", "groq/llama_3.1_versataile"])
        self.modelname.grid(row=2, column=2, padx=10, pady=10)  # Centered in the grid
        self.modelname.current(0)

        # LabelFrame: List extracted Recommendations
        # LabelFrame
        self.extracted_tips_labelframe = tb.LabelFrame(main_frame, text="Extracted Recommendations", padding=10)
        self.extracted_tips_labelframe.grid(row=5, column=0, columnspan=6, padx=20, pady=10, sticky="ew")
        #Label
        self.test_label = tb.Label(self.extracted_tips_labelframe, text="No Recommendations yet", font=("Helvetica", 12), anchor="center", justify="center")
        self.test_label.grid(row=0, column=0, pady=5, sticky="ew")




    # COMMANDS
    # DND Field Event Command
    target_dir = ""
    def on_drop(self, event):
        '''
        Display the name of the dropped folder and set target_dir
        '''
        if not os.path.isdir(event.data):
            self.dnd_label.config(text="No folder behind path!", bootstyle="inverse-secondary", foreground="red")
        else:
            pdf_found = any(file.lower().endswith('.pdf') for file in os.listdir(event.data))
            if pdf_found:
                self.dnd_label.config(text=Path(event.data).name, bootstyle="inverse-info", foreground="white")  # Display the path of the dropped file
                self.target_dir = event.data
            else:
                self.dnd_label.config(text="No PDF file in directory!", bootstyle="inverse-secondary", foreground="red")
            
    # Extract Recommendations
    def extract_recommendations(self):
        target_dir = self.dnd_label.cget("text")
        model = self.modelname.get()
        '''
        # Call the pdf_to_tips function and get the output
        try:
            tips = pdf_to_tips(target_dir, target_dir, model)
        except Exception as e:
            print(f"An error occured: {e}")
        '''
        #TESTING
        tips = ["Tip1", "Tip2", "Tip3"]

        # Create a canvas for scrolling
        canvas = tb.Canvas(self.extracted_tips_labelframe)  
        scrollbar = tb.Scrollbar(self.extracted_tips_labelframe, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tb.Frame(canvas)  # Initialize the scrollable frame

        # Configure the canvas and scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")  # Pack the scrollbar
        canvas.pack(side="left", fill="both", expand=True)  # Pack the canvas

        # Create a window in the canvas to hold the scrollable frame
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Update the scroll region of the canvas
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        for tip in tips:
            tip_frame = tb.Frame(self.scrollable_frame, borderwidth=2, relief="groove")  # Create a frame for each tip
            tip_frame.pack(pady=5, padx=5, fill='x')  # Add some padding and fill horizontally
            tip_label = tb.Label(tip_frame, text=tip)  # Create a label for the tip
            tip_label.pack(padx=10, pady=10)  # Add padding inside the frame


        # --SIMILARITY_CHECK
    def setup_similarity_check_frame(self):
        similarity_check_frame = tb.Frame(self.notebook)
        self.notebook.add(similarity_check_frame, text="Similarity Check")
        # Button: 'Check'
        check_button = tb.Button(
            similarity_check_frame,
            text="Check",
            bootstyle="success",
            command=lambda: self.check_similarities(
                self.user_entry.get(),
                self.password_entry.get(),
                self.host_entry.get(),
                int(self.port_entry.get()),
                self.database_entry.get(),
                5  # You can adjust the threshold as needed
            )
        )
        check_button.pack(pady=20)

        # Treeview to display results
        self.result_treeview = tb.Treeview(similarity_check_frame, columns=("Results"), show='headings')
        self.result_treeview.heading("Results", text="Results")
        self.result_treeview.pack(pady=10)


    def check_similarities(self, user, password, host, port, database, threshold):
        # Call the find_similarities function from maria_db
        from tip_generator.maria_db import find_similarities

        # Capture the output from find_similarities
        results = find_similarities(user, password, host, port, database, threshold)

        # Clear previous results
        self.result_treeview.delete(*self.result_treeview.get_children())

        # Display results in the Treeview
        for result in results:
            self.result_treeview.insert("", "end", values=(result))


    def test_connection(self):
        '''
        Test the connection to Maria DataBase
        '''
        try:
            connection = mariadb.connect(
                user=self.user_entry.get(),
                password=self.password_entry.get(),
                host=self.host_entry.get(),
                database=self.database_entry.get()
            )
            self.connection_status_label.config(text="Success!", foreground="green")
        except Exception as e:
            self.connection_status_label.config(text="Failed!", foreground="red")


def start_gui():
    root = tk2.TkinterDnD.Tk()
    app = MainApp(root)
    root.mainloop()
start_gui()