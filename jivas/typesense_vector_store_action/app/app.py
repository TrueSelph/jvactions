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

    with st.expander("Import Knodes", False):
        knode_data = st.text_area(
            "Agent Knodes in YAML or JSON",
            value="",
            height=170,
            key=f"{model_key}_knode_data",
        )
        embeddings = st.toggle(
            "Import with Embeddings",
            value=True,
            key=f"{model_key}_import_embeddings_json",
        )

        if st.button("Import", key=f"{model_key}_btn_import_knodes"):
            # Call the function to import
            if result := call_action_walker_exec(
                agent_id,
                module_root,
                "import_knodes",
                {"data": knode_data, "embeddings": embeddings},
            ):
                st.success("Agent knode imported successfully")
            else:
                st.error(
                    "Failed to import knodes. Ensure that the descriptor is in valid YAML or JSON format."
                )

            uploaded_file = st.file_uploader(
                "Upload file", key=f"{model_key}_agent_knode_upload"
            )

            if uploaded_file is not None:
                loaded_config = yaml.safe_load(uploaded_file)
                if loaded_config:
                    st.write(loaded_config)
                    if call_action_walker_exec(
                        agent_id,
                        module_root,
                        "import_knodes",
                        {"data": knode_data, "embeddings": embeddings},
                    ):
                        st.success("Agent knodes imported successfully")
                    else:
                        st.error(
                            "Failed to import agent knode. Ensure that you are uploading a valid YAML file"
                        )

                else:
                    st.error("File is invalid. Please upload a valid YAML or JSON file")

    with st.expander("Export Knodes", False):
        export_json = st.toggle(
            "Export as JSON", value=True, key=f"{model_key}_export_json"
        )
        embeddings = st.toggle(
            "Export with Embeddings",
            value=True,
            key=f"{model_key}_export_embeddings_json",
        )

        # Toggle label adjustment
        toggle_label = "Export as JSON" if export_json else "Export as YAML"
        st.caption(f"**{toggle_label} enabled**")

        if st.button("Export", key=f"{model_key}_btn_export_knodes"):
            # Prepare parameters
            params = {"export_json": export_json, "embeddings": embeddings}

            # Call the function to export memory
            result = call_action_walker_exec(
                agent_id, module_root, "export_knodes", params
            )

            # Log results and provide download options
            if result:
                st.success("Agent memory exported successfully!")

                # Process the first two entries of memory
                knode_entries = result
                if export_json:
                    # JSON display
                    st.json(knode_entries)

                    # Prepare downloadable JSON file
                    json_data = json.dumps(result, indent=4)

                    json_file = BytesIO(json_data.encode("utf-8"))
                    st.download_button(
                        label="Download JSON File",
                        data=json_file,
                        file_name="exported_knodes.json",
                        mime="application/json",
                        key="download_json",
                    )
                else:
                    # YAML display
                    st.code(knode_entries, language="yaml")

                    # full memory dump
                    full_yaml_data = jac_yaml_dumper(data=result, sort_keys=False)

                    # Prepare downloadable YAML file
                    yaml_file = BytesIO(full_yaml_data.encode("utf-8"))
                    st.download_button(
                        label="Download YAML File",
                        data=yaml_file,
                        file_name="exported_knodes.yaml",
                        mime="application/x-yaml",
                        key="download_yaml",
                    )
            else:
                st.error(
                    "Failed to export knodes. Please check your inputs and try again."
                )

    # Initialize page state
    if "page" not in st.session_state:
        st.session_state["page"] = 1

    # Host Configuration
    with st.expander("Typesense Configuration"):
        # add app main controls
        app_controls(agent_id, action_id)

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
