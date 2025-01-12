import streamlit as st
import easyocr
from PIL import Image
import pyheif
import os
import tempfile
import uuid
from docx import Document
from fpdf import FPDF
import time

@st.cache_resource
def load_easyocr_reader():
    return easyocr.Reader(["en"], gpu=False)

def convert_heic_to_png(image_file):
    """Convert HEIC image to PNG format."""
    heif_file = pyheif.read(image_file.read())
    image = Image.frombytes(
        heif_file.mode, heif_file.size, heif_file.data, "raw", heif_file.mode, heif_file.stride
    )
    return image

def extract_text_from_images(images, reader):
    """Extract text from a list of images using EasyOCR."""
    extracted_text = {}
    for image_file in images:
        if image_file.type == "image/heic":
            # Convert HEIC to PNG
            image = convert_heic_to_png(image_file)
            image_bytes = image.tobytes()
        else:
            # Read non-HEIC images directly
            image_bytes = image_file.read()

        # Pass bytes to EasyOCR
        results = reader.readtext(image_bytes, detail=0)
        extracted_text[image_file.name] = results
    return extracted_text

def generate_unique_filename(base_name):
    """Generate a unique filename to prevent conflicts."""
    unique_id = uuid.uuid4()
    return f"{unique_id}_{base_name}"

def generate_word_document(extracted_text):
    """Generate a Word document containing the extracted text."""
    doc = Document()
    doc.add_heading("Extracted Text from Images", level=1)

    for image_name, text in extracted_text.items():
        doc.add_heading(f"Image: {image_name}", level=2)
        for line in text:
            doc.add_paragraph(line)

    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, generate_unique_filename("extracted_text.docx"))
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

    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, generate_unique_filename("extracted_text.pdf"))
    pdf.output(output_path)
    return output_path

def main():
    st.title("Image Text Extraction App")

    # Preload EasyOCR model
    reader = load_easyocr_reader()

    # Add message and LinkedIn logo without animation
    st.markdown(
        """<div style='text-align: right;'>
        <strong style='color: green;'>Say Hi! to the developer</strong>
        <a href='https://www.linkedin.com/in/amanmiglani/' target='_blank'>
        <img src='https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png' alt='LinkedIn' style='width:40px; height:40px; margin-left: 10px;' />
        </a>
        </div>""",
        unsafe_allow_html=True
    )

    st.write("Upload 1-10 images to extract text and generate a document.")

    # Initialize session state variables
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "uploaded" not in st.session_state:
        st.session_state.uploaded = False
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = time.time()
    if "output_format" not in st.session_state:
        st.session_state.output_format = None
    if "idle_timer" not in st.session_state:
        st.session_state.idle_timer = 120

    # Check for inactivity
    elapsed_time = time.time() - st.session_state.last_activity
    if elapsed_time > 120:
        st.error("Too many requests, we are working on it.")
        st.stop()

    remaining_time = max(0, 120 - int(elapsed_time))
    st.info(f"The screen will reset in {remaining_time // 60} min {remaining_time % 60} sec if idle.")

    # File upload
    uploaded_files = st.file_uploader(
        "Upload Images", type=["jpg", "jpeg", "png", "heic"], accept_multiple_files=True
    )

    if uploaded_files:
        st.session_state.last_activity = time.time()
        with st.spinner("App is extracting text..."):
            if len(uploaded_files) > 10:
                st.error("You can upload a maximum of 10 images.")
            else:
                extracted_text = extract_text_from_images(uploaded_files, reader)
                st.success("Text extracted from images successfully!")
                st.session_state.uploaded = True
                st.session_state.extracted_text = extracted_text  # Save extracted text in session

    # Output format selection
    if st.session_state.uploaded:
        st.session_state.output_format = st.selectbox(
            "Select Output Format", ["Word", "PDF"], disabled=not st.session_state.uploaded
        )

    # Generate and download document
    if st.session_state.uploaded and st.session_state.output_format:
        if st.button("Generate Document"):
            st.session_state.last_activity = time.time()
            with st.spinner("Preparing your document..."):
                if st.session_state.output_format == "Word":
                    output_path = generate_word_document(st.session_state.extracted_text)
                elif st.session_state.output_format == "PDF":
                    output_path = generate_pdf_document(st.session_state.extracted_text)

                with open(output_path, "rb") as file:
                    st.download_button(
                        label=f"Download {st.session_state.output_format} Document",
                        data=file,
                        file_name=os.path.basename(output_path),
                        mime="application/octet-stream",
                        on_click=lambda: st.session_state.update(
                            uploaded=False, submitted=False, last_activity=time.time(), output_format=None
                        )
                    )

    # Start over button
    if st.session_state.submitted:
        if st.button("Start Over"):
            st.session_state.update(
                uploaded=False, submitted=False, last_activity=time.time(), output_format=None
            )

if __name__ == "__main__":
    main()
