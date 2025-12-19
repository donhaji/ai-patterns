"""
Technical Documentation Visual Asset Indexer

This script utilizes Gemini Vision (Multimodal) to analyze PDF technical documents
and generate a structured JSON manifest of all significant visual assets such as
wiring diagrams, dimensional drawings, performance graphs, and product photos.

The resulting manifest includes bounding box coordinates, allowing for precise 
image extraction and improved RAG (Retrieval-Augmented Generation) performance.
"""

import vertexai
from vertexai.generative_models import GenerativeModel, Part
import os
import json
import argparse
from datetime import datetime
import sys

# --- Environment Configuration ---
# These variables should be set in your environment or .env file
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
# Defaulting to the latest Pro Vision model for high-precision technical document analysis
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3-pro-preview")

def initialize_vertex_ai():
    """Initializes the Vertex AI SDK and returns a configured GenerativeModel."""
    if not PROJECT_ID:
        print("ERROR: GOOGLE_CLOUD_PROJECT environment variable is not set.")
        sys.exit(1)
        
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        
        # Configure model for structured JSON output
        return GenerativeModel(
            MODEL_NAME,
            generation_config={"response_mime_type": "application/json"}
        )
    except Exception as e:
        print(f"FAILED to initialize Vertex AI: {e}")
        sys.exit(1)

def load_pdf_as_part(path):
    """Reads a binary PDF file and wraps it in a multimodal Part object."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        return Part.from_data(mime_type="application/pdf", data=data)
    except Exception as e:
        print(f"ERROR reading PDF file: {e}")
        return None

def run_manifest_generation(pdf_path, model):
    """
    Sends the PDF to Gemini Vision with a specialized prompt to extract 
    metadata for all technical visual assets.
    """
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found at {pdf_path}")
        return

    print(f"--- Processing: {pdf_path} ---")

    # The System Prompt defines the extraction schema and business rules
    system_prompt = f"""
    You are a Computer Vision Metadata Engine for Technical Documentation.
    Your goal is to analyze the provided PDF and generate a structured "Image Manifest" of all significant visual assets.
    
    OUTPUT FORMAT (JSON Object):
    {{
        "source_pdf": "{os.path.basename(pdf_path)}",
        "product_name": "<string: Primary product name>",
        "product_description": "<string: 1-2 sentence technical summary>",
        "created_at": "ISO-8601-Timestamp", 
        "assets": [
            {{
                "page_number": <int>,
                "type": "<stats_graph|wiring_diagram|technical_drawing|product_photo>",
                "model_name": "<string: Specific product variant name>",
                "product_code": "<string: 12NC or SKU if available>",
                "description": "<detailed description of the asset content>",
                "bounding_box": [ymin, xmin, ymax, xmax]
            }}
        ]
    }}

    TARGET ASSET CLASSIFICATIONS:
    - Wiring Diagrams: Schematics showing electrical connections and terminals.
    - Dimensional Drawings: Technical sketches providing physical measurements.
    - Performance Graphs: Charts showing efficiency, operating windows, or spectral response.
    - Product Photos: High-quality isolated images of the actual hardware.
    
    EXTRACTION RULES:
    1. PRODUCT ASSOCIATION: Link every asset to a specific model name and code found in headers or order data tables.
    2. BOUNDING BOXES: Provide inclusive coordinates. For full-page-width diagrams, use xmin: 50, xmax: 950.
    3. INCLUSIVITY: Bounding boxes must include all axes, legends, labels, and captions.
    4. STRICT GROUNDING: Only index assets clearly visible in the document. Exclude decorative elements, logos, or icons.
    5. NO HALLUCINATION: Do not assume diagrams exist if they are not explicitly shown.
    """

    pdf_part = load_pdf_as_part(pdf_path)
    if not pdf_part:
        return

    # Multimodal input: Text prompt + PDF bytes
    inputs = [system_prompt, pdf_part, "Extract the visual asset manifest as JSON."]
    
    print(f"Requesting multimodal analysis from {MODEL_NAME}...")
    
    try:
        response = model.generate_content(inputs)
        
        # The model returns a JSON string due to the response_mime_type config
        manifest_data = json.loads(response.text)
        
        # Enforce consistent metadata
        manifest_data["created_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        manifest_data["source_pdf"] = os.path.basename(pdf_path)

        # Output to console for verification
        print("\n--- EXTRACTED MANIFEST ---\n")
        print(json.dumps(manifest_data, indent=2))
        print("\n--- END OF MANIFEST ---")

        # Save to output directory
        output_dir = "output_manifests"
        os.makedirs(output_dir, exist_ok=True)
        
        filename = os.path.basename(pdf_path).replace(".pdf", ".json")
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, "w") as f:
            json.dump(manifest_data, f, indent=2)
        
        print(f"\n✅ SUCCESS: Manifest saved to {output_path}")

    except Exception as e:
        print(f"FAILED to generate manifest: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Extract a structured visual asset manifest from a PDF using Google Gemini Vision."
    )
    parser.add_argument("pdf_path", help="Local path to the PDF datasheet.")
    
    args = parser.parse_args()
    
    # Initialize SDK
    model = initialize_vertex_ai()
    
    # Run processing
    run_manifest_generation(args.pdf_path, model)

if __name__ == "__main__":
    main()
