"""This module render the streamlit app for the google sheet action."""

from jvclient.client.lib.widgets import app_controls, app_header, app_update_action
from streamlit_router import StreamlitRouter


def render(router: StreamlitRouter, agent_id: str, action_id: str, info: dict) -> None:
    """Render the streamlit app for the google sheet action.

    :param router: StreamlitRouter instance
    :param agent_id: agent id
    :param action_id: action id
    :param info: action info
    """

    # add app header controls
    (model_key, module_root) = app_header(agent_id, action_id, info)
    # add app main controls
    app_controls(agent_id, action_id)
    # add update button to apply changes
    app_update_action(agent_id, action_id)
