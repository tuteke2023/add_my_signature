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
from streamlit_drawable_canvas import st_canvas
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="PDF Signature Tool", page_icon="✍️", layout="wide")

st.title("✍️ PDF Signature Tool")
st.markdown("Upload a PDF, position your signature, and download the signed version!")

# Initialize session state
if 'signature_x' not in st.session_state:
    st.session_state.signature_x = 400
if 'signature_y' not in st.session_state:
    st.session_state.signature_y = 100
if 'selected_page' not in st.session_state:
    st.session_state.selected_page = 1
if 'add_date' not in st.session_state:
    st.session_state.add_date = True

def create_signature_overlay(signature_image, date_text, position, page_size, add_date=True, sig_width=150, sig_height=50):
    """Create a PDF overlay with signature and optionally date"""
    packet = io.BytesIO()
    
    # Create a new PDF with ReportLab
    c = canvas.Canvas(packet, pagesize=page_size)
    
    # Save signature image to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        signature_image.save(tmp_file.name, 'PNG')
        tmp_file_path = tmp_file.name
    
    try:
        sig_x, sig_y = position
        c.drawImage(tmp_file_path, sig_x, sig_y, width=sig_width, height=sig_height, preserveAspectRatio=True)
        
        # Add date below signature if requested
        if add_date:
            c.setFont("Helvetica", 10)
            c.drawString(sig_x + sig_width * 0.3, sig_y - 10, date_text)
    finally:
        # Clean up temp file
        os.unlink(tmp_file_path)
    
    c.save()
    
    # Move to the beginning of the BytesIO buffer
    packet.seek(0)
    return PdfReader(packet)

def add_signature_to_pdf(pdf_file, signature_image, position, selected_page=1, add_date=True, sig_dimensions=(150, 50)):
    """Add signature and optionally date to specified page of PDF"""
    # Read the existing PDF
    reader = PdfReader(pdf_file)
    writer = PdfWriter()
    
    # Get current date in dd mm yyyy format
    date_text = datetime.now().strftime("%d %m %Y")
    
    # Process each page
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        
        # Add signature to the selected page (convert from 1-based to 0-based indexing)
        if page_num == selected_page - 1:
            # Get page dimensions
            page_box = page.mediabox
            page_width = float(page_box.width)
            page_height = float(page_box.height)
            
            # Create overlay with signature and optionally date
            overlay = create_signature_overlay(
                signature_image, 
                date_text, 
                position,
                (page_width, page_height),
                add_date,
                sig_dimensions[0],
                sig_dimensions[1]
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

def pdf_to_image(pdf_file, page_num=1):
    """Convert specified page of PDF to image for preview"""
    try:
        # Use pdf2image to convert PDF to image
        images = pdf2image.convert_from_bytes(pdf_file.read(), first_page=page_num, last_page=page_num, dpi=150)
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
    
    # Page selection for multi-page PDFs
    if uploaded_pdf:
        reader = PdfReader(uploaded_pdf)
        num_pages = len(reader.pages)
        uploaded_pdf.seek(0)  # Reset file pointer
        
        if num_pages > 1:
            st.subheader("📑 Page Selection")
            st.session_state.selected_page = st.selectbox(
                "Select page to sign:",
                options=list(range(1, num_pages + 1)),
                index=st.session_state.selected_page - 1 if st.session_state.selected_page <= num_pages else 0,
                format_func=lambda x: f"Page {x} of {num_pages}"
            )
        else:
            st.session_state.selected_page = 1
    
    st.header("✍️ Signature")
    signature_method = st.radio("Choose signature method:", ["Upload Image", "Draw Signature"])
    
    uploaded_signature = None
    drawn_signature = None
    
    if signature_method == "Upload Image":
        uploaded_signature = st.file_uploader("Choose your signature image", type=["png", "jpg", "jpeg"])
        
        if uploaded_signature:
            sig_image = Image.open(uploaded_signature)
            st.image(sig_image, caption="Your Signature", width=200)
    
    else:  # Draw Signature
        st.write("Draw your signature below:")
        # Create a canvas component
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",  # Transparent fill
            stroke_width=3,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=150,
            width=400,
            drawing_mode="freedraw",
            key="canvas",
        )
        
        # Convert canvas to image if there's drawing
        if canvas_result.image_data is not None:
            # Check if there's actual drawing (not just blank canvas)
            if np.any(canvas_result.image_data[:, :, 3] > 0):
                # Convert to PIL Image
                drawn_image = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                drawn_signature = drawn_image
                st.image(drawn_image, caption="Your Drawn Signature", width=200)
        
        if st.button("Clear Signature"):
            st.rerun()
    
    # Add date toggle
    st.header("⚙️ Options")
    st.session_state.add_date = st.checkbox("Add date below signature", value=st.session_state.add_date)

