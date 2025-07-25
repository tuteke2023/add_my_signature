#!/usr/bin/env python3
"""
PDF Signature Addition Script
Adds a signature image and current date to PDF invoices
"""

import argparse
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io


def create_signature_overlay(signature_path, date_text, position, page_size):
    """Create a PDF overlay with signature and date"""
    packet = io.BytesIO()
    
    # Create a new PDF with ReportLab
    c = canvas.Canvas(packet, pagesize=page_size)
    
    # Add signature image
    if os.path.exists(signature_path):
        sig_x, sig_y = position
        c.drawImage(signature_path, sig_x, sig_y, width=150, height=50, preserveAspectRatio=True)
        
        # Add date below signature
        c.setFont("Helvetica", 10)
        c.drawString(sig_x + 30, sig_y - 5, date_text)
    
    c.save()
    
    # Move to the beginning of the BytesIO buffer
    packet.seek(0)
    return PdfReader(packet)


def add_signature_to_pdf(input_pdf, output_pdf, signature_image, position=(400, 100)):
    """Add signature and date to PDF"""
    # Read the existing PDF
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    
    # Get current date in dd mm yyyy format
    date_text = datetime.now().strftime("%d %m %Y")
    
    # Process each page
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        
        # Only add signature to the first page
        if page_num == 0:
            # Get page dimensions
            page_box = page.mediabox
            page_width = float(page_box.width)
            page_height = float(page_box.height)
            
            # Create overlay with signature and date
            overlay = create_signature_overlay(
                signature_image, 
                date_text, 
                position,
                (page_width, page_height)
            )
            
            # Merge the overlay with the page
            overlay_page = overlay.pages[0]
            page.merge_page(overlay_page)
        
        # Add the page to writer (signed or unsigned)
        writer.add_page(page)
    
    # Write the output PDF
    with open(output_pdf, 'wb') as output_file:
        writer.write(output_file)


def main():
    parser = argparse.ArgumentParser(description='Add signature and date to PDF invoice')
    parser.add_argument('input_pdf', help='Path to input PDF file')
    parser.add_argument('-o', '--output', help='Output PDF file path (default: input_signed.pdf)')
    parser.add_argument('-s', '--signature', default='signature.png', 
                        help='Path to signature image file (default: signature.png)')
    parser.add_argument('-x', '--x-position', type=int, default=400,
                        help='X position for signature (default: 400)')
    parser.add_argument('-y', '--y-position', type=int, default=100,
                        help='Y position for signature (default: 100)')
    
    args = parser.parse_args()
    
    # Set default output filename if not provided
    if not args.output:
        base_name = os.path.splitext(args.input_pdf)[0]
        args.output = f"{base_name}_signed.pdf"
    
    # Check if input file exists
    if not os.path.exists(args.input_pdf):
        print(f"Error: Input file '{args.input_pdf}' not found")
        return 1
    
    # Check if signature file exists
    if not os.path.exists(args.signature):
        print(f"Error: Signature file '{args.signature}' not found")
        print("Please create a signature image file (PNG format recommended)")
        return 1
    
    try:
        # Add signature to PDF
        add_signature_to_pdf(
            args.input_pdf,
            args.output,
            args.signature,
            position=(args.x_position, args.y_position)
        )
        print(f"Successfully added signature to {args.output}")
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())