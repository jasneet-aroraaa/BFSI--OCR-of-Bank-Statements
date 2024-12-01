import easyocr

class EasyOCRProcessor:
    def __init__(self, 
                 languages=['en'], 
                 gpu=True, 
                 text_threshold=0.4, 
                 low_text=0.4, 
                 link_threshold=0.4,
                 canvas_size=2560,
                 mag_ratio=1.5):
        self.reader = easyocr.Reader(
            languages, 
            gpu=gpu,  # Enable/disable GPU
        )
        self.text_threshold = text_threshold  # Confidence threshold for text detection
        self.low_text = low_text  # Low text threshold
        self.link_threshold = link_threshold  # Threshold for linking text
        self.canvas_size = canvas_size  # Maximum image size for processing
        self.mag_ratio = mag_ratio  # Magnification ratio

    def perform_ocr(self, image_path):
        results = self.reader.readtext(
            image_path, 
            text_threshold=self.text_threshold,
            low_text=self.low_text,
            link_threshold=self.link_threshold,
            canvas_size=self.canvas_size,
            mag_ratio=self.mag_ratio
        )
        
        extracted_data = []
        for (bbox, text, prob) in results:
            try:
                min_x = int(min(p[0] for p in bbox))
                min_y = int(min(p[1] for p in bbox))
                max_x = int(max(p[0] for p in bbox))
                max_y = int(max(p[1] for p in bbox))
                extracted_data.append([text, prob, min_x, min_y, max_x - min_x, max_y - min_y])
            except (ValueError, TypeError) as e:
                print(f"Error processing bbox in EasyOCR: {e}, bbox: {bbox}")
                continue
        return extracted_data