import streamlit as st

from fax_page import render_fax_page
from sms_page import render_sms_page

USERNAME = st.secrets["username"]
PASSWORD = st.secrets["password"]

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def show_login_page():
    st.title("RingRx Bot Login")
    st.write("Please login to access the fax sender.")

    with st.form("login_form"):
        entered_username = st.text_input("Username")
        entered_password = st.text_input("Password", type="password")
        login_submitted = st.form_submit_button("Login")

    if login_submitted:
        if entered_username == USERNAME and entered_password == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid username or password")


if not st.session_state.authenticated:
    show_login_page()
    st.stop()

st.title("RingRx Bot")

if st.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.subheader("Service")
service_type = st.sidebar.radio(
    "Choose Service",
    options=["Fax", "SMS"],
)

if service_type == "Fax":
    render_fax_page()
else:
    render_sms_page()

