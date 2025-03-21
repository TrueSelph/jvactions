"""This module renders the main app UI for the Ultramsg action."""

from jvclient.client.lib.widgets import app_controls, app_header, app_update_action

from streamlit_router import StreamlitRouter


def render(router: StreamlitRouter, agent_id: str, action_id: str, info: dict) -> None:
    """
    Render the main app UI for the Ultramsg action.

    :param router: StreamlitRouter object
    :param agent_id: Agent ID
    :param action_id: Action ID
    :param info: Action info
    """

    # add app header controls
    (model_key, module_root) = app_header(agent_id, action_id, info)
    # add app main controls
    app_controls(agent_id, action_id)
    # add update button to apply changes
    app_update_action(agent_id, action_id)
