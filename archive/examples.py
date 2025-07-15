import os
import logging
import warnings
from src.conf import *
from src.utils import *
from IPython import embed
import warnings
import json
from pandas.errors import SettingWithCopyWarning

warnings.simplefilter(action="ignore", category=(SettingWithCopyWarning))

ROOT = os.path.dirname(os.path.abspath(__file__))


# merger data path
#
merged_data_path = os.path.join(ROOT, output_data_folder, merged_data_json)
examples_path = os.path.join(ROOT, output_csv_folder, "examples.csv")
cat_examples_path = os.path.join(ROOT, output_data_folder, "cat_examples.json")

with open(merged_data_path, "r") as f:
    merged_data = json.load(f)

examples = pd.read_csv(examples_path)
list_profiles = list(merged_data.keys())

list_examples = examples["BadgeId"].tolist()
list_types = examples["type"].tolist()

category_examples = []
for key in list_profiles:
    badge_id = key.split("_")[-1]
    if badge_id in list_examples:
        index_list = list_examples.index(badge_id)
        category = list_types[index_list]
        profile = merged_data.get(key)
        category_examples.append(
            {"profile_id": badge_id, "category": category, "input": profile}
        )


with open(cat_examples_path, "w") as f:
    json.dump(category_examples, f, indent=4)


def generate_examples(examples):
    output_text = ""
    for item in examples:
        category = item["category"]
        input_str = item["input"]

        output_text += f"{category}:\n"  # Add the category as a heading

        lines = input_str.splitlines()  # Split input string into lines
        for line in lines:
            if line:  # check if the line is empty
                try:
                    key, value = line.split(
                        ":", 1
                    )  # Split each line into key and value
                    output_text += f"{key.strip()} = {value.strip()}\n"  # Add to output
                except ValueError:  # Handle lines without a colon
                    output_text += (
                        f"{line.strip()}\n"  # add the line without key and value
                    )
        output_text += "\n"  # Add an extra newline for separation

    return output_text


text = generate_examples(category_examples)

print(text)
