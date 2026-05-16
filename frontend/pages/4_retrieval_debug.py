import streamlit as st
import requests
import json
import os

API_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.title("Retrieval Debugger")
st.markdown("Use this tool to inspect the raw retrieval outputs, metadata filtering, and similarity scores.")

if not st.session_state.get("token"):
    st.warning("Please login first.")
    st.stop()

query = st.text_input("Enter a query to debug retrieval:")

if st.button("Debug Retrieval"):
    with st.spinner("Fetching debug trace..."):
        try:
            response = requests.post(
                f"{API_URL}/api/chat/query",
                json={"query": query},
                headers={"Authorization": f"Bearer {st.session_state['token']}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                st.subheader("Router & Trace Logs")
                for log in data["trace_logs"]:
                    st.code(log, language="log")
                
                st.subheader("Retrieved Citations & Scores")
                st.write(f"**Final Confidence Score:** {data['confidence_score']}")
                
                if data["citations"]:
                    for cit in data["citations"]:
                        st.json(cit)
                else:
                    st.info("No sources retrieved.")
                    
                st.subheader("Final Generated Response")
                st.markdown(data["response"])
                
            elif response.status_code == 403:
                st.error("Security Block: Query denied by RBAC.")
            else:
                st.error("Failed to execute debug query.")
        except Exception as e:
            st.error(f"Connection error: {e}")
