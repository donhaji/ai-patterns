"""
PDF Spatial Asset Extractor

This utility provides precision cropping of visual assets from PDF documents
using normalized coordinates (0-1000). It is typically used in conjunction 
with a spatial manifest to extract diagrams, drawings, or photos for use 
in RAG systems or technical documentation.
"""

import os
import argparse
import json
import sys
from typing import List, Optional
from pdf2image import convert_from_path
from PIL import Image

# --- Configuration ---
# Default directory where extracted images will be saved
DEFAULT_OUTPUT_DIR = os.getenv("SPATIAL_OUTPUT_DIR", "extracted_assets")

def extract_spatial_asset(
    pdf_path: str, 
    page_num: int, 
    bbox: List[float], 
    output_name: str,
    output_dir: str = DEFAULT_OUTPUT_DIR
) -> Optional[str]:
    """
    Extracts a specific region from a PDF page based on normalized coordinates.
    
    Args:
        pdf_path: Path to the source PDF file.
        page_num: 1-based page number to extract from.
        bbox: List of 4 normalized coordinates [ymin, xmin, ymax, xmax] (0 to 1000).
        output_name: Filename for the extracted image (without extension).
        output_dir: Directory where the image will be saved.
        
    Returns:
        The path to the saved PNG file if successful, else None.
    """
    if not os.path.exists(pdf_path):
        print(f"ERROR: Source PDF not found: {pdf_path}")
        return None

    if len(bbox) != 4:
        print(f"ERROR: Bounding box must contain exactly 4 coordinates. Got: {bbox}")
        return None

    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        print(f"Processing {pdf_path} (Page {page_num})...")

        # 1. Convert specific PDF page to high-resolution image
        # Note: pdf2image uses 1-based indexing for page selection
        images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num)
        if not images:
            print(f"ERROR: Failed to convert PDF page {page_num} to image.")
            return None
        
        img = images[0]
        width, height = img.size
        
        # 2. De-normalize coordinates (0-1000 scale to pixel scale)
        ymin, xmin, ymax, xmax = bbox
        
        # Add a 5% safety margin (padding) to avoid tight crops of labels/axes
        h_padding = (ymax - ymin) * 0.05
        w_padding = (xmax - xmin) * 0.05
        
        ymin = max(0, ymin - h_padding)
        xmin = max(0, xmin - w_padding)
        ymax = min(1000, ymax + h_padding)
        xmax = min(1000, xmax + w_padding)
        
        # Calculate pixel-level boundaries
        left = (xmin / 1000) * width
        top = (ymin / 1000) * height
        right = (xmax / 1000) * width
        bottom = (ymax / 1000) * height
        
        # 3. Perform the crop
        cropped_img = img.crop((left, top, right, bottom))
        
        # 4. Save as high-quality PNG
        output_path = os.path.join(output_dir, f"{output_name}.png")
        cropped_img.save(output_path, "PNG")
        
        print(f"✅ SUCCESS: Asset extracted to: {output_path}")
        return output_path

    except Exception as e:
        print(f"FAILED to extract asset: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Extract a visual asset from a PDF using spatial coordinates."
    )
    parser.add_argument("--pdf", required=True, help="Path to the source PDF document.")
    parser.add_argument("--page", type=int, required=True, help="1-based page number.")
    parser.add_argument(
        "--bbox", 
        required=True, 
        help='JSON list of coordinates [ymin, xmin, ymax, xmax], e.g., "[100, 50, 400, 950]"'
    )
    parser.add_argument("--name", required=True, help="Output filename (no extension).")
    parser.add_argument(
        "--outdir", 
        default=DEFAULT_OUTPUT_DIR, 
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    
    args = parser.parse_args()
    
    try:
        bbox_list = json.loads(args.bbox)
    except json.JSONDecodeError:
        print("ERROR: Invalid JSON format for --bbox. Expected a list like [ymin, xmin, ymax, xmax]")
        sys.exit(1)
    
    extract_spatial_asset(
        pdf_path=args.pdf, 
        page_num=args.page, 
        bbox=bbox_list, 
        output_name=args.name,
        output_dir=args.outdir
    )

if __name__ == "__main__":
    main()
