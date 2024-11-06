import tkinter as tk
from tkinter import ttk
from tip_generator.tip_generator import pdf_to_tips
import pathlib
from pathlib import Path
import pandas as pd

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("tip_generator")
        self.root.geometry("1000x700")
        
        # Initialize ttk.Notebook (tabbed window)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        # Set up frames/tabs
        self.setup_main_frame()
        self.setup_pdf_to_tips_frame()


        # MAIN FRAME
    def setup_main_frame(self):
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Main")
        
        main_label = tk.Label(main_frame, text="Welcome to tip_generator", font=("Arial", 14))
        main_label.pack(pady=20)

        # User
        user_label = tk.Label(main_frame, text="User:")
        user_label.pack(pady=5)
        user_entry = tk.Entry(main_frame)
        user_entry.pack(pady=5)

        # Password
        password_label = tk.Label(main_frame, text="Password:")
        password_label.pack(pady=5)
        password_entry = tk.Entry(main_frame, show="*")  # Hide password input
        password_entry.pack(pady=5)

        # Host
        host_label = tk.Label(main_frame, text="Host:")
        host_label.pack(pady=5)
        host_entry = tk.Entry(main_frame)
        host_entry.pack(pady=5)

        # Port
        port_label = tk.Label(main_frame, text="Port:")
        port_label.pack(pady=5)
        port_entry = tk.Entry(main_frame)
        port_entry.pack(pady=5)

        # Database
        database_label = tk.Label(main_frame, text="Database:")
        database_label.pack(pady=5)
        database_entry = tk.Entry(main_frame)
        database_entry.pack(pady=5)

        # Similarity Check Frame
        similarity_frame = ttk.Frame(self.notebook)
        self.notebook.add(similarity_frame, text="Similarity Check")

        # Button: 'Check'
        check_button = tk.Button(
            similarity_frame,
            text="Check",
            command=lambda: self.check_similarities(
                user_entry.get(),
                password_entry.get(),
                host_entry.get(),
                int(port_entry.get()),
                database_entry.get(),
                5  # You can adjust the threshold as needed
            )
        )
        check_button.pack(pady=20)

        # Listbox to display results
        self.result_listbox = tk.Listbox(similarity_frame, width=80, height=20)
        self.result_listbox.pack(pady=10)


        # PDF_TO_TIPS_FRAME
    def setup_pdf_to_tips_frame(self):
        pdf_to_tips_frame = ttk.Frame(self.notebook)
        self.notebook.add(pdf_to_tips_frame, text="PDF to Tips")

        # Widgets
        # input_directory
        input_dir_label = tk.Label(pdf_to_tips_frame, text="Input Directory:")
        input_dir_label.grid(row=0, column=0, padx=5, pady=5, sticky='e')  # Align to the right
        input_dir_entry = tk.Entry(pdf_to_tips_frame, width=50)
        input_dir_entry.grid(row=0, column=1, padx=5, pady=5)

        # output_directory
        output_dir_label = tk.Label(pdf_to_tips_frame, text="Output Directory:")
        output_dir_label.grid(row=1, column=0, padx=5, pady=5, sticky='e')  # Align to the right
        output_dir_entry = tk.Entry(pdf_to_tips_frame, width=50)
        output_dir_entry.grid(row=1, column=1, padx=5, pady=5)

        # Model
        modelname = ttk.Combobox(
            pdf_to_tips_frame,
            state="readonly",
            values=["gpt_4o_mini", "groq/llama_3.1_versataile"]
        )
        modelname.grid(row=2, column=0, columnspan=2, pady=10)  # Centered in the grid
        modelname.current(0)
       

        # Create a canvas for scrolling
        self.canvas = tk.Canvas(pdf_to_tips_frame)
        self.scrollbar = tk.Scrollbar(pdf_to_tips_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Configure the canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Pack the canvas and scrollbar
        self.canvas.grid(row=5, column=0, columnspan=2, pady=10, sticky="nsew")
        self.scrollbar.grid(row=5, column=2, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Button: 'Generate Tips'
        generate_button = tk.Button(
            pdf_to_tips_frame, 
            text="Generate Tips", 
            command=lambda: self.generate_tips(input_dir_entry.get(), output_dir_entry.get(), modelname.get()))
        generate_button.grid(row=4, column=0, columnspan=2, pady=20)


    def generate_tips(self, input_dir, output_dir, model):
        # Call the pdf_to_tips function and get the output
        tips = pdf_to_tips(input_dir, output_dir, model)
        
        # Clear the output frame before inserting new tips
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Insert each tip into a separate box
        for tip in tips:
            tip_frame = ttk.Frame(self.scrollable_frame, borderwidth=2, relief="groove")  # Create a frame for each tip
            tip_frame.pack(pady=5, padx=5, fill='x')  # Add some padding and fill horizontally
            tip_label = tk.Label(tip_frame, text=tip)  # Create a label for the tip
            tip_label.pack(padx=10, pady=10)  # Add padding inside the frame
        
        # Create a Treeview for displaying a table
        self.tree = ttk.Treeview(self.root, columns=("Tip", "Information", "Category"), show='headings')
        
    def check_similarities(self, user, password, host, port, database, threshold):
        # Call the find_similarities function from maria_db
        from tip_generator.maria_db import find_similarities

        # Capture the output from find_similarities
        results = find_similarities(user, password, host, port, database, threshold)

        # Clear previous results
        self.result_listbox.delete(0, tk.END)

        # Display results in the Listbox
        for result in results:
            self.result_listbox.insert(tk.END, result)

def start_gui():
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()

start_gui()