import streamlit as st
from jvcli.client.lib.widgets import dynamic_form
from jvcli.client.lib.widgets import app_header, app_update_action
from streamlit_router import StreamlitRouter

def render(router:StreamlitRouter, agent_id: str, action_id: str, info:dict):
        
    (model_key, module_root) = app_header(agent_id, action_id, info)

    # Manage the 'language' field
    st.session_state[model_key]['language'] = st.selectbox(
        "Language", ["en", "es", "fr", "de", "it"],
        index=(["en", "es", "fr", "de", "it"].index(st.session_state[model_key]["language"])),
        key="language"
    )
                
    # Using expander to manage dynamic phoneme editing
    with st.expander("Edit Phonemes"):
        
        # define fields for dynamic form
        fields = [
            {"name": "Word", "type": "text"},
            {"name": "Pronunciation", "type": "text"}
        ]
        # prepare data from model for dynamic form
        form_data = []
        for key, value in (st.session_state[model_key]["phonemes"]).items():
            form_data.append({"Word":key, "Pronunciation":value})
        # add it to the layout
        container = st.columns(1)
        with container[0]:
            phoneme_data = dynamic_form(fields, initial_data=form_data)

            # keep the model updated with changes
            phonemes = {}
            for phoneme_pair in phoneme_data:
                phoneme_key = phoneme_pair["Word"]
                phoneme_value = phoneme_pair["Pronunciation"]
                phonemes[phoneme_key] = phoneme_value
                st.session_state[model_key]['phonemes'] = phonemes
                
    # Add update button to apply changes
    app_update_action(agent_id, action_id)


                
    