import streamlit as st
from streamlit import session_state as ss
import os
from pathlib import Path
import logging
from src.maps import config as conf, init_session_num, reset_session_num
from src.conf import *
from src.maintenance import selected_modifica, visualiza_modify_nomemclature


def change_state_1(session, pp):
    """
    change state after leave conversation
    params:
    st (streamlit): streamlit object
    pp (streamlit.empty): placeholder

    """
    reset_session_num(session, "1")
    pp.empty()
    del pp
    session.empty()
    session.cache_data.clear()
    session.stop()
    return


def main(placeholder):
    """
    Configuration page APP
    Args:
        placeholder (streamlit.empty): placeholder
    """
    if st.button("Salir", on_click=change_state_1, args=(st, placeholder)):
        logging.info("Salir and writing history")

    col1, col2 = 50, 50
    row1_1, row1_2 = st.columns((col1, col2))
    if "init_run_1" not in st.session_state:
        st.session_state["init_run_1"] = False
    if st.session_state["init_run_1"] == False:
        init_session_num(st, ss, "1", col1, col2, conf["1"]["config_1"], None)

    with row1_1:

        keys_nomemclatures = list(nomenclature.keys())
        nomemclatures_selection = st.selectbox(
            "Select Model to Test 👇👇👇",
            keys_nomemclatures,
            index=None,
            on_change=selected_modifica,
            args=[st, "1", False],
            key="select_box_modifica_1",
        )
        if st.session_state["selector_selected_modifica_1"] == True:
            visualiza_modify_nomemclature(
                st,
                nomemclatures_selection,
                num=1,
            )


if __name__ == "__main__":

    # access to keys and service account
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    path = Path(ROOT_DIR)
    PROJECT_DIR = path.parent.absolute().as_posix()
    # Set page layout
    st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
    st.title("CSM. Configuration")
    # go to login page if not authenticated
    if (
        st.session_state["authentication_status"] == None
        or st.session_state["authentication_status"] == False
    ):
        st.session_state.runpage = "main.py"
        st.switch_page("main.py")

    if "salir_1" not in st.session_state:
        st.session_state["salir_1"] = False

    if st.session_state["salir_1"] == False:
        placeholder_conf = st.empty()

    main(placeholder=placeholder_conf)
