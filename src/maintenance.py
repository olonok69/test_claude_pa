
import streamlit as st

from src.conf import nomenclature



def selected_modifica(st, num: int = 10, reset_box: bool = True):
    st.session_state[f"selector_selected_modifica_{num}"] = True  #
    if reset_box:
        st.session_state[f"select_box_modifica_prompt_{num}"] = None


# selected_modify_prompt


# this is for modifica
def selected_modify_prompt(st, num):
    st.session_state[f"selector_selected_section_{num}"] = True


def dialog_modify_prompt(st, num):
    st.session_state[f"dialog_selected_section_{num}"] = True


@st.dialog("Modify Prompt 👇", width="large")
def visualiza_modify_profile(st, profile_id: str, profile: str, num: int = 10):
    """
    Visualize prompt
    Args:
        st (_type_): session streamlit
        df (pd.DataFrame): dataframe with all prompts
        fname (str): name of the file
    """

    # transform the row into a dictionary

    _ = st.text_area(
        "Profile ID 👇",
        value=profile_id,
        key=f"profile_id_{num}",
        disabled=True,
        height=68,
    )
    st.session_state["profile_12"] = st.text_area(
        "Modify Profile 👇",
        value=profile,
        key=f"profile_box_{num}",
        height=450,
    )
    if st.button("Close"):
        st.session_state[f"prompt_dialog_open_{num}"] = True
        st.rerun()  # force rerun to close the dialog.
    return


@st.dialog("Modify Prompt 👇", width="large")
def visualiza_modify_nomemclature(st, nomenclature_key: str, num: int = 10):
    """
    Visualize prompt
    Args:
        st (_type_): session streamlit
        df (pd.DataFrame): dataframe with all prompts
        fname (str): name of the file
    """

    # transform the row into a dictionary
    nomenclature_text = nomenclature.get(nomenclature_key, "")

    _ = st.text_area(
        "Profile ID 👇",
        value=nomenclature_key,
        key=f"nomemclature_key_id_{num}",
        disabled=True,
        height=68,
    )
    st.session_state[f"profile_{num}"] = st.text_area(
        "Modify Profile 👇",
        value=nomenclature_text,
        key=f"nomemclature_text_box_{num}",
        height=450,
    )
    if st.button("Close"):
        st.session_state[f"prompt_dialog_open_{num}"] = True
        st.rerun()  # force rerun to close the dialog.
    return
