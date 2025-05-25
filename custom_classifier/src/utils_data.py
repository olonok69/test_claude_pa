import nltk
from nltk.corpus import stopwords
from typing import List, Dict
from functools import lru_cache
import os
import pathlib
import magic
import numpy as np
import pandas as pd
from sklearn.utils import shuffle
import mlflow
from datetime import datetime
from datasets import Dataset
from sklearn.model_selection import train_test_split
import logging

# Download NTLK
nltk.download("stopwords")
stop_words = stopwords.words("english")
prt = nltk.stem.PorterStemmer()


@lru_cache(maxsize=128)
def preprocess(document_path):
    """
    Clean text with NLTK

    Args:
        document_path (_type_): _description_

    Returns:
        _type_: _description_
    """

    with open(document_path, "r", encoding="utf-8") as file:
        document = file.read()
        document = document.replace("\n", " ")
        document = document.replace("\t", " ")
        tokens = document.split(" ")
        #     tokens = nltk.word_tokenize(document)
        tokens_pun_lower = [i.lower() for i in tokens if i.isalnum()]
        tokens_stop = [i for i in tokens_pun_lower if (len(i) > 1)]
    # terms = [prt.stem(i) for i in tokens_stop]

    return " ".join(tokens_stop)


def create_dataframe(path: str, labels: List) -> pd.DataFrame:
    """
    create Dataframe from labels and path with txt files, organized in folders with its name as labels

    Args:
        path (str): _description_
        labels (dict): _description_

    Returns:
        _type_: _description_
    """
    data = []
    # Iterate trough the path and read the files
    path = pathlib.Path(path)
    for p in path.rglob("*"):
        path_abs = p.absolute()

        if p.absolute().is_file():
            filename = os.path.join(path_abs.parent, path_abs.name)

            magicf = magic.from_file(filename, mime=True)
            if magicf == "text/plain" or magicf == "application/octet-stream":
                for label in labels:
                    if os.path.join(path, label) in filename:
                        try:

                            documents = preprocess(filename)
                            data.append([documents, label])
                        except:
                            logging.error(f"Exception reading file {filename}")
    return pd.DataFrame(data, columns=["text", "label"])


def check_num_samples_per_label(
    df: pd.DataFrame, labels: List, min_num_samples: int = 100
):
    """Check number of samples per label in dataframe

    Args:
        df (pd.DataFrame): _description_
        labels (List): _description_
        min_num_samples (int, optional): _description_. Defaults to 150.
    """
    for label in labels:
        dataframe = df[df.label == label]
        if len(dataframe) < min_num_samples:
            raise Exception(
                f"Label {label} has less than minimun number of samples {min_num_samples}"
            )
    return


def map_labels_to_class(data: pd.DataFrame, labels: List):
    """
    Mapping label strings to numbers

    Args:
        data (pd.DataFrame): _description_
        labels (List): _description_

    Returns:
        _type_: _description_
    """

    label_dic = {}
    label_dic_reverse = {}

    for label, i in zip(labels, range(len(labels))):
        label_dic[label] = i
        label_dic_reverse[i] = label

    data["label"] = data["label"].map(label_dic)
    return data, label_dic, label_dic_reverse


