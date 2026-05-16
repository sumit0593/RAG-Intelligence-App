import streamlit as st
import requests
import pandas as pd
import os

API_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.title("Audit & Security Logs")

if not st.session_state.get("token") or st.session_state.get("user_role") not in ["ADMIN", "AUDITOR", "SECURITY"]:
    st.error("Access Denied. Admin, Auditor, or Security privileges required.")
    st.stop()

tab1, tab2 = st.tabs(["Security Logs", "Audit Logs"])

with tab1:
    st.subheader("Security Incidents & Blocked Queries")
    try:
        response = requests.get(
            f"{API_URL}/api/admin/security_logs",
            headers={"Authorization": f"Bearer {st.session_state['token']}"}
        )
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No security logs found.")
        else:
            st.error("Failed to fetch security logs.")
    except Exception as e:
        st.error(f"Connection error: {e}")

with tab2:
    st.subheader("System Audit Logs")
    try:
        response = requests.get(
            f"{API_URL}/api/admin/audit_logs",
            headers={"Authorization": f"Bearer {st.session_state['token']}"}
        )
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No audit logs found.")
        else:
            st.error("Failed to fetch audit logs.")
    except Exception as e:
        st.error(f"Connection error: {e}")
