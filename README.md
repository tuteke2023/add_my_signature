# PDF Signature Addition Script

This script adds your signature and the current date to PDF invoices.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create your signature image:
   - Create a PNG image of your signature with transparent background
   - Save it as `signature.png` in the same directory as the script
   - Recommended size: approximately 300x100 pixels

## Usage

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

## Tips

1. The position coordinates (0,0) start from the bottom-left corner of the PDF
2. You may need to adjust the x,y position based on your invoice layout
3. The script adds the signature to all pages of the PDF
4. The date format is "Month Day, Year" (e.g., "January 22, 2025")