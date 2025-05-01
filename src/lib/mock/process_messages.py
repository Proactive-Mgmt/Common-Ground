from datetime import datetime, timezone
import uuid
from shared import ptmlog

def process_messages(appointments):
    logger = ptmlog.get_logger()
    
    for appointment in appointments:
        # Simulate creating a survey link
        link = f'https://mock-survey-link.com/?id={appointment["RowKey"]}'
        
        # Create message body
        message_body = f'Hi {appointment["patientName"].title()}, thank you for visiting us! We hope your recent appointment was helpful. Please take a moment to share your feedback anonymously in our short survey. Your input helps us improve our services. Tap {link} to start. Thank you!'

        # Simulate sending a message
        mock_message_sid = str(uuid.uuid4())  # Generate a random UUID as a mock message SID
        
        logger.info('mock sms sent', sid=mock_message_sid, message_body=message_body, recipient=appointment["patientPhone"])

        # Update appointment with mock data
        appointment["sentOn"] = datetime.now(timezone.utc)
        appointment["message_sid"] = mock_message_sid

    return appointments