###  This script reads DICOM files from a directory, modifies them, and saves the modified files to a new directory.
###  The script uses the pydicom library to read and write DICOM files and the OpenCV library to draw text on the images.
###  The modify_dicom_image() function redacts the patient's name and date of birth by replacing them with fake values.
###  The draw_text_on_image_opencv() function draws text on a NumPy array representing an image using OpenCV.
###  The modify_and_save_dicom() function reads DICOM files from a directory, modifies them using a specified function, and saves them to a new directory.
###  The modify_dicom_image_variable() function redacts the patient's name and date of birth and adjusts the text size based on the image size.
###  The script processes DICOM files in a directory using the modify_dicom_image_variable() function and saves the modified files to a new directory.
###  The script can be run from the command line by providing the input and output directories as arguments.
###  Example usage: python batch_dicom.py /path/to/input/directory /path/to/output/directory

import cv2
from pathlib import Path
import pydicom
import os
from faker import Faker


def draw_text_on_image_opencv(
    image_array,
    text,
    position=(10, 30),
    font_scale=1,
    font_color=(255, 255, 255),
    thickness=2,
    font=cv2.FONT_HERSHEY_SIMPLEX,
):
    """
    Draws text on a NumPy array representing an image using OpenCV.

    Args:
        image_array (numpy.ndarray): The image as a NumPy array (e.g., shape (height, width, 3) for RGB).
        text (str): The text to draw.
        position (tuple): The (x, y) coordinates of the text's bottom-left corner.
        font_scale (float): The font scale factor.
        font_color (tuple): The BGR color of the text (e.g., (0, 0, 255) for red).
        thickness (int): The thickness of the text lines.
        font (int): The OpenCV font type (e.g., cv2.FONT_HERSHEY_SIMPLEX).

    Returns:
        numpy.ndarray: The modified image as a NumPy array.
    """
    try:
        # OpenCV uses BGR color format, so we reverse the RGB tuple
        bgr_color = (font_color[2], font_color[1], font_color[0])

        # Draw the text using cv2.putText()
        cv2.putText(image_array, text, position, font, font_scale, bgr_color, thickness)

        return image_array

    except Exception as e:
        print(f"Error drawing text: {e}")
        return image_array


def draw_text_on_image_opencv(
    image_array,
    text,
    position=(10, 30),
    font_scale=1,
    font_color=(255, 255, 255),
    thickness=2,
    font=cv2.FONT_HERSHEY_SIMPLEX,
):
    try:
        bgr_color = (font_color[2], font_color[1], font_color[0])
        cv2.putText(image_array, text, position, font, font_scale, bgr_color, thickness)
        return image_array
    except Exception as e:
        print(f"Error drawing text: {e}")
        return image_array


def modify_dicom_image(dicom_instance):
    """
    Modifies the DICOM image by redacting the patient's name and date of birth.

    Args:
        dicom_instance (pydicom.dataset.FileDataset): The DICOM instance to modify.

    Returns:
        pydicom.dataset.FileDataset: The modified DICOM instance.
    """
    # Redact the patient's name and date of birth
    fake = Faker()
    dicom_instance.PatientBirthDate = fake.date_of_birth().strftime("%Y%m%d")
    dicom_instance.PatientName = fake.name()
    dicom_instance.PatientID = "123456"
    dicom_instance.PatientSex = "M"
    dicom_instance.PatientAddress = "123 Main St"
    dicom_instance.PatientTelephoneNumbers = "123-456-7890"
    dicom_instance.PatientWeight = "180"
    dicom_instance.PatientSize = "180"

    position = (20, 80)
    font_scale = 2.0
    font_color = (0, 0, 0)  # Red (BGR)
    thickness = 4
    font = cv2.FONT_HERSHEY_SIMPLEX  # Change font if desired

    modified_image_array = draw_text_on_image_opencv(
        dicom_instance.pixel_array,
        str(dicom_instance.PatientName),
        position,
        font_scale,
        font_color,
        thickness,
        font,
    )

    dicom_instance.PixelData = modified_image_array.tobytes()
    position = (20, 140)
    modified_image_array = draw_text_on_image_opencv(
        dicom_instance.pixel_array,
        str(dicom_instance.PatientBirthDate),
        position,
        font_scale,
        font_color,
        thickness,
        font,
    )
    dicom_instance.PixelData = modified_image_array.tobytes()
    return dicom_instance


