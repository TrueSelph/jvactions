"""This module contains the Streamlit app for the Typesense Vector Store Action"""

import os

from jvclient.client.lib.utils import call_action_walker_exec
from jvclient.client.lib.widgets import app_header, app_update_action

import streamlit as st

from streamlit_router import StreamlitRouter

import yaml


def render(router: StreamlitRouter, agent_id: str, action_id: str, info: dict) -> None:
    """
    Renders the app for the Typesense Vector Store Action.

    :param router: The StreamlitRouter instance.
    :param agent_id: The agent ID.
    :param action_id: The action ID.
    :param info: A dictionary containing additional information.
    """

    (model_key, module_root) = app_header(agent_id, action_id, info)

    with st.expander("Import Knodes", False):

        knode_data = st.text_area(
            "Agent Knodes in YAML or JSON",
            value="",
            height=170,
            key=f"{model_key}_knode_data",
        )

        if st.button("Import", key=f"{model_key}_btn_import_knodes"):
            # Call the function to import
            if result := call_action_walker_exec(
                agent_id, module_root, "import_knodes", {"data": knode_data}
            ):
                st.success("Agent knode imported successfully")
            else:
                st.error(
                    "Failed to import agent. Ensure that the  descriptor is in valid YAML format."
                )

            uploaded_file = st.file_uploader(
                "Upload file", key=f"{model_key}_agent_knode_upload"
            )

            if uploaded_file is not None:

                loaded_config = yaml.safe_load(uploaded_file)
                if loaded_config:
                    st.write(loaded_config)
                    if call_action_walker_exec(
                        agent_id, module_root, "import_knodes", {"data": knode_data}
                    ):
                        st.success("Agent knode imported successfully")
                    else:
                        st.error(
                            "Failed to import agent knode. Ensure that you are uploading a valid YAML file"
                        )

                else:
                    st.error("File is invalid. Please upload a valid YAML file")

    # Initialize page state
    if "page" not in st.session_state:
        st.session_state["page"] = 1

    # Host Configuration
    with st.expander("Typesense Configuration"):
        # Add fields for Typesense and OpenAI configurations
        st.session_state[model_key]["typesense_host"] = st.text_input(
            "Typesense Host",
            value=st.session_state[model_key].get(
                "host", os.environ.get("TYPESENSE_HOST", "typesense")
            ),
        )
        st.session_state[model_key]["typesense_port"] = st.text_input(
            "Typesense Port",
            value=st.session_state[model_key].get(
                "port", os.environ.get("TYPESENSE_PORT", "8108")
            ),
        )
        st.session_state[model_key]["typesense_protocol"] = st.text_input(
            "Typesense Protocol",
            value=st.session_state[model_key].get(
                "protocol", os.environ.get("TYPESENSE_PROTOCOL", "http")
            ),
        )
        st.session_state[model_key]["typesense_api_key"] = st.text_input(
            "Typesense API Key",
            value=st.session_state[model_key].get(
                "api_key", os.environ.get("TYPESENSE_API_KEY", "abcd")
            ),
            type="password",
        )  # Hide API key
        st.session_state[model_key]["typesense_api_key_name"] = st.text_input(
            "Typesense API Key Name",
            value=st.session_state[model_key].get("api_key_name", "typesense_key"),
        )
        st.session_state[model_key]["openai_api_key"] = st.text_input(
            "OpenAI API Key",
            value=st.session_state[model_key].get("openai_api_key", ""),
            type="password",
        )  # Hide API key
        st.session_state[model_key]["connection_timeout"] = st.number_input(
            "Connection Timeout (seconds)",
            value=int(
                st.session_state[model_key].get(
                    "connection_timeout",
                    os.environ.get("TYPESENSE_CONNECTION_TIMEOUT_SECONDS", "2"),
                )
            ),
            min_value=0,
        )
        st.session_state[model_key]["collection_name"] = st.text_input(
            "Collection Name",
            value=st.session_state[model_key].get("collection_name", ""),
        )

    # Add update button to apply changes
    app_update_action(agent_id, action_id)

    with st.expander("Purge Collection", False):

        if st.button("Delete all documents", key=f"{model_key}_btn_delete_collection"):
            # Call the function to purge
            if result := call_action_walker_exec(
                agent_id, module_root, "delete_collection"
            ):
                st.success("Collection purged successfully")
            else:
                st.error("Failed to complete purge.")

    # Paginated document display
    page = st.session_state[model_key].get("page", 1)
    per_page = 5

    result = call_list_documents(agent_id, module_root, page, per_page)

    if result:
        total = result.get("total", 0)
        documents = result.get("documents", [])
        render_paginated_documents(
            model_key, agent_id, module_root, documents, page, per_page, total
        )
    else:
        st.error("Unable to list documents")


