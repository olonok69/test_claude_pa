from inscriptis import get_text
import pandas as pd
import datetime
import re
from langdetect import detect_langs
from langdetect import detect
import numpy as np
import pickle
from pathlib import Path
from typing import List
import random
import platform
import os
from detectaicore import FILE_NAME_COL, FILE_TYPE_COL, COLS_ROT, Job


def get_rot_analisys(
    docs: List[dict],
    path_picke: str,
    filters: dict,
    create_new: bool,
    jobs: dict,
    new_task: Job,
    document_count: int,
    five_up: str,
    dont_use_now: bool,
    date_timestamp: str,
    is_image: list,
    is_business: list,
    documents_non_processed: List[dict],
    documents_processed: int,
):
    """
    Create Rot Metadata , Data and apply filters
    """
    analyzer = rot_analyzer(
        docs=docs,
        jobs=jobs,
        new_task=new_task,
        use_random_data=False,
        filter_embedded_level=False,
        dont_use_now=dont_use_now,
        date_timestamp=date_timestamp,
        is_image=is_image,
        is_business=is_business,
        documents_non_processed=documents_non_processed,
        documents_processed=documents_processed,
    )
    jobs[
        new_task.uid
    ].status = f"Creating metadata dictionary. Number of Documents {document_count}"

    analyzer = get_create_metadata(path_picke, analyzer, create_new=create_new)
    jobs[new_task.uid].status = "Creating Dataframe"

    analyzer.create_metadata_dataframe()
    jobs[new_task.uid].status = "Updating Dataframe"

    analyzer.update_rot_dataframe()

    # APPLY FLITERS
    jobs[new_task.uid].status = "Apply redundant filter"
    analyzer.apply_filter_redundant(
        col_group="file_name", filter_to_apply=filters.get("redundant")
    )

    jobs[new_task.uid].status = "Apply trivial filter"
    analyzer.apply_trivial_filter(filter_to_apply=filters.get("trivial"))

    jobs[new_task.uid].status = "Apply obsolete filter"
    analyzer.apply_filter_obsolete(filter_to_apply=filters.get("obsolete"))

    jobs[new_task.uid].status = "Flagging Documents"
    analyzer.flag_rot_files()

    jobs[new_task.uid].status = "Creating Pivot Table"
    analyzer.create_pivot_duplicates()

    if platform.system() == "Windows":
        # Dataframe after creating Metadata
        path = os.path.join(five_up, "files", "dataframe.csv")
        analyzer.dataframe.to_csv(path, index=False)
        # Updated Dataframe
        path = os.path.join(five_up, "files", "dataframe_updated.csv")
        analyzer.dataframe_updated.to_csv(path, index=False)
        path = os.path.join(five_up, "files", "dataframe_updated_100.csv")
        analyzer.dataframe_updated[:100].to_csv(path, index=False)
        # Rot Dataframe
        path = os.path.join(five_up, "files", "rot.csv")
        analyzer.dataframe_rot.to_csv(path, index=False)
        # Rot Dataframe
        path = os.path.join(five_up, "files", "redundant.csv")
        analyzer.dataframe_redundant.to_csv(path, index=False)

    return analyzer


