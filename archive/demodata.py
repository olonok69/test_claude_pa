import json
from src.conf import *
from IPython import embed
import pandas as pd
import string
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def remove_punctuation(text):
    custom_punctuation = string.punctuation + "‘’“”…"
    return text.translate(str.maketrans("", "", custom_punctuation))


def count_areas_interest(row):
    if row["QuestionText"] == "your main areas of interest":
        return len(row["AnswerText"].split(";"))
    else:
        return row["AnswerText"]


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


path_output_demographic = os.path.join(ROOT, output_csv_folder, demographic_2025)

demodata = pd.read_csv(path_output_demographic)

demodata = modify_demographic_data(demodata)
list_questions = list(demodata["QuestionText"].unique())
demodata["AnswerText"] = demodata.apply(lambda row: count_areas_interest(row), axis=1)

main_areas_of_interest = demodata[
    demodata["QuestionText"] == "your main areas of interest"
]
demodata.to_csv(os.path.join(ROOT, output_csv_folder, "demo_modified.csv"), index=False)

print(list_questions)
