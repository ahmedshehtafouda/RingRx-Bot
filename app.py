import streamlit as st
import requests
import pandas as pd

# البيانات الخاصة بك
TOKEN = st.secrets["token_id"]  
SECRET = st.secrets["secret"]

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

    # البيانات التي سيتم إرسالها
fax_data = {}
# make it require user input
# MAKE A LOGIN PAGE FIRST THEN SHOW THE FAX SENDER PAGE




company_name = st.text_input("Company Name", key="company_name" , value="Healthy All Time Nutrition")
contact_number = st.text_input("Contact Number *", key="contact_number")
subject = st.text_input("Subject", key="subject")
comment = st.text_area("Comment", key="comment")
# get file path from user
fax_file = st.file_uploader("Upload Fax File (pdf, doc, docx) *", type=["pdf", "doc", "docx"], key="fax_file")
all_numbers_file = st.file_uploader("Numbers File (xlsx)*", type=["xlsx"], key="all_numbers_file")



#showe a sample of the numbers file
if all_numbers_file is not None:
    st.write("Numbers File:")
    all_numbers_file = pd.read_excel(all_numbers_file)
    st.dataframe(all_numbers_file)
    st.write("please choose the column containing phone numbers:")
    phone_number_column = st.selectbox("Select Phone Number Column", options=all_numbers_file.columns)
    

        
def get_access_token():
    url = "https://portal.ringrx.com/auth/token"

    # الطريقة الصحيحة هي POST مع إرسال البيانات
    payload = {
        "token": TOKEN,
        "secret": SECRET
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    try:
        # استخدام POST بدلاً من GET
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to obtain access token: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error obtaining access token: {e}")
        st.stop()
        
    access_token = response.json()['access_token']
    return access_token

def send_fax(fax_data  , called_number, access_token, fax_file):

    # الرابط المتوقع بناءً على هيكلة RingRx
    url = "https://portal.ringrx.com/voicemails/fax"

    headers = {
        "accept": "application/json",
        "Authorization": access_token
    }

    # البيانات التي سيتم إرسالها
    data = {
        "called_number": called_number,
        "company_name": fax_data["company_name"],
        "contact_number": fax_data["contact_number"],
        "subject": fax_data["subject"],
        "comment": fax_data["comment"]
    }

    # الملف المراد إرساله
    files = {
        "faxfiles[]": (
            fax_file.name,        # اسم الملف
            fax_file.getvalue(),  # محتوى الملف bytes
            fax_file.type         # content-type
        )
    }

    try:
        # استخدام POST بدلاً من GET مع multipart/form-data
        response = requests.post(url, headers=headers , data=data, files=files)
        
        if response.status_code == 200:
            return 'success'
            
        else:
            return f'failed: {response.status_code} - {response.text}'
          
    except Exception as e:
        return f"failed: {e}"

# Submit button
if st.button("Send Faxes"):
    # Validate required fields
    if not contact_number:
        st.error("Contact Number is required")
        st.stop()

    if not fax_file:
        st.error("Fax File is required")
        st.stop()

    if all_numbers_file is None:
        st.error("Numbers File is required")
        st.stop()

    # All fields are filled, proceed with sending fax
    fax_data = {
        "company_name": company_name,
        "contact_number": contact_number,
        "subject": subject,
        "comment": comment
    }

    st.json(fax_data)

    with st.spinner("Sending faxes..."):
        access_token = get_access_token()
        total_numbers = len(all_numbers_file)

        progress_bar = st.progress(0)
        st_text = st.empty()

        number_status = []

        # Use enumerate to fix progress calculation
        for i, (_, row) in enumerate(all_numbers_file.iterrows()):
            called_number = str(row[phone_number_column])

            status = send_fax(
                fax_data=fax_data,
                called_number=called_number,
                access_token=access_token,
                fax_file=fax_file
            )

            number_status.append({
                "number": called_number,
                "status": status
            })

            # Update progress UI
            progress = (i + 1) / total_numbers
            progress_bar.progress(progress)
            st_text.text(f"Sending: {i + 1}/{total_numbers}")

            # Refresh token every 5 faxes (not first one)
            if i != 0 and i % 5 == 0:
                access_token = get_access_token()

    # Completion
    progress_bar.progress(100)
    st_text.text(f"✅ Completed: {total_numbers}/{total_numbers}")

    success_count = sum(
        1 for x in number_status if str(x["status"]).lower() == "success"
    )

    st.success(f"Sent {success_count}/{total_numbers} faxes")

    df = pd.DataFrame(number_status)
    st.dataframe(df)


        
            

