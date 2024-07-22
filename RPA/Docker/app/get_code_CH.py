import json
import re
from typing import LiteralString
import requests
import pyotp

def get_token():
    # Call Harbor API credentials
    client_id = "proactivemgmt"
    client_secret = "11b521761b6ed524a519818835289b31"
    username = "sms@proactivemgmt"
    password = "kB8zaXGbDD4-xdk0"

    # Construct the request URL
    url = f"https://control.callharbor.com/ns-api/oauth2/token/?grant_type=password&client_id={client_id}&client_secret={client_secret}&username={username}&password={password}"

    # Send the GET request
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the access token from the response
        access_token = response.json().get("access_token")
        if access_token:
            print(f"Access Token: {access_token}")
            return access_token
        else:
            print("Failed to retrieve access token")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def get_session(access_token):
    # Generate the MFA code using PyOTP
    secret = "YOUR_SECRET_KEY"  # Replace with your actual secret key
    totp = pyotp.TOTP(secret)
    mfa_code = totp.now()

    # Construct the request headers
    headers: dict[str, str] = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "X-MFA-Code": mfa_code,  # Add the MFA code to the headers
    }
    # print(access_token)
    # Construct the request URL
    url = "https://control.callharbor.com/ns-api/?object=messagesession&action=read&domain=proactivemgmt.com&user=1000&limit=5&session_id=a106d2896653bf9eb03c9226efaadb69"

    # Send the GET request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Print the response content
        # print("session_id: ", response.json())
        return response.json()

    else:
        print(f"Error: {response.status_code} - {response.text}")


def get_message():
    access_token = get_token()
    session_json = get_session(access_token)
    if session_json:
        # Assuming the response is a list of dictionaries
        pattern = r"Your code is: (\d+)"

        for data in session_json:
            # Extract the last_mesg attribute
            message = data["last_mesg"]
            match: re.Match[str] | None = re.search(pattern, message)
            if match:
                code: str | json.Any = match.group(1)
                return code
            else:
                print(f"No code found in the message. Message= {message}")
    else:
        print(f"Error: No message")


if __name__ == "__main__":
    print(f" The code is  {get_message()}")
