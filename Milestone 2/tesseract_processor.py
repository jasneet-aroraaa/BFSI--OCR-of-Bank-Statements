import pytesseract
import cv2

class TesseractProcessor:
    def __init__(self, 
                 psm=2,  # Page Segmentation Mode
                 oem=3,  # OCR Engine Mode
                 lang='eng',
                 config='',
                 min_conf=0):
        self.psm = psm
        self.oem = oem
        self.lang = lang
        self.config = config
        self.min_conf = min_conf

    def perform_ocr(self, image_path):
        img = cv2.imread(image_path)
        
        # Construct custom configuration
        custom_config = f'--oem {self.oem} --psm {self.psm} {self.config}'
        
        try:
            # Perform OCR with custom configuration
            data = pytesseract.image_to_data(
                img, 
                lang=self.lang,
                config=custom_config, 
                output_type=pytesseract.Output.DICT
            )
            
            extracted_data = []
            for i in range(len(data['text'])):
                # Apply confidence and custom filtering
                conf = float(data['conf'][i]) / 100
                if conf > self.min_conf and data['text'][i].strip():
                    try:
                        x, y, w, h = (
                            int(data['left'][i]), 
                            int(data['top'][i]), 
                            int(data['width'][i]), 
                            int(data['height'][i])
                        )
                        extracted_data.append([
                            data['text'][i], 
                            conf, 
                            x, y, w, h
                        ])
                    except (ValueError, TypeError, IndexError) as e:
                        print(f"Error extracting data from Tesseract: {e}")
                        continue
            return extracted_data
        except Exception as e:
            print(f"Error performing Tesseract OCR: {e}")
            return []