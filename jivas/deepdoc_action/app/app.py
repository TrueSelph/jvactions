"""This module contains the Streamlit app for the Typesense Vector Store Action"""

import json
from io import BytesIO

from jvclient.client.lib.utils import call_action_walker_exec, jac_yaml_dumper
from jvclient.client.lib.widgets import app_controls, app_header, app_update_action

import streamlit as st

from streamlit_router import StreamlitRouter

import yaml


def render(router: StreamlitRouter, agent_id: str, action_id: str, info: dict) -> None:
    """
    Renders a paginated list of documents.

    :param agent_id: The agent ID.
    :param action_id: The action ID.
    :param info: Additional information.
    """
    (model_key, module_root) = app_header(agent_id, action_id, info)

    # Add new PDF Parser section
    with st.expander("Parse PDFs", False):
        # File upload section
        uploaded_pdfs = st.file_uploader(
            "Upload PDF files",
            type=["pdf", "docx", "doc", "txt"],
            accept_multiple_files=True,
            key=f"{model_key}_pdf_upload"
        )

        # URL input section
        pdf_urls = st.text_area(
            "Enter PDF URLs (one per line)",
            height=100,
            help="Enter URLs to PDF files, one URL per line",
            key=f"{model_key}_pdf_urls"
        )

        # Process URLs into a list
        url_list = [url.strip() for url in pdf_urls.split('\n') if url.strip()]

        # Validation message
        if not uploaded_pdfs and not url_list:
            st.info("Please either upload PDF files or provide PDF URLs (or both)")

        if st.button("Parse PDFs", key=f"{model_key}_btn_parse_pdfs"):
            # Prepare the payload
            payload = {
                "files": uploaded_pdfs if uploaded_pdfs else [],
                "urls": url_list if url_list else []
            }
            print("Payload:", payload)

            # Call the parse_pdfs walker
            result = call_action_walker_exec(
                agent_id,
                module_root,
                "parse_pdfs",
                payload
            )
            
            if result:
                st.success("PDFs parsed successfully!")
                # Display number of processed files
                total_processed = len(uploaded_pdfs) + len(url_list)
                st.info(f"Processed {total_processed} {'file' if total_processed == 1 else 'files'}")
            else:
                st.error("Failed to parse PDFs. Please check your inputs and try again.")

    # Add update button to apply changes
    app_update_action(agent_id, action_id)

# Additional function definitions remain unchanged


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
