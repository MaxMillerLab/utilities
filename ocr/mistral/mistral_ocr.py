import os
import sys
import base64
import zipfile
import tempfile
import shutil
from pathlib import Path
from mistralai import Mistral
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent.parent / '.env')

def data_uri_to_bytes(data_uri):
    """Convert base64 image string to bytes"""
    _, encoded = data_uri.split(",", 1)
    return base64.b64decode(encoded)

def export_image(image, save_dir):
    """Export base64-encoded image to disk"""
    parsed_image = data_uri_to_bytes(image.image_base64)
    image_path = os.path.join(save_dir, image.id + ".jpeg")
    with open(image_path, "wb") as file:
        file.write(parsed_image)
    return image_path

def process_pdf_to_zip(pdf_path):
    """Process a PDF file and create a zip file with markdown and images"""
    # Initialize Mistral client
    api_key = os.getenv('MISTRAL_API_KEY')
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not found in environment variables")
    
    client = Mistral(api_key=api_key)
    
    # Get file information
    pdf_path = Path(pdf_path)
    if not pdf_path.exists() or not pdf_path.suffix.lower() == '.pdf':
        raise ValueError(f"Invalid PDF file: {pdf_path}")
    
    filename = pdf_path.name
    basename = pdf_path.stem
    output_zip = pdf_path.parent / f"{basename}_ocr.zip"
    
    print(f"📄 Processing: {filename}")
    
    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Upload the PDF file
            with open(pdf_path, "rb") as f:
                uploaded_pdf = client.files.upload(
                    file={"file_name": filename, "content": f},
                    purpose="ocr"
                )
            
            # Get signed URL for the uploaded file
            signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
            
            # Perform OCR using Mistral
            print("🔍 Performing OCR...")
            ocr_response = client.ocr.process(
                model="mistral-ocr-latest",
                document={"type": "document_url", "document_url": signed_url.url},
                include_image_base64=True
            )
            
            # Create markdown file
            md_path = Path(temp_dir) / f"{basename}.md"
            image_paths = []
            
            with open(md_path, "w", encoding="utf-8") as f_out:
                for page in ocr_response.pages:
                    f_out.write(f"# Page {page.index + 1}\n\n")
                    
                    # Process markdown content to update image references
                    markdown_content = page.markdown
                    
                    # Export images for this page
                    for image in page.images:
                        img_path = export_image(image, temp_dir)
                        image_paths.append(img_path)
                        # Update image reference in markdown to use relative path
                        markdown_content = markdown_content.replace(
                            f"![{image.id}]", 
                            f"![{image.id}]({os.path.basename(img_path)})"
                        )
                    
                    f_out.write(markdown_content)
                    f_out.write("\n\n---\n\n")
            
            # Create zip file
            print(f"📦 Creating zip file: {output_zip.name}")
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add markdown file
                zipf.write(md_path, arcname=md_path.name)
                # Add all images
                for img_path in image_paths:
                    zipf.write(img_path, arcname=os.path.basename(img_path))
            
            print(f"✅ Success! Output saved to: {output_zip}")
            print(f"   - Contains {len(image_paths)} images and 1 markdown file")
            
        except Exception as e:
            print(f"❌ Failed to process {filename}")
            print(f"Error: {e}")
            raise

def main():
    if len(sys.argv) != 2:
        print("Usage: python mistral_ocr.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    process_pdf_to_zip(pdf_path)

if __name__ == "__main__":
    main()
