import requests
import json
# from django.db import models

from datetime import date
from pydantic import BaseModel, Field, validator
from typing import Literal

from utils.redis_utils import (
    get_redis_value,
    set_redis,
)
# Define a Pydantic model for user data
class User(BaseModel):
    firstName: str = Field(..., min_length=1)
    lastName: str = Field(..., min_length=1)
    mobile: str 
    gender: str # Literal["male", "female", "other"] = Field(...)
    maritalStatus: str # Literal["single", "married", "divorced", "widowed"] = Field(...)
    dob: date = Field(...)
    # state: int
    # district: int 
    @validator('dob', pre=True)
    def parse_dob(cls, value):
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                raise ValueError(f"Invalid date format for dob: {value}")
        return value

def profile_creation(parameters: dict) -> int:
    url = "https://testapi.haqdarshak.com/api/create_citizen"
    '''parameters = {"firstName": value, "lastName": value, "mobile": value, "gender": value, 
    "maritalStatus": value, "dob": value, "state": value, "district": value, "livingType": value, 
    "ulb": value, "ward": value, "pincode": value}
    '''
    location_details = {"state": 27, "district": 468, "livingType": "urban", "ulb": 251323, "ward": 65537, "pincode": "422603"}
    parameters.update(location_details)
    print(parameters)
    
    try:
        payload = json.dumps(parameters)
    except Exception as e:
        print(e)
        # payload = json.dumps({
        #     "firstName": "Shriram",
        #     "lastName": "Kanawade",
        #     "mobile": "7020922248",
        #     "gender": "M",
        #     "maritalStatus": "Married",
        #     "dob": "1992-04-11",
        #     "state": 27,
        #     "district": 468,
        #     "livingType": "urban",
        #     "ulb": 251323,
        #     "ward": 65537,
        #     "pincode": "422603"
        # })
    token = generate_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text) # it's in string format - {"code": 200, "message": "Success", "data": {"personId": 505099}}
    # type(response) is <class 'requests.models.Response'>
    try:
        answer = json.loads(response.text)
    except Exception as e:
        print(e)
        print(response.status_code)
        return 0 # 0 for false profile creation
    try:
        if answer.get("code") == 200 and answer.get("message") == "Success":
            print("Done!")
            PID = answer.get("data")["personId"]
            set_redis(PID, PID)
            # create a function to save the profile information in digiform's django database
            save_user_data(PID) 
            return PID # returns the person id of profile just created
    except Exception as e:
        print(e)
        print(response.status_code)
        return 0 # 0 for false profile creation

def save_user_data(PID): # using PID as proxy for user_data
    url = 'http://django-server/digiform/api/users/' # use django API endpoint
    response = requests.post(url, data=PID)
    '''
    user_data = {
    'user_id': 'some-uuid',
    'first_name': 'Sam',
    'last_name': 'Alt',
    'father_name': 'Father Name',
    'mother_name': 'Mother Name',
    'gender': 'MALE',
    'marital_status': 'UNMARRIED',
    'dob': '2000-01-01',
    'mobile': 1234567890,
    'nationality': 'Indian',
    'email': 'john.doe@example.com',
    'permanent_address_id': 'some-uuid',
    'mailing_address_id': 'some-uuid',
    'current_address_id': 'some-uuid',
    'user_photo_link': 'http://example.com/photo.jpg',
    'store_personal_data': True,
    'consent_for_digiform': True,
    'notifications_allowed': True,
}
    '''
    if response.status_code == 201:
        print('User data saved successfully')
    else:
        print('Failed to save user data')
    

def generate_token() -> int:

    url = "https://testapi.haqdarshak.com/api/generate_token"

    payload = json.dumps({
    "api_key": "346ca1a3fb416f084b8e737970f57751",
    "secret_key": "358567b4d67e639bbb02bb02e6df58605eed447a",
    "state_code": "MH",
    "agent_id": "451"
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    token_res = json.loads(response.text)
    token = token_res.get("token")
    return token

def mini_screening(PID):
    url = "https://testapi.haqdarshak.com/api/save_mini_scr_question"
    PID = get_redis_value(PID)
    payload = json.dumps({
    "personId": PID,
    "answers": [
        {
        "concept": "CT0000OU",
        "value": "CT0000OT"
        },
        {
        "concept": "CT00003I",
        "value": "LT000001"
        },
        {
        "concept": "CT00001D",
        "value": "CT00002D"
        }
    ]
    })
    headers = {
    'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJvcmdhbml6YXRpb25faWQiOjE5LCJzdGF0ZSI6Ik1haGFyYXNodHJhIiwidXNlcl9pZCI6Mjg5NjAsImlkIjoyODk2MCwiZXhwIjoxNzE0MTQ1NjI5fQ.59HQnIt5iYaE9IVj8_zFd7ev7Kpp-pPHn1d0lJ5ZJio',
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)



# if __name__ == '__main__':
#     message = ""
#     message = profile_creation({}, "")
#     print(message)