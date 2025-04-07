# --- Imports: data loading, GUI interaction, PDF generation, and formatting ---
import pickle
import json
import tkinter as tk
from tkinter import messagebox, filedialog
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from textwrap import wrap

# --- File paths for LLM responses and raw clustered messages ---
FILE_PATH_LLM = '../llm-response.pkl'
FILE_PATH_OG = '../cleaned_data.pkl'


# --- Function to generate a PDF report from LLM responses and message clusters ---
def save_to_pdf(data, raw_data, save_path):
    c = canvas.Canvas(save_path, pagesize=letter)
    width, height = letter  # Default page size (8.5 x 11 inches)
    
    # Set font for headings
    c.setFont("Helvetica-Bold", 12)
    
    # Set font for body text
    body_font = "Helvetica"
    body_font_size = 10
    c.setFont(body_font, body_font_size)
    
    # Line height for text and spacing
    line_height = 14
    section_spacing = 20  # Space between sections (e.g., after each OG DATA message)
    reduced_gap = section_spacing / 2  # Reduced gap between OG DATA sections
    page_margin = 72  # Margin from top of the page
    
    def check_and_create_new_page():
        nonlocal y_position
        if y_position < page_margin + line_height:  # Check if we're near the bottom of the page
            c.showPage()  # Create a new page
            c.setFont(body_font, body_font_size)  # Reset font for new page
            y_position = height - page_margin  # Reset y_position to the top of the new page
    
    for index, i in enumerate(data):
        response = json.loads(i['response'])  # Convert the string to a dictionary
        window_start = i['window_start']
        window_end = i['window_end']

        orignal_data = raw_data[index]
        
        # Wrap and process each section to ensure it fits within the page width
        text = f"[WINDOW_START] [{index}]: {window_start}\n"
        text += f"[WINDOW_END] [{index}]: {window_end}\n"
        text += f"[WINDOW_SUMMARY] [{index}]: {response['window_summary']}\n"

        # Set starting position for content
        y_position = height - page_margin  # 72 is for the margin from top of the page
        
        # Add window start, end, and summary at the top
        c.drawString(72, y_position, f"[WINDOW_START] [{index}]: {window_start}")
        y_position -= line_height
        check_and_create_new_page()  # Check for overflow before moving on
        
        c.drawString(72, y_position, f"[WINDOW_END] [{index}]: {window_end}")
        y_position -= line_height
        check_and_create_new_page()  # Check for overflow before moving on
        
        y_position -= section_spacing  # Add extra space after window section
        check_and_create_new_page()  # Check for overflow before moving on

        c.drawString(72, y_position, f"[WINDOW_SUMMARY] [{index}]:")
        y_position -= line_height
        check_and_create_new_page()  # Check for overflow before moving on

        # Wrap and print window summary in multiple lines
        for line in wrap(response['window_summary'], width=80):
            c.drawString(72, y_position, line)
            y_position -= line_height  # Move down
            check_and_create_new_page()  # Check for overflow before moving on
        
        y_position -= section_spacing  # Add extra space after "WINDOW SUMMARY"
        check_and_create_new_page()  # Check for overflow before moving on
        
        # Handle OG Data dynamically as separate sections
        for msg in orignal_data["messages"]:
            message_text = f"{msg['Date/Time']}: {msg['From Phone Number']}: {msg['Text']}"
            
            # Print each message on a new line (wrap text if it's too long)
            c.drawString(72, y_position, "[OG DATA]:")
            y_position -= line_height  # Move down
            check_and_create_new_page()  # Check for overflow before moving on
            
            # Wrap the message text to fit within the page width
            for line in wrap(message_text, width=80):
                c.drawString(72, y_position, line)
                y_position -= line_height  # Move down
                check_and_create_new_page()  # Check for overflow before moving on
            
            # Add reduced gap between each OG DATA message
            y_position -= reduced_gap
            check_and_create_new_page()  # Check for overflow before moving on
        
        c.showPage()  # Move to next page after each index
    
    c.save()  # Save the PDF


# ---------------------------------------

# --- Load pre-generated data files ---
with open(FILE_PATH_LLM, 'rb') as file:
    data = pickle.load(file)

with open(FILE_PATH_OG, 'rb') as fileOG:
    raw_data = pickle.load(fileOG)

# --- Setup GUI dialog using Tkinter ---
root = tk.Tk()
root.withdraw()  

save_pdf = messagebox.askyesno("Save Output", "Do you want to save the output as a PDF?")
if save_pdf:
    save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
    
    if save_path:
        save_to_pdf(data, raw_data, save_path)
        messagebox.showinfo("Success", f"PDF saved successfully at {save_path}")
    else:
        messagebox.showwarning("No Location", "No save location selected, PDF not saved.")
else:
    for index, i in enumerate(data):
        response = json.loads(i['response'])  # Convert the string to a dictionary
        window_start = i['window_start']
        window_end = i['window_end']
        
        orignal_data = raw_data[index]
        formatted_og_data =  "\n".join([
            f"{msg['Date/Time']}: {msg['From Phone Number']}: {msg['Text']}"
            for msg in orignal_data["messages"]
        ])
        print(f"[OG DATA]: \n {formatted_og_data}")
        print(f"[WINDOW_START] [{index}]: {window_start}")
        print(f"[WINDOW_END] [{index}]: {window_end}\n")
        print(f"[WINDOW_SUMMARY] [{index}]: {response['window_summary']}\n")

        print(f"+--------------------------+")
