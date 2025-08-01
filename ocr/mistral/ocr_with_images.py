import os
import base64
from mistralai import Mistral

# Set API Key
api_key = "MHwl2C0kGvf1tuiAZmpSODUDqoUPRHQh"
client = Mistral(api_key=api_key)

# Specify the path to a single PDF file
pdf_path = "/Users/xinongshi/AFTER MQE/Research/blue_books_pdf/bermuda_blue_books/bermuda-blue-book-1918.pdf"
filename = os.path.basename(pdf_path)
basename = os.path.splitext(filename)[0]

# Create output directory
output_dir = os.path.join(os.path.dirname(pdf_path), basename + "_ocr_output")
os.makedirs(output_dir, exist_ok=True)

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

# Start processing
print(f"📄 Processing: {filename}")
try:
    with open(pdf_path, "rb") as f:
        uploaded_pdf = client.files.upload(
            file={"file_name": filename, "content": f},
            purpose="ocr"
        )

    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)

    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={"type": "document_url", "document_url": signed_url.url},
        include_image_base64=True
    )

    # Output markdown file
    md_output_path = os.path.join(output_dir, f"{basename}.md")
    with open(md_output_path, "w", encoding="utf-8") as f_out:
        for page in ocr_response.pages:
            f_out.write(f"# Page {page.index + 1}\n\n")
            f_out.write(page.markdown)
            f_out.write("\n\n---\n\n")

            # Output images
            for image in page.images:
                export_image(image, save_dir=output_dir)

    print(f"✅ Markdown saved to: {md_output_path}")
    print(f"🖼️ Images saved to: {output_dir}")

except Exception as e:
    print(f"❌ Failed: {filename}")
    print(e)
