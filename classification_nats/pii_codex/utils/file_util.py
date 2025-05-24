"""
File utils
"""

import json
import os
from pathlib import Path
import pandas as pd
from .logging import logger

dirname = os.path.dirname(__file__)

# Cols New weights
cols = [
    "PII_Type",
    "GDPR_Category",
    "GDPR_Sensitivity",
    "GRPR_Likelihood",
    "GDPR_Impact",
    "GDPR_Importance_Weighting",
    "GDPR_Risk_Score",
    "Risk_Level_GDPR",
    "Country",
    "PII_Category",
    "PII_Sensitivity_Score",
    "PII_Likelihood_Score",
    "PII_Impact_Score",
    "PII_Importance_Weighting",
    "PII_Risk_Score",
]


def get_relative_path(path_to_file: str):
    """
    Returns the file_path relative to the project

    @param path_to_file:
    @return:
    """
    filename = os.path.join(dirname, path_to_file)

    return Path(__file__).parent / filename


def write_json_file(folder_name: str, file_name: str, json_data):
    """
    Writes json file given json data, a folder name, and a file name.

    @param folder_name:
    @param file_name:
    @param json_data:
    """
    # Create a new directory because it does not exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

        logger.info(f"A new version directory has been created: {folder_name}")

    with open(file_name, "w", encoding="utf-8") as json_file:
        json.dump(
            json.loads(json_data),
            json_file,
            ensure_ascii=False,
            indent=4,
        )


def delete_file(
    file_path: str = "pii_type_mappings",
):
    """
    Deletes a version file if it exists

    @param file_path:
    @return:
    """

    # Delete file if it exists
    if os.path.exists(file_path):
        os.remove(file_path)

        logger.info(f"The file {file_path} has been deleted")
    else:
        raise AttributeError(f"The file {file_path} does not exist")


def delete_folder(
    folder_path: str,
):
    """
    Deletes a folder if it exists and nothing is within it

    @param folder_path:
    """

    # Delete folder if it exists
    if os.path.exists(folder_path):
        os.rmdir(folder_path)

        logger.info(f"The folder {folder_path} has been deleted")
    else:
        raise AttributeError(f"The folder {folder_path} does not exist")


# region MAPPING FILE UTILS


def open_pii_type_mapping_csv(
    mapping_file_version: str = "v1", mapping_file_name: str = "pii_type_mappings"
):
    """

    @param mapping_file_name:
    @param mapping_file_version:
    """
    file_path = get_relative_path(
        f"../data/{mapping_file_version}/{mapping_file_name}.csv"
    )
    with file_path.open():
        return pd.read_csv(file_path)


def open_pii_type_mapping_csv_reload(
    mapping_file_version: str = "v1",
    mapping_file_name: str = "pii_type_mappings",
    weignts=None,
):
    """

    @param mapping_file_name:
    @param mapping_file_version:
    @param weignts:
    """
    if mapping_file_version == "v1":
        raise AttributeError("only version 2 of model")

    file_path = get_relative_path(
        f"../data/{mapping_file_version}/{mapping_file_name}.csv"
    )
    with file_path.open():
        df = pd.read_csv(file_path)

    list_pii_ori = list(df.PII_Type.unique())

    df_weigths = pd.json_normalize(weignts)
    # create a list of PII identifiers from the personalize list of weigths
    list_pii = list(df_weigths.PII_Type.unique())
    # raise an Exception if any of the PII identifiers in the personalize list of weigths are not in the original list of PII identifiers.
    for pii in list_pii:
        if pii not in list_pii_ori:
            raise AttributeError(f"Pii {pii} not in original list")

    df = df[df.PII_Type.isin(list_pii)]

    for col in cols:
        df[col] = df_weigths[col].values
    return df


def open_pii_type_mapping_csv_test(
    mapping_file_version: str = "v1", mapping_file_name: str = "pii_type_mappings"
):
    """

    @param mapping_file_name:
    @param mapping_file_version:
    """
    file_path = f"../classification/pii_codex/data/{mapping_file_version}/{mapping_file_name}.csv"

    return pd.read_csv(file_path, engine="python")


def open_pii_type_mapping_json(
    mapping_file_version: str = "v1", mapping_file_name: str = "pii_type_mappings"
):
    """

    @param mapping_file_name:
    @param mapping_file_version:
    @return:
    """

    file_path = get_relative_path(
        f"../data/{mapping_file_version}/{mapping_file_name}.json"
    )
    with file_path.open() as file:
        json_file_dataframe = pd.read_json(file)
        json_file_dataframe.drop("index", axis=1, inplace=True)

        return json_file_dataframe


def convert_pii_type_mapping_csv_to_json(
    data_frame: pd.DataFrame,
    mapping_file_version: str = "v1",
    json_file_name: str = "pii_type_mappings",
):
    """
    Writes JSON mapping file given a dataframe. Used primarily to update data folder with new versions

    @param data_frame:
    @param mapping_file_version:
    @param json_file_name:
    """

    folder_path = get_relative_path(f"../data/{mapping_file_version}")

    file_path = get_relative_path(
        f"../data/{mapping_file_version}/{json_file_name}.json"
    )

    write_json_file(
        folder_name=folder_path,
        file_name=file_path,
        json_data=data_frame.reset_index().to_json(orient="records"),
    )


def delete_json_mapping_file(
    mapping_file_version: str = "v1",
    json_file_name: str = "pii_type_mappings",
):
    """
    Deletes a version file within a data version folder

    @param mapping_file_version:
    @param json_file_name:
    """

    file_path = get_relative_path(
        f"../data/{mapping_file_version}/{json_file_name}.json"
    )

    delete_file(file_path)


def delete_json_mapping_folder(
    mapping_file_version: str,
):
    """
    Deletes a version folder within the data folder

    @param mapping_file_version:
    """

    folder_path = get_relative_path(f"../data/{mapping_file_version}")
    delete_folder(folder_path)


# endregion
