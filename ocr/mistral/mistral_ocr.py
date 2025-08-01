import os
from mistralai import Mistral

# Initialize Mistral client
api_key = "17hQ5HvXPjV8a22guudWItOp9iqkHOtd"  # ⚠️ Warning: avoid hardcoding API keys in production
client = Mistral(api_key=api_key)

# Path to the Bermuda folder containing PDF files
folder_path = "/Users/xinongshi/AFTER MQE/Research/blue_books_pdf/bermuda_blue_books"

# Iterate through all PDF files in the folder
for filename in os.listdir(folder_path):
    if filename.lower().endswith(".pdf"):
        pdf_path = os.path.join(folder_path, filename)
        print(f"📄 Processing: {filename}")

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
            ocr_response = client.ocr.process(
                model="mistral-ocr-latest",
                document={"type": "document_url", "document_url": signed_url.url},
                include_image_base64=True
            )

            # Write OCR output to a Markdown (.md) file
            output_md_path = os.path.splitext(pdf_path)[0] + ".md"
            with open(output_md_path, "w", encoding="utf-8") as f_out:
                for page in ocr_response.pages:
                    f_out.write(f"# Page {page.index + 1}\n\n")
                    f_out.write(page.markdown)
                    f_out.write("\n\n---\n\n")

            print(f"✅ Saved to: {output_md_path}")

        except Exception as e:
            print(f"❌ Failed: {filename}")
            print(e)
