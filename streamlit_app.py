import streamlit as st
import easyocr
from PIL import Image, ImageDraw, ImageFont
import os
from docx import Document

def extract_text_from_images(images, reader):
    """Extract text from a list of images using EasyOCR."""
    extracted_text = {}
    for image_file in images:
        # Convert file-like object to bytes
        image_bytes = image_file.read()
        # Pass bytes to EasyOCR
        results = reader.readtext(image_bytes, detail=0)
        extracted_text[image_file.name] = results
    return extracted_text

def generate_word_document(extracted_text):
    """Generate a Word document containing the extracted text."""
    doc = Document()
    doc.add_heading("Extracted Text from Images", level=1)

    for image_name, text in extracted_text.items():
        doc.add_heading(f"Image: {image_name}", level=2)
        for line in text:
            doc.add_paragraph(line)

    output_path = "extracted_text.docx"
    doc.save(output_path)
    return output_path

def generate_png_document(extracted_text):
    """Generate a PNG image containing the extracted text."""
    font_size = 20
    padding = 10
    font = ImageFont.load_default()

    # Calculate the dimensions of the image
    total_width = 800
    total_height = 0
    lines = []

    for image_name, text in extracted_text.items():
        lines.append(f"Image: {image_name}")
        lines.extend(text)
        lines.append("")

    for line in lines:
        total_height += font_size + padding

    img = Image.new("RGB", (total_width, total_height), color="white")
    draw = ImageDraw.Draw(img)

    y = 0
    for line in lines:
        draw.text((padding, y), line, fill="black", font=font)
        y += font_size + padding

    output_path = "extracted_text.png"
    img.save(output_path)
    return output_path

def main():
    st.title("Image Text Extraction App")
    st.write("Upload 1-10 images to extract text and generate a document.")

    uploaded_files = st.file_uploader("Upload Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded_files:
        if len(uploaded_files) > 10:
            st.error("You can upload a maximum of 10 images.")
        else:
            reader = easyocr.Reader(["en"], gpu=False)

            extracted_text = extract_text_from_images(uploaded_files, reader)
            st.write("Text extracted from images successfully!")

            output_format = st.selectbox("Select Output Format", ["Word", "PNG"])

            if st.button("Generate Document"):
                if output_format == "Word":
                    output_path = generate_word_document(extracted_text)
                elif output_format == "PNG":
                    output_path = generate_png_document(extracted_text)

                with open(output_path, "rb") as file:
                    st.download_button(
                        label=f"Download {output_format} Document",
                        data=file,
                        file_name=os.path.basename(output_path),
                        mime="application/octet-stream",
                    )

if __name__ == "__main__":
    main()
