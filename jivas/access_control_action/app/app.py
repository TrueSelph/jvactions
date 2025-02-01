"""AccessControlAction Streamlit app."""

from jvclient.client.lib.widgets import app_controls, app_header, app_update_action
from streamlit_router import StreamlitRouter


def render(router: StreamlitRouter, agent_id: str, action_id: str, info: dict) -> None:
    """Render the streamlit app."""
    (model_key, module_root) = app_header(agent_id, action_id, info)
    app_controls(agent_id, action_id)
    app_update_action(agent_id, action_id)
