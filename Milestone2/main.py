import streamlit as st
import os
import cv2
import numpy as np
import pandas as pd
import pytesseract
from PIL import Image
from easyocr_processor import EasyOCRProcessor
from tesseract_processor import TesseractProcessor
from llama_ocr_processor import LlamaOCRProcessor
import tempfile
import fitz 

try:
    from together import Together
except ImportError:
    print("Could not import Together. LlamaOCR will be unavailable.")
    Together = None

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class OCRComparator:
    def __init__(self):
        self.easyocr_processor = EasyOCRProcessor()
        self.tesseract_processor = TesseractProcessor()
        self.llama_ocr_processor = LlamaOCRProcessor() if Together is not None else None
        
    
    def draw_boxes(self, image, ocr_data):
        # Ensure the image is in color (3 channels)
        if len(image.shape) < 3:
            img = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else :
            img = image.copy()
            
        for item in ocr_data:
            if len(item) > 2:
                try:
                    text, conf, x, y, w, h = item
                    x, y, w, h = int(x), int(y), int(w), int(h)
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green in BGR
                except (ValueError, TypeError) as e:
                    print(f"Error drawing box: {e}, Item: {item}")
                    continue
        return img


def process_pdf(file):
    images = []
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
    return images
    
    
def process_image(image, comparator, uploaded_file):
    # Convert image to OpenCV format (BGR)
    image_cv2 = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Display uploaded image in color
    st.image(image, caption="Uploaded Image", use_column_width=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        temp_path = temp_file.name
        cv2.imwrite(temp_path, image_cv2)

    filename_without_ext = os.path.splitext(uploaded_file.name)[0]
    
    # LlamaOCR
    if comparator.llama_ocr_processor:
        llama_ocr_result = comparator.llama_ocr_processor.perform_ocr(temp_path)
        st.header("LlamaOCR Results")
        st.write(llama_ocr_result)
        if llama_ocr_result and llama_ocr_result not in [
            "Error: Together library not available.", "No text found.", "Error: Image not found.",
            "Error performing Llama OCR: Could not find image at the provided URL."
        ]:
            st.download_button("Download LlamaOCR Text", llama_ocr_result,
                               file_name=f"{filename_without_ext}_llama.txt")

    # EasyOCR Hyperparameters
    st.sidebar.header("EasyOCR Parameters")
    easy_text_threshold = st.sidebar.slider("Text Threshold", 0.0, 1.0, 0.4, 0.01)
    easy_low_text = st.sidebar.slider("Low Text Threshold", 0.0, 1.0, 0.4, 0.01)
    easy_link_threshold = st.sidebar.slider("Link Threshold", 0.0, 1.0, 0.4, 0.01)
    easy_canvas_size = st.sidebar.number_input("Canvas Size", 1000, 5000, 2560)
    easy_mag_ratio = st.sidebar.slider("Magnification Ratio", 1.0, 3.0, 1.5, 0.1)
    
    # Update EasyOCR Processor with new parameters
    comparator.easyocr_processor = EasyOCRProcessor(
        text_threshold=easy_text_threshold,
        low_text=easy_low_text,
        link_threshold=easy_link_threshold,
        canvas_size=easy_canvas_size,
        mag_ratio=easy_mag_ratio
    )

    # EasyOCR Processing
    easyocr_result = comparator.easyocr_processor.perform_ocr(temp_path)
    st.header("EasyOCR Results")
    
    # Convert bounding box image to RGB for correct color display
    image_with_easyocr_boxes = cv2.cvtColor(
        comparator.draw_boxes(image_cv2.copy(), easyocr_result), 
        cv2.COLOR_BGR2RGB
    )
    st.image(image_with_easyocr_boxes, caption="EasyOCR Bounding Boxes")
    
    df_easyocr = pd.DataFrame(easyocr_result, columns=['Text', 'Confidence', 'x', 'y', 'w', 'h'])
    st.table(df_easyocr[['Text', 'Confidence']])
    if easyocr_result:
        # Download Text and Confidence columns
        csv_easyocr = df_easyocr[['Text', 'Confidence']].to_csv(index=False)
        st.download_button(
            "Download EasyOCR Table", 
            csv_easyocr, 
            file_name=f"{filename_without_ext}_easyocr.csv", 
            mime='text/csv'
        )

    # Tesseract OCR Hyperparameters
    st.sidebar.header("Tesseract OCR Parameters")
    tesseract_psm = st.sidebar.selectbox("Page Segmentation Mode (PSM)", 
        [0, 1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13], 2)
    tesseract_oem = st.sidebar.selectbox("OCR Engine Mode (OEM)", [0, 1, 2, 3], 3)
    tesseract_min_conf = st.sidebar.slider("Minimum Confidence", 0.0, 1.0, 0.0, 0.01)
    
    # Update Tesseract Processor with new parameters
    comparator.tesseract_processor = TesseractProcessor(
        psm=tesseract_psm,
        oem=tesseract_oem,
        min_conf=tesseract_min_conf
    )

    # Tesseract OCR Processing
    tesseract_result = comparator.tesseract_processor.perform_ocr(temp_path)
    st.header("Tesseract OCR Results")
    
    # Convert bounding box image to RGB for correct color display
    image_with_tesseract_boxes = cv2.cvtColor(
        comparator.draw_boxes(image_cv2.copy(), tesseract_result), 
        cv2.COLOR_BGR2RGB
    )
    st.image(image_with_tesseract_boxes, caption="TesseractOCR Bounding Boxes")
    
    df_tesseract = pd.DataFrame(tesseract_result, columns=['Text', 'Confidence', 'left', 'top', 'width', 'height'])
    st.table(df_tesseract[['Text', 'Confidence']])
    if tesseract_result:
        # Download Text and Confidence columns
        csv_tesseract = df_tesseract[['Text', 'Confidence']].to_csv(index=False)
        st.download_button(
            "Download Tesseract Table", 
            csv_tesseract, 
            file_name=f"{filename_without_ext}_tesseract.csv", 
            mime='text/csv'
        )

    os.remove(temp_path) 


def main():
    st.set_page_config(page_title="OCR Comparator")
    st.title("OCR Comparator")

    comparator = OCRComparator()
    uploaded_file = st.file_uploader("Upload an image or PDF", type=["png", "jpg", "jpeg", "pdf"])

    if uploaded_file is not None:
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()

        if file_ext == ".pdf":
            images = process_pdf(uploaded_file)
            for i, image in enumerate(images):
                st.subheader(f"Page {i+1}")
                process_image(image, comparator, uploaded_file)
        else:
            image = Image.open(uploaded_file)
            process_image(image, comparator, uploaded_file)


if __name__ == "__main__":
    main()