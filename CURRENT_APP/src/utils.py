import pandas as pd
import json
from pandas import json_normalize
from .conf import *
import sys
import traceback
import logging
import os
import copy
import string
import logging
from typing import List


def remove_punctuation(text):
    custom_punctuation = string.punctuation + "‘’“”…"
    return text.translate(str.maketrans("", "", custom_punctuation))


def print_stack():
    """
    catch stack after exception
    """
    # cath exception with sys and return the error stack
    ex_type, ex_value, ex_traceback = sys.exc_info()
    # Extract unformatter stack traces as tuples
    trace_back = traceback.extract_tb(ex_traceback)
    # Format stacktrace
    stack_trace = list()
    for trace in trace_back:
        stack_trace.append(
            "File : %s , Line : %d, Func.Name : %s, Message : %s"
            % (trace[0], trace[1], trace[2], trace[3])
        )
    error = ex_type.__name__ + "\n" + str(ex_value) + "\n"
    for err in stack_trace:
        error = error + str(err) + "\n"

    return error


def return_domain(x):
    return x.split("@")[-1]


def calculate_date_difference(df, date_column, given_date_str):
    """
    Calculate the difference in days between the given date and the date in the column
    ARgs:
        df: Pandas Dataframe
        date_column: Column with the Registration Date
        given_date_str: Given date in string format
    """
    # Convert the column to datetime
    # Convert the column to datetime format and handle errors
    df[date_column] = df[date_column].astype(str)
    df[date_column] = df[date_column].str[:10]
    df[date_column] = pd.to_datetime(df[date_column])

    # Convert the given date to datetime
    given_date = pd.to_datetime(given_date_str)

    # Calculate the difference in days
    df["Days_since_registration"] = (given_date - df[date_column]).dt.days

    return df


def remove_nan_columns(df, columns):
    """
    Remove the columns from the dataframe when Nan
    """
    df_cleaned = df.dropna(subset=columns)
    return df_cleaned


def open_regdata(path_regdata):
    """
    Open the registration data file and return the dataframe
    """
    with open(path_regdata, "r") as f:
        regdata = json.load(f)

    df = json_normalize(regdata)
    return df


def concatenate_qa_registration_data(
    df_registration, list_badge_id_events, additional_columns_to_exclude=["Email"]
):
    """
    Concatenate Registration Values of a Particpant"
    Args:
        df_registration : Pandas Dataframe with values of Participants
        list_badge_id_events : List with all BadgeId from which we have Geographic Data. Answer to the questionarie
    """

    def create_string_from_dict(data):
        keys_to_exclude = ["ShowRef", "BadgeId"] + additional_columns_to_exclude
        result = []

        for key, value in data.items():
            if key not in keys_to_exclude:
                if value is not None:
                    result.append(f"{key}: {value}")
                else:
                    result.append(f"{key}: no_data")

        return ", ".join(result)

    reg_data_list = []
    for badge_ID, i in zip(list_badge_id_events, range(len(list_badge_id_events))):
        df = df_registration[df_registration["BadgeId"] == badge_ID]
        df_d = json.loads(df.to_json(orient="records"))
        reg_data = {}
        for row in df_d:
            ID = "_".join([row.get("ShowRef"), row.get("BadgeId")])
            reg_data[ID] = create_string_from_dict(row)
        reg_data_list.append(reg_data)

    return reg_data_list


def concatenate_showref_badgeid(row):
    """
    Concatenate ShowRef and BadgeId
    """
    return "_".join([row["ShowRef"], row["BadgeId"]])


def list_emails_2_years(df_reg_24, df_reg_25):
    """
    List of emails that registered in both years
    """
    # list of emails
    email_24_list = list(df_reg_24["Email"].unique())
    email_25_list = list(df_reg_25["Email"].unique())
    # emails that registered in both years
    email_24_25 = set(email_25_list).intersection(set(email_24_list))
    # Vistors that registered in both years
    dfreg_24_25 = df_reg_25[df_reg_25["Email"].isin(email_24_25)]
    # Merge the data
    dfreg_24_25 = pd.merge(
        dfreg_24_25, df_reg_24[["Email", "ShowRef", "BadgeId"]], on="Email", how="inner"
    )
    return dfreg_24_25


def create_scan_data_repiting_visitors(
    scans_data_24_25_enriched, dfreg_24_25_good_badge_id
):
    """
    Create a Dataframe with visitor that repited in 2025 and 2024 and have a badge in List badgeIDs_list
    use the Scan data and create a column with the concatenated Seminar Names for thos visitors that scanned their badge ina Stand
    Args:
        scans_data_24_25_enriched: Dataframe with the scan data of the visitors that repited in 2025 and 2024
        dfreg_24_25_good_badge_id: Dataframe with the visitors that repited in 2025 and 2024 and have a badge in List badgeIDs_list
    """

    grouped_df = (
        scans_data_24_25_enriched.groupby("Badge Id")["Seminar Name"]
        .apply(", ".join)
        .reset_index()
    )

    # Rename the columns
    grouped_df.columns = ["Badge Id", "Concatenated Seminar Names"]

    # Merging the DataFrames on 'BadgeId_y' and 'Badge Id'
    merged_df = pd.merge(
        dfreg_24_25_good_badge_id,
        grouped_df,
        left_on="BadgeId_y",
        right_on="Badge Id",
        how="left",
    )

    # Dropping the redundant 'Badge Id' column if needed
    merged_df = merged_df.drop(columns=["Badge Id"])

    merged_df = merged_df[initial_columns_merge_visitor]

    merged_df.columns = columns_merge_visitor_24_25
    merged_df = merged_df[columns_merge_visitor_24_25_final]
    return merged_df


def concatenate_qa_demografic_data_old(
    df_demografic, list_badge_id_events, list_no, list_vip, key_questions_demographic
):
    """
    Concatenate Questions and Answers of a Particpant"
    Args:
        df_demografic : Pandas Dataframe with values of Participants
        list_badge_id_events : List with all BadgeId from which we have Geographic Data. Answer to the questionarie
        list_no : List of questions that should be excluded
        list_vip : List of questions that are key
        key_questions_demographic : List of key questions which decide if to include the data in the LLM classification
    """
    demo_data = []
    demo_data_full = []
    for badge_ID, i in zip(list_badge_id_events, range(len(list_badge_id_events))):
        df = df_demografic[df_demografic["BadgeId"] == badge_ID]
        df_d = json.loads(df.to_json(orient="records"))
        list_vipq, list_noq, list_noq_text, list_key = [], [], [], []
        qa, qai = {}, {}
        OLD_ID = "_".join([df_d[0].get("showref"), df_d[0].get("BadgeId")])
        qa[OLD_ID] = ""
        qai[OLD_ID] = ""
        for row in df_d:
            ID = "_".join([row.get("showref"), row.get("BadgeId")])

            if row.get("QuestionText") == None or row.get("AnswerText") == None:
                logging.warning(
                    f"Issue with records ID {ID} NO ANSWER/QUESTION, row {i}, length dataframe: {len(df)}"
                )
                continue

            question = row.get("QuestionText").strip()
            answer = str(row.get("AnswerText")).strip()
            if question in list_no:
                list_noq.append(f"Question: {question} not included")
                list_noq_text.append(f"Question: {question} Answer: {answer}")
                continue
            # Questions to be consider in the LLM classifications
            if question in key_questions_demographic:
                list_key.append(f"Question: {question} is Key")

            if ID == OLD_ID:
                qa_row = " : ".join([question, answer])
                if question in list_vip:
                    list_vipq.append(f"Question: {question} is VIP")
                    qai[ID] = " , ".join([qai[ID], qa_row])
                else:
                    qa[ID] = " , ".join([qa[ID], qa_row])
            else:
                logging.warning("check_case")
                if question in list_vip:
                    qai[ID] = " , ".join([qai[ID], qa_row])
                else:
                    qa[ID] = " , ".join([qa[ID], qa_row])
                OLD_ID = ID
        # remove Initial padding
        qai[ID] = qai[ID][3:]
        qa[ID] = qa[ID][3:]
        # build final dictionary
        final = {}
        final[ID] = {}
        final[ID]["vip"] = qai[ID]
        final[ID]["normal"] = qa[ID]
        if len(list_key) >= 6:
            final[ID]["pre-classification"] = "Enought_data"
        else:
            final[ID]["pre-classification"] = "Not_enought_data"

        final_full = copy.deepcopy(final)
        final_full[ID]["exclude"] = list_noq_text

        # if len(list_vipq) !=2 :
        #     logging.warning(f"Issue with records ID {ID} , row {i}, length dataframe: {len(df)}")
        demo_data.append(final)
        demo_data_full.append(final_full)
        if i % 1000 == 0:
            logging.info(f"Proccesed {i} records")
    return demo_data, demo_data_full


def concatenate_qa_demografic_data(
    df_demografic,
    list_badge_id_events,
    list_no,
    list_vip,
    key_questions_demographic,
    questions_backup: str = "your main areas of interest",
    padding: int = 3,
    num_questions: int = 6,
):
    """
    Concatenate Questions and Answers of a Participant
    Args:
        df_demografic : Pandas Dataframe with values of Participants
        list_badge_id_events : List with all BadgeId from which we have Geographic Data. Answer to the questionnaire
        list_no : List of questions that should be excluded
        list_vip : List of questions that are key
        key_questions_demographic : List of key questions which decide if to include the data in the LLM classification
        questions_backup : List of questions we need to carry over to full list for latest review
        padding : remove this chars from begining of Question. Need it in HPI
        num_questions : number of questions to be asked
    """
    demo_data = []
    demo_data_full = []

    for i, badge_ID in enumerate(list_badge_id_events):
        df = df_demografic[df_demografic["BadgeId"] == badge_ID]
        df_d = json.loads(df.to_json(orient="records"))

        qa = {badge_ID: {"vip": "", "normal": ""}}
        list_noq_text, list_key = [], []
        # ANswer to the question "your main areas of interest"
        answer_backup = "NA"
        for row in df_d:
            ID = "_".join([row.get("showref"), row.get("BadgeId")])

            question = row.get("QuestionText")
            answer = row.get("AnswerText")

            if not question or not answer:
                logging.warning(
                    f"Issue with records ID {ID} NO ANSWER/QUESTION, row {i}, length dataframe: {len(df)}"
                )
                continue
            # get the answer from the backup if the answer is "your main areas of interest":
            if question == questions_backup:
                answer_backup = row.get("AnswerText_backup")

            question = question.strip()
            answer = str(answer).strip()
            qa_row = f"Question: {question} Answer: {answer}"

            if question in list_no:
                list_noq_text.append(qa_row)
                continue

            if question in key_questions_demographic:
                list_key.append(f"Question: {question} is Key")

            target = "vip" if question in list_vip else "normal"
            qa[badge_ID][target] += f" , {qa_row}"

        for key in qa[badge_ID]:
            qa[badge_ID][key] = qa[badge_ID][key][padding:]

        pre_classification = (
            "Enought_data" if len(list_key) >= num_questions else "Not_enought_data"
        )
        qa[badge_ID]["pre-classification"] = pre_classification
        qa[badge_ID]["list_key"] = list_key

        final = {ID: qa[badge_ID]}
        final_full = copy.deepcopy(final)
        final_full[ID]["exclude"] = list_noq_text
        final_full[ID]["main_area_interest_text"] = answer_backup

        demo_data.append(final)
        demo_data_full.append(final_full)

        if i % 1000 == 0:
            logging.info(f"Processed {i} records")

    return demo_data, demo_data_full


def include_scan_Data_demo_data(
    demo_data: List,
    list_badgesid_with_seminars: List,
    merged_df: pd.DataFrame,
    list_badgesid_with_seminars_post_event: List,
    merged_df_post_event: pd.DataFrame,
    post_event_process: str = "no",
):
    """
    Include the Scan Data in the Demografic Data
    Args:

        demo_data: List of dictionaries with the concatenated Questions and Answers
        list_badgesid_with_seminars: List of BadgeId with seminars
        merged_df: Dataframe with the scan data
    """

    for ele in demo_data:
        key = list(ele.keys())[0]
        badge_id = key.split("_")[-1]
        if badge_id in list_badgesid_with_seminars:

            temp = merged_df[merged_df["BadgeId"] == badge_id]
            temp_dict = json.loads(temp.to_json(orient="records"))
            ele[key]["Seminars"] = temp_dict[0].get("Concatenated Seminar Names")
        if post_event_process == "yes":
            if badge_id in list_badgesid_with_seminars_post_event:
                temp = merged_df_post_event[merged_df_post_event["BadgeId"] == badge_id]
                temp_dict = json.loads(temp.to_json(orient="records"))
                ele[key]["Seminars_2025"] = temp_dict[0].get(
                    "Concatenated Seminar Names"
                )

    return demo_data


