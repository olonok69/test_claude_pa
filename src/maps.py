# -*- coding: utf-8 -*-
import logging


# Session configuration
config = {
    "1": {
        "config_1_del": [
            "salir_1",
            "init_run_1",
            "select_box_modifica_1",
            "selector_selected_modifica_1",
            "prompt_dialog_open_1",
        ],
        "config_1": [
            "selector_selected_modifica_1",
        ],
    },
    "12": {
        "config_12_del": [
            "salir_12",
            "init_run_12",
            "select_box_modifica_12",
            "selector_selected_modifica_12",
            "select_box_modifica_prompt_12",
            "select_box_modifica_pericial_12",
            "selector_selected_section_12",
            "selector_selected_pericial_12",
            "dialog_selected_section_12",
            "prompt_dialog_open_12",
            "upload_state_12",
            "expander_12",
        ],
        "config_12": [
            "selector_selected_modifica_12",
            "selector_selected_section_12",
            "selector_selected_pericial_12",
            "dialog_selected_section_12",
            "prompt_dialog_open_12",
            "upload_state_12",
            "expander_12",
        ],
    },
    "13": {
        "config_13_del": [
            "salir_13",
            "init_run_13",
            "select_box_modifica_13",
            "selector_selected_modifica_13",
            "selector_selected_section_13",
            "dialog_selected_section_13",
            "prompt_dialog_open_13",
            "upload_state_13",
            "expander_13",
            "output_13",
            "show_df_13",
            "model_13",
            "llm_13",
            "file_uploader_13",
        ],
        "config_13": [
            "selector_selected_modifica_13",
            "selector_selected_section_13",
            "selector_selected_pericial_13",
            "dialog_selected_section_13",
            "prompt_dialog_open_13",
            "upload_state_13",
            "expander_13",
            "output_13",
            "show_df_13",
        ],
    },
    "14": {
        "config_14_del": [
            "salir_14",
            "init_run_14",
            "visitor_selector_14",
            "recommendation_service_14",
            "visitor_list_14",
            "last_recommendation_result_14",
            "last_processing_time_14",
            "selected_visitor_14",
            "recommendations_generated_14",
            "custom_business_rules_14",
            "saved_custom_rules_14",
            "rule_set_option_14",
            "switch_to_rules_tab_14",
        ],
        "config_14": [
            "recommendation_service_14",
            "visitor_list_14",
            "last_recommendation_result_14",
            "last_processing_time_14",
            "selected_visitor_14",
            "recommendations_generated_14",
            "custom_business_rules_14",
            "saved_custom_rules_14",
            "switch_to_rules_tab_14",
        ],
    },
}


def reset_session_num(session, num: int = "10"):
    """
    Delete session state for multiple files option
    param: st  session
    param: ss  session state
    param: model  chat (gemini model)
    """

    for x in list(session.session_state.keys()):
        if num in x and x in config[num][f"config_{num}_del"]:
            try:
                del session.session_state[x]
                logging.info(f"deleted {x}")
            except:
                logging.info(f"error deleting {x}")

    # placeholder for multiple files

    return


