import json
from azure.data.tables import TableClient, TableEntity


def get_appoiments():

    appointments: list[dict[str, str]] = [
        {
            "patientName": "BRUCE WAYNE",
            "patientDOB": "2001-06-15",
            "patientPhone": "1234123412",
            "appointmentTime": "2024-04-29T11:00",
            "appointmentStatus": "Seen",
        }
    ]
    return appointments


def save_appointments(appointments):
    print("This is save_appointments ")

    with open("config.json") as config_file:
        config = json.load(config_file)
        credentials = config["connection_string"]
        account_key = credentials["account_key"]
        account_name = credentials["account_name"]

    connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};==>REPLACED==>={account_key};EndpointSuffix=core.windows.net"
    print(connection_string)
    table_name = "appointments"
    table_client = TableClient.from_connection_string(connection_string, table_name)

    appointments_json = json.loads(appointments)

    for appointment in appointments_json:
        print(f"Patient Name: {appointment['patientName']}")
        print(f"DOB: {appointment['patientDOB']}")
        print(f"Phone: {appointment['patientPhone']}")
        print(f"Appointment Time: {appointment['appointmentTime']}")
        print(f"Status: {appointment['appointmentStatus']}")
        print(f"Provider: {appointment['provider']}")
        print(f"Type: {appointment['type']}")
        print("-" * 30)  # Separator between appointments

        appointment["RowKey"] = appointment["patientPhone"]
        appointment["PartitionKey"] = appointment["patientPhone"][-1]

        entity = TableEntity(**appointment)
        table_client.upsert_entity(entity)

    print("Data inserted/updated successfully!")


# if __name__ == "__main__":
#     appointments: list[dict[str, str]] = get_appoiments()
#     save_appointments(appointments)
