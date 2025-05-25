import evaluate
import os
import mlflow
from mlflow import MlflowClient
import numpy as np
from typing import List, Dict, Tuple
import transformers
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)
from datasets import DatasetDict, Dataset
from datetime import datetime
import torch
import gc
from copy import deepcopy
from sklearn.metrics import classification_report
from sklearn import metrics
import matplotlib.pyplot as plt
import logging


def clean_gpu(endpoint):
    """
    clean models from GPU Memory and Cache
    Args
    endpoint : Fastapi endpoint. come with model, trainer and tokenizer
    """
    del endpoint.model
    del endpoint.trainer
    del endpoint.tokenizer
    gc.collect()
    torch.cuda.empty_cache()


def create_tokenizer(model_id: str):
    return AutoTokenizer.from_pretrained(model_id)


def tokenize_function(examples, tokenizer):
    """# Pad/truncate each text to 512 tokens. Enforcing the same shape
    # could make the training faster.

    Args:
        examples (_type_): _description_
        tokenizer (_type_): _description_

    Returns:
        _type_: _description_
    """

    return tokenizer(
        examples["text"],
        padding="max_length",
        truncation=True,
        max_length=512,
    )


def tokenize_dataset(tokenizer, dataset, seed: int = 42):
    """tokenize Dataset

    Args:
        tokenizer (_type_): _description_
        dataset (_type_): _description_
    """
    dataset = dataset.map(
        tokenize_function, batched=True, fn_kwargs={"tokenizer": tokenizer}
    )
    dataset = dataset.remove_columns(["text"]).shuffle(seed=seed)
    return dataset


def tokenize_datasets(train_dataset, test_dataset, tokenizer):
    """ "
    tokenize train/test dataset
    Args:
        tokenizer (_type_): _description_
        dataset (_type_): _description_
    """
    train_tokenized = tokenize_dataset(tokenizer, train_dataset)
    test_tokenized = tokenize_dataset(tokenizer, test_dataset)
    return train_tokenized, test_tokenized


def create_dictionary_dataset(train_dataset, test_dataset):
    """create Dataset Dictionary

    Args:
        train_tokenized (_type_): _description_
        test_tokenized (_type_): _description_
    """
    return DatasetDict({"train": train_dataset, "test": test_dataset})


def create_model_sequence_classification(
    model_name: str, label2id: Dict, id2label: Dict, device: str = "cpu"
):
    """create model for Sequence Classification / text classification

    Args:
        model_name (str): Model Name
        label2id (Dict): Dictionary Label to ID text to int
        id2label (Dict): Dictionary ID to Label int to text
    """
    num_labels = len(label2id.keys())
    if device == "cuda":
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=num_labels,
            label2id=label2id,
            id2label=id2label,
            torch_dtype=torch.bfloat16,  # load in brain float
        )
    elif device == "cpu":

        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=num_labels,
            label2id=label2id,
            id2label=id2label,
        )
    print(f"Model loaded in {device}")
    return model


def create_data_collator_text_classification(tokenizer, pad_to_multiple_of: int = 8):
    """Create Data collator for token classification

    Args:
        tokenizer (_type_): _description_
        pad_to_multiple_of (int, optional): _description_. Defaults to 8.

    Returns:
        _type_: _description_
    """

    return DataCollatorWithPadding(
        tokenizer=tokenizer, pad_to_multiple_of=pad_to_multiple_of
    )


