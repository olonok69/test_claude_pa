import mlflow
import pandas as pd
from mlflow import MlflowClient
import pymysql
from typing import List
import shutil
import logging


def search_n_experiments(experiment_name: str = "Default", num: int = 3):
    """
    search Experiment and return n latest experiments
    Args:
        experiment_name:str Experiment name
        num:int Number experiments

    """

    active_runs = mlflow.search_runs(
        experiment_names=[experiment_name],
        order_by=["start_time DESC"],
    )
    out = active_runs[:num]
    return out


def get_all_experiments_last_run(mlflow_uri: str):
    """
    search Experiment and return n latest experiments
    Args:
        mlflow_uri:str Mlflow uri

    """

    mlflow.set_tracking_uri(mlflow_uri)
    cols = [
        "run_id",
        "status",
        "experiment_name",
        "tags.mlflow.runName",
    ]
    experiments = mlflow.search_experiments()
    dataframes = []
    for exp in experiments:
        temp = search_n_experiments(experiment_name=exp.name, num=1)
        temp["experiment_name"] = exp.name
        dataframes.append(temp)
    df = pd.concat(dataframes, ignore_index=True)

    out = df[cols]
    status = out.to_json(orient="records")
    return status


def get_mlflow_job_status(mlflow_uri: str, experiment_name: str, num_runs: int = 3):
    """
    get status last 3 runs of experiment name
    Args:
        mlflow_uri : MLFLOW URI
        experiment_name: Name of Experiment
        num_runs: Number of Runs to return, default 3
    """
    mlflow.set_tracking_uri(mlflow_uri)
    cols = [
        "run_id",
        "status",
        "params.label2id",
        "params.id2label",
        "tags.mlflow.runName",
    ]
    # get all_runs of experiment in paramns
    active_runs = mlflow.search_runs(
        experiment_names=[experiment_name],
        order_by=["start_time DESC"],
    )
    out = active_runs[cols]
    # return only the 3 more recent
    out = out[:num_runs].to_json(orient="records")
    return out


def delete_experiment_soft(mlflow_uri: str, experiment_name: str):
    """
    delete experiment with name experiment_name
    Args:
        mlflow_uri : MLFLOW URI
        experiment_name: Name of Experiment

    """
    mlflow.set_tracking_uri(mlflow_uri)
    client = MlflowClient()
    status = ""
    try:
        exp_id = client.get_experiment_by_name(experiment_name)

        # Show experiment info
        logging.info(f"Name: {exp_id.name}")
        logging.info(f"Experiment ID: {exp_id.experiment_id}")
        logging.info(f"Artifact Location: {exp_id.artifact_location}")
        logging.info(f"Lifecycle_stage: {exp_id.lifecycle_stage}")
        if exp_id.lifecycle_stage == "active":
            client.delete_experiment(exp_id.experiment_id)
            status = f"Experiment {experiment_name} deleted (soft)"
        else:
            status = f"Problem deleting Experiment {experiment_name}. Status {exp_id.lifecycle_stage}"
    except Exception:
        status = f"Experiment {experiment_name} does not exists"
    logging.info(status)
    status = {"status": status}
    return status


def create_database_connection(
    host: str, user: str, port: int, password: str, db: str = "mlflow_db"
):
    """
    Create connection to database
        Args:
        host : hostname database
        user: user connect database
        port: port where database is listening
        password: to access database
        db: database name

    """
    connection = pymysql.connect(
        host=host,
        user=user,
        port=port,
        password=password,
        db=db,
        cursorclass=pymysql.cursors.DictCursor,
    )
    return connection


