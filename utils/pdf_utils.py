# utils/pdf_utils.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from io import BytesIO
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image

PAGE_WIDTH, PAGE_HEIGHT = A4

def create_cover_pdf(lab_report) -> BytesIO:
    """
    Create a one-page cover PDF with details and a clickable hyperlink to result_url if exists.
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"LabReport_{lab_report.id}")

    x = 20 * mm
    y = PAGE_HEIGHT - 20 * mm

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(x, y, f"Lab Report ID: {lab_report.id}")
    pdf.setFont("Helvetica", 11)
    y -= 12 * mm
    student_id = getattr(lab_report.prescription.student, "id_number", "N/A") if lab_report.prescription else "N/A"
    student_name = getattr(lab_report.prescription.student, "name", "N/A") if lab_report.prescription else "N/A"
    pdf.drawString(x, y, f"Student ID: {student_id}")
    y -= 8 * mm
    pdf.drawString(x, y, f"Student Name: {student_name}")
    y -= 8 * mm
    pdf.drawString(x, y, f"Test Name: {lab_report.test_name}")
    y -= 8 * mm
    pdf.drawString(x, y, f"Status: {lab_report.status}")
    y -= 8 * mm
    pdf.drawString(x, y, f"Result: {lab_report.result or 'N/A'}")
    y -= 8 * mm
    created = getattr(lab_report, "created_at", None)
    updated = getattr(lab_report, "updated_at", None)
    pdf.drawString(x, y, f"Created At: {created.isoformat() if created else 'N/A'}")
    y -= 8 * mm
    pdf.drawString(x, y, f"Updated At: {updated.isoformat() if updated else 'N/A'}")
    y -= 12 * mm

    # If result_url exists: draw a hyperlink (visible and clickable)
    result_url = getattr(lab_report, "result_url", None)
    if result_url:
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(x, y, "Attached File:")
        y -= 8 * mm
        link_text = result_url if len(result_url) < 80 else result_url[:76] + "..."
        pdf.setFont("Helvetica-Oblique", 9)
        text_x = x
        text_y = y
        pdf.drawString(text_x, text_y, link_text)
        # Add clickable link area (approximate bounding box)
        text_width = pdf.stringWidth(link_text, "Helvetica-Oblique", 9)
        link_rect = (text_x, text_y - 2, text_x + text_width, text_y + 10)
        pdf.linkURL(result_url, link_rect, relative=0)
        y -= 12 * mm

    # Optionally add a small note about how the attached file is included
    pdf.setFont("Helvetica", 9)
    pdf.drawString(x, y, "Note: If attached file is a PDF or image, it will be appended to this document.")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer

def merge_pdfs(pdf_buffers: list) -> BytesIO:
    """
    Merge a list of BytesIO PDF buffers (cover first, then others) using PyPDF2.
    Each element in pdf_buffers should be a BytesIO (seeked to 0).
    """
    writer = PdfWriter()

    for buf in pdf_buffers:
        buf.seek(0)
        reader = PdfReader(buf)
        for page in reader.pages:
            writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output

def embed_image_into_pdf(cover_buf: BytesIO, image_bytes: BytesIO) -> BytesIO:
    """
    Create a PDF by taking cover_buf and appending the provided image as one or more pages.
    If the image is large, it will be scaled to fit the page while keeping aspect ratio.
    """
    # Recreate cover into a writer
    # Strategy: create new PDF for image pages, then merge
    # 1) create image PDF
    image_bytes.seek(0)
    img = Image.open(image_bytes)
    img_mode = img.mode
    if img_mode in ("RGBA", "LA"):
        # convert to RGB to avoid issues
        img = img.convert("RGB")

    # If multi-frame (animated GIF) take first frame
    try:
        img.seek(0)
    except Exception:
        pass

    # create a PDF with the image fit to page
    image_pdf_buf = BytesIO()
    c = canvas.Canvas(image_pdf_buf, pagesize=A4)

    # Fit image into page with margins
    max_w = PAGE_WIDTH - (20 * mm)
    max_h = PAGE_HEIGHT - (30 * mm)

    iw, ih = img.size
    # convert pixel sizes to points (1 px ~ 1 point at 72dpi) — better to use image dpi if available
    scale = min(max_w / iw, max_h / ih, 1.0)
    draw_w = iw * scale
    draw_h = ih * scale

    x = (PAGE_WIDTH - draw_w) / 2
    y = (PAGE_HEIGHT - draw_h) / 2

    img_reader = ImageReader(img)
    c.drawImage(img_reader, x, y, draw_w, draw_h, preserveAspectRatio=True)
    c.showPage()
    c.save()
    image_pdf_buf.seek(0)

    # 2) merge cover + image_pdf
    return merge_pdfs([cover_buf, image_pdf_buf])