def compute_metrics(eval_preds):
    """create metrics for training

    Args:
        eval_preds (_type_): _description_

    Returns:
        _type_: _description_
    """
    # load metrics
    metric = evaluate.load("f1")
    metric1 = evaluate.load("roc_auc")
    metric2 = evaluate.load("recall")
    metric3 = evaluate.load("precision")

    logits, labels = eval_preds
    if isinstance(logits, tuple):
        logits = logits[0]
    predictions = np.argmax(logits, axis=-1)
    result = {}
    # Multiclass we remove roc and use accuracy
    if np.array(logits).shape[1] > 2:

        metric1 = evaluate.load("accuracy")

        result["f1"] = metric.compute(
            predictions=predictions, references=labels, average="micro"
        )["f1"]
        result["accuracy"] = metric1.compute(
            predictions=predictions, references=labels
        )["accuracy"]
        result["recall"] = metric2.compute(
            predictions=predictions, references=labels, average="micro"
        )["recall"]
        result["precision"] = metric3.compute(
            predictions=predictions, references=labels, average="micro"
        )["precision"]

    else:

        result["f1"] = metric.compute(
            predictions=predictions, references=labels, average="macro"
        )["f1"]
        result["roc_auc"] = metric1.compute(
            prediction_scores=predictions, references=labels, average="macro"
        )["roc_auc"]
        result["recall"] = metric2.compute(
            predictions=predictions, references=labels, average="macro"
        )["recall"]
        result["precision"] = metric3.compute(
            predictions=predictions, references=labels, average="macro"
        )["precision"]

    return result


def create_trainer(
    endpoint, train_tokenized, test_tokenized, labels: List = [], device: str = "cpu"
):
    """create trainer

    Args:
        endpoint (_type_): _description_
        train_tokenized (_type_): _description_
        test_tokenized (_type_): _description_
        labels  (_type_): _description_
        device (_type_): _description_
    """
    ### this TODO in the future look at this way to assign learning rate and number Epoch

    if len(labels) > 2:
        learning_rate = 1e-3
        num_train_epochs = 8
    else:
        learning_rate = 2e-3
        num_train_epochs = 4
    # Checkpoints will be output to this `training_output_dir`.
    if device == "cpu":
        use_cpu = True
        no_cuda = True
    elif device == "cuda":
        use_cpu = False
        no_cuda = False

    training_output_dir = "/tmp/sms_trainer"
    training_args = TrainingArguments(
        report_to="mlflow",
        output_dir=training_output_dir,
        evaluation_strategy="epoch",
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        learning_rate=learning_rate,
        weight_decay=0.01,
        logging_steps=8,
        num_train_epochs=num_train_epochs,
        load_best_model_at_end=True,
        save_strategy="epoch",
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        use_cpu=use_cpu,
        no_cuda=no_cuda,
    )
    data_collator = create_data_collator_text_classification(endpoint.tokenizer)
    # Instantiate a `Trainer` instance that will be used to initiate a training run.
    trainer = Trainer(
        model=endpoint.model,
        args=training_args,
        train_dataset=train_tokenized,
        eval_dataset=test_tokenized,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )
    return trainer


def evaluate_model(datatest, model_info, label2id) -> Tuple:
    """
    Evaluate the model on the test dataset.
    Args:
        datatest: validation Dataset
        model_info: run info training  experiment
        label2id :dictionary labels to classes int
    """
    predictions_list, labels_list, scores = [], [], []
    classification_components = mlflow.transformers.load_model(
        model_info.model_uri, return_type="components"
    )
    reconstructed_pipeline = transformers.pipeline(**classification_components)

    samples_number = len(datatest)
    # Inference validation Dataset

    for i in range(samples_number):
        text = datatest["text"][i]
        pred_dict = reconstructed_pipeline(text)
        pred = pred_dict[0].get("label")
        pred = label2id.get(pred)
        predictions_list.append(pred)
        scores.append(pred_dict[0].get("score"))
        labels_list.append(int(datatest["label"][i]))

    report = classification_report(labels_list, predictions_list, output_dict=True)

    return predictions_list, labels_list, scores, report


