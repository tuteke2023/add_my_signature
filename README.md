# PDF Signature Tool

A tool to add your signature and the current date to PDF documents. Available as both a command-line script and a web application.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create your signature image:
   - Create a PNG image of your signature with transparent background
   - Save it as `signature.png` in the same directory as the script
   - Recommended size: approximately 300x100 pixels

## Command-Line Usage

Basic usage:
```bash
python add_signature.py invoice.pdf
```

This will create `invoice_signed.pdf` with your signature and today's date.

### Options

- `-o, --output`: Specify output filename
- `-s, --signature`: Path to signature image (default: signature.png)
- `-x, --x-position`: X position for signature (default: 400)
- `-y, --y-position`: Y position for signature (default: 100)

### Examples

```bash
# Custom output file
python add_signature.py invoice.pdf -o signed_invoice.pdf

# Custom signature file
python add_signature.py invoice.pdf -s my_signature.png

# Adjust signature position
python add_signature.py invoice.pdf -x 350 -y 150
```

## Web Application

### Running Locally

```bash
streamlit run app.py
```

### Features

- **Upload PDF**: Drag and drop or browse to select your PDF file
- **Signature Options**:
  - **Upload Image**: Upload a PNG/JPG image of your signature
  - **Draw Signature**: Draw your signature directly on the canvas
- **Interactive Positioning**: Use sliders to position your signature exactly where you want
- **Live Preview**: See exactly where your signature will appear before applying
- **Download**: Get your signed PDF with one click

### Deployment

The app can be deployed on [Streamlit Cloud](https://streamlit.io/cloud):
1. Fork this repository
2. Sign in to Streamlit Cloud with GitHub
3. Deploy using your forked repository

## Tips

1. The position coordinates (0,0) start from the bottom-left corner of the PDF
2. You may need to adjust the x,y position based on your invoice layout
3. The script signs only the first page of the PDF
4. The date format is "dd mm yyyy" (e.g., "27 01 2025")