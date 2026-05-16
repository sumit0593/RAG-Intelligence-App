import streamlit as st
import requests
import os

API_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.title("Enterprise Chat")

if not st.session_state.get("token"):
    st.warning("Please login first.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("citations") and msg["role"] == "assistant":
            with st.expander("Sources & Confidence"):
                st.write(f"Confidence Score: {msg.get('confidence_score')}")
                for cit in msg["citations"]:
                    st.write(f"- Source: {cit['source']} (Score: {cit.get('score', 1.0):.2f})")
        if msg.get("trace_logs") and msg["role"] == "assistant":
            with st.expander("Retrieval Traceability"):
                for log in msg["trace_logs"]:
                    st.text(log)

if prompt := st.chat_input("Ask something..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call API
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}/api/chat/query",
                    json={"query": prompt},
                    headers={"Authorization": f"Bearer {st.session_state['token']}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.markdown(data["response"])
                    
                    with st.expander("Sources & Confidence"):
                        st.write(f"**Confidence Score:** {data['confidence_score']}")
                        for cit in data["citations"]:
                            st.write(f"- Source: {cit['source']} (Chunk: {cit['chunk']}) - SimScore: {cit.get('score', 1.0):.2f}")
                            
                    with st.expander("Retrieval Traceability"):
                        for log in data["trace_logs"]:
                            st.text(log)
                            
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": data["response"],
                        "confidence_score": data["confidence_score"],
                        "citations": data["citations"],
                        "trace_logs": data["trace_logs"]
                    })
                elif response.status_code == 403:
                    st.error("Access Denied. You do not have permissions for this sensitive query.")
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")
