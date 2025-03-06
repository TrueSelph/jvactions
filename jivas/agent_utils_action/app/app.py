import uuid
import streamlit as st
import yaml
import json
from io import BytesIO
from jvcli.client.lib.utils import call_action_walker_exec, call_import_agent
from jvcli.client.lib.widgets import app_header, app_update_action
from streamlit_router import StreamlitRouter

def render(router: StreamlitRouter, agent_id: str, action_id: str, info:dict):
    # Add application header controls
    (model_key, module_root) = app_header(agent_id, action_id, info)
    
    with st.expander('Logging', False):
        
        _logging = call_action_walker_exec(agent_id, module_root, 'get_logging')    
        logging = st.checkbox("Log Interactions", value=_logging, key=f"{model_key}_logging")

        if st.button('Update', key=f"{model_key}_btn_logging_update"):
            # Call the function to purge
            if result := call_action_walker_exec(agent_id, module_root, 'set_logging', {'agent_logging':logging}):
                st.success("Agent logging config updated")       
            else:
                st.error("Failed to update logging config. Ensure that there is something to refresh or check functionality")
                
    with st.expander('Refresh Memory', False):
        session_id = st.text_input('Session ID', value='', key=f"{model_key}_refresh_session_id")

        if st.button('Purge', key=f"{model_key}_btn_refresh", disabled=(not session_id)):
            # Call the function to purge
            if result := call_action_walker_exec(agent_id, module_root, 'refresh_memory', {'session_id':session_id}):
                st.success("Agent memory refreshed successfully")       
            else:
                st.error("Failed to refresh agent memory. Ensure that there is something to refresh or check functionality")


    with st.expander('Purge Memory', False):
        session_id = st.text_input('Session ID (optional)', value='', key=f"{model_key}_purge_session_id")
        
        if st.button('Purge', key=f"{model_key}_btn_purge"):
            # Call the function to purge
            if result := call_action_walker_exec(agent_id, module_root, 'purge_memory', {'session_id':session_id}):
                st.success("Agent memory purged successfully")       
            else:
                st.error("Failed to purge agent memory. Ensure that there is something to purge or check functionality")
    

    with st.expander('Import Agent', False):

        agent_descriptor = st.text_area('Agent Descriptor in YAML/JSON', value="", height=170, key=f"{model_key}_agent_descriptor")

        if st.button('Import', key=f"{model_key}_btn_import_agent"):
            # Call the function to import
            if result := call_import_agent(descriptor=agent_descriptor):
                st.success("Agent imported successfully")
            else:
                st.error("Failed to import agent. Ensure that the  descriptor is in valid YAML format")

        uploaded_file = st.file_uploader("Upload Desciptor file")

        if uploaded_file is not None:

            st.write(uploaded_file)                    
            if imported := call_import_agent(descriptor = uploaded_file):
                st.success("Agent imported successfully")
            else:
                st.error("Failed to import agent. Ensure that you are uploading a valid YAML file")

                   
                    
    with st.expander('Import Memory', False):
        
        memory_data = st.text_area('Agent Memory in YAML or JSON', value="", height=170, key=f"{model_key}_memory_data")
        overwite = st.toggle("Overwite", value=True, key=f"{model_key}_overide_memory")

        if st.button('Import', key=f"{model_key}_btn_import_memory"):
            # Call the function to import
            if result := call_action_walker_exec(agent_id, module_root, 'import_memory', {'data': memory_data, "overwite": overwite}):
                st.success("Agent memory imported successfully")
            else:
                st.error("Failed to import agent. Ensure that the  descriptor is in valid YAML format")

            uploaded_file = st.file_uploader("Upload file", key=f"{model_key}_agent_memory_upload")

            if uploaded_file is not None:

                loaded_config = yaml.safe_load(uploaded_file)
                if loaded_config:
                    st.write(loaded_config)                    
                    if imported:= call_action_walker_exec(agent_id, module_root, 'import_memory', {'data': memory_data}):
                        st.success("Agent memory imported successfully")
                    else:
                        st.error("Failed to import agent memory. Ensure that you are uploading a valid YAML file")

                else:
                    st.error("File is invalid. Please upload a valid YAML file")
    
    with st.expander('Export Memory', False):
        # User input and toggle
        session_id = st.text_input('Session ID (optional)', value='', key=f"{model_key}_export_session_id")
        export_json = st.toggle("Export as JSON", value=True, key=f"{model_key}_export_json")

        # Toggle label adjustment
        toggle_label = "Export as JSON" if export_json else "Export as YAML"
        st.caption(f"**{toggle_label} enabled**")

        if st.button('Export', key=f"{model_key}_btn_export_memory"):
            # Prepare parameters
            params = {
                "session_id": session_id,
                "json": export_json
            }

            # Call the function to export memory
            result = call_action_walker_exec(agent_id, module_root, 'export_memory', params)

            # Log results and provide download options
            if result and "memory" in result:
                st.success("Agent memory exported successfully!")

                # Process the first two entries of memory
                memory_entries = result["memory"][:2]  # First 2 entries
                if export_json:
                    # JSON display
                    st.json(memory_entries)

                    # Prepare downloadable JSON file
                    json_data = json.dumps(result, indent=4)
                    json_file = BytesIO(json_data.encode("utf-8"))
                    st.download_button(
                        label="Download JSON File",
                        data=json_file,
                        file_name="exported_memory.json",
                        mime="application/json",
                        key="download_json"
                    )
                else:
                    # YAML display
                    yaml_data = yaml.dump(memory_entries, sort_keys=False)
                    st.code(yaml_data, language="yaml")

                    # full memory dump
                    full_yaml_data = yaml.dump(result, sort_keys=False)

                    # Prepare downloadable YAML file
                    yaml_file = BytesIO(full_yaml_data.encode("utf-8"))
                    st.download_button(
                        label="Download YAML File",
                        data=yaml_file,
                        file_name="exported_memory.yaml",
                        mime="application/x-yaml",
                        key="download_yaml"
                    )
            else:
                st.error("Failed to export agent memory. Please check your inputs and try again.")

    with st.expander('Memory Healthcheck', False):
        # User input fields
        session_id = st.text_input('Session ID (optional)', value='', key=f"{model_key}_healthcheck_session_id")
        verbose = st.checkbox("Verbose", value=False, key=f"{model_key}_healthcheck_verbose")

        if st.button('Run Healthcheck', key=f"{model_key}_btn_healthcheck"):
            # Prepare parameters
            params = {
                "session_id": session_id,
                "verbose": verbose
            }

            # Call the function for healthcheck
            result = call_action_walker_exec(agent_id, module_root, 'memory_healthcheck', params)

            # Display results
            if result:
                st.success("Memory healthcheck completed successfully!")

                # Dynamically display key-value pairs
                for key, value in result.items():
                    st.write(f"**{key}:** {value}")
            else:
                st.error("Failed to run memory healthcheck. Please check your inputs or try again.")
              
    with st.expander('Delete Agent', False):
        
            if st.button('Delete Agent', key=f"{model_key}_btn_delete_agent", disabled=(not agent_id)):
                # Call the function to purge
                if result := call_action_walker_exec(agent_id, module_root, 'delete_agent', {'agent_id':agent_id}):
                    st.success("Agent deleted successfully")       
                else:
                    st.error("Failed to delete agent. Ensure that there is something to refresh or check functionality")

    # Add update button to apply changes
    app_update_action(agent_id, action_id)