with col2:
    # Check if we have a signature (either uploaded or drawn)
    has_signature = uploaded_signature is not None or drawn_signature is not None
    
    if uploaded_pdf and has_signature:
        st.header("📍 Position Your Signature")
        
        # Convert selected page of PDF to image for preview
        pdf_image = pdf_to_image(uploaded_pdf, st.session_state.selected_page)
        
        if pdf_image:
            # Get image dimensions
            img_width, img_height = pdf_image.size
            
            # Interactive positioning
            st.subheader("Position Your Signature")
            st.info("💡 Click on the document preview below to position your signature")
            
            # Prepare signature for overlay
            if uploaded_signature:
                sig_img = Image.open(uploaded_signature)
            else:
                sig_img = drawn_signature
            sig_img = sig_img.resize((150, 50), Image.Resampling.LANCZOS)
            
            # Create the interactive plot with plotly
            fig = go.Figure()
            
            # Convert PIL image to numpy array for plotly
            img_array = np.array(pdf_image)
            
            # Add the PDF page as background
            fig.add_trace(go.Image(z=img_array))
            
            # Add a scatter point for the signature position
            fig.add_trace(go.Scatter(
                x=[st.session_state.signature_x + 75],  # Center of signature
                y=[st.session_state.signature_y + 25],  # Center of signature
                mode='markers',
                marker=dict(size=20, color='red', symbol='x'),
                name='Signature Position',
                hovertemplate='Click anywhere to move signature here<extra></extra>'
            ))
            
            # Configure the layout
            fig.update_layout(
                height=600,
                xaxis=dict(
                    range=[0, img_width],
                    showgrid=False,
                    zeroline=False,
                    visible=False
                ),
                yaxis=dict(
                    range=[img_height, 0],  # Invert y-axis for image coordinates
                    showgrid=False,
                    zeroline=False,
                    visible=False,
                    scaleanchor='x'
                ),
                margin=dict(l=0, r=0, t=0, b=0),
                hovermode='closest',
                dragmode=False,
                showlegend=False
            )
            
            # Display the interactive plot
            click_data = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
            
            # Handle click events
            if click_data and 'selection' in click_data and click_data['selection']['points']:
                # Get the clicked coordinates
                point = click_data['selection']['points'][0]
                if 'x' in point and 'y' in point:
                    # Update signature position (adjust for signature size to center on click)
                    # Allow positioning anywhere on the document within bounds
                    new_x = max(0, min(int(point['x']) - 75, img_width - 150))
                    new_y = max(0, min(int(point['y']) - 25, img_height - 50))
                    st.session_state.signature_x = new_x
                    st.session_state.signature_y = new_y
                    st.rerun()
            
            # Optional: Keep sliders for fine-tuning
            with st.expander("Fine-tune position with sliders"):
                col_x, col_y = st.columns(2)
                
                with col_x:
                    # Allow positioning up to image width minus signature width
                    max_x = max(0, img_width - 150)
                    x_pos = st.slider("Horizontal Position", 0, max_x, 
                                     value=min(st.session_state.signature_x, max_x), key="x_slider")
                    if x_pos != st.session_state.signature_x:
                        st.session_state.signature_x = x_pos
                        st.rerun()
                
                with col_y:
                    # Allow positioning up to image height minus signature height
                    max_y = max(0, img_height - 50)
                    y_pos = st.slider("Vertical Position", 0, max_y, 
                                     value=min(st.session_state.signature_y, max_y), key="y_slider")
                    if y_pos != st.session_state.signature_y:
                        st.session_state.signature_y = y_pos
                        st.rerun()
            
            # Show preview with signature
            st.subheader("Preview with Signature")
            
            # Create a copy of the PDF image
            preview_img = pdf_image.copy()
            
            # Overlay signature on preview
            if uploaded_signature:
                sig_img = Image.open(uploaded_signature)
            else:
                sig_img = drawn_signature
            sig_img = sig_img.resize((150, 50), Image.Resampling.LANCZOS)
            
            # Calculate position for preview
            preview_x = st.session_state.signature_x
            preview_y = st.session_state.signature_y
            
            # Paste signature on preview
            if sig_img.mode == 'RGBA':
                preview_img.paste(sig_img, (preview_x, preview_y), sig_img)
            else:
                preview_img.paste(sig_img, (preview_x, preview_y))
            
            # Add date text to preview if enabled
            if st.session_state.add_date:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(preview_img)
                date_text = datetime.now().strftime("%d %m %Y")
                # Try to use a basic font, fallback to default if not available
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
                except:
                    font = ImageFont.load_default()
                draw.text((preview_x + 65, preview_y + 52), date_text, fill='black', font=font)
            
            # Show preview
            page_label = f"Page {st.session_state.selected_page}" if num_pages > 1 else "Preview"
            st.image(preview_img, caption=f"{page_label} with Signature", use_container_width=True)
            
            
            # Process button
            if st.button("🎯 Sign PDF", type="primary"):
                with st.spinner("Processing..."):
                    # Get PDF page dimensions for the selected page
                    reader = PdfReader(uploaded_pdf)
                    page = reader.pages[st.session_state.selected_page - 1]
                    page_box = page.mediabox
                    pdf_width = float(page_box.width)
                    pdf_height = float(page_box.height)
                    
                    # Scale coordinates from image to PDF
                    scale_x = pdf_width / img_width
                    scale_y = pdf_height / img_height
                    
                    # Signature dimensions in preview (pixels) and scaled for PDF
                    preview_sig_width = 150
                    preview_sig_height = 50
                    pdf_sig_width = preview_sig_width * scale_x
                    pdf_sig_height = preview_sig_height * scale_y
                    
                    # Convert coordinates - PDF Y axis is bottom-up, image Y axis is top-down
                    pdf_x = st.session_state.signature_x * scale_x
                    # Y position: convert from top-down to bottom-up coordinate system
                    pdf_y = pdf_height - (st.session_state.signature_y * scale_y) - pdf_sig_height
                    
                    # Process the PDF
                    uploaded_pdf.seek(0)  # Reset file pointer
                    if uploaded_signature:
                        sig_image = Image.open(uploaded_signature)
                    else:
                        sig_image = drawn_signature
                    signed_pdf = add_signature_to_pdf(
                        uploaded_pdf,
                        sig_image,
                        (pdf_x, pdf_y),
                        st.session_state.selected_page,
                        st.session_state.add_date,
                        (pdf_sig_width, pdf_sig_height)
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
        st.info("👈 Please upload a PDF file and provide a signature (upload or draw) to begin")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit")