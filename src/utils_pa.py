import pandas as pd
import json
import warnings
from pandas.errors import SettingWithCopyWarning
from datetime import datetime
import string
import logging

warnings.simplefilter(action="ignore", category=(SettingWithCopyWarning))


def calculate_date_difference(df, date_column, given_date_str):
    """
    Calculate the difference in days between a given date and the dates in a specified column of a DataFrame.
    Args:
        df (pd.DataFrame): The DataFrame containing the date column.
        date_column (str): The name of the column containing dates.
        given_date_str (str): The date in 'YYYY-MM-DD' format to compare against.
    Returns:
        pd.DataFrame: The DataFrame with an additional column 'Days_since_registration' indicating the difference in days.
    """
    # Convert the column to datetime
    df[date_column] = pd.to_datetime(df[date_column])

    # Convert the given date to datetime
    given_date = datetime.strptime(given_date_str, "%Y-%m-%d")

    # Calculate the difference in days
    df["Days_since_registration"] = (given_date - df[date_column]).dt.days

    return df


def concat_forename_email(row):
    """
    Concatenate the forename, surname, and email of a row into a single string.
    Args:
        row (pd.Series): A row of the DataFrame.
    Returns:
        str: A concatenated string of forename, surname, and email in lowercase.
    """
    return (
        row["Forename"].lower()
        + "_"
        + row["Surname"].lower()
        + "_"
        + row["Email"].lower()
    )


def return_domain(x):
    """
    Extract the domain from an email address.
    Args:
        x (str): The email address.
    Returns:
        str: The domain part of the email address.
    """
    return x.split("@")[-1]


def assits_year_before(x, list_email):
    """
    Check if the email address exists in a list of emails.
    Args:
        x (pd.Series): A row of the DataFrame.
        list_email (List[str]): A list of email addresses.
    Returns:
        int: 1 if the email address exists in the list, otherwise 0.
    """
    if x["id_both_years"] in list_email:
        return 1
    else:
        return 0


def remove_punctuation(text):
    """Removes punctuation from a string, excluding hyphens."""
    custom_punctuation = (
        string.punctuation.replace("-", "").replace("/", "") + "‘’“”…" + "â€™Â"
    )
    return text.translate(str.maketrans("", "", custom_punctuation))


def concatenate_qa_registration_data(df_registration, list_badge_id_events):
    """
    Concatenate Registration Values of a Particpant"
    Args:
        df_registration : Pandas Dataframe with values of Participants
        list_badge_id_events : List with all BadgeId from which we have Geographic Data. Answer to the questionarie
    """

    def create_string_from_dict(data):
        keys_to_exclude = ["ShowRef", "BadgeId"]
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


def concatenate_qa_demografic_data_pa(df_demografic, list_badge_id_events, list_keep):
    """
    Concatenate Questions and Answers of a Participant
    Args:
        df_demografic : Pandas Dataframe with values of Participants
        list_badge_id_events : List with all BadgeId from which we have Geographic Data. Answer to the questionnaire
        list_keep : List of questions that should be keept
    """
    demo_data = []

    for i, badge_ID in enumerate(list_badge_id_events):
        df = df_demografic[df_demografic["BadgeId"] == badge_ID]
        df_d = json.loads(df.to_json(orient="records"))
        qa = {badge_ID: {}}
        for row in df_d:

            question = row.get("QuestionText")
            answer = row.get("AnswerText")

            if not question or not answer:
                logging.warning(
                    f"Issue with records ID {badge_ID} NO ANSWER/QUESTION, row {i}, length dataframe: {len(df)}"
                )
                continue
            if question in list_keep:
                qq = question.lower().replace(" ", "_")
                qa[badge_ID][qq] = answer
        if len(qa[badge_ID].keys()) > 0:
            demo_data.append(qa)
        else:
            logging.warning(f"No demo data for {badge_ID}")
    return demo_data


def create_col_placeholders(df, list_to_keep):
    """
    Create new columns in the DataFrame for demographic data.
    Args:
        df (pd.DataFrame): The DataFrame containing the registration data.
        list_to_keep (List[str]): List of questions that should be kept.
    Returns:
        pd.DataFrame: The DataFrame with new columns for demographic data.
    1. Create new columns in the DataFrame for demographic data.
    2. Initialize these columns with "NA".
    3. Return the modified DataFrame.
    """

    for col in list_to_keep:
        qq = col.lower().replace(" ", "_")
        df[qq] = "NA"
    return df


def create_democols_in_registration_data(df, demo_data, list_keep):
    """
    Populate columns demo data with its values
    Args:
        df (pd.DataFrame): The DataFrame containing the registration data.
        demo_data (List[Dict]): List of dictionaries containing demographic data.
        list_keep (List[str]): List of questions that should be kept.
    Returns:
        pd.DataFrame: The DataFrame with new columns populated with demographic data.
    1. Create new columns in the DataFrame for demographic data.
    2. Populate these columns with values from the demographic data.
    3. Return the modified DataFrame.
    """
    # create new columns
    df = create_col_placeholders(df, list_keep)
    # populate with demo data
    for reg in demo_data:
        badgeid = list(reg.keys())[0]
        list_keys_this_reg = list(reg[badgeid].keys())
        for col in list_keys_this_reg:
            df.loc[df["BadgeId"] == badgeid, col] = reg[badgeid][col]
    return df


def generate_streams(streams, list_streams):
    """
    Generate a set of unique streams from a list of strings.
    Args:
        streams (set): A set to store unique stream names.
        list_streams (List[str]): A list of strings containing stream names.
    Returns:
        set: A set of unique stream names.
    1. Iterate through each string in the list.
    2. Split the string by semicolons.
    3. Convert each substring to lowercase and strip whitespace.
    4. Add the cleaned stream name to the set.
    5. Return the set of unique stream names.
    """
    for ele in list_streams:
        for sub_ele in ele.split(";"):
            stream = sub_ele.lower().strip()
            streams.add(stream)
    return streams
