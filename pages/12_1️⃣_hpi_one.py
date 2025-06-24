import streamlit as st
from streamlit import session_state as ss
import os
from pathlib import Path
import json
from dotenv import dotenv_values
from datetime import datetime
from src.maintenance import (
    selected_modifica,
    selected_modify_prompt,
    visualiza_modify_profile,
)
import logging
from src.utils import print_stack
from src.maps import config as conf, init_session_num, reset_session_num
from src.conf import *
from src.classes import LLama_PromptTemplate
from src.work_llms import create_llm, inference_llama, inference_gpt_azure_online

# Read all Dataframe need in this page
# where I am
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
path = Path(ROOT_DIR)
PROJECT_DIR = path.parent.absolute().as_posix()
logging.info(f"PROJECT DIR: {PROJECT_DIR}, this folder: {ROOT_DIR}")


def change_state_12(session, pp):
    """
    change state after leave conversation
    params:
    st (streamlit): streamlit object
    pp (streamlit.empty): placeholder

    """
    reset_session_num(session, "12")
    pp.empty()
    del pp
    session.empty()
    session.cache_data.clear()
    session.stop()
    return


def main(options, placeholder):
    """
    Main function
    Argr:
        options: list of options for the select box
        embeddings: embeddings model
        index: pinecone index
        vectorstore: pinecone vectorstore
        placeholder: placeholder for the streamlit app
    """
    with placeholder.container():

        if st.button("Salir", on_click=change_state_12, args=(st, placeholder)):
            logging.info("Salir and writing history")
        col1, col2 = 50, 50
        row1_1, row1_2 = st.columns((col1, col2))
        if "init_run_12" not in st.session_state:
            st.session_state["init_run_12"] = False
        if st.session_state["init_run_12"] == False:
            init_session_num(st, ss, "12", col1, col2, conf["12"]["config_12"], None)

        if "selector_selected_pericial_12" not in st.session_state:
            st.session_state["selector_selected_pericial_12"] = False

        try:
            with row1_1:
                # Select Model from Combox
                model = st.selectbox(
                    "Select Model to Test 👇👇👇",
                    options,
                    index=None,
                    on_change=selected_modifica,
                    args=[st, "12"],
                    key="select_box_modifica_12",
                )

                if st.session_state["selector_selected_modifica_12"] == True:
                    # Select Profile from Combox
                    p = st.selectbox(
                        "Select Profile to Test 👇👇👇",
                        st.session_state["list_profiles_12"],
                        index=None,
                        on_change=selected_modify_prompt,
                        key="select_box_modifica_prompt_12",
                        args=[st, "12"],
                    )
                    if st.session_state["selector_selected_section_12"] == True:
                        # get profile and status
                        st.session_state["profile_12"] = st.session_state[
                            "merged_data_12"
                        ].get(p)
                        st.session_state["status_12"] = st.session_state[
                            "merged_data_status_12"
                        ].get(p)
                        if st.session_state["prompt_dialog_open_12"] == False:
                            visualiza_modify_profile(
                                st,
                                p,
                                st.session_state["profile_12"],
                                num=12,
                            )

                        elif st.session_state["prompt_dialog_open_12"] == True:
                            # lOAD MODEL
                            if "model_12" not in st.session_state:
                                if model == "Llama3.1:11B":
                                    st.session_state["model_12"] = "llama3.1:11B"
                                elif model == "Gpt4o-Mini":
                                    st.session_state["model_12"] = "gpt4o-mini"
                                elif model == "o3-mini":
                                    st.session_state["model_12"] = "o3-mini"
                                st.session_state["llm_12"] = create_llm(st, model=model)

                            if st.session_state["model_12"] != model:
                                st.session_state["model_12"] = model
                                st.session_state["llm_12"] = create_llm(st, model=model)
                                st.session_state["prompt_dialog_open_12"] = False
                                st.session_state["selector_selected_section_12"] = False

                            if st.session_state["status_12"] == "Enought_data":
                                if model == "Llama3.1:11B":
                                    inference_llama(
                                        st,
                                        p,
                                        num=12,
                                    )
                                elif model == "Gpt4o-Mini":
                                    inference_gpt_azure_online(
                                        st,
                                        p,
                                        num=12,
                                    )
                                st.session_state["prompt_dialog_open_12"] = False
                                st.session_state["selector_selected_section_12"] = False

                            else:
                                logging.warning("Not enough data")
            with row1_2:
                model_expander = (
                    st.session_state["model_12"]
                    if "model_12" in st.session_state
                    else "llama3.1:11B"
                )
                with st.expander(
                    f"���️Instruccion to send to {model_expander} 👇",
                    expanded=st.session_state["expander_12"],
                ):
                    upload_state = st.text_area(
                        "Status selection", "", key="upload_state_12", height=600
                    )
        except:
            st.session_state["salir_12"] = True
            placeholder.empty()
            text = print_stack()
            text = "Menu 12 Modify " + text
            logging.error(text)


if __name__ == "__main__":
    # configure access to table . for now we can add prompts and periciales
    options = ["Llama3.1:11B", "Gpt4o-Mini", "o3-mini"]

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
    st.title("CSM. High Purchase Interest Individuals")
    # go to login page if not authenticated
    if (
        st.session_state["authentication_status"] == None
        or st.session_state["authentication_status"] == False
    ):
        st.session_state.runpage = "main.py"
        st.switch_page("main.py")

    if "salir_12" not in st.session_state:
        st.session_state["salir_12"] = False

    if st.session_state["salir_12"] == False:
        placeholder_modifica = st.empty()
        with placeholder_modifica.container():
            config = dotenv_values(os.path.join(PROJECT_DIR, "keys", ".env"))


            if "examples_12" not in st.session_state:
                # OPEN FILES
                with open(examples_path, "r") as f:
                    st.session_state["examples_12"] = json.load(f)
                with open(merger_data_path, "r") as f:
                    st.session_state["merged_data_12"] = json.load(f)
                with open(merger_data_status_path, "r") as f:
                    st.session_state["merged_data_status_12"] = json.load(f)

                st.session_state["list_profiles_12"] = list(
                    st.session_state["merged_data_12"].keys()
                )
                st.session_state["list_profiles_status_12"] = list(
                    st.session_state["merged_data_status_12"].keys()
                )
            if "csm_template_12" not in st.session_state:
                st.session_state["csm_template_12"] = LLama_PromptTemplate(
                    nomenclature, st.session_state["examples_12"]
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
            )
