"""Provide the Streamlit UI for the Facebook action."""

from jvclient.client.lib.widgets import app_controls, app_header, app_update_action

from streamlit_router import StreamlitRouter


def render(router: StreamlitRouter, agent_id: str, action_id: str, info: dict) -> None:
    """
    Render the Facebook action interface.

    Args:
        router (StreamlitRouter): The Streamlit router instance.
        agent_id (str): The agent ID.
        action_id (str): The action ID.
        info (dict): Additional metadata information.
    """
    # Add app header controls
    model_key, module_root = app_header(agent_id, action_id, info)

    # Add app main controls
    app_controls(agent_id, action_id)

    # Add update button to apply changes
    app_update_action(agent_id, action_id)
