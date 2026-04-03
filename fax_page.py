import pandas as pd
import requests
import streamlit as st


def get_access_token():
    url = "https://portal.ringrx.com/auth/token"

    payload = {
        "token": st.secrets["token_id"],
        "secret": st.secrets["secret"],
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to obtain access token: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error obtaining access token: {e}")
        st.stop()

    return response.json()["access_token"]


def send_fax(fax_data, called_number, access_token, fax_file):
    url = "https://portal.ringrx.com/voicemails/fax"

    headers = {
        "accept": "application/json",
        "Authorization": access_token,
    }

    data = {
        "called_number": called_number,
        "company_name": fax_data["company_name"],
        "contact_number": fax_data["contact_number"],
        "subject": fax_data["subject"],
        "comment": fax_data["comment"],
    }

    files = {
        "faxfiles[]": (
            fax_file.name,
            fax_file.getvalue(),
            fax_file.type,
        )
    }

    try:
        response = requests.post(url, headers=headers, data=data, files=files)
        if response.status_code == 200:
            return "success"
        return f"failed: {response.status_code} - {response.text}"
    except Exception as e:
        return f"failed: {e}"


def render_fax_page():
    st.subheader("Fax Sender")

    fax_data = {}

    company_name = st.text_input("Company Name", key="company_name", value="Healthy All Time Nutrition")
    contact_number = st.text_input("Contact Number *", key="contact_number")
    subject = st.text_input("Subject", key="subject")
    comment = st.text_area("Comment", key="comment")

    fax_file = st.file_uploader(
        "Upload Fax File (pdf, doc, docx) *",
        type=["pdf", "doc", "docx"],
        key="fax_file",
    )
    all_numbers_file = st.file_uploader(
        "Numbers File (xlsx)*",
        type=["xlsx"],
        key="all_numbers_file",
    )

    phone_number_column = None

    if all_numbers_file is not None:
        st.write("Numbers File:")
        all_numbers_file = pd.read_excel(all_numbers_file)
        st.dataframe(all_numbers_file)
        st.write("Please choose the column containing phone numbers:")
        phone_number_column = st.selectbox(
            "Select Phone Number Column",
            options=all_numbers_file.columns,
        )

    if st.button("Send Faxes"):
        if not contact_number:
            st.error("Contact Number is required")
            st.stop()

        if not fax_file:
            st.error("Fax File is required")
            st.stop()

        if all_numbers_file is None:
            st.error("Numbers File is required")
            st.stop()

        if phone_number_column is None:
            st.error("Please select a phone number column")
            st.stop()

        fax_data = {
            "company_name": company_name,
            "contact_number": contact_number,
            "subject": subject,
            "comment": comment,
        }

        st.json(fax_data)

        with st.spinner("Sending faxes..."):
            access_token = get_access_token()
            total_numbers = len(all_numbers_file)

            progress_bar = st.progress(0)
            st_text = st.empty()
            number_status = []

            for i, (_, row) in enumerate(all_numbers_file.iterrows()):
                called_number = str(row[phone_number_column])

                status = send_fax(
                    fax_data=fax_data,
                    called_number=called_number,
                    access_token=access_token,
                    fax_file=fax_file,
                )

                number_status.append({
                    "number": called_number,
                    "status": status,
                })

                progress = (i + 1) / total_numbers
                progress_bar.progress(progress)
                st_text.text(f"Sending: {i + 1}/{total_numbers}")

                if i != 0 and i % 5 == 0:
                    access_token = get_access_token()

        progress_bar.progress(100)
        st_text.text(f"✅ Completed: {total_numbers}/{total_numbers}")

        success_count = sum(1 for x in number_status if str(x["status"]).lower() == "success")

        st.success(f"Sent {success_count}/{total_numbers} faxes")
        st.dataframe(pd.DataFrame(number_status))