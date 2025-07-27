import streamlit as st
import os
from datetime import datetime
from PIL import Image
import io
import base64
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile
import pdf2image

st.set_page_config(page_title="PDF Signature Tool", page_icon="✍️", layout="wide")

st.title("✍️ PDF Signature Tool")
st.markdown("Upload a PDF, position your signature, and download the signed version!")

# Initialize session state
if 'signature_x' not in st.session_state:
    st.session_state.signature_x = 400
if 'signature_y' not in st.session_state:
    st.session_state.signature_y = 100

def create_signature_overlay(signature_image, date_text, position, page_size):
    """Create a PDF overlay with signature and date"""
    packet = io.BytesIO()
    
    # Create a new PDF with ReportLab
    c = canvas.Canvas(packet, pagesize=page_size)
    
    # Save signature image to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        signature_image.save(tmp_file.name, 'PNG')
        tmp_file_path = tmp_file.name
    
    try:
        sig_x, sig_y = position
        c.drawImage(tmp_file_path, sig_x, sig_y, width=150, height=50, preserveAspectRatio=True)
        
        # Add date below signature
        c.setFont("Helvetica", 10)
        c.drawString(sig_x + 30, sig_y - 5, date_text)
    finally:
        # Clean up temp file
        os.unlink(tmp_file_path)
    
    c.save()
    
    # Move to the beginning of the BytesIO buffer
    packet.seek(0)
    return PdfReader(packet)

def add_signature_to_pdf(pdf_file, signature_image, position):
    """Add signature and date to PDF"""
    # Read the existing PDF
    reader = PdfReader(pdf_file)
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
    
    # Write to bytes
    output_bytes = io.BytesIO()
    writer.write(output_bytes)
    output_bytes.seek(0)
    
    return output_bytes

def pdf_to_image(pdf_file):
    """Convert first page of PDF to image for preview"""
    try:
        # Use pdf2image to convert PDF to image
        images = pdf2image.convert_from_bytes(pdf_file.read(), first_page=1, last_page=1, dpi=150)
        pdf_file.seek(0)  # Reset file pointer
        return images[0] if images else None
    except Exception as e:
        st.error(f"Error converting PDF to image: {str(e)}")
        return None

# Create two columns
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📄 Upload PDF")
    uploaded_pdf = st.file_uploader("Choose a PDF file", type="pdf")
    
    st.header("✍️ Upload Signature")
    uploaded_signature = st.file_uploader("Choose your signature image", type=["png", "jpg", "jpeg"])
    
    if uploaded_signature:
        sig_image = Image.open(uploaded_signature)
        st.image(sig_image, caption="Your Signature", width=200)

with col2:
    if uploaded_pdf and uploaded_signature:
        st.header("📍 Position Your Signature")
        
        # Convert PDF to image for preview
        pdf_image = pdf_to_image(uploaded_pdf)
        
        if pdf_image:
            # Get image dimensions
            img_width, img_height = pdf_image.size
            
            # Create sliders for positioning
            st.subheader("Adjust Position")
            col_x, col_y = st.columns(2)
            
            with col_x:
                x_pos = st.slider("Horizontal Position", 0, int(img_width * 0.8), 
                                 value=st.session_state.signature_x, key="x_slider")
                st.session_state.signature_x = x_pos
            
            with col_y:
                # Invert Y for display (PDF coordinates are bottom-up)
                y_display = st.slider("Vertical Position", 0, int(img_height * 0.8), 
                                     value=100, key="y_slider")
                st.session_state.signature_y = int(img_height * 0.8) - y_display
            
            # Show preview with signature position
            st.subheader("Preview")
            
            # Create a copy of the PDF image
            preview_img = pdf_image.copy()
            
            # Overlay signature on preview
            sig_img = Image.open(uploaded_signature)
            sig_img = sig_img.resize((150, 50), Image.Resampling.LANCZOS)
            
            # Calculate position for preview
            preview_x = x_pos
            preview_y = y_display
            
            # Paste signature on preview
            if sig_img.mode == 'RGBA':
                preview_img.paste(sig_img, (preview_x, preview_y), sig_img)
            else:
                preview_img.paste(sig_img, (preview_x, preview_y))
            
            # Show preview
            st.image(preview_img, caption="Preview with Signature", use_column_width=True)
            
            # Process button
            if st.button("🎯 Sign PDF", type="primary"):
                with st.spinner("Processing..."):
                    # Get PDF page dimensions
                    reader = PdfReader(uploaded_pdf)
                    page = reader.pages[0]
                    page_box = page.mediabox
                    pdf_width = float(page_box.width)
                    pdf_height = float(page_box.height)
                    
                    # Scale coordinates from image to PDF
                    scale_x = pdf_width / img_width
                    scale_y = pdf_height / img_height
                    
                    pdf_x = st.session_state.signature_x * scale_x
                    pdf_y = st.session_state.signature_y * scale_y
                    
                    # Process the PDF
                    uploaded_pdf.seek(0)  # Reset file pointer
                    sig_image = Image.open(uploaded_signature)
                    signed_pdf = add_signature_to_pdf(
                        uploaded_pdf,
                        sig_image,
                        (pdf_x, pdf_y)
                    )
                    
                    # Offer download
                    st.success("✅ PDF signed successfully!")
                    
                    # Get original filename
                    original_name = uploaded_pdf.name
                    signed_name = original_name.replace('.pdf', '_signed.pdf')
                    
                    st.download_button(
                        label="📥 Download Signed PDF",
                        data=signed_pdf.getvalue(),
                        file_name=signed_name,
                        mime="application/pdf"
                    )
    else:
        st.info("👈 Please upload both a PDF file and your signature image to begin")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit")