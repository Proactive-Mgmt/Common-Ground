import json
import uuid
from azure.data.tables import TableClient, TableEntity


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

    # appointments_json = json.loads(appointments)

    for appointment in appointments:
        #  compound key (dob+lastname+phonenumber)+
        row_key = (
            appointment["patientDOB"]
            + appointment["patientName"].split()[1]
            + appointment["patientPhone"]
        )
        # print("row_key ", row_key)
        appointment["RowKey"] = row_key
        appointment["PartitionKey"] = appointment["patientPhone"][-1]
        appointment["sentOn"] = ""
        appointment["message_sid"] = ""
        appointment["guid"] = uuid.uuid4()

        entity = TableEntity(**appointment)
        try:
            table_client.create_entity(entity)
        except:
            continue

    print("Data inserted successfully!")


def get_appointments() -> None:
    print("This is get_appointments ")

    with open("config.json") as config_file:
        config = json.load(config_file)
        credentials = config["connection_string"]
        account_key = credentials["account_key"]
        account_name = credentials["account_name"]

    connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};==>REPLACED==>={account_key};EndpointSuffix=core.windows.net"
    print(connection_string)

    table_name = "appointments"

    table_client: TableClient = TableClient.from_connection_string(
        conn_str=connection_string, table_name=table_name
    )
    my_filter = "appointmentStatus eq 'Seen' and provider eq 'BHUC COMMON GROUND' and type eq 'CLINICIAN' and sentOn eq ''"
    entities = table_client.query_entities(my_filter)

    # for entity in entities:
    #     for key in entity.keys():
    #         print(f"Key: {key}, Value: {entity[key]}")
    return list(entities)


def save_processed_appointments(appointments):
    print("This is save_processed_appointments ")

    with open("config.json") as config_file:
        config = json.load(config_file)
        credentials = config["connection_string"]
        account_key = credentials["account_key"]
        account_name = credentials["account_name"]

    connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};==>REPLACED==>={account_key};EndpointSuffix=core.windows.net"
    print(connection_string)
    table_name = "appointments"
    table_client = TableClient.from_connection_string(connection_string, table_name)

    # appointments_json = json.loads(appointments)

    for appointment in appointments:
        entity = TableEntity(**appointment)
        try:
            table_client.update_entity(entity)
        except:
            continue

    print("Data updated successfully!")


if __name__ == "__main__":
    get_appointments()