def init_session_num(sess, ss, num, col1, col2, config, model: None):
    """
    initialize session state
    initialize session state
    Args:
    param: st  session
    param: ss  session state
    param: num  number of session
    param: col1  column 1
    param: col2  column 2
    param: config  configuration
    param: model  chat (gemini model)
    """
    if (
        f"user_prompt_history_{num}" not in sess.session_state
        and f"user_prompt_history_{num}" in config
    ):

        sess.session_state[f"user_prompt_history_{num}"] = []

    if (
        f"user_prompt_history_faiss_{num}" not in sess.session_state
        and f"user_prompt_history_faiss_{num}" in config
    ):
        sess.session_state[f"user_prompt_history_faiss_{num}"] = []

    if f"output_{num}" not in sess.session_state and f"output_{num}" in config:
        sess.session_state[f"output_{num}"] = []

    if (
        f"chat_answers_history_faiss_{num}" not in sess.session_state
        and f"chat_answers_history_faiss_{num}" in config
    ):
        sess.session_state[f"chat_answers_history_faiss_{num}"] = []

    if (
        f"chat_answers_history_{num}" not in sess.session_state
        and f"chat_answers_history_{num}" in config
    ):
        sess.session_state[f"chat_answers_history_{num}"] = []

    if (
        f"multi_file_name_{num}" not in sess.session_state
        and f"multi_file_name_{num}" in config
    ):

        sess.session_state[f"multi_file_name_{num}"] = []

    if (
        f"multi_file_pages_{num}" not in sess.session_state
        and f"multi_file_pages_{num}" in config
    ):

        sess.session_state[f"multi_file_pages_{num}"] = []

    if f"pages_{num}" not in sess.session_state and f"pages_{num}" in config:
        sess.session_state[f"pages_{num}"] = []

    if f"metadatas_{num}" not in sess.session_state and f"metadatas_{num}" in config:
        sess.session_state[f"metadatas_{num}"] = []

    if f"ids_{num}" not in sess.session_state and f"ids_{num}" in config:
        sess.session_state[f"ids_{num}"] = []

    if (
        f"chat_history_{num}" not in sess.session_state
        and f"chat_history_{num}" in config
    ):

        sess.session_state[f"chat_history_{num}"] = []

    if (
        f"docs_context_names_{num}" not in sess.session_state
        and f"docs_context_names_{num}" in config
    ):
        sess.session_state[f"docs_context_names_{num}"] = []

    if f"documents_{num}" not in sess.session_state and f"documents_{num}" in config:
        sess.session_state[f"documents_{num}"] = []

    if (
        f"docs_context_{num}" not in sess.session_state
        and f"docs_context_{num}" in config
    ):

        sess.session_state[f"docs_context_{num}"] = []

    if (
        f"initialized_{num}" not in sess.session_state
        and f"initialized_{num}" in config
    ):

        sess.session_state[f"initialized_{num}"] = "False"

    if f"chat_{num}" not in sess.session_state and f"chat_{num}" in config:
        sess.session_state[f"chat_{num}"] = None

    if (
        f"conversational_rag_chain_{num}" not in sess.session_state
        and f"conversational_rag_chain_{num}" in config
    ):

        sess.session_state[f"conversational_rag_chain_{num}"] = None

    if f"retriever_{num}" not in sess.session_state and f"retriever_{num}" in config:
        sess.session_state[f"retriever_{num}"] = None

    if f"file_bytes_{num}" not in sess.session_state and f"file_bytes_{num}" in config:
        sess.session_state[f"file_bytes_{num}"] = None

    if f"embeddings_{num}" not in sess.session_state and f"embeddings_{num}" in config:
        sess.session_state[f"embeddings_{num}"] = None

    if (
        f"vectorstore_{num}" not in sess.session_state
        and f"vectorstore_{num}" in config
    ):

        sess.session_state[f"vectorstore_{num}"] = None

    if f"index_{num}" not in sess.session_state and f"index_{num}" in config:
        sess.session_state[f"index_{num}"] = None

    if (
        f"list_images_{num}" not in sess.session_state
        and f"list_images_{num}" in config
    ):

        sess.session_state[f"list_images_{num}"] = []

    if (
        f"user_prompt_history_{num}" not in sess.session_state
        and f"user_prompt_history_{num}" in config
    ):
        sess.session_state[f"user_prompt_history_{num}"] = []

    if (
        f"chat_answers_history_{num}" not in sess.session_state
        and f"chat_answers_history_{num}" in config
    ):
        sess.session_state[f"chat_answers_history_{num}"] = []

    # placeholder for multiple files
    if f"file_name_{num}" not in sess.session_state and f"file_name_{num}" in config:
        sess.session_state[f"file_name_{num}"] = "no file"

    if (
        f"file_history_{num}" not in sess.session_state
        and f"file_history_{num}" in config
    ):
        sess.session_state[f"file_history_{num}"] = "no file"

    if (
        f"prompt_introduced_{num}" not in sess.session_state
        and f"prompt_introduced_{num}" in config
    ):
        sess.session_state[f"prompt_introduced_{num}"] = ""

    if (
        f"name_file_kb_faiss_selected_{num}" not in sess.session_state
        and f"name_file_kb_faiss_selected_{num}" in config
    ):
        sess.session_state[f"name_file_kb_faiss_selected_{num}"] = ""

    if (
        f"history_conversation_with_model_{num}" not in sess.session_state
        and f"history_conversation_with_model_{num}" in config
    ):
        sess.session_state[f"history_conversation_with_model_{num}"] = ""

    if (
        f"current_prompt_{num}" not in sess.session_state
        and f"current_prompt_{num}" in config
    ):
        sess.session_state[f"current_prompt_{num}"] = ""

    if (
        f"answer_prompt_{num}" not in sess.session_state
        and f"answer_prompt_{num}" in config
    ):
        sess.session_state[f"answer_prompt_{num}"] = ""

    if (
        f"seccion_introduced_{num}" not in sess.session_state
        and f"seccion_introduced_{num}" in config
    ):
        sess.session_state[f"seccion_introduced_{num}"] = ""

    if (
        f"upload_state_{num}" not in sess.session_state
        and f"upload_state_{num}" in config
    ):
        sess.session_state[f"upload_state_{num}"] = ""

    if (
        f"answer_introduced_{num}" not in sess.session_state
        and f"answer_introduced_{num}" in config
    ):
        sess.session_state[f"answer_introduced_{num}"] = ""

    if f"answer_{num}" not in sess.session_state and f"answer_{num}" in config:
        sess.session_state[f"answer_{num}"] = ""

    if (
        f"prompt_combined_filename_{num}" not in sess.session_state
        and f"prompt_combined_filename_{num}" in config
    ):
        sess.session_state[f"prompt_combined_filename_{num}"] = ""

    if (
        f"instruction_to_be_send_{num}" not in sess.session_state
        and f"instruction_to_be_send_{num}" in config
    ):
        sess.session_state[f"instruction_to_be_send_{num}"] = ""

    if f"prompt_{num}" not in sess.session_state and f"prompt_{num}" in config:
        sess.session_state[f"prompt_{num}"] = ""

    if f"chat_true_{num}" not in sess.session_state and f"chat_true_{num}" in config:
        sess.session_state[f"chat_true_{num}"] = "no_chat"

    if (
        f"buttom_popup_{num}" not in sess.session_state
        and f"buttom_popup_{num}" in config
    ):
        sess.session_state[f"buttom_popup_{num}"] = "no_buttom"

    if (
        f"buttom_has_send_{num}" not in sess.session_state
        and f"buttom_has_send_{num}" in config
    ):
        sess.session_state[f"buttom_has_send_{num}"] = "no_buttom"

    if (
        f"buttom_send_clicked_{num}" not in sess.session_state
        and f"buttom_send_clicked_{num}" in config
    ):
        sess.session_state[f"buttom_send_clicked_{num}"] = False

    if (
        f"dialog_selected_section_{num}" not in sess.session_state
        and f"dialog_selected_section_{num}" in config
    ):
        sess.session_state[f"dialog_selected_section_{num}"] = False

    if f"show_df_{num}" not in sess.session_state and f"show_df_{num}" in config:
        sess.session_state[f"show_df_{num}"] = False
    if (
        f"selector_selected_pericial_{num}" not in sess.session_state
        and f"selector_selected_pericial_{num}" in config
    ):
        sess.session_state[f"selector_selected_pericial_{num}"] = False

    if (
        f"selector_selected_section_{num}" not in sess.session_state
        and f"selector_selected_section_{num}" in config
    ):
        sess.session_state[f"selector_selected_section_{num}"] = False

    if (
        f"selector_selected_modifica_{num}" not in sess.session_state
        and f"selector_selected_modifica_{num}" in config
    ):
        sess.session_state[f"selector_selected_modifica_{num}"] = False

    if (
        f"pdf_dialog_open_{num}" not in sess.session_state
        and f"pdf_dialog_open_{num}" in config
    ):
        sess.session_state[f"pdf_dialog_open_{num}"] = False
    if (
        f"prompt_dialog_open_{num}" not in sess.session_state
        and f"prompt_dialog_open_{num}" in config
    ):
        sess.session_state[f"prompt_dialog_open_{num}"] = False

    if (
        f"selector_selected_section_delete_{num}" not in sess.session_state
        and f"selector_selected_section_delete_{num}" in config
    ):
        sess.session_state[f"selector_selected_section_delete_{num}"] = False

    if (
        f"selector_selected_delete_{num}" not in sess.session_state
        and f"selector_selected_delete_{num}" in config
    ):
        sess.session_state[f"selector_selected_delete_{num}"] = False

    if (
        f"selector_selected_add_{num}" not in sess.session_state
        and f"selector_selected_add_{num}" in config
    ):
        sess.session_state[f"selector_selected_add_{num}"] = False

    if (
        f"selector_selected_answer_delete_{num}" not in sess.session_state
        and f"selector_selected_answer_delete_{num}" in config
    ):
        sess.session_state[f"selector_selected_answer_delete_{num}"] = False

    if (
        f"selector_selected_answer_delete_no_case_{num}" not in sess.session_state
        and f"selector_selected_answer_delete_no_case_{num}" in config
    ):
        sess.session_state[f"selector_selected_answer_delete_no_case_{num}"] = False

    if (
        f"add_file_kb_selected_{num}" not in sess.session_state
        and f"add_file_kb_selected_{num}" in config
    ):
        sess.session_state[f"add_file_kb_selected_{num}"] = False

    if (
        f"file_faiss_selected_{num}" not in sess.session_state
        and f"file_faiss_selected_{num}" in config
    ):
        sess.session_state[f"file_faiss_selected_{num}"] = False

    if (
        f"selector_selected_pericial_delete_{num}" not in sess.session_state
        and f"selector_selected_pericial_delete_{num}" in config
    ):
        sess.session_state[f"selector_selected_pericial_delete_{num}"] = False

    if (
        f"buttom_visualiza_faiss_clicked_{num}" not in sess.session_state
        and f"buttom_visualiza_faiss_clicked_{num}" in config
    ):

        sess.session_state[f"buttom_visualiza_faiss_clicked_{num}"] = False

    if f"checkbox_{num}" not in sess.session_state and f"checkbox_{num}" in config:
        sess.session_state[f"checkbox_{num}"] = False

    if (
        f"file_kb_faiss_selected_{num}" not in sess.session_state
        and f"file_kb_faiss_selected_{num}" in config
    ):
        sess.session_state[f"file_kb_faiss_selected_{num}"] = False

    if (
        f"buttom_send_visualiza_{num}" not in sess.session_state
        and f"buttom_send_visualiza_{num}" in config
    ):
        sess.session_state[f"buttom_send_visualiza_{num}"] = False

    if (
        f"file_prompt_selected_visualiza_{num}" not in sess.session_state
        and f"file_prompt_selected_visualiza_{num}" in config
    ):
        sess.session_state[f"file_prompt_selected_visualiza_{num}"] = False

    if (
        f"file_and_answer_select_has_changed_{num}" not in sess.session_state
        and f"file_and_answer_select_has_changed_{num}" in config
    ):
        sess.session_state[f"file_and_answer_select_has_changed_{num}"] = False

    if (
        f"section_prompt_selected_{num}" not in sess.session_state
        and f"section_prompt_selected_{num}" in config
    ):
        sess.session_state[f"section_prompt_selected_{num}"] = False

    if (
        f"pericial_prompt_selected_{num}" not in sess.session_state
        and f"pericial_prompt_selected_{num}" in config
    ):
        sess.session_state[f"pericial_prompt_selected_{num}"] = False

    if (
        f"buttom_resfresh_clicked_{num}" not in sess.session_state
        and f"buttom_resfresh_clicked_{num}" in config
    ):
        sess.session_state[f"buttom_resfresh_clicked_{num}"] = False

    if (
        f"b_accept_inside_pericial_{num}" not in sess.session_state
        and f"b_accept_inside_pericial_{num}" in config
    ):
        sess.session_state[f"b_accept_inside_pericial_{num}"] = False

    if f"store_{num}" not in sess.session_state and f"store_{num}" in config:
        sess.session_state[f"store_{num}"] = {}

    if f"pdf_ref_{num}" not in ss and f"pdf_ref_{num}" in config:
        ss[f"pdf_ref_{num}"] = None

    if f"pdf_{num}" not in ss and f"pdf_{num}" in config:
        ss[f"pdf_{num}"] = None

    if f"value_{num}" not in sess.session_state and f"value_{num}" in config:
        sess.session_state[f"value_{num}"] = 0

    # buttom send to gemini
    if (
        f"buttom_send_not_clicked_{num}" not in sess.session_state
        and f"buttom_send_not_clicked_{num}" in config
    ):

        sess.session_state[f"buttom_send_not_clicked_{num}"] = False

    if (
        f"file_prompt_selected_{num}" not in sess.session_state
        and f"file_prompt_selected_{num}" in config
    ):

        sess.session_state[f"file_prompt_selected_{num}"] = False

    if f"vcol1doc_{num}" not in sess.session_state and f"vcol1doc_{num}" in config:
        sess.session_state[f"vcol1doc_{num}"] = col1

    if f"vcol2doc_{num}" not in sess.session_state and f"vcol2doc_{num}" in config:
        sess.session_state[f"vcol2doc_{num}"] = col2

    if f"expander_{num}" not in sess.session_state and f"expander_{num}" in config:
        sess.session_state[f"expander_{num}"] = True
    sess.session_state[f"init_run_{num}"] = True
    return