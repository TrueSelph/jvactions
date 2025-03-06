import streamlit as st
from jvcli.client.lib.utils import call_action_walker_exec
from jvcli.client.lib.widgets import app_header, app_controls, app_update_action
from streamlit_router import StreamlitRouter

def render(router:StreamlitRouter, agent_id: str, action_id: str, info:dict):
    # add app header controls       
    (model_key, module_root) = app_header(agent_id, action_id, info)
    
    # add app main controls
    with st.expander('Advanced Configuration', False):
        app_controls(agent_id, action_id)
        # add update button to apply changes
        app_update_action(agent_id, action_id)
    
    st.session_state[model_key]['biodata'] = st.text_area(
        label = "Biodata",
        value = st.session_state[model_key]['biodata'],
        placeholder = "Briefly describe the agent; be sure to provide a name, role and temperament."
    )
    
    if st.button("Compose Persona", key=f"compose_persona_{model_key}"):

        result = call_compose(
            agent_id = agent_id, 
            module_root=module_root,
            biodata = st.session_state[model_key]['biodata'],
            attributes = st.session_state[model_key]['attributes']
        )
        if(result):
            st.success("Persona updated")
        else: 
            st.error("Unable to update persona")


def call_compose(agent_id: str, module_root:str, biodata:str, attributes:dict):
    
    args = {"agent_id": agent_id, "biodata": biodata, "attributes": attributes}
    return call_action_walker_exec(agent_id, module_root, 'compose', args)
    