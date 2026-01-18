from fpdf import FPDF
import os

FONT_PATH = "DejaVuSans.ttf"

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()

    # ✅ Unicode font
    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
    pdf.set_font("DejaVu", size=11)

    # Normalize line endings
    text = text.replace("\r\n", "\n")

    pdf.multi_cell(0, 8, text)

    output_path = "FitnessPlan.pdf"
    pdf.output(output_path)

    return output_path