class rot_analyzer(object):
    cols = [
        "index",
        "created",
        "accessed",
        "modified",
        "size",
        "uri",
        "file_type",
        "file_name",
        "text",
        "blake3",
        "embedded_depth",
        "is_image",
        "is_business",
    ]
    business_extensions = [
        "pdf",
        "doc",
        "docx",
        "csv",
        "rtf",
        "ppt",
        "pptx",
        "xls",
        "mdb",
        "ppsx",
    ]
    images = ["jpeg", "wmf", "gif", "png", "emf", "ico", "bmp"]

    def __init__(
        self,
        docs,
        jobs: dict,
        new_task: Job,
        use_random_data: bool = True,
        filter_embedded_level: bool = False,
        dont_use_now: bool = False,
        date_timestamp: str = "",
        is_image: list = [],
        is_business: list = [],
        documents_non_processed=[],
        documents_processed=0,
    ):
        self.tika_response = docs
        self.list_docs = None
        self.metadata = None
        self.dataframe = None
        self.dataframe_updated = None
        self.pivot = None
        self.use_random_data = use_random_data
        self.filter_embedded_level = filter_embedded_level
        self.dataframe_redundant = None
        self.duplicates = None
        self.dataframe_trivial = None
        self.dataframe_obsolete = None
        self.dataframe_rot = None
        self.number_pos_timestamps = 19
        self.number_keys = 6
        self.jobs = jobs
        self.new_task = new_task
        self.date_timestamp = date_timestamp
        self.dont_use_now = dont_use_now
        self.is_image = self.images if len(is_image) == 0 else is_image
        self.is_business = (
            self.business_extensions if len(is_business) == 0 else is_business
        )
        self.documents_non_processed = documents_non_processed
        self.documents_processed = documents_processed

    def get_metadata(self):
        """
        extract metadata from list of documents returned from TIKA
        """
        metadata = {}
        self.list_docs = self.tika_response
        ids_to_remove = []
        for file, i in zip(self.list_docs, range(len(self.list_docs))):
            _id = file.get("id")
            # if the file has id
            if not (_id is None) and len(_id) > 0:
                metadata[_id] = {}
                metadata[_id]["index"] = file.get("index")
                # creation date
                if len(file.get("source").get("fs").get("created")) > 18:
                    metadata[_id]["created"] = (
                        file.get("source").get("fs").get("created")
                    )

                else:
                    self.documents_non_processed.append(
                        {file.get("id"): "Document without creation date"}
                    )
                    ids_to_remove.append(file.get("id"))
                # accessed date
                if len(file.get("source").get("fs").get("accessed")) > 18:
                    metadata[_id]["accessed"] = (
                        file.get("source").get("fs").get("accessed")
                    )
                else:
                    self.documents_non_processed.append(
                        {file.get("id"): "Document without accessed date"}
                    )
                    ids_to_remove.append(file.get("id"))
                # modified date
                if len(file.get("source").get("fs").get("modified")) > 18:
                    metadata[_id]["modified"] = (
                        file.get("source").get("fs").get("modified")
                    )
                else:
                    self.documents_non_processed.append(
                        {file.get("id"): "Document without modified date"}
                    )
                    ids_to_remove.append(file.get("id"))
                metadata[_id]["size"] = file.get("source").get("fs").get("size")
                metadata[_id]["uri"] = file.get("source").get("fs").get("uri")

                # File Extension
                if (
                    not (file.get("source").get("file_type") is None)
                    and len(file.get("source").get("file_type")) > 0
                ):
                    metadata[_id]["file_type"] = file.get("source").get("file_type")
                else:
                    self.documents_non_processed.append(
                        {file.get("id"): "Document without File extension "}
                    )
                    ids_to_remove.append(file.get("id"))

                metadata[_id]["file_name"] = file.get("source").get("file_name")

                if file.get("source").get("content") != None:
                    metadata[_id]["text"] = get_text(file.get("source").get("content"))
                else:
                    metadata[_id]["text"] = ""

                # content_blake3
                if file.get("source").get("content_blake3"):
                    metadata[_id]["content_blake3"] = file.get("source").get(
                        "content_blake3"
                    )
                else:
                    self.documents_non_processed.append(
                        {file.get("id"): "Non valid blake3 hash"}
                    )
                    ids_to_remove.append(file.get("id"))

                metadata[_id]["embedded_depth"] = file.get("source").get(
                    "embedded_depth"
                )
                self.jobs[self.new_task.uid].status = f"Creating metadata file {i}"
            else:
                self.documents_non_processed.append(
                    {file.get("source").get("fs").get("uri"): "Non valid document ID"}
                )
        ids_to_remove = set(ids_to_remove)
        for key in ids_to_remove:
            del metadata[key]

        self.metadata = metadata
        return

    def create_metadata_dataframe(self):
        """
        create a dataframe with the metadata extracted from tika output for this index
        """
        dataframes = []
        metadata = self.metadata
        for key, i in zip(metadata.keys(), range(len(metadata.keys()))):
            ftype = metadata[key].get("file_type")
            is_business = 0
            is_image = 0
            if ftype in self.is_business:
                is_business = 1
            if ftype in self.is_image:
                is_image = 1
            # create records
            record = [
                (
                    key,
                    metadata[key].get("created"),
                    metadata[key].get("accessed"),
                    metadata[key].get("modified"),
                    metadata[key].get("size"),
                    metadata[key].get("uri"),
                    metadata[key].get("file_type"),
                    metadata[key].get("file_name"),
                    metadata[key].get("text"),
                    metadata[key].get("content_blake3"),
                    metadata[key].get("embedded_depth"),
                    is_image,
                    is_business,
                )
            ]
            temp = pd.DataFrame(data=record, columns=self.cols)
            dataframes.append(temp)
            self.jobs[
                self.new_task.uid
            ].status = f"gettings values for document {key}, number = {i}"
        self.dataframe = pd.concat(dataframes, ignore_index=True)
        return

    def get_type_value_counts(self):
        return self.dataframe.file_type.value_counts().to_dict()

    def get_is_business(self):
        return len(self.dataframe[self.dataframe.is_business == 1])

    def get_is_image(self):
        return len(self.dataframe[self.dataframe.is_image == 1])

    def update_rot_dataframe(self):
        """
        update dataframe with calculated columns
        """

        def change_to_datetime(x):
            return pd.to_datetime(
                x[: self.number_pos_timestamps], format="%Y-%m-%dT%H:%M:%S"
            )

        def calculate_days_of_access(x):
            delta = datetime.datetime.now() - x
            return delta.days

        def calculate_days_of_access_from_timestamp(x):
            delta = self.date_timestamp - x
            return delta.days

        def calculate_seconds_from_timestamp(x):
            delta = self.date_timestamp - x
            return int(delta.total_seconds())

        def change_to_datetime_random(x):
            d = pd.to_datetime(
                x[: self.number_pos_timestamps], format="%Y-%m-%dT%H:%M:%S"
            )
            choices = [
                1,
                31,
                56,
                71,
                44,
                32,
                130,
                220,
                257,
                380,
                449,
                401,
                275,
                180,
                331,
                500,
                600,
                700,
                800,
                900,
                1000,
                1500,
                2000,
            ]
            days_to_subtract = random.choice(choices)
            return d - datetime.timedelta(days=days_to_subtract)

        def calculate_seconds_now_timestamp(x):
            delta = datetime.datetime.now() - x
            return int(delta.total_seconds())

        def group_outdated(row):
            """
            Categorization based in number of days created/accesed/modified. take max of these three timestamps
            """
            mod = row.days_modified
            acc = row.days_accesed
            created = row.days_created
            days = max(max(mod, acc), created)
            outdated_group = ""

            if days < 10:
                outdated_group = "Less 10 days"
            elif days < 30:
                outdated_group = "Less 1 Months"
            elif days < 90:
                outdated_group = "Less 3 Months"
            elif days < 180:
                outdated_group = "Less 6 Months"
            elif days < 360:
                outdated_group = "Less 1 year"
            elif days < 720:
                outdated_group = "Less 2 year"
            elif days < 1080:
                outdated_group = "Less 3 year"
            else:
                outdated_group = "more 3 year"

            return outdated_group

        rot = self.dataframe.copy()

        # convert strings to datetime
        rot["accessed_datetime"] = rot["accessed"].apply(change_to_datetime)
        rot["modified_datetime"] = rot["modified"].apply(change_to_datetime)
        if self.use_random_data:
            rot["created_datetime"] = rot["created"].apply(change_to_datetime_random)
        else:
            rot["created_datetime"] = rot["created"].apply(change_to_datetime)

        # If we use now as timestamp for calculations or a timestamp on the parameter date_timestamp
        # date_timestamp have to come in forma %Y-%m-%d as string
        if self.dont_use_now == False:
            # calculate number of days
            rot["days_accesed"] = rot["accessed_datetime"].apply(
                calculate_days_of_access
            )
            rot["days_modified"] = rot["modified_datetime"].apply(
                calculate_days_of_access
            )
            rot["days_created"] = rot["created_datetime"].apply(
                calculate_days_of_access
            )

            # calculate number of days
            rot["seconds_accesed"] = rot["accessed_datetime"].apply(
                calculate_seconds_now_timestamp
            )
            rot["seconds_modified"] = rot["modified_datetime"].apply(
                calculate_seconds_now_timestamp
            )
            rot["seconds_created"] = rot["created_datetime"].apply(
                calculate_seconds_now_timestamp
            )
        else:
            try:
                self.date_timestamp = datetime.datetime.strptime(
                    self.date_timestamp, "%Y-%m-%d"
                )
            except:
                raise AttributeError("Format Date not correct shall be YYYY-mm-dd")
            # calculate number of days
            rot["days_accesed"] = rot["accessed_datetime"].apply(
                calculate_days_of_access_from_timestamp
            )
            rot["days_modified"] = rot["modified_datetime"].apply(
                calculate_days_of_access_from_timestamp
            )
            rot["days_created"] = rot["created_datetime"].apply(
                calculate_days_of_access_from_timestamp
            )

            # calculate number of days
            rot["seconds_accesed"] = rot["accessed_datetime"].apply(
                calculate_seconds_from_timestamp
            )
            rot["seconds_modified"] = rot["modified_datetime"].apply(
                calculate_seconds_from_timestamp
            )
            rot["seconds_created"] = rot["created_datetime"].apply(
                calculate_seconds_from_timestamp
            )

        # create outdated category
        rot["outdated_group"] = rot.apply(lambda row: group_outdated(row), axis=1)

        # create columns trivial and obsolete
        rot["trivial"], rot["obsolete"] = np.nan, np.nan
        # filter for documents which have non embedded content
        if self.filter_embedded_level:
            rot = rot[rot.embedded_depth == 0]

        # remove records with no file_name
        rot = rot[rot["file_name"].str.strip() != ""]
        self.dataframe_updated = rot.copy()
        return

    def create_pivot_duplicates(self):
        """
        create pivot table duplicates
        """
        rotp = self.dataframe_updated.pivot_table(
            index=["file_name"], aggfunc="size", sort=True
        )
        rotp = rotp.reset_index()
        rotp.columns = ["file_name", "count"]
        self.pivot = rotp[rotp["count"] > 1].sort_values(["count"], ascending=False)
        return

    def get_duplicates_dict(self):
        return self.pivot.to_dict(orient="records")

    def get_rot_dict(self):
        return self.dataframe_rot.to_dict(orient="records")

    def apply_filter_redundant(
        self,
        col_group: str = "blake3",
        filter_to_apply: dict = {},
        use_timestamps: bool = False,
    ):
        def apply_filter(row):
            """
            Apply redundant filter
            """
            if row[f"ref_{COLUMN}"] == row[filter_to_apply.get("col")]:
                return 0
            else:
                return 1

        def get_filename_metadata(file_name, new_l):
            """
            get filename
            """
            dictionary = {}
            for d in new_l:
                if file_name == d.get("file_name"):
                    dictionary = d.copy()
                    break
            return dictionary

        COLUMN = filter_to_apply.get("col")
        dataframe = self.dataframe_updated.copy()

        if (
            len(filter_to_apply.keys()) == 2
            and "col" in filter_to_apply.keys()
            and "type" in filter_to_apply.keys()
        ):
            group = dataframe.groupby(col_group).agg({col_group: "count"})
            group.columns = ["count"]
            group.reset_index(inplace=True)
            dataframe_joined = pd.merge(dataframe, group, on=[col_group], how="inner")
            duplicates = dataframe_joined[dataframe_joined["count"] > 1]
            # apply filter selected by user
            if filter_to_apply.get("type") == "oldest":
                duplicatesg = duplicates.groupby(col_group).agg({COLUMN: "min"})
            elif filter_to_apply.get("type") == "newest":
                duplicatesg = duplicates.groupby(col_group).agg({COLUMN: "max"})
            else:
                raise ValueError("type filter shall be oldest or newest")

            duplicatesg.columns = [f"ref_{COLUMN}"]
            duplicatesg.reset_index(inplace=True)

            duplicates = pd.merge(duplicates, duplicatesg, on=[col_group], how="inner")

            duplicates["redundant"] = duplicates.apply(
                lambda row: apply_filter(row), axis=1
            )
            # second refinement redundant
            redundants = duplicates[
                [
                    "index",
                    "count",
                    f"ref_{COLUMN}",
                    "file_name",
                    "size",
                    "redundant",
                    "seconds_created",
                    "seconds_accesed",
                    "seconds_modified",
                ]
            ]
            # create Dataframe with redundant
            redundants_0 = redundants[redundants.redundant == 0]
            redundants_1 = redundants[redundants.redundant == 1]
            dict_redundants = redundants_0.to_dict(orient="records")
            # remove duplicates
            seen = set()
            new_dict_redundants = []
            for d in dict_redundants:
                t = tuple(d.items())
                if t not in seen:
                    seen.add(t)
                    new_dict_redundants.append(d)

            for index, row in redundants_1.iterrows():
                file_name = row.at["file_name"]
                size = row.at["size"]
                seconds_created = row.at["seconds_created"]
                seconds_accesed = row.at["seconds_accesed"]
                seconds_modified = row.at["seconds_modified"]
                metadata_file = get_filename_metadata(file_name, new_dict_redundants)

                if len(metadata_file.keys()) == self.number_keys:
                    if size != metadata_file.get("size"):
                        redundants_1.at[index, "redundant"] = 0
                    if use_timestamps:
                        if seconds_created != metadata_file.get("seconds_created"):
                            redundants_1.at[index, "redundant"] = 0
                        elif seconds_accesed != metadata_file.get("seconds_accesed"):
                            redundants_1.at[index, "redundant"] = 0
                        elif seconds_modified != metadata_file.get("seconds_modified"):
                            redundants_1.at[index, "redundant"] = 0
            duplicates = pd.concat([redundants_0, redundants_1], ignore_index=True)

            dataframe = pd.merge(
                dataframe,
                duplicates[["index", "count", f"ref_{COLUMN}", "redundant"]],
                on=["index"],
                how="left",
            )
            dataframe = dataframe.fillna(
                {"count": 0, f"ref_{COLUMN}": 0, "redundant": 0}
            )
            # convert to int
            dataframe["redundant"] = dataframe["redundant"].astype(int)
            self.duplicates = duplicates.copy()
        else:
            (
                dataframe["count"],
                dataframe[f"ref_{COLUMN}"],
                dataframe["redundant"],
            ) = (np.nan, np.nan, np.nan)
            dataframe = dataframe.fillna(
                {"count": 0, f"ref_{COLUMN}": 0, "redundant": 0}
            )
            # convert to int
            dataframe["redundant"] = dataframe["redundant"].astype(int)

        self.dataframe_redundant = dataframe.copy()

        return

    def apply_trivial_filter(
        self,
        col: str = FILE_TYPE_COL,
        filter_to_apply: dict = {},
    ):
        def check_in_file_is_in_list(row, final_list, col_name):
            if row[col_name] in final_list:
                return 1
            else:
                return 0

        rot = self.dataframe_redundant.copy()
        if len(filter_to_apply.keys()) >= 1:
            cl = filter_to_apply.get("custom_list")
            tl = filter_to_apply.get("template_list")
            # all file extensions to lower letters
            tl = set([x.lower() for x in tl])
            cl = set([x.lower() for x in cl])

            final_list = cl.union(tl)
            rot["trivial"] = rot.apply(
                lambda row: check_in_file_is_in_list(
                    row,
                    final_list,
                    col,
                ),
                axis=1,
            )
        else:
            rot["trivial"] = np.nan

            rot = rot.fillna({"trivial": 0})

        self.dataframe_trivial = rot.copy()

        return

    def apply_filter_obsolete(
        self,
        filter_to_apply: dict = {},
    ):
        def flag_obsolete(row, days_back, col):
            if row[col] > days_back:
                return 1
            else:
                return 0

        dataframe = self.dataframe_trivial.copy()
        if len(filter_to_apply.keys()) == 3:
            if filter_to_apply.get("timeframe") == "days":
                days_back = filter_to_apply.get("older_than")
            elif filter_to_apply.get("timeframe") == "months":
                days_back = filter_to_apply.get("older_than") * 30
            elif filter_to_apply.get("timeframe") == "years":
                days_back = filter_to_apply.get("older_than") * 365

            dataframe["obsolete"] = dataframe.apply(
                lambda row: flag_obsolete(row, days_back, filter_to_apply.get("col")),
                axis=1,
            )
        else:
            dataframe["obsolete"] = np.nan
            dataframe = dataframe.fillna({"obsolete": 0})

        self.dataframe_obsolete = dataframe.copy()

        return

    def flag_rot_files(self):
        """
        Create Rot Dataframe
        """

        def flag_rot(row):
            if row["trivial"] == 1 or row["obsolete"] == 1 or row["redundant"] == 1:
                return 1
            else:
                return 0

        data = self.dataframe_obsolete.copy()
        if not ("trivial" in data.columns):
            data["trivial"] = np.nan
        if not ("obsolete" in data.columns):
            data["obsolete"] = np.nan
        if not ("redundant" in data.columns):
            data["redundant"] = np.nan

        data = data.fillna({"trivial": 0, "obsolete": 0, "redundant": 0})
        data["is_rot"] = data.apply(lambda row: flag_rot(row), axis=1)
        # select only necessary cols
        data = data[COLS_ROT]
        data["document_id"] = data["index"].values
        data = data.drop("index", axis=1)
        self.dataframe_rot = data.copy()
        return


def get_pure_text(text: str):
    return re.sub("[^A-Za-z@ñ\\s\\:\\.]+", " ", text)


def detect_languages(text: str) -> dict:
    """Detects the text's language."""

    language = ""
    confidence = 0
    try:
        language = detect(text)
        confidence = 1.0
    except:
        result = detect_langs(text)
        language = result[0].lang
        confidence = result[0].prob


def get_create_metadata(path_picke, analyzer, create_new: bool = False):
    """ "
    Create Metadata from documents or read from pickle file
    """
    pickle_file = Path(path_picke)
    if pickle_file.is_file() and create_new == False:
        with open(path_picke, "rb") as handle:
            analyzer.metadata = pickle.load(handle)
    else:
        analyzer.get_metadata()
        with open(path_picke, "wb") as handle:
            pickle.dump(analyzer.metadata, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return analyzer
