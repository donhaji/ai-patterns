# Prism Pattern: Gemini Implementation Examples

This directory contains Python implementations of the **Prism Pattern** (Spatial RAG) using Google Cloud Gemini Vision. These tools allow you to index and extract technical visual assets from PDF documentation with high precision.

## 🚀 Overview

The implementation is divided into two main stages:
1.  **Spatial Indexing**: Analyzing PDFs to find visual assets (diagrams, graphs, photos) and recording their spatial coordinates (bounding boxes).
2.  **Asset Extraction**: Surgically cropping those assets from the source PDF for use in multimodal RAG responses.

## 🛠️ Setup

### 1. Prerequisites
- A Google Cloud Project with the **Vertex AI API** enabled.
- Python 3.9+ installed.
- **Poppler** installed on your system (required for `pdf2image`):
    - **macOS**: `brew install poppler`
    - **Linux**: `sudo apt-get install poppler-utils`
    - **Windows**: [Download and add to PATH](https://github.com/oschwartz10612/poppler-windows/releases/)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Authentication
The scripts use Google Cloud **Application Default Credentials (ADC)**. Authenticate your local environment:
```bash
gcloud auth application-default login
```

### 4. Configure Environment
Set your Google Cloud Project ID:
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

## 📖 Usage

### Stage 1: Generate Spatial Manifest
Use the `spatial_manifest_generator.py` script to analyze a PDF and create a JSON manifest of all visual assets.

```bash
python spatial_manifest_generator.py path/to/datasheet.pdf
```
*Output: A JSON file in `output_manifests/` containing bounding boxes and descriptions.*

### Stage 2: Extract Specific Asset
Use `extract_image_from_pdf.py` to crop a specific asset from a PDF using coordinates from the manifest.

```bash
python extract_image_from_pdf.py \
  --pdf path/to/datasheet.pdf \
  --page 5 \
  --bbox "[ymin, xmin, ymax, xmax]" \
  --name sns212_wiring
```
*Output: A PNG image in `extracted_assets/`.*

## 🧩 Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `GOOGLE_CLOUD_PROJECT` | Your GCP Project ID | **Required** |
| `GOOGLE_CLOUD_LOCATION` | GCP Region | `us-central1` |
| `GEMINI_MODEL_NAME` | Gemini Model ID | `gemini-2.0-pro-exp-02-05` |
| `SPATIAL_OUTPUT_DIR` | Directory for crops | `extracted_assets` |