def train_model(
    endpoint,
    mlflow_uri: str,
    experiment_name: str,
    labels: List,
    label2id: Dict,
    validation: int = 0,
    validation_dataset: Dataset = None,
    output_folder: str = "output",
):
    """train model

    Args:
        endpoint (_type_): FastAPI endpoint
        mlflow_uri (str): MLFLOW URI to set mlflow tracking URI
        experiment_name (str): Name of experiment
        labels (list) : List of lables use to train this model
        label2id (Dict) : Dictionaty key--> str to value--> int
        validation (int) : If to perform Validation or no.  1 yes, 0 no
        validation_dataset (HF Dataset): Tokenized Validation Dataset
        output_folder (str) : Folder to deposit images and artifacts to log to MLFLOW

    Returns:
        _type_: _description_
    """

    mlflow.set_tracking_uri(mlflow_uri)

    try:
        mlflow.create_experiment(experiment_name)
    except:
        logging.info("experiment exists")
    mlflow.set_experiment(experiment_name)
    name = "training_classifier" + datetime.now().strftime("%Y-%m-%d_%H%M%S")
    custom_path = "/tmp/flan-T5-fine-tune"
    # create custom path to save model locally
    os.makedirs(custom_path, exist_ok=True)
    # Log Datasets to Mlflow
    with mlflow.start_run(run_name=name) as run:
        train_results = endpoint.trainer.train()
        logging.info(train_results.metrics)
        endpoint.trainer.model.save_pretrained(custom_path)
        endpoint.trainer.data_collator.tokenizer.save_pretrained(custom_path)

        transformers_model = {
            "model": endpoint.trainer.model,
            "tokenizer": endpoint.trainer.data_collator.tokenizer,
        }
        task = "text-classification"
        model_info = mlflow.transformers.log_model(
            transformers_model=transformers_model,
            artifact_path="text_classifier",
            task=task,
        )
        if model_info:
            logging.info(model_info.metadata)

    if validation == 1:
        this_run = run.to_dictionary()
        name = (
            f"validation_model_{this_run['info']['run_id']}"
            + datetime.now().strftime("%Y-%m-%d_%H%M%S")
        )
        with mlflow.start_run(run_name=name):
            predictions_list, labels_list, _, cr = evaluate_model(
                validation_dataset, model_info, label2id
            )
            # Logging all metrics in classification_report
            mlflow.log_metric("accuracy", cr.pop("accuracy"))
            for class_or_avg, metrics_dict in cr.items():
                for metric, value in metrics_dict.items():
                    mlflow.log_metric(class_or_avg + "_" + metric, value)

            plt.figure(figsize=(20, 20))
            confusion_matrix = metrics.confusion_matrix(labels_list, predictions_list)
            cm_display = metrics.ConfusionMatrixDisplay(
                confusion_matrix=confusion_matrix, display_labels=labels
            )
            cm_display.plot()

            plt.savefig(os.path.join(output_folder, "confusion_matrix.png"))
            # log Images
            mlflow.log_artifact(
                os.path.join(output_folder, "confusion_matrix.png"),
                artifact_path="images",
            )
    return run, model_info


def predict(runid: str, text: str, mlflow_uri: str, device: str = "cpu"):
    """predict

    Args:
        runid (str): predict with new model
        text (str): text to classify


    Returns:
        Dictionary:
    """
    mlflow.set_tracking_uri(mlflow_uri)

    client = MlflowClient()
    run_name = deepcopy(runid)
    runid = f"runs:/{runid}/text_classifier"
    logging.info(f"RunID training {runid}")
    # get params labels dictionaries
    exp_id = client.get_run(run_name)
    # activate if need it --> id2label = eval(exp_id.data.params.get("id2label"))
    label2id = eval(exp_id.data.params.get("label2id"))
    # download_model from mlflow
    classification_components = mlflow.transformers.load_model(
        runid, return_type="components"
    )

    tokenizer_kwargs = {
        "padding": True,
        "truncation": True,
        "max_length": 512,
    }
    #
    pipeline = transformers.pipeline(**classification_components, **tokenizer_kwargs)
    logging.info(f"Inference in {pipeline.device}")

    pred_dict = pipeline(text)
    label = pred_dict[0].get("label")

    prediction = label2id.get(label)
    score = pred_dict[0].get("score")

    data = {"label": label, "prediction": prediction, "score": score}
    del pipeline
    gc.collect()
    torch.cuda.empty_cache()
    return data
