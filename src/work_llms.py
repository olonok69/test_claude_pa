

import logging
from langchain_ollama import ChatOllama
from typing import List
from openai import AzureOpenAI
from langchain_openai import  AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
import json
import os
from src.conf import *
from src.inference_visitors_batch import create_chunks, send_chunks_to_batch


def get_conf_model(steps, model):
    """
    Get the model configuration
    :param config: config
    :param model: model
    :return: model configuration
    """
    for step in steps:
        if step["name"] == model:
            logging.info(f"Model {model} found")
            return step
    return None


def create_llm(st, model: str = "Llama3.1:11B"):
    """
    Create the chat model
    :param st: st state
    :return: ChatGoogleGenerativeAI
    """
    steps = st.session_state["config_models"]["steps"]
    llm = None
    step = get_conf_model(steps, model)
    parameters = step.get("parameters")
    if model == "Llama3.1:11B":
        return create_llm_ollama(**parameters)
    elif model in ["Gpt4o-Mini", "o3-Mini"]:
        return create_llm_azure(**parameters)
    elif model == "Gpt4o-Mini-batch":
        return create_llm_azure_batch(**parameters), parameters

    return llm


def create_llm_ollama(
    root_dir: str,
    config: dict,
    num_samples: int = 100000000,
    model: str = "llama3.1:latest",
    temperature: float = 0.5,
    top_p: float = 0.9,
    top_k: int = 30,
    repetition_penalty: float = 1.1,
    do_sample: bool = True,
    num_ctx: int = 16184,
    format: str = "json",
    base_url: List[str] = ["http://localhost:11435", "http://localhost:11434"],
    include_examples: bool = True,
    timestamp_str: str = None,
    create_files: str = "no",
):
    """
    Classify Visitors
    Args:
    root_dir: str: Root Directory
    config: dict: Configuration
    num_samples: int: Number of Samples
    model: str: Model
    temperature: float: Temperature
    top_p: float: Top P
    top_k: int: Top K
    repetition_penalty: float: Repetition Penalty
    do_sample: bool: Do Sample
    num_ctx: int: Number of Context
    format: str: Format
    base_url: List[str]: Base URL
    include_examples: bool: Include Examples
    timestamp_str: str: Timestamp
    create_files: str: Flag to create files
    """

    # "llama3.1:latest"

    llm = ChatOllama(
        model=model,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        repetition_penalty=repetition_penalty,
        do_sample=num_ctx,
        num_ctx=num_ctx,
        format=format,
        base_url=base_url[0],
    )
    return llm


def create_llm_azure(
    root_dir: str,
    config: dict,
    num_samples: int = 100000000,
    model: str = "gpt-4o-mini",
    temperature: float = 0.5,
    top_p: float = 0.9,
    top_k: int = 30,
    repetition_penalty: float = 1.1,
    do_sample: bool = True,
    num_ctx: int = 16184,
    format: str = "json",
    include_examples: bool = True,
    timestamp_str: str = None,
    create_files: str = "no",
    max_chunk_size: int = 100,
):
    """
    Classify Visitors
    Args:
    root_dir: str: Root Directory
    config: dict: Configuration
    num_samples: int: Number of Samples
    model: str: Model
    temperature: float: Temperature
    top_p: float: Top P
    top_k: int: Top K
    repetition_penalty: float: Repetition Penalty
    do_sample: bool: Do Sample
    num_ctx: int: Number of Context
    format: str: Format
    base_url: List[str]: Base URL
    include_examples: bool: Include Examples
    timestamp_str: str: Timestamp
    create_files: str: Flag to create files
    """

    # "Azure OpenAI"

    llm = AzureChatOpenAI(
        azure_endpoint=config["AZURE_ENDPOINT"],
        azure_deployment=config["AZURE_DEPLOYMENT"],
        api_key=config["AZURE_API_KEY"],
        api_version=config["AZURE_API_VERSION"],
        temperature=0.5,
        top_p=0.9,
    )
    return llm