def render_paginated_documents(
    model_key: str,
    agent_id: str,
    module_root: str,
    documents: list[dict],
    page: int,
    per_page: int,
    total: int,
) -> None:
    """
    Renders a paginated list of documents.

    :param model_key: The model key.
    :param agent_id: The agent ID.
    :param module_root: The module root.
    :param documents: The list of documents.
    :param page: The current page.
    :param per_page: The number of documents per page.
    :param total: The total number of documents.
    """

    st.divider()
    st.subheader("Documents")

    for document in documents:
        text_preview = document["text"][:200] + (
            "..." if len(document["text"]) > 100 else ""
        )

        # Display edit document form if triggered
        if st.session_state.get(f"show_edit_document_form_{document['id']}", False):
            with st.form(f"edit_document_form_{document['id']}"):
                edit_document_text = st.text_area(
                    "Document Text", value=document["text"]
                )
                submitted = st.form_submit_button("Update")

                if submitted:
                    # Call the function to add the new text document
                    if call_update_document(
                        agent_id,
                        module_root,
                        id=document["id"],
                        data={"text": edit_document_text},
                    ):
                        st.session_state[
                            f"show_edit_document_form_{document['id']}"
                        ] = False
                        st.rerun()
                    else:
                        st.error("Failed to update document")
        else:
            st.text(text_preview)

        # Add buttons for each document
        col1, col2, col3 = st.columns([1, 1, 10])
        with col1:
            if st.button("Edit", key=f"edit_{document['id']}"):
                st.session_state[f"show_edit_document_form_{document['id']}"] = True
                st.rerun()
        with col2:
            if st.button("Delete", key=f"delete_{document['id']}"):
                # Call the function to delete the text document
                if call_delete_document(agent_id, module_root, id=document["id"]):
                    st.rerun()
                else:
                    st.error("Failed to delete document")

    st.divider()

    # Add a button to add a new document
    if st.button("Add Document"):
        # Trigger form visibility in session state
        st.session_state["show_add_document_form"] = True

    # Display add document form if triggered
    if st.session_state.get("show_add_document_form", False):
        with st.form("add_document_form"):
            new_document_text = st.text_area("Document Text")
            submitted = st.form_submit_button("Submit")

            if submitted:
                # Call the function to add the new text document
                if call_add_texts(agent_id, module_root, texts=[new_document_text]):
                    st.session_state["show_add_document_form"] = False
                    st.rerun()
                else:
                    st.error("Failed to add document")

    st.divider()

    if total > 0:

        # Navigation through pages
        pages = total // per_page + (1 if total % per_page > 0 else 0)
        st.write(f"Page {page} of {pages}")

        if page > 1 and st.button("Previous Page"):
            st.session_state[model_key]["page"] = page - 1

        if page < pages and st.button("Next Page"):
            st.session_state[model_key]["page"] = page + 1


def call_list_documents(
    agent_id: str, module_root: str, page: int, per_page: int
) -> dict:
    """
    Calls the list_documents walker in the Typesense Vector Store Action.

    :param agent_id: The agent ID.
    :param module_root: The module root.
    :param page: The page number.
    :param per_page: The number of documents per page.
    :return: The response dictionary.
    """

    args = {"page": page, "per_page": per_page}
    return call_action_walker_exec(agent_id, module_root, "list_documents", args)


def call_add_texts(agent_id: str, module_root: str, texts: list[str]) -> dict:
    """
    Calls the add_texts walker in the Typesense Vector Store Action.

    :param agent_id: The agent ID.
    :param module_root: The module root.
    :param texts: The list of texts to add.
    :return: The response dictionary.
    """

    args = {"texts": texts}
    return call_action_walker_exec(agent_id, module_root, "add_texts", args)


def call_delete_document(agent_id: str, module_root: str, id: str) -> dict:
    """
    Calls the delete_document walker in the Typesense Vector Store Action.

    :param agent_id: The agent ID.
    :param module_root: The module root.
    :param id: The document ID.
    :return: The response dictionary.
    """

    args = {"id": id}
    return call_action_walker_exec(agent_id, module_root, "delete_document", args)


def call_update_document(agent_id: str, module_root: str, id: str, data: dict) -> dict:
    """
    Calls the update_document walker in the Typesense Vector Store Action.

    :param agent_id: The agent ID.
    :param module_root: The module root.
    :param id: The document ID.
    :param data: The data to update.
    :return: The response dictionary.
    """

    args = {"id": id, "data": data}
    return call_action_walker_exec(agent_id, module_root, "update_document", args)
