# Description: This script is used to redact the DICOM files in a folder and save the redacted files in another folder.
# The script uses the DicomImageRedactorEngine class from the presidio_image_redactor package to redact the DICOM files.
# The redacted files are saved in the output folder.
# The script calculates the time taken to redact the files in the input folder and save the redacted files in the output folder.
# The script takes the input folder, output folder, and root folder as input arguments.
# The input folder contains the DICOM files to be redacted.
# The output folder is used to save the redacted DICOM files.
# The root folder is the parent folder containing the input and output folders.
# The script reads the DICOM files from the input folder, redacts the PHI, and saves the redacted files in the output folder.
# The script calculates the time taken to redact the files and save the redacted files in the output folder.
# The script can be run using the following command:
# python batch_processing.py


from presidio_image_redactor import DicomImageRedactorEngine
import os
from pathlib import Path
import datetime


def process_dicom_folder(
    folder_in: str, folder_out: str, engine: DicomImageRedactorEngine, root_folder: str
):
    """Read a DICOM file, redact PHI, and save the redacted instance.

    Args:
        folder_in (str): Path to a folder containing DICOM files.
        folder_out (str): Path to a folder to save redacted DICOM files.
        root_folder (str): Path to the root folder containing the input folder.
    """
    status = False
    folder_in = os.path.join(root_folder, folder_in)
    folder_out = os.path.join(root_folder, folder_out)
    try:
        engine.redact_from_directory(
            input_dicom_path=folder_in,
            output_dir=folder_out,
            fill="contrast",
            save_bboxes=True,  # if True, saves the redacted region bounding box info to .json files in the output dir
        )
        status = True
    except Exception as e:
        print(f"Error: {e}")
    return status


ROOT_FOLDER = Path("/home/detectai/data")
engine = DicomImageRedactorEngine()
imput_foldert = "dicom_modified"
output_folder = "output"
time3 = datetime.datetime.now()
process_dicom_folder(imput_foldert, output_folder, engine, ROOT_FOLDER)

time4 = datetime.datetime.now()

time_batch = (
    (time4 - time3).seconds * 1000000 + (time4 - time3).microseconds
) / 1000000
print(f"Time taken for batch processing: {time_batch} seconds")


##########################################
# python batch_processing.py
# /home/detectai/anaconda3/envs/dicom/lib/python3.11/site-packages/presidio_image_redactor/dicom_image_redactor_engine.py:346: RuntimeWarning: invalid value encountered in divide
#   (image_2d_float.max() - image_2d_float)
# /home/detectai/anaconda3/envs/dicom/lib/python3.11/site-packages/presidio_image_redactor/dicom_image_redactor_engine.py:351: RuntimeWarning: invalid value encountered in cast
#   image_2d_scaled = np.uint8(image_2d_scaled)
# /home/detectai/anaconda3/envs/dicom/lib/python3.11/site-packages/presidio_image_redactor/dicom_image_redactor_engine.py:346: RuntimeWarning: invalid value encountered in divide
#   (image_2d_float.max() - image_2d_float)
# /home/detectai/anaconda3/envs/dicom/lib/python3.11/site-packages/presidio_image_redactor/dicom_image_redactor_engine.py:351: RuntimeWarning: invalid value encountered in cast
# #   image_2d_scaled = np.uint8(image_2d_scaled)
# Output written to /home/detectai/data/output/dicom_modified
# Time taken for batch processing: 787.682828 seconds
