# Import the necessary libraries
import json
import os
from twilio.rest import Client
from azure.data.tables import TableClient

with open("config.json") as config_file:
    config = json.load(config_file)

    credentials = config["twilio_credentials"]
    account_sid = credentials["account_sid"]
    auth_token = credentials["auth_token"]
    my_twilio_phone_number = credentials["my_twilio_phone_number"]
    campaign_sid = credentials["campaign_sid"]


def main():
    # Initialize the Twilio client
    client = Client(account_sid, auth_token)
    entities = get_appointments()
    for entity in entities:
        for key in entity.keys():
            print(f"Key: {key}, Value: {entity[key]}")
        sendMessage(client, entity["patientPhone"])
    print("OK")


def get_appointments() -> None:

    connection_string = "==>REPLACED==>=***REMOVED***;EndpointSuffix=core.windows.net"
    table_name = "appointments"

    table_client: TableClient = TableClient.from_connection_string(
        conn_str=connection_string, table_name=table_name
    )

    my_filter = "patientName  eq 'BRUCE WAYNE'"
    entities = table_client.query_entities(my_filter)

    # for entity in entities:
    #     for key in entity.keys():
    #         print(f"Key: {key}, Value: {entity[key]}")
    return list(entities)


def sendMessage(client, to_phone_number):

    # Define the message parameters
    to_phone_number = (
        "+12487237903"  # Replace with the recipient's phone number  248 882 9722
    )
    message_body = "Hello new message from your Python SMS app!"

    # Send the SMS
    message = client.messages.create(
        body=message_body,
        # from_=my_twilio_phone_number,
        to=to_phone_number,
        messaging_service_sid=campaign_sid,
    )
    print(f"SMS sent with SID: {message.sid}")
    return True


if __name__ == "__main__":
    main()