def delete_experiment_from_table(
    experiment_name: str, database: str, connection: pymysql.connections.Connection
):
    """
    Delete experiment from MLFLOW tables
    Args:
        experiment_name: Name of Experiment
        connection : mysql connection
        database: mlflow database

    """
    status = ""
    with connection.cursor() as cursor:
        # SELECT DATABASE
        query = f"USE {database};"
        cursor.execute(query.strip())
        # deactivating check foreign constrains
        query = "SET FOREIGN_KEY_CHECKS=0;"
        cursor.execute(query.strip())

        # get the locations of that experiment
        query = f"""
        select * from experiments where lifecycle_stage="deleted" and name="{experiment_name}" ;
        """
        cursor.execute(query.strip())
        artifact_locations = []
        for row in cursor:
            artifact_locations.append(
                row.get("artifact_location").replace("file://", "")
            )
        # if we have the experiment in table experiments
        if len(artifact_locations) > 0:

            # delete from table experiment_tags
            query = f"""
            DELETE FROM experiment_tags WHERE experiment_id=ANY(SELECT experiment_id FROM experiments where lifecycle_stage="deleted" and name="{experiment_name}");
            """
            try:
                cursor.execute(query.strip())
                logging.info("Deleting from table experiment_tags")
            except Exception:
                logging.error("problem deleting table experiment_tags")

            # delete from table latest_metrics
            query = f"""
            DELETE FROM latest_metrics WHERE run_uuid=ANY(SELECT run_uuid FROM runs WHERE experiment_id=ANY(SELECT experiment_id FROM experiments where lifecycle_stage="deleted" and name="{experiment_name}"));
            """
            try:
                cursor.execute(query.strip())
                logging.info("Deleting from table latest_metrics")
            except Exception:
                logging.error("problem deleting table latest_metrics")

            # delete from table metrics
            query = f"""
            DELETE FROM metrics WHERE run_uuid=ANY(SELECT run_uuid FROM runs WHERE experiment_id=ANY(SELECT experiment_id FROM experiments where lifecycle_stage="deleted" and name="{experiment_name}"));
            """
            try:
                cursor.execute(query.strip())
                logging.info("Deleting from table metrics")
            except Exception:
                logging.error("problem deleting table metrics")

            # delete from table tags
            query = f"""
            DELETE FROM tags WHERE run_uuid=ANY(SELECT run_uuid FROM runs WHERE experiment_id=ANY(SELECT experiment_id FROM experiments where lifecycle_stage="deleted" and name="{experiment_name}"));
            """
            cursor.execute(query.strip())
            logging.info("Deleting from table tags")

            # delete from table runs
            query = f"""
            DELETE FROM runs WHERE experiment_id=ANY(SELECT experiment_id FROM experiments where lifecycle_stage="deleted" and name="{experiment_name}");
            """
            logging.info("Deleting from table runs")

            # delete  experiments
            query = f"""
            DELETE FROM experiments where lifecycle_stage="deleted" and name="{experiment_name}";
            """
            cursor.execute(query.strip())
            logging.info("Deleting from table experiments")

            status = f"Experiment: {experiment_name} deleted from tables database"
            # commit delete
            connection.commit()
            # set control foreign keys to 1
            query = "SET FOREIGN_KEY_CHECKS=1;"
            cursor.execute(query.strip())
        else:
            status = f"Experiment: {experiment_name} does not exists in database"
    logging.info(status)
    with connection.cursor() as cursor:
        query = "SET FOREIGN_KEY_CHECKS=1;"
        cursor.execute(query.strip())

    # close connection
    connection.close()

    return status, artifact_locations


def delete_experiment_folder(artifact_locations: List[str], experiment_name: str):
    """
    delete permanently artifacts folder from hard disk
    Args:
        artifact_locations: List with absulute paths to folders whit the folders of Experiments to delete

    """

    for loc in artifact_locations:
        logging.info(f"deleting location {loc}")
        shutil.rmtree(loc, ignore_errors=False, onerror=None)
    status = f"Folders of experiment {experiment_name} deleted"
    logging.info(status)
    return status


def delete_experiment_hard(
    mlflow_uri: str,
    experiment_name: str,
    host: str,
    user: str,
    port: int,
    password: str,
    db: str = "mlflow_db",
):
    """
    delete permanently experiment with name experiment_name
    Args:
        mlflow_uri : MLFLOW URI
        experiment_name: Name of Experiment
        host : hostname database
        user: user connect database
        port: port where database is listening
        password: to access database
        db: database name

    """

    mlflow.set_tracking_uri(mlflow_uri)
    client = MlflowClient()
    status = ""
    try:
        exp_id = client.get_experiment_by_name(experiment_name)

        # Show experiment info
        logging.info(f"Name: {exp_id.name}")
        logging.info(f"Experiment ID: {exp_id.experiment_id}")
        logging.info(f"Artifact Location: {exp_id.artifact_location}")
        logging.info(f"Lifecycle_stage: {exp_id.lifecycle_stage}")
        if exp_id.lifecycle_stage == "active":
            client.delete_experiment(exp_id.experiment_id)
            status = f"Experiment {experiment_name} deleted (soft)"
        else:
            status = f"Problem deleting Experiment {experiment_name}. Status {exp_id.lifecycle_stage}"
    except Exception:
        status = f"Experiment {experiment_name} does not exists"
        logging.warning(f"Experiment {experiment_name} does not exists")
    logging.info(status)

    if status != f"Experiment {experiment_name} does not exists":
        # crear connection
        connection = create_database_connection(
            host=host, user=user, port=port, password=password, db=db
        )
        status_tables, artifact_locations = delete_experiment_from_table(
            experiment_name=experiment_name,
            database=db,
            connection=connection,
        )

        status_deleted_files = delete_experiment_folder(
            artifact_locations=artifact_locations, experiment_name=experiment_name
        )

        # build the final status message
        status = status_tables + "\n" + status_deleted_files
        logging.info(status)
        status = {"status": status}
    return status


def delete_run_id_soft(mlflow_uri: str, run_id: str):
    """
    Delete run with run_id
    Args:
        mlflow_uri : MLFLOW URI
        run_id: RunID of   this run

    """
    mlflow.set_tracking_uri(mlflow_uri)
    client = MlflowClient()
    status = ""
    try:
        exp_id = client.get_run(run_id)
        # print(exp_id)
        # embed()
        # # Show experiment info
        logging.info(f"Name: {exp_id.info.run_name}")
        logging.info(f"Experiment ID: {exp_id.info.run_id}")
        logging.info(f"Artifact Location: {exp_id.info.artifact_uri}")
        logging.info(f"Lifecycle_stage: {exp_id.info.lifecycle_stage}")
        if exp_id.info.lifecycle_stage == "active":
            client.delete_run(exp_id.info.run_id)
            status = f"Run {run_id} deleted (soft)"
        else:
            status = (
                f"Problem deleting run {run_id}. Status {exp_id.info.lifecycle_stage}"
            )
            logging.warning(status)
    except Exception:
        status = f"Run {run_id} does not exists"
        logging.error(status)
    status = {"status": status}
    return status
