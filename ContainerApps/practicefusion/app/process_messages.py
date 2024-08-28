from twilio.rest import Client
from datetime import datetime, timezone
import logging
import os

def process_messages(appointments):
    logging.info('process_messages')
    TWILIO_ACCOUNT_SID  = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN   = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_CAMPAIGN_SID = os.getenv('TWILIO_CAMPAIGN_SID')
    TWILIO_SURVEY_LINK  = os.getenv('TWILIO_SURVEY_LINK')

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    for appointment in appointments:
        link = f'{TWILIO_SURVEY_LINK}&id={appointment["RowKey"]}'
        message_body = f'Hi {appointment["patientName"].title()}, thank you for visiting us! We hope your recent appointment was helpful. Please take a moment to share your feedback anonymously in our short survey. Your input helps us improve our services. Tap {link} to start. Thank you!'

        message = client.messages.create(
            messaging_service_sid = TWILIO_CAMPAIGN_SID,
            to                    = appointment["patientPhone"],
            body                  = message_body,
        )

        logging.info(f'SMS sent with SID: {message.sid}')

        appointment["sentOn"] = datetime.now(timezone.utc)
        appointment["message_sid"] = message.sid

    return appointments