import pandas as pd
import json
import argparse
import yaml
import os
from conf import *


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def concatenate_showref_badgeid(row):
    """
    Concatenate ShowRef and BadgeId
    """
    return "_".join([row["ShowRef"], row["BadgeId"]])


def get_dict_content(demodata, key):
    for data_dict in demodata:
        if key in data_dict:
            return data_dict[key]
    return None


def get_registration_data(regdata, key):
    return regdata[regdata["profile_id"] == key]


def transform_inference_file(
    root_dir: str,
    config: dict,
    model: str = "llama3.1:latest",
    timestamp_str: str = None,
    post_event_process: str = "no",
    include_previous_scan_data: str = "no",
):
    """
    Transform Inference File
    Args:
    root_dir: str: Root Directory
    config: dict: Configuration
    model: str: Model
    timestamp_str: str: Timestamp
    post_event_process: str: Flag to include post event process
    include_previous_scan_data: str: Flag to include previous scan data"""

    # output model
    model = model.split(":")[0]
    model = model.replace(".", "_")

    root_filename = f"{model}_{post_event_process}_{include_previous_scan_data}_{timestamp_str}.json"
    filename = os.path.join(
        root_dir,
        input_data_folder,
        classification_data_folder,
        root_filename,
    )
    # demo data with exclude
    path_demodata_output_full = os.path.join(
        root_dir,
        input_data_folder,
        output_data_folder,
        demographic_data_with_badge_json_full,
    )
    # registration data before remove exclude columns
    path_output_regdata_full = os.path.join(
        root_dir, input_data_folder, output_csv_folder, registration_2025_full
    )
    # registration data RAW after transform from json
    path_output_regdata = os.path.join(
        root_dir, input_data_folder, output_csv_folder, registration_this_year
    )

    # OPEN FILES
    # Registration data
    with open(path_demodata_output_full, "r") as f:
        demodata = json.load(f)
    regdata_full = pd.read_csv(path_output_regdata_full)

    # registration data raw
    df_reg_25 = pd.read_csv(path_output_regdata)
    # create profile_id
    df_reg_25["profile_id"] = df_reg_25.apply(
        lambda row: concatenate_showref_badgeid(row), axis=1
    )

    with open(filename, "r") as f:
        regdata = json.load(f)
    columns = [
        "ShowRef",
        "BadgeId",
        "category",
        "certainty",
        "ranked_categories",
        "forename",
        "surname",
        "email",
        "company",
        "jobtitle",
        "tel",
        "mobile",
        "postcode",
        "country",
        "main_area_interest_text",
        "exclude_questions",
        "input",
    ]
    dfs = []

    # Create a CSV file for evaluation with the output of the model and some additional information (excluded from input datafra,e)
    for ele, i in zip(regdata, range(len(regdata))):
        profile_id = ele.get("profile_id")
        try:
            demodata_profile = get_dict_content(demodata, profile_id)
            # extract exclude_questions
            if demodata_profile is not None and "exclude" in demodata_profile.keys():
                exclude_questions = demodata_profile["exclude"]
                exclude_questions = " ; ".join(exclude_questions)

            else:
                exclude_questions = None
            # extract main_area_interest_text
            if (
                demodata_profile is not None
                and "main_area_interest_text" in demodata_profile.keys()
            ):
                main_area_interest_text = demodata_profile["main_area_interest_text"]
            else:
                main_area_interest_text = None

            regdata_profile = get_registration_data(regdata_full, profile_id)
            regdata_profile_raw = get_registration_data(df_reg_25, profile_id)

            (
                email,
                company,
                jobtitle,
                tel,
                mobile,
                postcode,
                country,
                forename,
                surname,
            ) = (
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            )
            # get original Values
            if len(regdata_profile_raw) == 1:
                email = regdata_profile_raw["Email"].values[0]
            if len(regdata_profile) == 1:

                company = regdata_profile["Company"].values[0]
                jobtitle = regdata_profile["JobTitle"].values[0]
                tel = regdata_profile["Tel"].values[0]
                mobile = regdata_profile["Mobile"].values[0]
                postcode = regdata_profile["Postcode"].values[0]
                country = regdata_profile["Country"].values[0]
                forename = regdata_profile["Forename"].values[0]
                surname = regdata_profile["Surname"].values[0]
            ShowRef = profile_id.split("_")[0].strip()
            BadgeId = profile_id.split("_")[1].strip()
            input_data = ele["input"]
            response = ele.get("response")
            # build the output
            if response == "Not_enought_data":
                category = "Not_enought_data"
                ranked_categories = "NA"
                certainty = "NA"

            else:
                output = json.loads(ele.get("response"))
                category = output.get("category")
                ranked_categories = output.get("ranked_categories")
                certainty = output.get("certainty")

            temp = pd.DataFrame(
                data=[
                    [
                        ShowRef,
                        BadgeId,
                        category,
                        certainty,
                        ranked_categories,
                        email,
                        forename,
                        surname,
                        company,
                        jobtitle,
                        tel,
                        mobile,
                        postcode,
                        country,
                        main_area_interest_text,
                        exclude_questions,
                        input_data,
                    ]
                ],
                columns=columns,
            )
            dfs.append(temp)
            if i % 500 == 0:
                print(f"Processed {i} records")

        except Exception as e:

            print(f"Profile {profile_id} error {e}")

    df = pd.concat(dfs, ignore_index=True)
    root_filename = root_filename.split(".json")[0]
    root_filename = root_filename.strip()
    filename = os.path.join(
        root_dir, input_data_folder, classification_data_folder, f"{root_filename}.csv"
    )
    df.to_csv(filename, index=False)


def main():
    parser = argparse.ArgumentParser(description="Transform Inference File")

    # Define the command-line arguments
    parser.add_argument("--root_dir", type=str, required=True, help="Root Directory")
    parser.add_argument(
        "--config", type=str, required=True, help="Path to Configuration YAML File"
    )
    parser.add_argument(
        "--model", type=str, default="llama3.1:latest", help="Model to Use"
    )
    parser.add_argument(
        "--timestamp_str", type=str, required=False, help="Timestamp String"
    )
    parser.add_argument(
        "--post_event_process",
        type=str,
        choices=["yes", "no"],
        default="no",
        help="Flag to include post event process",
    )
    parser.add_argument(
        "--include_previous_scan_data",
        type=str,
        choices=["yes", "no"],
        default="no",
        help="Flag to include previous scan data",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Load the YAML configuration file
    try:
        with open(args.config, "r") as config_file:
            config = yaml.safe_load(config_file)
    except FileNotFoundError:
        print(f"Configuration file {args.config} not found.")
        return
    except yaml.YAMLError as exc:
        print(f"Error parsing the YAML file: {exc}")
        return

    # Call the function
    transform_inference_file(
        root_dir=args.root_dir,
        config=config,
        model=args.model,
        timestamp_str=args.timestamp_str,
        post_event_process=args.post_event_process,
        include_previous_scan_data=args.include_previous_scan_data,
    )


if __name__ == "__main__":
    main()
