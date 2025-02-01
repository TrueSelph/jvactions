"""This module renders the streamlit application for the avatar action."""

import uuid

import streamlit as st
from jvclient.client.lib.utils import call_action_walker_exec, decode_base64_image
from jvclient.client.lib.widgets import app_header, app_update_action
from streamlit_router import StreamlitRouter


def render(router: StreamlitRouter, agent_id: str, action_id: str, info: dict) -> None:
    """Render the streamlit application for the avatar action.

    :param router: The StreamlitRouter instance.
    :param agent_id: The agent ID.
    :param action_id: The action ID.
    :param info: The action info.
    """

    # Add application header controls
    (model_key, module_root) = app_header(agent_id, action_id, info)

    # render the avatar image if there is one...
    if st.session_state[model_key]["image_data"]:
        st.image(
            decode_base64_image(st.session_state[model_key]["image_data"]),
            caption="image preview",
            width=200,
        )

    # we need a new uploader key per upload to completely reset the upload control once we're done with it
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = f"{str(uuid.uuid4())}_file_uploader"

    selected_file = st.file_uploader(
        "Choose an image file",
        type=["jpg", "png", "jpeg"],
        key=st.session_state.uploader_key,
    )

    if selected_file is not None:
        # Display the uploaded image
        st.image(selected_file, caption="image preview", width=200)

        if st.button("Upload"):
            # Prepare list of files if any are uploaded
            files_dict = {}
            if selected_file:
                files_dict[selected_file.name] = (
                    selected_file.read(),
                    selected_file.type,
                )

            # Call the function to add the new text document
            if call_set_avatar(agent_id, module_root, files_dict):
                # Remove uploader_key to hide the preview on success
                del st.session_state["uploader_key"]
                # Remove the model_key to refresh the model
                del st.session_state[model_key]
                # now reload
                st.rerun()

            else:
                st.error("Failed to add avatar")

    # Add update button to apply changes
    app_update_action(agent_id, action_id)


def call_set_avatar(agent_id: str, module_root: str, files: dict) -> dict:
    """Call the set_avatar action."""
    return call_action_walker_exec(agent_id, module_root, "set_avatar", None, files)


def call_get_avatar(agent_id: str, module_root: str) -> dict:
    """Call the get_avatar action."""
    return call_action_walker_exec(agent_id, module_root, "get_avatar")
