from twilio.rest import Client
import os
from shared import ptmlog

def send_survey(id: str, patient_name: str, patient_phone: str) -> str:
    """
    Send a survey to the patient using Twilio.
    Returns the message SID.
    """
    logger = ptmlog.get_logger()

    TWILIO_ACCOUNT_SID  = os.environ['TWILIO_ACCOUNT_SID']
    TWILIO_AUTH_TOKEN   = os.environ['TWILIO_AUTH_TOKEN']
    TWILIO_CAMPAIGN_SID = os.environ['TWILIO_CAMPAIGN_SID']
    TWILIO_SURVEY_LINK  = os.environ['TWILIO_SURVEY_LINK']

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    link = f'{TWILIO_SURVEY_LINK}&id={id}'
    message_body = f'Hi {patient_name.title()}, thank you for visiting us! We hope your recent appointment today with the BHUC clinic was helpful. Please take a moment to share your feedback anonymously in our short survey. Your input helps us improve our services. Tap {link} to start. Thank you!'

    message = client.messages.create(
        messaging_service_sid=TWILIO_CAMPAIGN_SID,
        to=patient_phone,
        body=message_body,
    )
    logger.info('sms sent', sid=message.sid, to=patient_phone)

    if message.sid is None:
        logger.error('message sent is missing sid', message=message)
        raise Exception('message sent is missing sid')

    return message.sid
