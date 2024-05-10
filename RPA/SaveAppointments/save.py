import json
from azure.data.tables import TableClient, TableEntity

# Initialize your Azure Table client
with open("config.json") as config_file:
    config = json.load(config_file)
    credentials = config["connection_string"]
    account_key = credentials["account_key"]
    account_name = credentials["account_name"]


def getAppoiments():
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


def main():
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};==>REPLACED==>={account_key};EndpointSuffix=core.windows.net"
    table_name = "appointments"
    table_client = TableClient.from_connection_string(connection_string, table_name)

    # Define your data (assuming you have a list of appointments in JSON format)
    appointments = getAppoiments()

    # Insert or update each appointment
    for appointment in appointments:

        appointment["RowKey"] = appointment["patientPhone"]
        appointment["PartitionKey"] = appointment["patientPhone"][-1]

        entity = TableEntity(**appointment)
        table_client.upsert_entity(entity)

    print("Data inserted/updated successfully!")


if __name__ == "__main__":
    main()