def modify_dicom_image_variable(dicom_instance):
    """
    Modifies the DICOM image by redacting the patient's name and date of birth.

    Args:
        dicom_instance (pydicom.dataset.FileDataset): The DICOM instance to modify.

    Returns:
        pydicom.dataset.FileDataset: The modified DICOM instance.
    """
    # Redact the patient's name and date of birth

    fake = Faker()
    dicom_instance.PatientBirthDate = fake.date_of_birth().strftime("%Y%m%d")
    dicom_instance.PatientName = fake.name()
    dicom_instance.PatientID = "123456"
    dicom_instance.PatientSex = "M"
    dicom_instance.PatientAddress = "123 Main St"
    dicom_instance.PatientTelephoneNumbers = "123-456-7890"
    dicom_instance.PatientWeight = "180"
    dicom_instance.PatientSize = "180"

    shape = dicom_instance.pixel_array.shape

    if shape[0] < 500:
        # Parameters for the second image
        second_image = draw_text_on_image_opencv(
            dicom_instance.pixel_array,
            str(dicom_instance.PatientName),
            position=(10, 30),
            font_scale=0.5,
            font_color=(255, 255, 255),
            thickness=1,
        )
        second_image = draw_text_on_image_opencv(
            second_image,
            str(dicom_instance.PatientBirthDate),
            position=(10, 50),
            font_scale=0.5,
            font_color=(255, 255, 255),
            thickness=1,
        )
        dicom_instance.PixelData = second_image.tobytes()
    elif shape[0] < 1000:
        # Parameters for the first image
        first_image = draw_text_on_image_opencv(
            dicom_instance.pixel_array,
            str(dicom_instance.PatientName),
            position=(10, 30),
            font_scale=1.0,
            font_color=(255, 255, 255),
            thickness=2,
        )
        first_image = draw_text_on_image_opencv(
            first_image,
            str(dicom_instance.PatientBirthDate),
            position=(10, 60),
            font_scale=1.0,
            font_color=(255, 255, 255),
            thickness=2,
        )
        dicom_instance.PixelData = first_image.tobytes()
    elif shape[0] < 1500:
        # Parameters for the third image
        third_image = draw_text_on_image_opencv(
            dicom_instance.pixel_array,
            str(dicom_instance.PatientName),
            position=(10, 30),
            font_scale=1.5,
            font_color=(255, 255, 255),
            thickness=3,
        )
        third_image = draw_text_on_image_opencv(
            third_image,
            str(dicom_instance.PatientBirthDate),
            position=(10, 90),
            font_scale=1.5,
            font_color=(255, 255, 255),
            thickness=3,
        )
        dicom_instance.PixelData = third_image.tobytes()
    elif shape[0] < 2000:
        # Parameters for the fourth image
        fourth_image = draw_text_on_image_opencv(
            dicom_instance.pixel_array,
            str(dicom_instance.PatientName),
            position=(10, 30),
            font_scale=2.0,
            font_color=(255, 255, 255),
            thickness=4,
        )
        fourth_image = draw_text_on_image_opencv(
            fourth_image,
            str(dicom_instance.PatientBirthDate),
            position=(10, 120),
            font_scale=2.0,
            font_color=(255, 255, 255),
            thickness=4,
        )
        dicom_instance.PixelData = fourth_image.tobytes()
    else:
        # Parameters for the fifth image
        fifth_image = draw_text_on_image_opencv(
            dicom_instance.pixel_array,
            str(dicom_instance.PatientName),
            position=(10, 30),
            font_scale=2.5,
            font_color=(255, 255, 255),
            thickness=5,
        )
        fifth_image = draw_text_on_image_opencv(
            fifth_image,
            str(dicom_instance.PatientBirthDate),
            position=(10, 150),
            font_scale=2.5,
            font_color=(255, 255, 255),
            thickness=5,
        )
        dicom_instance.PixelData = fifth_image.tobytes()
    return dicom_instance


def modify_and_save_dicom(doc_path, output_path, modify_function):
    """
    Reads DICOM files from doc_path, modifies them using modify_function,
    and saves them to output_path, preserving the directory structure.

    Args:
        doc_path (Path): Path to the directory containing DICOM files.
        output_path (Path): Path to the directory to save modified DICOM files.
        modify_function (function): Function that modifies a pydicom Dataset.
    """

    for root, _, files in os.walk(doc_path):
        for file in files:
            if file.lower().endswith((".dcm", ".dicom")):
                input_filepath = Path(root) / file
                relative_path = input_filepath.relative_to(doc_path)
                output_filepath = output_path / relative_path

                # Create the output subdirectories if they don't exist
                output_filepath.parent.mkdir(parents=True, exist_ok=True)

                try:
                    dicom_instance = pydicom.dcmread(str(input_filepath))
                    dicom_instance_modified = modify_function(dicom_instance)
                    dicom_instance_modified.save_as(str(output_filepath))
                    print(f"Modified and saved: {output_filepath}")

                except Exception as e:
                    print(f"Error processing {input_filepath}: {e}")


DOC_PATH = Path("/home/detectai/data/dicom")

OUTPUT_PATH = Path("/home/detectai/data/dicom_modified")


# Directory where the output will be written

modify_and_save_dicom(DOC_PATH, OUTPUT_PATH, modify_dicom_image_variable)
