import streamlit as st
import time
import os
from docx import Document
from fpdf import FPDF
import easyocr
import tempfile
import uuid
from PIL import Image
import pyheif

# Preload EasyOCR reader
@st.cache_resource
def load_easyocr_reader():
    return easyocr.Reader(["en"], gpu=False)

def convert_heic_to_png(image_file):
    heif_file = pyheif.read(image_file.read())
    image = Image.frombytes(
        heif_file.mode, heif_file.size, heif_file.data, "raw", heif_file.mode, heif_file.stride
    )
    return image

def extract_text_from_images(images, reader):
    extracted_text = {}
    for image_file in images:
        if image_file.type == "image/heic":
            image = convert_heic_to_png(image_file)
            image_bytes = image.tobytes()
        else:
            image_bytes = image_file.read()

        results = reader.readtext(image_bytes, detail=0)
        extracted_text[image_file.name] = results
    return extracted_text

def generate_word_document(extracted_text):
    doc = Document()
    doc.add_heading("Extracted Text from Images", level=1)
    for image_name, text in extracted_text.items():
        doc.add_heading(f"Image: {image_name}", level=2)
        for line in text:
            doc.add_paragraph(line)
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, f"{uuid.uuid4()}_extracted_text.docx")
    doc.save(output_path)
    return output_path

def generate_pdf_document(extracted_text):
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
    output_path = os.path.join(temp_dir, f"{uuid.uuid4()}_extracted_text.pdf")
    pdf.output(output_path)
    return output_path

def reset_session():
    st.session_state.clear()

def main():
    st.title("Image Text Extraction App")
    reader = load_easyocr_reader()

    if "start_time" not in st.session_state:
        st.session_state.start_time = None

    uploaded_files = st.file_uploader(
        "Upload Images (Max 10)", type=["jpg", "jpeg", "png", "heic"], accept_multiple_files=True
    )

    if uploaded_files:
        with st.spinner("Extracting text..."):
            if len(uploaded_files) > 10:
                st.error("You can upload a maximum of 10 images.")
            else:
                extracted_text = extract_text_from_images(uploaded_files, reader)
                st.success("Text extraction complete!")
                st.session_state["extracted_text"] = extracted_text

                # Select output format
                output_format = st.selectbox("Select Output Format", ["Word", "PDF"])
                if output_format:
                    st.session_state["output_format"] = output_format

                # Generate document only when button is clicked
                if st.button("Generate Document"):
                    with st.spinner("Preparing your document..."):
                        if output_format == "Word":
                            file_path = generate_word_document(extracted_text)
                        else:
                            file_path = generate_pdf_document(extracted_text)

                        st.session_state["file_path"] = file_path
                        st.success(f"{output_format} document ready!")

                        # Start timer for download
                        st.session_state.start_time = time.time()

                        # Download button
                        with open(file_path, "rb") as file:
                            download_button_clicked = st.download_button(
                                label=f"Download {output_format} Document",
                                data=file,
                                file_name=os.path.basename(file_path),
                                mime="application/octet-stream",
                            )

                            # If download button is clicked, ask to reset or stop
                            if download_button_clicked:
                                st.info("Do you want to reset the screen and start over?")
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("Yes, Reset"):
                                        reset_session()
                                        st.experimental_rerun()
                                with col2:
                                    if st.button("No, Stop"):
                                        st.success("Thank you! The app is now ready for the next user.")
                                        st.stop()  # Stops all further actions

    # Timer to reset session
    if st.session_state.start_time:
        elapsed_time = time.time() - st.session_state.start_time
        remaining_time = max(0, 120 - int(elapsed_time))
        st.info(f"Please download your document within {remaining_time // 60} min {remaining_time % 60} sec.")
        if elapsed_time > 120:
            st.warning("Time's up! Resetting the app for the next user.")
            reset_session()
            st.experimental_rerun()

if __name__ == "__main__":
    main()
