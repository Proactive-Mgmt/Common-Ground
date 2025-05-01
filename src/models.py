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
