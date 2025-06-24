import streamlit as st
from streamlit import session_state as ss
import os
from pathlib import Path
import json
from dotenv import dotenv_values
from datetime import datetime
import pandas as pd
from src.maintenance import selected_modifica
import logging
from src.utils import print_stack
from src.maps import config as conf, init_session_num, reset_session_num
from src.conf import *
from src.classes import LLama_PromptTemplate
from src.work_llms import (
    create_llm,
    inference_llama_batch,
    inference_gpt_azure_online_batch,
)
from src.transform import transform_inference_file

# Read all Dataframe need in this page
# where I am
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
path = Path(ROOT_DIR)
PROJECT_DIR = path.parent.absolute().as_posix()
logging.info(f"PROJECT DIR: {PROJECT_DIR}, this folder: {ROOT_DIR}")

# open periciales table
DATA_DIR = os.path.join(PROJECT_DIR, "pericial", "table")
logging.info(f"DATA DIR: {DATA_DIR}")


def change_state_13(session, pp):
    """
    change state after leave conversation
    params:
    st (streamlit): streamlit object
    pp (streamlit.empty): placeholder

    """
    reset_session_num(session, "13")
    pp.empty()
    del pp
    session.empty()
    session.cache_data.clear()
    session.stop()
    return


def main(options, placeholder, timestamp_str, config):
    """
    Main function
    Argr:
        options: list of options for the select box
        placeholder: placeholder for the streamlit app
        timestamp_str: timestamp string
    """
    with placeholder.container():

        if st.button("Salir", on_click=change_state_13, args=(st, placeholder)):
            logging.info("Salir and writing history")
        col1, col2 = 50, 50
        row1_1, row1_2 = st.columns((col1, col2))
        if "init_run_13" not in st.session_state:
            st.session_state["init_run_13"] = False
        if st.session_state["init_run_13"] == False:
            init_session_num(st, ss, "13", col1, col2, conf["13"]["config_13"], None)

        try:
            with row1_1:
                # Select Model from Combox
                model = st.selectbox(
                    "Select Model to Test 👇👇👇",
                    options,
                    index=None,
                    on_change=selected_modifica,
                    args=[st, "13", False],
                    key="select_box_modifica_13",
                )

                if st.session_state["selector_selected_modifica_13"] == True:
                    # Select Profile from Combox
                    uploaded_file = st.file_uploader(
                        "Choose a file",
                        key="file_uploader_13",
                        type="csv",
                        accept_multiple_files=False,
                    )
                    if uploaded_file is not None:
                        df = pd.read_csv(uploaded_file)
                        st.dataframe(df, height=300)
                        if st.button("Send for Inference", key="send_inference_13"):
                            if "model_13" not in st.session_state:
                                if model == "Llama3.1:11B":
                                    st.session_state["model_13"] = "llama3.1:11B"
                                    st.session_state["llm_13"] = create_llm(
                                        st, model=model
                                    )
                                    st.session_state["output_13"] = (
                                        inference_llama_batch(st, df, model, num=13)
                                    )
                                elif model == "Gpt4o-Mini-batch":
                                    st.session_state["model_13"] = "gpt4o-mini"
                                    st.session_state["llm_13"], parameters = create_llm(
                                        st, model=model
                                    )
                                    st.session_state["output_13"] = (
                                        inference_gpt_azure_online_batch(
                                            st, df, parameters=parameters, num=13
                                        )
                                    )
                            if (
                                len(st.session_state["output_13"]) > 0
                                and st.session_state["show_df_13"] == False
                            ):

                                model = model.split(":")[0]
                                model = model.replace(".", "_")
                                filename = os.path.join(
                                    PROJECT_DIR,
                                    input_data_folder,
                                    classification_data_folder,
                                    f"{model}_{timestamp_str}.json",
                                )
                                logging.info(f"Saving output to {filename}")
                                with open(filename, "w") as f:
                                    json.dump(
                                        st.session_state["output_13"], f, indent=4
                                    )
                                transform_inference_file(
                                    root_dir=PROJECT_DIR,
                                    config=config,
                                    model=model,
                                    timestamp_str=timestamp_str,
                                )

                                if "upload_state_13" in st.session_state:
                                    del st.session_state["upload_state_13"]
                                st.session_state["show_df_13"] = True

            with row1_2:
                model_expander = (
                    st.session_state["model_13"]
                    if "model_13" in st.session_state
                    else "llama3.1:11B"
                )
                with st.expander(
                    f"���️Instruccion to send to {model_expander} 👇",
                    expanded=st.session_state["expander_13"],
                ):

                    if st.session_state["show_df_13"] == True:
                        model = model.split(":")[0]
                        model = model.replace(".", "_")
                        filename = os.path.join(
                            PROJECT_DIR,
                            input_data_folder,
                            classification_data_folder,
                            f"{model}_{timestamp_str}.csv",
                        )
                        df = pd.read_csv(filename)
                        if df is not None:
                            st.dataframe(df, height=500)
        except:
            st.session_state["salir_13"] = True
            placeholder.empty()
            text = print_stack()
            text = "Menu 13 HPI Batch  " + text
            logging.error(text)


