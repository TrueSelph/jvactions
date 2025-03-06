import streamlit as st
from jvcli.client.lib.utils import call_action_walker_exec
from jvcli.client.lib.widgets import app_header, app_controls, app_update_action
from streamlit_router import StreamlitRouter

def render(router:StreamlitRouter, agent_id: str, action_id: str, info:dict):
    # add app header controls       
    (model_key, module_root) = app_header(agent_id, action_id, info)
    
    # add app main controls
    if 'elevenlabs_models' not in st.session_state:
        st.session_state['elevenlabs_models'] = call_action_walker_exec(agent_id, module_root, 'get_models')
        
    if 'elevenlabs_voices' not in st.session_state:
        result = call_action_walker_exec(agent_id, module_root, 'get_voices')
        if "voices" in result:
            st.session_state['elevenlabs_voices'] = result.get('voices')
        else:
            st.session_state['elevenlabs_voices'] = result
            
    # Create a dictionary to map descriptions to model IDs
    model_info_dict = {f"{model['name']} - {model['description']}": model['model_id'] for model in st.session_state['elevenlabs_models']}
    # Create a dictionary to map descriptions to voice IDs
    voice_info_dict = {f"{voice['name']}": voice['voice_id'] for voice in st.session_state['elevenlabs_voices']}
    
    # Initialize session state if it doesn't already exist
    if not st.session_state[model_key].get('model', None):
        st.session_state[model_key]['model'] = st.session_state['elevenlabs_models'][0]["model_id"]
    
    # Initialize session state if it doesn't already exist
    if not st.session_state[model_key].get('voice', None):
        st.session_state[model_key]['voice'] = st.session_state['elevenlabs_voices'][0]["name"]
    
    st.session_state[model_key]['api_key'] = st.text_input("API Key", value=st.session_state[model_key]['api_key'], type="password")
    
    # Select box for model selection with default from session state
    selected_model_info = st.selectbox(
        "Text-to-Speech Model:", 
        options=list(model_info_dict.keys()), 
        index=list(model_info_dict.values()).index(st.session_state[model_key]['model'])
    )
    
    # Select box for voice selection with default from session state
    selected_voice_info = st.selectbox(
        "Voice:", 
        options=list(voice_info_dict.keys()), 
        index=list(voice_info_dict.keys()).index(st.session_state[model_key]['voice'])
    )
    # Update the session state with the selected model ID
    st.session_state[model_key]['model'] = model_info_dict[selected_model_info]
    # Update the session state with the selected model ID
    st.session_state[model_key]['voice'] = selected_voice_info
    
    # app_controls(agent_id, action_id)
    # add update button to apply changes
    app_update_action(agent_id, action_id)
                
    