# def data_merger(
#     registration,
#     demographic,
#     year: str = "2024",
#     post_event_process: str = "no",
#     include_previous_scan_data: str = "no",
# ):
#     """
#     Merge the registration and demographic data
#     Args:
#         registration: List of dictionaries with the registration data
#         demographic: List of dictionaries with the demographic data
#     """
#     merged_data = {}
#     merged_data_status = {}
#     merged_data_list_key = {}
#     for reg, demo in zip(registration, demographic):

#         if len(reg.keys()) == 0:
#             logging.info("empty Dictionary")
#             continue
#         reg_key = list(reg.keys())[0]
#         demo_key = list(demo.keys())[0]
#         if demo_key != reg_key:
#             logging.info(f"key reg {reg_key} doesnt match key demo {demo_key}")
#             continue
#         else:
#             classification_status = demo.get(reg_key).get("pre-classification")
#             list_key = demo.get(reg_key).get("list_key")
#             seminars_key = "Seminars"
#             if seminars_key in list(demo.get(reg_key).keys()):
#                 if demo.get(reg_key).get(seminars_key) == "NA":
#                     txt = "No scan badge in stands"
#                 else:
#                     txt = demo.get(reg_key).get(seminars_key)
#                 texto = " ".join(
#                     [
#                         reg.get(reg_key),
#                         "\nKey Question:",
#                         demo.get(reg_key).get("vip"),
#                         "\nOther Questions:",
#                         demo.get(reg_key).get("normal"),
#                         f"\n Attended seminars in {year}:",
#                         txt,
#                     ]
#                 )
#             else:
#                 texto = " ".join(
#                     [
#                         reg.get(reg_key),
#                         "\nKey Question:",
#                         demo.get(reg_key).get("vip"),
#                         "\nOther Questions:",
#                         demo.get(reg_key).get("normal"),
#                     ]
#                 )
#             merged_data[reg_key] = texto
#             merged_data_status[reg_key] = classification_status
#             merged_data_list_key[reg_key] = list_key

#     return merged_data, merged_data_status, merged_data_list_key


def data_merger(
    registration,
    demographic,
    year: str = "2024",
    post_event_process: str = "no",
    include_previous_scan_data: str = "no",
):
    """
    Merge the registration and demographic data
    Args:
        registration: List of dictionaries with the registration data
        demographic: List of dictionaries with the demographic data
    """
    merged_data = {}
    merged_data_status = {}
    merged_data_list_key = {}
    for reg, demo in zip(registration, demographic):

        if len(reg.keys()) == 0:
            logging.info("empty Dictionary")
            continue
        reg_key = list(reg.keys())[0]
        demo_key = list(demo.keys())[0]
        if demo_key != reg_key:
            logging.info(f"key reg {reg_key} doesnt match key demo {demo_key}")
            continue
        else:
            classification_status = demo.get(reg_key).get("pre-classification")
            list_key = demo.get(reg_key).get("list_key")

            # Determine seminars_key based on rules
            if post_event_process == "no":
                seminars_key = "Seminars"
            elif post_event_process == "yes" and include_previous_scan_data == "no":
                seminars_key = "Seminars_2025"
            elif post_event_process == "yes" and include_previous_scan_data == "yes":
                # Concatenate "Seminars" and "Seminars_2025" data if available
                seminars_key = None  # Will handle concatenation logic below

            # Populate texto based on rules and keys
            if (
                seminars_key is None
            ):  # Concatenate logic for include_previous_scan_data == "yes"
                txt_current = demo.get(reg_key).get("Seminars", "NA")
                txt_next_year = demo.get(reg_key).get("Seminars_2025", "NA")
                txt_list = []
                if txt_current != "NA":
                    txt_list.append(txt_current)
                if txt_next_year != "NA":
                    txt_list.append(txt_next_year)
                txt = " | ".join(txt_list) if txt_list else "No scan badge in stands"
            elif seminars_key in list(demo.get(reg_key).keys()):
                if demo.get(reg_key).get(seminars_key) == "NA":
                    txt = "No scan badge in stands"
                else:
                    txt = demo.get(reg_key).get(seminars_key)
            else:
                txt = "No scan badge in stands"

            # Create texto variable
            texto = " ".join(
                [
                    reg.get(reg_key),
                    "\nKey Question:",
                    demo.get(reg_key).get("vip"),
                    "\nOther Questions:",
                    demo.get(reg_key).get("normal"),
                    f"\n Attended seminars in {year}:",
                    txt,
                ]
            )

            merged_data[reg_key] = texto
            merged_data_status[reg_key] = classification_status
            merged_data_list_key[reg_key] = list_key

    return merged_data, merged_data_status, merged_data_list_key


