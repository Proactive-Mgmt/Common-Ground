import hashlib
import json
import traceback
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
    table_client: TableClient = TableClient.from_connection_string(
        connection_string, table_name
    )

    # appointments_json = json.loads(appointments)

    for appointment in appointments:
        #  compound key (dob+lastname+phonenumber)+
        row_key = generate_deterministic_uuid(
            appointment["patientDOB"]
            + appointment["patientName"].split()[1]
            + appointment["patientPhone"]
        )
        # row_key = (
        #     appointment["patientDOB"]
        #     + appointment["patientName"].split()[1]
        #     + appointment["patientPhone"]
        # )

        # print("row_key ", row_key)
        print(f"row_key: {row_key}")
        print(f"row_key: {row_key[-1]}")

        appointment["RowKey"] = row_key
        appointment["PartitionKey"] = row_key[-1]
        appointment["sentOn"] = ""
        appointment["message_sid"] = ""
        entity = TableEntity(**appointment)
        try:
            print('create_entity here', entity)
            table_client.create_entity(entity)
            #table_client.upsert_entity(entity, mode=UpdateMode.MERGE)
        except Exception as e:
            print("An error occurred:", e)
            traceback.print_exc()

    print("Data inserted successfully!")


def generate_deterministic_uuid(input_string):
    # Create an MD5 hash of the input string
    md5_hash = hashlib.md5(input_string.encode()).hexdigest()

    # Convert the MD5 hash to a UUID
    deterministic_uuid = uuid.UUID(md5_hash)

    return str(deterministic_uuid)


# Example usage


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
            print('updated_entity here', entity)
            table_client.update_entity(entity)
            #table_client.upsert_entity(entity, mode=UpdateMode.MERGE)
        except:
            continue

    print("Data updated successfully!")


if __name__ == "__main__":
    get_appointments()
