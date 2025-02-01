"""This module contains the Streamlit app for the WhatsApp Connect action."""

import base64
from io import BytesIO

import requests
import streamlit as st
from jvclient.client.lib.utils import call_action_walker_exec, call_get_action
from jvclient.client.lib.widgets import app_controls, app_header, app_update_action
from PIL import Image
from streamlit_router import StreamlitRouter


def start_session(
    base_url: str,
    api_key: str,
    session_id: str,
    webhook: str = "",
    wait_qr_code: bool = False,
) -> dict:
    """
    Starts a session with the specified parameters.

    Args:
        base_url (str): The base URL for the API.
        api_key (str): The API key for authorization.
        session_id (str): The session ID to start.
        webhook (str): Optional webhook URL.
        wait_qr_code (bool): Whether to wait for the QR code.

    Returns:
        dict: Response data indicating success or error details.
    """

    url = f"{base_url}/api/{session_id}/start-session"
    headers = {
        "accept": "*/*",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"webhook": webhook, "waitQrCode": wait_qr_code}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def close_session(base_url: str, api_key: str, session_id: str) -> dict:
    """
    Closes the specified session.

    Args:
        base_url (str): The base URL for the API.
        api_key (str): The API key for authorization.
        session_id (str): The session ID to close.

    Returns:
        dict: Response data indicating success or error details.
    """

    url = f"{base_url}/api/{session_id}/close-session"
    headers = {"accept": "*/*", "Authorization": f"Bearer {api_key}"}

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def login(base_url: str, api_key: str, session_id: str) -> dict:
    """
    Logs in by fetching the QR code for the specified session.

    Args:
        base_url (str): The base URL for the API.
        api_key (str): The API key for authorization.
        session_id (str): The session ID to log in to.

    Returns:
        dict: Response data containing the QR code URL or error details.
    """

    url = f"{base_url}/api/{session_id}/qrcode-session"
    headers = {"accept": "*/*", "Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # If the response contains raw binary data (e.g., PNG), encode it as Base64
        return {"qrcode": base64.b64encode(response.content).decode("ascii")}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def logout(base_url: str, api_key: str, session_id: str) -> dict:
    """
    Logs out of the specified session.

    Args:
        base_url (str): The base URL for the API.
        api_key (str): The API key for authorization.
        session_id (str): The session ID to log out from.

    Returns:
        dict: Response data indicating success or error details.
    """

    url = f"{base_url}/api/{session_id}/logout"
    headers = {"accept": "*/*", "Authorization": f"Bearer {api_key}"}

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def status_session(base_url: str, api_key: str, session_id: str) -> dict:
    """
    Checks the status of the specified session.

    Args:
        base_url (str): The base URL for the API.
        api_key (str): The API key for authorization.
        session_id (str): The session ID to check.

    Returns:
        dict: Response data indicating the session status or error details.
    """
    url = f"{base_url}/api/{session_id}/status-session"
    headers = {"accept": "*/*", "Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def render_whatsapp_setup(agent_id: str, action_id: str) -> None:
    """
    Renders the WhatsApp setup page with session controls and QR code display.

    Args:
        agent_id (str): The agent ID.
        action_id (str): The action ID.
    """

    model_key = f"model_{agent_id}_{action_id}"

    if model_key not in st.session_state:
        st.session_state[model_key] = call_get_action(
            agent_id=agent_id, action_id=action_id
        )

    # Extract required parameters from the model
    base_url = st.session_state[model_key].get("api_url", "")
    api_key = st.session_state[model_key].get("api_key", "")
    session_id = st.session_state[model_key].get("instance_id", "")

    if not base_url or not api_key or not session_id:
        st.error("Missing required configuration parameters.")
        return

    st.title("WhatsApp Setup")

    # Session Status Display
    st.subheader("Session Status")
    status_response = status_session(base_url, api_key, session_id)
    if "error" in status_response:
        st.warning("Failed to retrieve session status.")
        session_status = "unknown"
    else:
        session_status = status_response.get("status", "unknown")

    # Status Box with Colors
    if session_status == "connected":
        status_color = "green"
        status_message = "Session is active"
    elif session_status == "closed":
        status_color = "red"
        status_message = "Session is closed"
    else:
        status_color = "orange"
        status_message = "Session status is unknown"

    st.markdown(
        f"""
        <div style="padding: 10px; border-radius: 5px; background-color: {status_color}; color: white; text-align: center;">
            <strong>{status_message}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Controls Section
    st.divider()
    st.subheader("Session Controls")

    col1, col2, col3 = st.columns([1, 1, 1])

    # Start Session Button
    with col1:
        if st.button("Start Session", key="start_session"):
            start_response = start_session(base_url, api_key, session_id)
            if "error" in start_response:
                st.error(f"Failed to start session: {start_response['error']}")
            else:
                st.success("Session started successfully.")

    # Close Session Button
    with col2:
        if st.button("Close Session", key="close_session"):
            close_response = close_session(base_url, api_key, session_id)
            if "error" in close_response:
                st.error(f"Failed to close session: {close_response['error']}")
            else:
                st.success("Session closed successfully.")

    # Logout Button
    with col3:
        if st.button("Log Out", key="logout_button"):
            logout_response = logout(base_url, api_key, session_id)
            if "error" in logout_response:
                st.error(f"Logout failed: {logout_response['error']}")
            else:
                st.success("Logged out successfully.")

    # QR Code Section
    st.subheader("QR Code for Login")

    # Styled Instruction Box with Inline Refresh Button
    with st.container():
        col1, col2 = st.columns([5, 1])  # Two columns: instruction text and button

        with col1:
            st.markdown(
                """
                <div style="padding: 10px; border-radius: 5px; background-color: #222831; color: white; display: flex; align-items: center; gap: 10px;">
                    <img src="https://img.icons8.com/color/48/000000/qr-code.png" width="40" alt="QR Code Icon">
                    <span style="font-size: 16px;">Please scan the QR code below with your WhatsApp app to log in.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            if st.button("🔄 Refresh", key="refresh_qr"):
                login_response = login(base_url, api_key, session_id)

                # Fetch the QR code data
                if "error" in login_response:
                    st.error(f"Error fetching QR code: {login_response['error']}")
                else:
                    qr_code_data = login_response.get("qrcode")
                    if qr_code_data:
                        try:
                            # Decode the Base64-encoded QR code
                            qr_code_bytes = BytesIO(base64.b64decode(qr_code_data))
                            qr_code_image = Image.open(qr_code_bytes)

                            # Store QR code image in session state
                            st.session_state["qr_code_image"] = qr_code_image

                            # Add success state
                            st.session_state["qr_code_success"] = True
                        except Exception as e:
                            st.error(f"Failed to process QR code image: {str(e)}")
                            st.session_state["qr_code_success"] = False
                    else:
                        st.error("No QR code data returned by the API.")
                        st.session_state["qr_code_success"] = False

    # Centered QR Code Display
    st.markdown(
        """
        <div style="text-align: center; margin-top: 20px;">
        """,
        unsafe_allow_html=True,
    )

    # Success Message Above QR Code
    if st.session_state.get("qr_code_success", False):
        st.markdown(
            """
            <div style="padding: 10px; border-radius: 5px; background-color: #4CAF50; color: white; text-align: center; margin-bottom: 10px;">
                <b>QR Code refreshed successfully!</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Display the QR Code if available
    if "qr_code_image" in st.session_state and st.session_state["qr_code_image"]:
        st.image(st.session_state["qr_code_image"], caption="Scan to log in", width=400)
    else:
        st.write("No QR code available. Click refresh to generate one.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_config_screen(
    router: StreamlitRouter, agent_id: str, action_id: str, info: dict
) -> None:
    """
    Renders the configuration screen for the WhatsApp Connect action.

    Args:
        router (StreamlitRouter): The Streamlit router instance.
        agent_id (str): The agent ID.
        action_id (str): The action ID.
        info (dict): The action information.
    """

    (model_key, module_root) = app_header(agent_id, action_id, info)

    # Add app main controls
    app_controls(agent_id, action_id)
    # Add update button to apply changes
    app_update_action(agent_id, action_id)

    # Add Register Webhook section
    with st.expander("Register Webhook", expanded=True):
        st.markdown("### Webhook Registration")
        st.markdown(
            "Click the button below to register the webhook. "
            "This enables your agent to communicate with WhatsApp."
        )

        # Register Webhook button
        if st.button("Register Webhook", key=f"{model_key}_btn_register_webhook"):
            result = call_action_walker_exec(
                agent_id, module_root, "register_wppconnect_webhook"
            )

            if result:
                st.success("Webhook registered successfully!")
            else:
                st.error("Failed to register webhook. Please try again.")


def render(router: StreamlitRouter, agent_id: str, action_id: str, info: dict) -> None:
    """
    Renders the WhatsApp Connect action page.

    Args:
        router (StreamlitRouter): The Streamlit router instance.
        agent_id (str): The agent ID.
        action_id (str): The action ID.
        info (dict): The action information.
    """

    tabs = st.tabs(["Configuration", "WhatsApp Setup"])

    with tabs[0]:
        render_config_screen(router, agent_id, action_id, info)

    with tabs[1]:
        render_whatsapp_setup(agent_id, action_id)