def modify_demographic_data(df):
    """
    Modify the demographic data
    Args:
        df: Pandas Dataframe with the demographic data
    """
    df["QuestionText"] = df["QuestionText"].str.replace("/", " ")
    df["QuestionText"] = df["QuestionText"].str.lower()
    df["QuestionText"] = df["QuestionText"].apply(remove_punctuation)
    df["QuestionText"] = df["QuestionText"].str.strip()
    return df


def count_areas_interest(row):
    """
    Count the number of areas of interest
    Args:
        row: Pandas Series"""

    if row["QuestionText"] == "your main areas of interest":
        return len(row["AnswerText"].split(";"))
    else:
        return row["AnswerText"]


def create_dataframes_post_event(
    reference_data_post: pd.DataFrame,
    scan_data_post: pd.DataFrame,
    registration_data: pd.DataFrame,
):
    """
    Create Dataframes  Registration and Scan Data  Post Event
    Args:
        reference_data_post: Dataframe with the seminars reference data
        scan_data_post: Dataframe with the scan data
        registration_data: Dataframe with the registration data
    """

    list_badgeid_post_event = list(registration_data["BadgeId"].unique())

    scans_data_post_event_valid_id = scan_data_post[
        scan_data_post["Badge Id"].isin(list_badgeid_post_event)
    ]
    logging.info(
        f"Number of Visitors in 2025 that have a badge scan: {scans_data_post_event_valid_id.shape[0]}"
    )
    # merge registration with scan data
    scans_data_post_event_enriched = pd.merge(
        scans_data_post_event_valid_id[["Short Name", "Badge Id"]],
        reference_data_post[["Short Name", "Seminar Name"]],
        on=["Short Name"],
        how="inner",
    )

    # Group by 'Badge Id' and concatenate 'Seminar Name'
    grouped_df = (
        scans_data_post_event_enriched.groupby("Badge Id")["Seminar Name"]
        .apply(", ".join)
        .reset_index()
    )

    # Rename the columns
    grouped_df.columns = ["Badge Id", "Concatenated Seminar Names"]
    # Merging the DataFrames on 'BadgeId' and 'Badge Id' to add Post Event Scan Data to the Registration Data
    merged_df = pd.merge(
        registration_data,
        grouped_df,
        left_on="BadgeId",
        right_on="Badge Id",
        how="left",
    )
    # Dropping the redundant 'Badge Id' column if needed
    merged_df = merged_df.drop(columns=["Badge Id"])
    # Selecting the columns to keep
    merged_df = merged_df[["Email", "ShowRef", "BadgeId", "Concatenated Seminar Names"]]
    return merged_df


