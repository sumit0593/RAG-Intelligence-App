import streamlit as st
import requests
import os

API_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.title("Login")

if st.session_state.get("token"):
    st.success("You are already logged in.")
else:
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            try:
                response = requests.post(
                    f"{API_URL}/token",
                    data={"username": username, "password": password}
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state["token"] = data["access_token"]
                    
                    # Fetch user details
                    user_resp = requests.get(
                        f"{API_URL}/users/me",
                        headers={"Authorization": f"Bearer {data['access_token']}"}
                    )
                    if user_resp.status_code == 200:
                        user_data = user_resp.json()
                        st.session_state["user_role"] = user_data["role"]["name"]
                        st.session_state["username"] = user_data["username"]
                        st.success("Login successful!")
                        st.rerun()
                else:
                    st.error("Invalid username or password.")
            except Exception as e:
                st.error(f"Connection error: {e}")
