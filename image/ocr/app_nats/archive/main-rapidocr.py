from rapidocr_onnxruntime import RapidOCR
from pathlib import Path
import os
from IPython import embed


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


DEFAULT_CFG_PATH = os.path.join(ROOT_DIR, "keys", "config.yaml")


def ocr_to_text(ocr_output):
    """
    # Sort the OCR output based on the y-coordinate of the bounding box
    each element of the list is another list wihich contain 3 elements

        element 0 bounding box coordinates

        element 1 Text extracted

        element 2 score

        Example:

        [[[529.0, 149.0], [577.0, 149.0], [577.0, 174.0], [529.0, 174.0]],
        'R&D',
        0.9749892751375834]
    Args:
        ocr_output : list of lists, output from Rapid OCR
    """
    # Sort the OCR output based on the y-coordinate of the bounding box
    sorted_ocr = sorted(ocr_output, key=lambda x: x[0][0][1])

    # Initialize variables
    lines = []
    current_line = []
    current_y = sorted_ocr[0][0][0][1]

    # Iterate through the sorted OCR output
    for item in sorted_ocr:
        bbox, text, score = item
        bbox_y = bbox[0][1]

        # Check if the bounding box is on the same line as the current line
        if abs(bbox_y - current_y) <= 3:
            current_line.append(text + " ")
        else:
            lines.append(" ".join(current_line))
            current_line = [text + " "]
            current_y = bbox_y

    # Append the last line
    if current_line:
        lines.append(" ".join(current_line))

    # Join all lines into a single text output
    text_output = "\n".join(lines)
    return text_output


engine = RapidOCR(config_path=DEFAULT_CFG_PATH)


images_dir = "images"
output_text_dir = "output_text"

# Create the output directory if it doesn't exist
Path(output_text_dir).mkdir(parents=True, exist_ok=True)

# Process each image in the images directory
for filename in os.listdir(images_dir):
    if filename.lower().endswith(
        (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif")
    ):  # process only image files.
        image_path = os.path.join(images_dir, filename)
        print(f"Processing {filename}...")
        results, _ = engine(image_path)
        extracted_text = ocr_to_text(results)

        # Create the output text file name
        output_filename = os.path.splitext(filename)[0] + ".txt"
        output_filepath = os.path.join(output_text_dir, output_filename)

        # Save the extracted text to the output file
        with open(output_filepath, "w") as f:
            f.write(extracted_text)

        print(f"Processed {filename} and saved text to {output_filename}")

print("All images processed.")