def create_dataframes(
    root,
    path_regdata_refresh,
    path_regdata,
    path_seminar_reference_24,
    path_badge_scan_24,
    path_seminar_reference_25,
    path_badge_scan_25,
    path_reg_data_list,
    path_demodata_output,
    path_demodata,
    path_demodata_output_full,
    post_event_process,
):
    """
    Create Dataframes Demographic , Registration and Scan Data  for Visitors in 2025 that were in 2024
    Args:
        root: Path to the root folder
        path_regdata_refresh: Path to the registration data file
        path_regdata: Path to the registration data file
        path_seminar_reference_24: Path to the seminars reference file
        path_badge_scan_24: Path to the seminars reference file
        path_seminar_reference_25: Path to the seminars reference file
        path_badge_scan_25: Path to the seminars reference file
        path_reg_data_list: Path to the output file with the registration data
        path_demodata_output: Path to the output file with the demographic data
        path_demodata: Path to the demographic data file
        path_demodata_output_full: Path to the output file with the demographic data
        post_event_process: How to manage the scan visitor data post event. no not include the data in the LLM classification , yes include the data in the LLM classification
    """
    logging.info("Creating Registration Data for Visitors in 2025 and Vistors in 2024")
    # Open the registration data file and return the dataframe
    df = open_regdata(path_regdata_refresh)
    logging.info(
        f"Open Registration Data {path_regdata}. Number of rows: {df.shape[0]}"
    )
    # Remove the columns from the dataframe when Nan
    df = remove_nan_columns(df, reg_data_nan_columns)

    # Calculate the difference in days
    result_df = calculate_date_difference(df, date_column, given_date_str)
    logging.info(f"length of the result_df: {result_df.shape[0]}")
    # Data 2024
    df_all = open_regdata(path_regdata)
    df_reg_24 = df_all[df_all.ShowRef.isin(shows_24)]
    logging.info(f"Registration Data 2024. Number of rows: {df_reg_24.shape[0]}")
    # Data 2025
    df_reg_25 = result_df[result_df["ShowRef"].isin(shows_25)]
    # save list of all registrant this year
    df_reg_25.to_csv(
        os.path.join(root, input_data_folder, "csv", f"{registration_this_year}"),
        index=False,
    )

    logging.info(f"Registration Data 2025. Number of rows: {df_reg_25.shape[0]}")

    # Visitor in 2025 that are were in 2024
    dfreg_24_25 = list_emails_2_years(df_reg_24, df_reg_25)
    logging.info(f"Number of Visitors in 2025 that were in 2024: {len(dfreg_24_25)}")

    #   Save the data to csv

    df_reg_25["Email"] = df_reg_25["Email"].apply(return_domain)
    # Save Full Registration Data for later evaluation
    path_output_regdata_full = os.path.join(
        root, input_data_folder, output_csv_folder, registration_2025_full
    )
    df_reg_25["profile_id"] = df_reg_25.apply(
        lambda row: concatenate_showref_badgeid(row), axis=1
    )
    df_reg_25.to_csv(path_output_regdata_full, index=False)
    df_reg_25 = df_reg_25[valid_columns]

    # save the data to csv
    path_output_regdata = os.path.join(
        root, input_data_folder, output_csv_folder, registration_2025
    )
    df_reg_25.to_csv(path_output_regdata, index=False)

    ### Badge Data ############################
    logging.info(
        "Creating Badge Data for Visitors in 2025 that were in 2024 and scan a badge in a Stand"
    )
    # Visitor in 2025 that are were in 2024 and have a badge in List badgeIDs_list
    dfreg_24_25_good_badge_id = dfreg_24_25[
        dfreg_24_25["BadgeType"].isin(badgeIDs_list)
    ]
    # Read scan Data
    reference_data_24 = pd.read_csv(path_seminar_reference_24)
    scans_data_24 = pd.read_csv(path_badge_scan_24)
    # Create a list of BadgeID of those Visitor which are registered to both events
    list_badges_24_25 = list(dfreg_24_25_good_badge_id["BadgeId_y"].unique())
    logging.info(
        f"Number of Visitors in 2025 that were in 2024 and have a badge in List badgeIDs_list: {len(list_badges_24_25)}"
    )

    # Common Sessions Sessions That appear in both files

    badge_scan_list = set(list(scans_data_24["Badge Id"].unique())).intersection(
        set(list_badges_24_25)
    )
    logging.info(
        f"Number of Visitors in 2025 that were in 2024 and have a badge in List badgeIDs_list and have a badge scan: {len(badge_scan_list)}"
    )

    # Extract activity in 2024 of Visitors which are registered in both years
    scans_data_24_25 = scans_data_24[scans_data_24["Badge Id"].isin(badge_scan_list)]
    logging.info(
        f"Number of Visitors in 2025 that were in 2024 and have a badge in List badgeIDs_list and have a badge scan: {scans_data_24_25.shape[0]}"
    )
    # Enrich the data with the Seminar Name
    scans_data_24_25_enriched = pd.merge(
        scans_data_24_25[["Short Name", "Badge Id"]],
        reference_data_24[["Short Name", "Seminar Name"]],
        on=["Short Name"],
        how="inner",
    )

    #   Save the data to csv
    path_output_scans_data_24_25_enriched = os.path.join(
        root, input_data_folder, output_csv_folder, scans_data_24_25_enriched_csv
    )
    scans_data_24_25_enriched.to_csv(path_output_scans_data_24_25_enriched, index=False)

    merged_df = create_scan_data_repiting_visitors(
        scans_data_24_25_enriched, dfreg_24_25_good_badge_id
    )
    path_output_visitors_24_25_with_scan_data = os.path.join(
        root,
        input_data_folder,
        output_csv_folder,
        Registration_data_24_25_both_only_valid_badge_type_with_seminars,
    )
    merged_df.to_csv(path_output_visitors_24_25_with_scan_data, index=False)

    ### DEMOGRAPHIC DATA ############################
    logging.info(
        "Creating Demographic Data for Visitors in 2025 that were in 2024 and scan a badge in a Stand"
    )
    # Open Demographic Data

    df2 = open_regdata(path_demodata)
    # remove puctuation and convert lower
    df2 = modify_demographic_data(df2)
    # Count the number of areas of interest
    df2["AnswerText_backup"] = df2["AnswerText"].astype(str)
    df2["AnswerText"] = df2.apply(lambda row: count_areas_interest(row), axis=1)

    logging.info(
        f"Open Demographic Data {path_demodata}. Number of rows: {df2.shape[0]}"
    )
    df_demo_25 = df2[df2["showref"].isin(shows_25)]
    logging.info(f"Demographic Data 2025. Number of rows: {df_demo_25.shape[0]}")
    # save the data to csv
    path_output_demographic = os.path.join(
        root, input_data_folder, output_csv_folder, demographic_2025
    )
    df_demo_25.to_csv(path_output_demographic, index=False)
    # List of BadgeId
    demo_badge_id_25 = list(df_demo_25["BadgeId"].unique())

    reg_data_list = concatenate_qa_registration_data(
        df_reg_25,
        demo_badge_id_25,
        additional_columns_to_exclude=additional_columns_to_exclude,
    )

    with open(path_reg_data_list, "w") as f:
        json.dump(reg_data_list, f, indent=4)

    ### Concatenate Data ########################################
    logging.info("Concatenate Registration Data, Demographic Data and Scan Data")
    demo_data, demo_data_full = concatenate_qa_demografic_data(
        df_demo_25, demo_badge_id_25, list_no, list_vip, key_questions_demographic
    )
    logging.info(f"Lenght of the list of concatenated data: {len(demo_data)}")
    # fill the Nans in Scan Data
    merged_df = merged_df.fillna("NA")
    # List of BadgeId with seminars
    list_badgesid_with_seminars = list(merged_df["BadgeId"].unique())

    if post_event_process == "yes":
        logging.info("Post event process")
        # Read scan Data
        reference_data_25 = pd.read_csv(path_seminar_reference_25)
        scans_data_25 = pd.read_csv(path_badge_scan_25)
        #  REsgistration Data with Visitor id,s that are in the list badgeIDs_list
        df_reg_25_valid_id = df_reg_25[df_reg_25["BadgeType"].isin(badgeIDs_list)]
        merged_df_post_event = create_dataframes_post_event(
            reference_data_post=reference_data_25,
            scan_data_post=scans_data_25,
            registration_data=df_reg_25_valid_id,
        )
        # save to disk
        path_output_visitors_post_event_with_scan_data = os.path.join(
            root,
            input_data_folder,
            output_csv_folder,
            Registration_data_post_event_only_valid_badge_type_with_seminars,
        )
        merged_df_post_event.to_csv(
            path_output_visitors_post_event_with_scan_data, index=False
        )
        # fill the Nans in Scan Data
        merged_df_post_event = merged_df_post_event.fillna("NA")
        # List of BadgeId with seminars
        list_badgesid_with_seminars_post_event = list(
            merged_df_post_event["BadgeId"].unique()
        )

    # Include the Scan Data in the Demographic Data
    demo_data_final = include_scan_Data_demo_data(
        demo_data=demo_data,
        list_badgesid_with_seminars=list_badgesid_with_seminars,
        merged_df=merged_df,
        list_badgesid_with_seminars_post_event=list_badgesid_with_seminars_post_event,
        merged_df_post_event=merged_df_post_event,
        post_event_process=post_event_process,
    )
    # Dataframe Input to Model
    with open(path_demodata_output, "w") as f:
        json.dump(demo_data_final, f, indent=4)
    # Dataframe Full
    with open(path_demodata_output_full, "w") as f:
        json.dump(demo_data_full, f, indent=4)

    return
