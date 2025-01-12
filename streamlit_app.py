import streamlit as st
import easyocr
from PIL import Image
import os
from docx import Document
from fpdf import FPDF
import time

@st.cache_resource
def load_easyocr_reader():
    return easyocr.Reader(["en"], gpu=False)

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

def generate_pdf_document(extracted_text):
    """Generate a PDF document containing the extracted text."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Extracted Text from Images", ln=True, align='C')
    pdf.ln(10)

    for image_name, text in extracted_text.items():
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, txt=f"Image: {image_name}", ln=True)
        pdf.set_font("Arial", size=12)
        for line in text:
            pdf.multi_cell(0, 10, txt=line)
        pdf.ln(5)

    output_path = "extracted_text.pdf"
    pdf.output(output_path)
    return output_path

def main():
    st.title("Image Text Extraction App")

    # Add message and LinkedIn logo with animation
    st.markdown(
        """<div style='text-align: right;'>
        <strong style='color: green;'>Say Hi! to the developer</strong>
        <a href='https://www.linkedin.com/in/amanmiglani/' target='_blank'>
        <img src='https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png' alt='LinkedIn' style='width:40px; height:40px; margin-left: 10px; animation: pulse 2s infinite;' />
        </a>
        </div>
        <style>
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.write("Upload 1-10 images to extract text and generate a document.")

    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        uploaded_files = st.file_uploader("Upload Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

        if uploaded_files:
            with st.spinner("App is extracting text..."):
                if len(uploaded_files) > 10:
                    st.error("You can upload a maximum of 10 images.")
                else:
                    reader = load_easyocr_reader()

                    extracted_text = extract_text_from_images(uploaded_files, reader)

                    st.success("Text extracted from images successfully!")

                    output_format = st.selectbox("Select Output Format", ["Word", "PDF"])

                    if st.button("Generate Document"):
                        with st.spinner("Preparing your document..."):
                            if output_format == "Word":
                                output_path = generate_word_document(extracted_text)
                            elif output_format == "PDF":
                                output_path = generate_pdf_document(extracted_text)

                            # Artificial delay to ensure spinner visibility
                            time.sleep(1)

                        with open(output_path, "rb") as file:
                            st.download_button(
                                label=f"Download {output_format} Document",
                                data=file,
                                file_name=os.path.basename(output_path),
                                mime="application/octet-stream",
                            )
                        
                        # Reset the state after download
                        st.session_state.submitted = True
    else:
        st.button("Start Over", on_click=lambda: st.session_state.update(submitted=False))

if __name__ == "__main__":
    main()
