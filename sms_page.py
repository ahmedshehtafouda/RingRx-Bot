import streamlit as st
import pandas as pd
from twilio.rest import Client


def send_sms(to_number, message_body):
    account_sid = st.secrets["twilio_account_sid"]
    auth_token = st.secrets["twilio_auth_token"]
    from_number = st.secrets["twilio_from_number"]

    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=message_body,
        from_=from_number,
        to=to_number,
    )
    return message.sid

def normalize_phone_number(value):
    number = str(value).strip()
    if number.endswith(".0"):
        number = number[:-2]
    return number

def render_sms_page():
    st.subheader("SMS Sender")
    st.write("Upload a list of names and phone numbers, choose the columns, and send SMS messages through Twilio.")
    st.info("The message will always start with: hi {name}")

    sender_file = st.file_uploader(
        "Numbers File (xlsx) *",
        type=["xlsx"],
        key="sms_numbers_file",
    )

    recipients_df = None
    name_column = None
    phone_number_column = None

    if sender_file is not None:
        st.write("Numbers File:")
        recipients_df = pd.read_excel(sender_file)
        st.dataframe(recipients_df)

        st.write("Please choose the columns containing the recipient name and phone number:")
        name_column = st.selectbox(
            "Select Name Column",
            options=recipients_df.columns,
            key="sms_name_column",
        )
        phone_number_column = st.selectbox(
            "Select Phone Number Column",
            options=recipients_df.columns,
            key="sms_phone_column",
        )

    message_body = st.text_area(
        "Message Body *",
        key="sms_message_body",
        help="Write the rest of the message here. The app will prepend hi {name} automatically.",
    )

    if st.button("Send SMS"):
        if sender_file is None:
            st.error("Numbers File is required")
            st.stop()

        if not message_body:
            st.error("Message is required")
            st.stop()

        try:
            with st.spinner("Sending SMS..."):
                total_numbers = len(recipients_df)
                progress_bar = st.progress(0)
                st_text = st.empty()
                message_status = []

                for index, (_, row) in enumerate(recipients_df.iterrows()):
                    recipient_name = row[name_column]
                    to_number = normalize_phone_number(row[phone_number_column])
                    personalized_message = f"hi {recipient_name}\n{message_body}" if pd.notna(recipient_name) and str(recipient_name).strip() else message_body

                    try:
                        message_sid = send_sms(to_number=to_number, message_body=personalized_message)
                        status = "success"
                    except Exception as exc:
                        message_sid = ""
                        status = f"failed: {exc}"

                    message_status.append({
                        "name": recipient_name,
                        "number": to_number,
                        "status": status,
                        "message_sid": message_sid,
                    })

                    progress = (index + 1) / total_numbers
                    progress_bar.progress(progress)
                    st_text.text(f"Sending: {index + 1}/{total_numbers}")

                progress_bar.progress(100)
                st_text.text(f"Completed: {total_numbers}/{total_numbers}")

            success_count = sum(1 for item in message_status if str(item["status"]).lower() == "success")
            st.success(f"Sent {success_count}/{total_numbers} SMS messages")
            st.dataframe(pd.DataFrame(message_status))
        except Exception as exc:
            st.error(f"Failed to send SMS: {exc}")


if __name__ == "__main__":    render_sms_page()