import matplotlib.pyplot as plt
import pydicom
from presidio_image_redactor import DicomImageRedactorEngine
import logging
from pathlib import Path
import os


def compare_dicom_images(
    instance_original: pydicom.dataset.FileDataset,
    instance_redacted: pydicom.dataset.FileDataset,
    figsize: tuple = (11, 11),
) -> None:
    """Display the DICOM pixel arrays of both original and redacted as images.

    Args:
        instance_original (pydicom.dataset.FileDataset): A single DICOM instance (with text PHI).
        instance_redacted (pydicom.dataset.FileDataset): A single DICOM instance (redacted PHI).
        figsize (tuple): Figure size in inches (width, height).
    """
    _, ax = plt.subplots(1, 2, figsize=figsize)
    ax[0].imshow(instance_original.pixel_array, cmap="gray")
    ax[0].set_title("Original")
    ax[1].imshow(instance_redacted.pixel_array, cmap="gray")
    ax[1].set_title("Redacted")
    return ax


def process_dicom_images(
    dcm_path: str, engine: DicomImageRedactorEngine
) -> pydicom.dataset.FileDataset:
    """Read a DICOM file, redact PHI, and return the redacted instance.

    Args:
        dcm_path (str): Path to a DICOM file.
        engine (DicomImageRedactorEngine): A redaction engine for DICOM images.

    Returns:
        pydicom.dataset.FileDataset: A DICOM instance with redacted PHI.
    """
    instance = pydicom.dcmread(dcm_path, force=True)
    redacted_instance, bboxes = engine.redact_and_return_bbox(instance)
    return redacted_instance, bboxes


def process_dicom_folder(
    folder_in: str,
    folder_out: str,
    engine: DicomImageRedactorEngine,
    root_folder: str,
    data_folder: str = "data",
):
    """Read a DICOM file, redact PHI, and save the redacted instance.

    Args:
        folder_in (str): Path to a folder containing DICOM files.
        folder_out (str): Path to a folder to save redacted DICOM files.
        root_folder (str): Path to the root folder containing the input folder.
    """
    status = False

    folder_in = os.path.join(root_folder, data_folder, folder_in)
    logging.info(f"folder_in: {folder_in}")
    folder_out = os.path.join(root_folder, data_folder, folder_out)
    logging.info(f"folder_out: {folder_out}")
    try:
        engine.redact_from_directory(
            input_dicom_path=folder_in,
            output_dir=folder_out,
            fill="contrast",
            save_bboxes=True,  # if True, saves the redacted region bounding box info to .json files in the output dir
        )
        status = True
    except Exception as e:
        logging.error(f"Error: {e}")
    return status
