# Import the necessary libraries
import json
import os
from twilio.rest import Client
from azure.data.tables import TableClient
from datetime import datetime, timezone

with open("config.json") as config_file:
    config = json.load(config_file)

    credentials = config["twilio_credentials"]
    account_sid = credentials["account_sid"]
    auth_token = credentials["auth_token"]
    my_twilio_phone_number = credentials["my_twilio_phone_number"]
    campaign_sid = credentials["campaign_sid"]
    survey_link = credentials["survey_link"]


def process_messages(appointments):
    # Initialize the Twilio client
    client = Client(account_sid, auth_token)
    # appointments = get_appointments()

    for appointment in appointments:
        # for key in appointment.keys():
        #     print(f"Key: {key}, Value: {appointment[key]}")
        message_sid = sendMessage(
            client,
            appointment["patientPhone"],
            appointment["RowKey"],
            appointment["patientName"],
        )
        appointment["sentOn"] = datetime.now(timezone.utc)
        appointment["message_sid"] = message_sid

    return appointments


def get_appointments() -> None:
    return [
        {
            "patientName": "BRUCE WAYNE",
            "patientDOB": "2001-06-15",
            "patientPhone": "1234123412",
            "appointmentTime": "2024-04-29T11:00",
            "appointmentStatus": "Seen",
            "provider": "BHUC COMMON GROUND",
            "type": "CLINICIAN",
            "sentOn ": "",
            "message_sid ": "",
            "RowKey": "48fbd910-68e5-0ff7-4da1-f27035c3829e",
        }
    ]


def sendMessage(client, to_phone_number, rowKey, patientName):
    link = f"{survey_link}&id={rowKey}"
    # Define the message parameters
    to_phone_number = (
        "+12487237903"  # Replace with the recipient's phone number  248 882 9722
    )
    message_body = f"Hi {patientName.title()}, thank you for visiting us! We hope your recent appointment was helpful. Please take a moment to share your feedback anonymously in our short survey. Your input helps us improve our services. Tap {link} to start. Thank you! "

    # Send the SMS
    message = client.messages.create(
        body=message_body,
        # from_=my_twilio_phone_number,
        to=to_phone_number,
        messaging_service_sid=campaign_sid,
    )
    print(f"SMS sent with SID: {message.sid}")
    return message.sid


if __name__ == "__main__":
    process_messages(get_appointments())