def create_llm_azure_batch(
    root_dir: str,
    config: dict,
    num_samples: int = 100000000,
    model: str = "gpt-4o-mini-2",
    temperature: float = 0.5,
    top_p: float = 0.9,
    top_k: int = 30,
    repetition_penalty: float = 1.1,
    do_sample: bool = True,
    num_ctx: int = 16184,
    format: str = "json",
    include_examples: bool = True,
    timestamp_str: str = None,
    create_files: str = "no",
    max_chunk_size: int = 100,
):
    """
    Classify Visitors
    Args:
    root_dir: str: Root Directory
    config: dict: Configuration
    num_samples: int: Number of Samples
    model: str: Model
    temperature: float: Temperature
    top_p: float: Top P
    top_k: int: Top K
    repetition_penalty: float: Repetition Penalty
    do_sample: bool: Do Sample
    num_ctx: int: Number of Context
    format: str: Format
    base_url: List[str]: Base URL
    include_examples: bool: Include Examples
    timestamp_str: str: Timestamp
    create_files: str: Flag to create files
    """

    # "llama3.1:latest"

    llm = AzureOpenAI(
        azure_endpoint=config["AZURE_ENDPOINT"],
        api_key=config["AZURE_API_KEY"],
        api_version=config["AZURE_API_VERSION_BATCH"],
    )
    return llm


def inference_llama(st, p, num: int = 12):
    """
    Inference for llama
    Args:
    st (_type_): session streamlit
    p (str): profile
    num (int): number
    """
    profile_template = st.session_state[
        f"csm_template_{num}"
    ].generate_clustering_prompt(
        st.session_state[f"profile_{num}"], include_examples=True
    )
    logging.info(f"length of profile: {len(profile_template)}")

    ai_msg = st.session_state[f"llm_{num}"].invoke(profile_template)

    st.session_state[f"upload_state_{num}"] = (
        f"Profile: {p}\n\nRegistration & Demographic Information:\n{st.session_state[f'profile_{num}']}\n\nReponse:\n"
        + str(ai_msg.content)
    )

    return


def inference_llama_batch(st, df, p, num: int = 12):
    """
    Inference for llama
    Args:
    st (_type_): session streamlit
    df (pd.DataFrame): dataframe
    p (str): profile
    num (int): number
    """
    list_profiles = df["profile_id"].tolist()
    output = []
    for p in list_profiles:
        # get profile and status
        st.session_state[f"profile_{num}"] = st.session_state[f"merged_data_{num}"].get(
            p
        )
        st.session_state[f"status_{num}"] = st.session_state[
            f"merged_data_status_{num}"
        ].get(p)
        if st.session_state[f"status_{num}"] == "Enought_data":
            profile_template = st.session_state[
                f"csm_template_{num}"
            ].generate_clustering_prompt(
                st.session_state[f"profile_{num}"], include_examples=True
            )
            logging.info(f"length of profile {p}: {len(profile_template)}")
            st.session_state[f"upload_state_{num}"] = (
                st.session_state[f"upload_state_{num}"]
                + f"\nlength of profile {p}: {len(profile_template)}\n"
            )

            ai_msg = st.session_state[f"llm_{num}"].invoke(profile_template)
            output.append(
                {
                    "profile_id": p,
                    "response": ai_msg.content,
                    "input": st.session_state[f"profile_{num}"],
                }
            )
            st.session_state[f"upload_state_{num}"] = (
                st.session_state[f"upload_state_{num}"]
                + f"\nProfile: {p}\n\nRegistration & Demographic Information:\n{st.session_state[f'profile_{num}']}\n\nReponse:\n"
                + str(ai_msg.content)
                + "\n"
            )
        else:
            st.session_state[f"upload_state_{num}"] = (
                st.session_state[f"upload_state_{num}"]
                + f"\nStatus of profile {p}: Not Enough Data\n"
            )
            response = json.dumps(
                {
                    "category": st.session_state[f"status_{num}"],
                    "ranked_categories": "NA",
                    "certainty": "NA",
                }
            )
            output.append(
                {
                    "profile_id": p,
                    "response": response,
                    "input": st.session_state[f"profile_{num}"],
                }
            )
            st.session_state[f"upload_state_{num}"] = (
                st.session_state[f"upload_state_{num}"]
                + f"\nProfile: {p}\n\nRegistration & Demographic Information:\n{st.session_state[f'profile_{num}']}\n\nReponse:\n"
                + "Not Enough Data\n"
                + "\n"
            )
    return output


