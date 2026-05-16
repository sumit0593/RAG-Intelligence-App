import streamlit as st

st.set_page_config(page_title="Enterprise RAG Assistant", layout="wide", page_icon="🏢")

if "token" not in st.session_state:
    st.session_state["token"] = None
    st.session_state["user_role"] = None
    st.session_state["username"] = None

st.title("Enterprise RAG Intelligence System")
st.markdown("Welcome to the secure Enterprise RAG Assistant. Navigate using the sidebar.")

if st.session_state["token"]:
    st.sidebar.success(f"Logged in as: {st.session_state['username']} ({st.session_state['user_role']})")
    if st.sidebar.button("Logout"):
        st.session_state["token"] = None
        st.session_state["user_role"] = None
        st.session_state["username"] = None
        st.rerun()
else:
    st.sidebar.warning("Please login via the Login page.")
