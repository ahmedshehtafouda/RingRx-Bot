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


def compose_message(greeting_prefix, recipient_name, message_body):
    if pd.notna(recipient_name) and str(recipient_name).strip():
        return f"{greeting_prefix} {recipient_name}\n{message_body}" if greeting_prefix else f"{recipient_name}\n{message_body}"
    return f"{greeting_prefix}\n{message_body}" if greeting_prefix else message_body

def render_sms_page():
    st.subheader("SMS Sender")
    st.write("Send SMS messages through Twilio in bulk from Excel or to one recipient directly.")
    st.info("The message will start with the greeting you choose, then the selected name when available.")

    send_mode = st.radio(
        "Send Mode",
        options=["Bulk from file", "Single number"],
        horizontal=True,
        key="sms_send_mode",
    )

    recipients_df = None
    name_column = None
    phone_number_column = None
    single_recipient_name = ""
    single_recipient_number = ""

    if send_mode == "Bulk from file":
        sender_file = st.file_uploader(
            "Numbers File (xlsx) *",
            type=["xlsx"],
            key="sms_numbers_file",
        )

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
            phone_column_index = 1 if len(recipients_df.columns) > 1 else 0
            phone_number_column = st.selectbox(
                "Select Phone Number Column",
                options=recipients_df.columns,
                index=phone_column_index,
                key="sms_phone_column",
            )
    else:
        single_recipient_name = st.text_input(
            "Recipient Name",
            key="sms_single_name",
            help="Optional, used in the greeting when provided.",
        )
        single_recipient_number = st.text_input(
            "Recipient Phone Number *",
            key="sms_single_number",
        )

    greeting_prefix = st.text_input(
        "Greeting *",
        value="Hi",
        key="sms_greeting_prefix",
        help="This text will appear before the selected name.",
    )

    message_body = st.text_area(
        "Message Body *",
        key="sms_message_body",
        help="Write the rest of the message here. The app will prepend your greeting and the selected name automatically.",
    )

    if st.button("Send SMS"):
        if not message_body:
            st.error("Message is required")
            st.stop()

        try:
            with st.spinner("Sending SMS..."):
                if send_mode == "Bulk from file":
                    if recipients_df is None:
                        st.error("Numbers File is required")
                        st.stop()

                    total_numbers = len(recipients_df)
                    progress_bar = st.progress(0)
                    st_text = st.empty()
                    message_status = []

                    for index, (_, row) in enumerate(recipients_df.iterrows()):
                        recipient_name = row[name_column]
                        to_number = normalize_phone_number(row[phone_number_column])
                        personalized_message = compose_message(greeting_prefix, recipient_name, message_body)

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
                else:
                    if not single_recipient_number:
                        st.error("Recipient Phone Number is required")
                        st.stop()

                    to_number = normalize_phone_number(single_recipient_number)
                    personalized_message = compose_message(greeting_prefix, single_recipient_name, message_body)

                    try:
                        message_sid = send_sms(to_number=to_number, message_body=personalized_message)
                        status = "success"
                    except Exception as exc:
                        message_sid = ""
                        status = f"failed: {exc}"

                    result_df = pd.DataFrame([
                        {
                            "name": single_recipient_name,
                            "number": to_number,
                            "status": status,
                            "message_sid": message_sid,
                        }
                    ])
                    st.dataframe(result_df)
        except Exception as exc:
            st.error(f"Failed to send SMS: {exc}")


if __name__ == "__main__":
    render_sms_page()