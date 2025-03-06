import streamlit as st
from jvcli.client.lib.widgets import app_header, app_controls, app_update_action
from streamlit_router import StreamlitRouter

def render(router:StreamlitRouter, agent_id: str, action_id: str, info:dict):
    # add app header controls       
    (model_key, module_root) = app_header(agent_id, action_id, info)
    # add app main controls
    app_controls(agent_id, action_id)
    # add update button to apply changes
    app_update_action(agent_id, action_id)


                
    