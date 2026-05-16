import streamlit as st
import requests
import os

API_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.title("Admin Dashboard")

if not st.session_state.get("token") or st.session_state.get("user_role") != "ADMIN":
    st.error("Access Denied. Admin privileges required.")
    st.stop()

st.subheader("Upload Enterprise Document")

uploaded_file = st.file_uploader("Choose a file (PDF, CSV, JSON, TXT)", type=["pdf", "csv", "json", "txt"])
classification = st.selectbox("Classification", ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "SENSITIVE"])
department = st.selectbox("Department", ["HR", "Finance", "Engineering", "Security", "Company-Wide"])
allowed_roles = st.text_input("Allowed Roles (comma separated)", value="ADMIN,HR,FINANCE,ENGINEERING")

if st.button("Upload and Index"):
    if uploaded_file:
        with st.spinner("Uploading..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = {
                "classification": classification,
                "department": department,
                "allowed_roles": allowed_roles
            }
            try:
                response = requests.post(
                    f"{API_URL}/api/admin/upload",
                    files=files,
                    data=data,
                    headers={"Authorization": f"Bearer {st.session_state['token']}"}
                )
                if response.status_code == 200:
                    st.success("File uploaded and indexing started successfully.")
                else:
                    st.error(f"Upload failed: {response.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")
    else:
        st.warning("Please select a file first.")
