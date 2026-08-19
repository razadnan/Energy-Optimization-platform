from fpdf import FPDF
import datetime
import os

class PDFGenerator:
    """
    Generates beautifully styled corporate energy audit PDFs
    from markdown reports.
    """

    @staticmethod
    def generate_pdf(markdown_text: str, output_path: str):
        # Normalize characters not supported by standard Helvetica font
        markdown_text = markdown_text.replace("₹", "Rs.").replace("₂", "2")
        markdown_text = markdown_text.encode("latin-1", "replace").decode("latin-1")
        
        # Create output directory if not exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        class PDF(FPDF):
            def header(self):
                # Brand banner
                self.set_fill_color(31, 41, 55) # Slate Gray
                self.rect(0, 0, 210, 15, "F")
                
                # Header text
                self.set_text_color(255, 255, 255)
                self.set_font("helvetica", "B", 10)
                self.set_y(4)
                self.cell(0, 8, "AI ENERGY OPTIMIZATION AUDIT REPORT", align="C")
                self.set_y(15)

            def footer(self):
                # Position footer at 1.5 cm from bottom
                self.set_y(-15)
                self.set_font("helvetica", "I", 8)
                self.set_text_color(156, 163, 175)
                self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

        # Create PDF object
        pdf = PDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Set margins
        margin_left = 15
        margin_top = 20
        margin_right = 15
        pdf.set_margins(margin_left, margin_top, margin_right)
        
        # Printable width
        printable_width = pdf.w - margin_left - margin_right # 180 mm
        
        # Cover title page header
        pdf.set_y(25)
        pdf.set_text_color(16, 185, 129) # Emerald Green branding
        pdf.set_font("helvetica", "B", 20)
        pdf.cell(printable_width, 10, "Energy Intelligence Audit", new_x="LMARGIN", new_y="NEXT", align="L")
        
        pdf.set_text_color(55, 65, 81) # Slate gray secondary text
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(printable_width, 6, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(printable_width, 6, "Platform: QuickCart Energy Optimization SaaS", new_x="LMARGIN", new_y="NEXT")
        
        # Separator line
        pdf.set_draw_color(209, 213, 219)
        pdf.line(margin_left, pdf.get_y() + 4, pdf.w - margin_right, pdf.get_y() + 4)
        pdf.ln(10)
        
        # Content formatting
        pdf.set_text_color(31, 41, 55) # Dark gray body text
        
        lines = markdown_text.split("\n")
        for line in lines:
            line_str = line.strip()
            if not line_str:
                pdf.ln(2)
                continue
                
            # Headers formatting
            if line_str.startswith("# "):
                pdf.ln(4)
                pdf.set_text_color(16, 185, 129) # Emerald
                pdf.set_font("helvetica", "B", 14)
                pdf.multi_cell(printable_width, 8, line_str[2:])
                pdf.set_text_color(31, 41, 55)
            elif line_str.startswith("## "):
                pdf.ln(3)
                pdf.set_text_color(31, 41, 55)
                pdf.set_font("helvetica", "B", 12)
                pdf.multi_cell(printable_width, 7, line_str[3:])
            elif line_str.startswith("### "):
                pdf.ln(2)
                pdf.set_text_color(55, 65, 81)
                pdf.set_font("helvetica", "B", 10)
                pdf.multi_cell(printable_width, 6, line_str[4:])
            # Bullets
            elif line_str.startswith("- ") or line_str.startswith("* "):
                pdf.set_font("helvetica", "", 10)
                pdf.set_x(20)
                pdf.multi_cell(printable_width - 5, 5, f"* {line_str[2:]}")
                pdf.set_x(margin_left) # Reset X coordinate back to left margin
            elif any(line_str.startswith(f"{i}. ") for i in range(1, 10)):
                pdf.set_font("helvetica", "", 10)
                pdf.set_x(20)
                pdf.multi_cell(printable_width - 5, 5, line_str)
                pdf.set_x(margin_left) # Reset X coordinate back to left margin
            # Normal text
            else:
                pdf.set_font("helvetica", "", 10)
                pdf.multi_cell(printable_width, 5, line_str)
                
        # Save to file
        pdf.output(output_path)