def create_dataset_train_val_test(
    data,
    labels,
    label_dic_reverse,
    min_num_samples: int = 75,
    size_train: int = 75,
):
    """
    create datasets train and validation

    Args:
        data (_type_): _description_
        labels (_type_): _description_
        label_dic_reverse (_type_): _description_
        min_num_samples (int, optional): _description_. Defaults to 150.
        size_train (int, optional): _description_. Defaults to 100.

    Raises:
        Exception: _description_

    Returns:
        _type_: _description_
    """
    dataframe_dic = {}
    list_sizes = []
    list_sizes_rest = []
    dataframe_train_dic = {}
    dataframe_rest_dic = {}

    cols = list(data.columns)

    for label, i in zip(labels, range(len(labels))):
        str_label = label_dic_reverse.get(i)
        dataframe_dic[str_label] = data[data.label == i]
        if len(dataframe_dic[str_label]) < min_num_samples:

            raise Exception(
                f"Label {label} has less than minimun number of samples {min_num_samples}"
            )
        else:
            list_sizes.append(len(dataframe_dic[str_label]))
            # sample size train per label
            dataframe_train_dic[str_label] = dataframe_dic[str_label].sample(size_train)
            # build rest dataset with those not included in train
            a_index = dataframe_dic[str_label].set_index(cols).index
            b_index = dataframe_train_dic[str_label].set_index(cols).index
            # create mask
            mask = ~a_index.isin(b_index)
            # dataframe_rest_dic contains original dataset except train dataset
            dataframe_rest_dic[str_label] = dataframe_dic[str_label].loc[mask]
            list_sizes_rest.append(len(dataframe_rest_dic[str_label]))

    # take as number of samples the min of the size per class to build the validation dataset
    min_size_rest = np.array(list_sizes_rest).min()

    for key in dataframe_rest_dic.keys():
        dataframe_rest_dic[key] = dataframe_rest_dic[key].sample(min_size_rest)

    # final datasets
    train_dataset = pd.concat(list(dataframe_train_dic.values()), ignore_index=True)
    train_dataset = shuffle(train_dataset)
    validation_dataset = pd.concat(list(dataframe_rest_dic.values()), ignore_index=True)
    validation_dataset = shuffle(validation_dataset)

    return (
        data,
        list_sizes,
        list_sizes_rest,
        min_size_rest,
        train_dataset,
        validation_dataset,
    )


def label_transform(data: pd.DataFrame, data_test: pd.DataFrame, label_dic: Dict):
    """
    map label to strings case of text-to-text classifier

    Args:
        data (_type_): _description_
        data_test (_type_): _description_
        label_dic (_type_): _description_
    """
    data["label"] = data["label"].map(label_dic)
    data_test["label"] = data_test["label"].map(label_dic)
    return data, data_test


def split_train_dataset(
    data: pd.DataFrame, label: str = "label", test_size: float = 0.2
):
    """split train Dataset for Validation during Training

    Args:
        data (pd.DataFrame): _description_
        label (str, optional): _description_. Defaults to "label".
        test_size (float, optional): _description_. Defaults to 0.2.
    """
    # remove labels to split stratify
    y = data[label].values
    X = data.drop(label, axis=1)
    # split Dataframe

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=42
    )

    X_train[label] = y_train
    X_test[label] = y_test

    return X_train, X_test


def create_transformers_dataset(data: pd.DataFrame):
    """Transform pandas Dataframe into Transformers dataframe

    Args:
        data (pd.DataFrame): _description_

    Returns:
        _type_: _description_
    """
    data = Dataset.from_pandas(data)
    try:
        data = data.remove_columns(["__index_level_0__"])
    except:
        pass
    return data