def inference_gpt_azure_online(st, p, num: int = 12):
    """
    Inference for llama
    Args:
    st (_type_): session streamlit
    p (str): profile
    num (int): number
    """

    system_prompt = st.session_state[f"csm_template_{num}"].generate_llama_prompt()
    logging.info(
        f"length of profile: {len(st.session_state[f'profile_{num}']) + len(system_prompt)}"
    )
    prompt = PromptTemplate(
        input_variables=["profile"],
        template=system_prompt
        + """[INST] Classify and provide an output of this profile according to the instructions provided: \n\n {profile} [/INST]""",
    )
    chain = prompt | st.session_state[f"llm_{num}"]
    ai_msg = chain.invoke({"profile": st.session_state[f"profile_{num}"]})

    st.session_state[f"upload_state_{num}"] = (
        f"Profile: {p}\n\nRegistration & Demographic Information:\n{st.session_state[f'profile_{num}']}\n\nReponse:\n"
        + str(ai_msg.content)
    )

    return


def inference_gpt_azure_online_batch(
    st,
    df,
    parameters: dict,
    num: int = 12,
):
    """
    Inference for llama
    Args:
    st (_type_): session streamlit
    df (pd.DataFrame): dataframe
    parameters (dict): parameters
    num (int): number
    azure_deployment (str): azure deployment
    """
    list_profiles = df["profile_id"].tolist()
    output = []
    records = []
    azure_deployment = parameters.get("model")
    root_dir = parameters.get("root_dir")
    create_files = parameters.get("create_files")
    max_chunk_size = parameters.get("max_chunk_size")
    ### Create JSONL for Batch API
    for p in list_profiles:
        # get profile and status
        st.session_state[f"profile_{num}"] = st.session_state[f"merged_data_{num}"].get(
            p
        )
        st.session_state[f"status_{num}"] = st.session_state[
            f"merged_data_status_{num}"
        ].get(p)

        if st.session_state[f"status_{num}"] == "Enought_data":

            system_prompt = st.session_state[
                f"csm_template_{num}"
            ].generate_llama_prompt()
            logging.info(
                f"length of profile {p}: {len(st.session_state[f'profile_{num}'])}"
            )
            prompt = {
                "custom_id": f"task-{p}",
                "method": "POST",
                "url": "/chat/completions",
                "body": {
                    "model": azure_deployment,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": st.session_state[f"profile_{num}"]},
                    ],
                },
            }
            records.append(prompt)
        else:

            response = json.dumps(
                {
                    "category": st.session_state[f"status_{num}"],
                    "ranked_categories": "NA",
                    "certainty": "NA",
                }
            )
            output.append(
                {
                    "profile_id": p,
                    "response": response,
                    "input": st.session_state[f"profile_{num}"],
                }
            )
    # Send Batch API
    if create_files == "no":
        file_path = os.path.join(
            root_dir, input_data_folder, batch_data_folder, "records.jsonl"
        )
        logging.info(f"File Path: {file_path}")
        # Writing records to the JSONL file
        with open(file_path, "w") as file:
            for record in records:
                file.write(f"{json.dumps(record)}\n")

        # Directory to store output chunks
        chuncks_output_dir = os.path.join(
            root_dir, input_data_folder, batch_data_folder, "jsonl_chunks"
        )
        # Maximum chunk size in bytes (100MB)
        max_chunk_size = max_chunk_size * 1024 * 1024  # 100 MB
        os.makedirs(chuncks_output_dir, exist_ok=True)

        chunk_files = create_chunks(file_path, max_chunk_size, chuncks_output_dir)
        output = send_chunks_to_batch(
            root_dir=chuncks_output_dir,
            chunk_files=chunk_files,
            output=output,
            client=st.session_state[f"llm_{num}"],
            merged_data=st.session_state[f"merged_data_{num}"],
        )
    return output