if __name__ == "__main__":
    # configure access to table . for now we can add prompts and periciales
    options = ["Llama3.1:11B", "Gpt4o-Mini-batch"]

    # access to keys and service account
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    path = Path(ROOT_DIR)
    PROJECT_DIR = path.parent.absolute().as_posix()
    # Paths
    examples_path = os.path.join(
        PROJECT_DIR, input_data_folder, output_data_folder, cat_examples_json
    )
    merger_data_path = os.path.join(
        PROJECT_DIR, input_data_folder, output_data_folder, merged_data_json
    )
    merger_data_status_path = os.path.join(
        PROJECT_DIR, input_data_folder, output_data_folder, merged_data_status_json
    )

    # Set page layout
    st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
    st.title("CSM. High Purchase Interest. Batch Mode")
    # go to login page if not authenticated
    if (
        st.session_state["authentication_status"] == None
        or st.session_state["authentication_status"] == False
    ):
        st.session_state.runpage = "main.py"
        st.switch_page("main.py")

    if "salir_13" not in st.session_state:
        st.session_state["salir_13"] = False

    if st.session_state["salir_13"] == False:
        placeholder_modifica = st.empty()
        with placeholder_modifica.container():
            config = dotenv_values(os.path.join(PROJECT_DIR, "keys", ".env"))


            if "examples_13" not in st.session_state:
                # OPEN FILES
                with open(examples_path, "r") as f:
                    st.session_state["examples_13"] = json.load(f)
                with open(merger_data_path, "r") as f:
                    st.session_state["merged_data_13"] = json.load(f)
                with open(merger_data_status_path, "r") as f:
                    st.session_state["merged_data_status_13"] = json.load(f)

                st.session_state["list_profiles_13"] = list(
                    st.session_state["merged_data_13"].keys()
                )
                st.session_state["list_profiles_status_13"] = list(
                    st.session_state["merged_data_status_13"].keys()
                )
            if "csm_template_13" not in st.session_state:
                st.session_state["csm_template_13"] = LLama_PromptTemplate(
                    nomenclature, st.session_state["examples_13"]
                )
            steps = st.session_state["config_models"]["steps"]
            # Create a timestamp string to identify classification file
            timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            for step in steps:
                if step.get("active", True):  # default active to true if not present.
                    step["parameters"]["config"] = config
                    step["parameters"]["root_dir"] = PROJECT_DIR
                    if "timestamp_str" in step["parameters"].keys():
                        step["parameters"]["timestamp_str"] = timestamp_str
            main(
                options=options,
                placeholder=placeholder_modifica,
                timestamp_str=timestamp_str,
                config=config,
            )
