from datetime import datetime, timezone
import logging
import uuid

def process_messages(appointments):
    logging.info('process_messages')
    
    for appointment in appointments:
        # Simulate creating a survey link
        link = f'https://mock-survey-link.com/?id={appointment["RowKey"]}'
        
        # Create message body
        message_body = f'Hi {appointment["patientName"].title()}, thank you for visiting us! We hope your recent appointment was helpful. Please take a moment to share your feedback anonymously in our short survey. Your input helps us improve our services. Tap {link} to start. Thank you!'

        # Simulate sending a message
        mock_message_sid = str(uuid.uuid4())  # Generate a random UUID as a mock message SID
        
        logging.info(f'Mock SMS sent with SID: {mock_message_sid}')
        logging.info(f'Mock message body: {message_body}')
        logging.info(f'Mock message recipient: {appointment["patientPhone"]}')

        # Update appointment with mock data
        appointment["sentOn"] = datetime.now(timezone.utc)
        appointment["message_sid"] = mock_message_sid

    return appointments