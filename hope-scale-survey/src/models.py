from pydantic import BaseModel
from datetime import date, datetime

class PracticeFusionAppointment(BaseModel): 
    patient_name       : str
    patient_dob        : date
    patient_phone      : str
    appointment_time   : datetime
    appointment_status : str
    provider           : str
    type               : str

class TableAppointment(BaseModel): 
    row_key       : str
    partition_key : str
    patient_name  : str
    patient_phone : str
