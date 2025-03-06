"""This module contains the Streamlit app for the Typesense Vector Store Action"""

import json
from io import BytesIO

from jvcli.client.lib.utils import call_action_walker_exec, jac_yaml_dumper
from jvcli.client.lib.widgets import app_controls, app_header, app_update_action

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
        # User chooses between inputting YAML/JSON text or uploading a file
        knode_source = st.radio(
            "Choose data source:",
            ("Text input", "Upload file"),
            key=f"{model_key}_knode_source"
        )

        data_to_import = ""
        if knode_source == "Text input":
            data_to_import = st.text_area(
                "Agent Knodes in YAML or JSON",
                value="",
                height=170,
                key=f"{model_key}_knode_data",
            )

        uploaded_file = None
        if knode_source == "Upload file":
            uploaded_file = st.file_uploader(
                "Upload file (YAML or JSON)",
                type=["yaml", "json"],
                key=f"{model_key}_agent_knode_upload"
            )

        embeddings = st.toggle(
            "Import with Embeddings",
            value=True,
            key=f"{model_key}_import_embeddings_json",
        )

        if st.button("Import", key=f"{model_key}_btn_import_knodes"):
            if uploaded_file:
                # Read the contents of the uploaded file
                file_content = uploaded_file.read().decode("utf-8")
                
                # Determine if it's YAML or JSON and parse accordingly
                try:
                    if isinstance(file_content, str):
                        if uploaded_file.type == "application/json":
                            data_to_import = json.loads(file_content)  # parsed JSON object
                        else:
                            data_to_import = yaml.safe_load(file_content)  # parsed YAML object
                    else:
                        data_to_import = file_content
                        
                    if data_to_import is None:
                        st.error("File is empty or invalid.")

                except Exception as e:
                    st.error(f"Error loading file: {e}")

            if data_to_import:
                # Call the function to import with parsed data (either JSON or YAML object)
                if result := call_action_walker_exec(
                    agent_id,
                    module_root,
                    "import_knodes",
                    {"data": data_to_import, "embeddings": embeddings},
                ):
                    st.success("Agent knode imported successfully")
                else:
                    st.error(
                        "Failed to import knodes. Ensure that the descriptor is in valid YAML or JSON format."
                    )
            else:
                st.error("No data to import. Please provide valid text or upload a valid file.")



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
            params = {"export_json": export_json, "embeddings": embeddings, "include_id": False}

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

                    # JSON display
                    st.json(knode_entries)

                else:

                    knode_entries = jac_yaml_dumper(data=result, indent=2, sort_keys=False)
                    # Prepare downloadable YAML file
                    yaml_file = BytesIO(knode_entries.encode("utf-8"))
                    st.download_button(
                        label="Download YAML File",
                        data=yaml_file,
                        file_name="exported_knodes.yaml",
                        mime="application/x-yaml",
                        key="download_yaml",
                    )

                    # YAML display
                    st.code(knode_entries, language="yaml")

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
    params = {"export_json": True, "embeddings": False, "include_id": True}
    documents = call_action_walker_exec(
        agent_id, module_root, "export_knodes", params
    )

    if documents:
        render_paginated_documents(
            agent_id, module_root, documents
        )
    else:
        st.error("Unable to list documents")


# Additional function definitions remain unchanged


def render_paginated_documents(
    agent_id: str,
    module_root: str,
    documents: list[dict]
) -> None:
    """
    Renders a paginated list of documents.

    :param agent_id: The agent ID.
    :param module_root: The module root.
    :param documents: The list of documents.
    """

    st.divider()
    col1, col2 = st.columns([0.3, 0.7])  # Adjust width ratio as needed

    with col1:
        st.subheader("Documents")  # Title

    with col2:
        search_query = st.text_input("🔍 Search Documents", placeholder="Type to search by text...", label_visibility="collapsed")

    params = {"export_json": True, "embeddings": False, "include_id": True}

    # Call the function to export memory
    documents = call_action_walker_exec(
        agent_id, module_root, "export_knodes", params
    )
    if isinstance(documents, str):
        try:
            documents = json.loads(documents)
        except json.JSONDecodeError:
            st.write("❌ The string is not valid JSON.")
            documents = []


    if search_query:
        filtered_documents = [doc for doc in documents if search_query.lower() in doc["text"].lower()]
    else:
        filtered_documents = documents

    # Pagination settings
    ITEMS_PER_PAGE = 5

    # Initialize the page number in session state if not already set
    if "page" not in st.session_state:
        st.session_state.page = 1

    total_items = len(filtered_documents)
    total_pages = (total_items - 1) // ITEMS_PER_PAGE + 1

    # Ensure current page is within valid range
    if st.session_state.page < 1:
        st.session_state.page = 1
    elif st.session_state.page > total_pages:
        st.session_state.page = total_pages

    start_idx = (st.session_state.page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    documents_to_display = filtered_documents[start_idx:end_idx]


    for document in documents_to_display:
        text_preview = document["text"][:200] + (
            "..." if len(document["text"]) > 100 else ""
        )

        # Display edit document form if triggered
        if st.session_state.get(f"show_edit_document_form_{document['id']}", False):
            with st.form(f"edit_document_form_{document['id']}"):
                num_lines = document["text"].count("\n") + 1  # Count lines
                line_height = 20  # Approximate pixel height per line
                estimated_height = min(max(num_lines * line_height, 100), 800)  # Keep within reasonable bounds

                edit_document_text = st.text_area(
                    "Document Text", value=document["text"], height=estimated_height
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
    # Pagination Navigation Buttons
    col_prev, col_page, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.session_state.page > 1:
            if st.button("⬅️ Previous Page"):
                st.session_state.page -= 1
    with col_page:
        st.write(f"Page {st.session_state.page} of {total_pages}")
    with col_next:
        if st.session_state.page < total_pages:
            if st.button("Next Page ➡️"):
                st.session_state.page += 1
    
    st.divider()

    # Add a button to add a new document
    if st.button("Add Document"):
        # Trigger form visibility in session state
        st.session_state["show_add_document_form"] = True

    # Display add document form if triggered
    if st.session_state.get("show_add_document_form", False):
        with st.form("add_document_form"):
            new_document_text = st.text_area("Document Text")
            metadatas_input = st.text_area("Metadata (JSON format)")
            try:
                metadatas = json.loads(metadatas_input) if metadatas_input else []
                if isinstance(metadatas, dict):
                    metadatas = [metadatas]
            except json.JSONDecodeError:
                st.error("Invalid JSON format for metadata")
                metadatas = []
            submitted = st.form_submit_button("Submit")

            if submitted:
                # Call the function to add the new text document
                if call_add_texts(agent_id, module_root, texts=[new_document_text], metadatas=metadatas):
                    st.session_state["show_add_document_form"] = False
                    st.rerun()
                else:
                    st.error("Failed to add document")



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


def call_add_texts(agent_id: str, module_root: str, texts: list[str], metadatas: list[dict]) -> dict:
    """
    Calls the add_texts walker in the Typesense Vector Store Action.

    :param agent_id: The agent ID.
    :param module_root: The module root.
    :param texts: The list of texts to add.
    :param metadatas: The list of metadatas associated with the texts.
    :return: The response dictionary.
    """

    args = {"texts": texts, "metadatas": metadatas}
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