def create_dataframe_full(
    path,
    labels,
    min_num_samples,
    size_train,
    mlflow_uri,
    experiment_name,
    output_folder: str = "output",
    experiment_type: str = "text-classifier",
    validation: int = 0,
):
    """Create Dataframe for Training

    Args:
        path (_type_): _description_
        labels (_type_): _description_
        min_num_samples (_type_): _description_
        size_train (_type_): _description_
        mlflow_uri (_type_): _description_
        experiment_name (_type_): _description_
    """
    # set Mlflow
    mlflow.set_tracking_uri(mlflow_uri)

    try:
        mlflow.create_experiment(experiment_name)
    except:
        logging.info("experiment exists")
    mlflow.set_experiment(experiment_name)

    df = create_dataframe(path=path, labels=labels)
    # print count of labels
    logging.info(df["label"].value_counts())
    # check number of samples
    check_num_samples_per_label(df, labels, min_num_samples=min_num_samples)
    # maps labels to class
    data, label_dic, label_dic_reverse = map_labels_to_class(df, labels)
    (
        data,
        list_sizes,
        list_sizes_rest,
        min_size_rest,
        train_dataset,
        validation_dataset,
    ) = create_dataset_train_val_test(
        data,
        labels,
        label_dic_reverse,
        min_num_samples=min_num_samples,
        size_train=size_train,
    )

    # in text-to-text-classifier map labels to strings
    if experiment_type == "text-to-text-classifier":
        train_dataset, validation_dataset = label_transform(
            train_dataset, validation_dataset, label_dic
        )

    # split train dataset in train and validation for training
    X_train, X_test = split_train_dataset(data=train_dataset)

    # convert pandas dataframe to transformers Dataframes
    train_dataset_transformers = create_transformers_dataset(X_train)
    test_dataset_transformers = create_transformers_dataset(X_test)
    validation_dataset_transformers = create_transformers_dataset(validation_dataset)
    # Serialize train/test/datasets
    X_train.to_csv(os.path.join(output_folder, "train_dataset.csv"), index=False)
    X_test.to_csv(os.path.join(output_folder, "test_dataset.csv"), index=False)

    # serialize other Datasets
    train_dataset.to_csv(
        os.path.join(output_folder, "train_dataset_full.csv"), index=False
    )
    validation_dataset.to_csv(
        os.path.join(output_folder, "validation_dataset.csv"), index=False
    )
    data.to_csv(os.path.join(output_folder, "full_dataset.csv"), index=False)
    name = "dataset_info " + datetime.now().strftime("%Y-%m-%d_%H%M%S")
    # Log Datasets to Mlflow
    with mlflow.start_run(run_name=name) as run:
        # log metrics
        mlflow.log_metric("length_train", len(train_dataset))
        mlflow.log_metric("length_validation", len(validation_dataset))
        mlflow.log_metric("min_num_samples_per_label", min_num_samples)
        mlflow.log_metric("size_train_dataset", size_train)
        # logs label dictionaries
        mlflow.log_dict(label_dic, "labels/label2id.json")
        mlflow.log_dict(label_dic_reverse, "labels/id2label.json")

        # log dataframes
        mlflow.log_artifact(
            os.path.join(output_folder, "train_dataset.csv"),
            artifact_path="train_datasets",
        )
        mlflow.log_artifact(
            os.path.join(output_folder, "test_dataset.csv"),
            artifact_path="train_datasets",
        )
        mlflow.log_artifact(
            os.path.join(output_folder, "full_dataset.csv"), artifact_path="datasets"
        )
        # log train_dataset
        mlflow.log_artifact(
            os.path.join(output_folder, "train_dataset_full.csv"),
            artifact_path="datasets",
        )
        # log validation_dataset

        mlflow.log_artifact(
            os.path.join(output_folder, "validation_dataset.csv"),
            artifact_path="datasets",
        )

    return (
        run,
        train_dataset_transformers,
        test_dataset_transformers,
        validation_dataset_transformers,
        label_dic,
        label_dic_reverse,
        list_sizes,
        list_sizes_rest,
        min_size_rest,
    )


def validate_validation_dataset(
    data: Dataset, labels: List, label2id: Dict, min_size_label: int
):
    """
    Validate the size of sample labels per class validation dataset
    Args:
        data: pandas dataframe to be validated
        labels: list of labels to fine tune classifier
        label2id : dictionary label strings to category indices Ex:  {"non-cv":0, "cv":1}
        min_size_label : minimun size of label training dataset per class

    """
    data = pd.DataFrame(data)
    dataframe_dic = {}
    list_sizes = []
    val_min_size_label = min_size_label // 5
    for label, i in zip(labels, range(len(labels))):

        str_label = label2id.get(i)
        dataframe_dic[str_label] = data[data.label == i]
        size_label = len(dataframe_dic[str_label])
        if size_label >= val_min_size_label:
            list_sizes.append(size_label)
        else:
            raise ValueError(
                f"Size validation dataset label {label} bellow minimun {val_min_size_label}"
            )

    return list_sizes
