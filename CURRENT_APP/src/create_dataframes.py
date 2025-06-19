import json

import argparse
import os
import logging
import warnings
from src.conf import *
from src.utils import create_dataframes, data_merger

import warnings

from pandas.errors import SettingWithCopyWarning

warnings.simplefilter(action="ignore", category=(SettingWithCopyWarning))


def create_dataframe(
    create_dataframe: str,
    root_dir: str,
    config: dict,
    post_event_process: str = "no",
    include_previous_scan_data: str = "no",
):
    """
    Create Dataframes
    Args:
    create_dataframe: str: Flag to create DataFrame
    root_dir: str: Root Directory
    config: dict: Configuration
    post_event_process: str: Flag to include post event process
    include_previous_scan_data: str: Flag to include previous scan data"""

    path_regdata = os.path.join(root_dir, input_data_folder, regdata)
    path_regdata_refresh = os.path.join(root_dir, input_data_folder, regdata_refresh)
    path_demodata = os.path.join(root_dir, input_data_folder, demodata)
    # path to SCan Data
    path_seminar_reference_24 = os.path.join(
        root_dir, input_data_folder, output_csv_folder, seminar_reference_24
    )
    path_badge_scan_24 = os.path.join(
        root_dir, input_data_folder, output_csv_folder, badge_scan_24
    )
    path_seminar_reference_25 = os.path.join(
        root_dir, input_data_folder, output_csv_folder, seminar_reference_25
    )
    path_badge_scan_25 = os.path.join(
        root_dir, input_data_folder, output_csv_folder, badge_scan_25
    )
    # outputs
    # registration data this year
    path_reg_data_list = os.path.join(
        root_dir, input_data_folder, output_data_folder, registration_data_json
    )
    # Demographic Data with Scan Data
    path_demodata_output = os.path.join(
        root_dir,
        input_data_folder,
        output_data_folder,
        demographic_data_with_badge_json,
    )
    path_demodata_output_full = os.path.join(
        root_dir,
        input_data_folder,
        output_data_folder,
        demographic_data_with_badge_json_full,
    )
    # merger data path
    merged_data_path = os.path.join(
        root_dir, input_data_folder, output_data_folder, merged_data_json
    )
    merged_data_status_path = os.path.join(
        root_dir, input_data_folder, output_data_folder, merged_data_status_json
    )
    merged_data_list_key_path = os.path.join(
        root_dir, input_data_folder, output_data_folder, merged_data_list_key_json
    )
    if str(create_dataframe).lower() == "yes":
        logging.info("Creating Dataframes")
        create_dataframes(
            root=root_dir,
            path_regdata_refresh=path_regdata_refresh,
            path_regdata=path_regdata,
            path_seminar_reference_24=path_seminar_reference_24,
            path_badge_scan_24=path_badge_scan_24,
            path_seminar_reference_25=path_seminar_reference_25,
            path_badge_scan_25=path_badge_scan_25,
            path_reg_data_list=path_reg_data_list,
            path_demodata_output=path_demodata_output,
            path_demodata=path_demodata,
            path_demodata_output_full=path_demodata_output_full,
            post_event_process=post_event_process,
        )

        logging.info("Dataframes created")
    # prepare data for classification
    with open(path_demodata_output, "r") as f:
        demographic_data_badge = json.load(f)
    with open(path_reg_data_list, "r") as f:
        registration_data = json.load(f)
    logging.info("Data loaded")
    logging.info(
        "Length of the demographic data: {}".format(len(demographic_data_badge))
    )
    logging.info("Length of the registration data: {}".format(len(registration_data)))
    # Merge the data
    merged_data, merged_data_status, merged_data_list_key = data_merger(
        registration_data,
        demographic_data_badge,
        year=last_year,
        post_event_process=post_event_process,
        include_previous_scan_data=include_previous_scan_data,
    )
    list_badge_id = len(merged_data.keys())
    logging.info("Length of the merged data ID,s: {}".format(list_badge_id))

    with open(merged_data_path, "w") as f:
        json.dump(merged_data, f, indent=4)
    with open(merged_data_status_path, "w") as f:
        json.dump(merged_data_status, f, indent=4)
    with open(merged_data_list_key_path, "w") as f:
        json.dump(merged_data_list_key, f, indent=4)


def main(args):
    create_dataframe(create_dataframe=args.create_dataframe)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Input DaTa HPI.")
    parser.add_argument(
        "--create_dataframe", type=str, default="no", help="Flag to create DataFrame"
    )

    # ROOT = os.path.dirname(os.path.abspath(__file__))
    # ### Create folders
    # os.makedirs(input_data_folder, exist_ok=True)
    # os.makedirs(output_csv_folder, exist_ok=True)
    # os.makedirs(output_data_folder, exist_ok=True)
    # main(args=parser.parse_args())
