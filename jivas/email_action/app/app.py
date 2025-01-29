"""Provide the main application logic for the email action interface."""

from jvclient.client.lib.widgets import app_controls, app_header, app_update_action

from streamlit_router import StreamlitRouter


def render(router: StreamlitRouter, agent_id: str, action_id: str, info: dict) -> None:
    """
    Render the application UI.

    Args:
        router (StreamlitRouter): The Streamlit router instance.
        agent_id (str): The ID of the agent.
        action_id (str): The ID of the action.
        info (dict): Additional information for rendering.
    """
    # Add app header controls
    model_key, module_root = app_header(agent_id, action_id, info)
    # Add app main controls
    app_controls(agent_id, action_id)
    # Add update button to apply changes
    app_update_action(agent_id, action_id)
