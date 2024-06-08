from dotenv import load_dotenv
from utils.bhashini_utils import bhashini_translate
from utils.redis_utils import set_redis
import random
from pydub import AudioSegment
import time
import os


load_dotenv(
    dotenv_path="ops/.env",
)

# with open("prompts/prompt.txt", "r") as file:
#     main_prompt = file.read().replace('\n', ' ')

with open("prompts/digiform_v1.txt", "r") as file:
    main_prompt = file.read().replace('\n', ' ')

openai_api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("ASSISTANT_ID")
model_name = os.getenv("MODEL_NAME")

#OPENAI FUNCTION CALLS
'''
{
    "firstName": <value>,
    "lastName": <value>,
    "mobile": <value>,
    "gender": <value>,
    "maritalStatus": <value>,
    "dob": <value>,
}
'''   

get_user_information = {
    "name": "get_user_information",
    "description": "Get user information including personal details, contact information, and profile settings.",
    "parameters": {
        "type": "object",
        "properties": {
            # "user_id": {
            #     "type": "string",
            #     "description": "Unique ID of the user"
            # },
            "firstName": {
                "type": "string",
                "description": "First Name of Person"
            },
            "lastName": {
                "type": "string",
                "description": "Last Name of Person"
            },
            "fatherName": {
                "type": "string",
                "description": "Father's Name of Person"
            },
            # "motherName": {
            #     "type": "string",
            #     "description": "Mother's Name of Person"
            # },
            "gender": {
                "type": "string",
                "description": "Gender of Person",
                "enum": ["Male", "Female", "Other"]
            },
            "maritalStatus": {
                "type": "string",
                "description": "Marital Status of Person",
                "enum": ["Unmarried", "Married"]
            },
            "dob": {
                "type": "string",
                "description": "Date of Birth of Person. Format is YYYY-MM-DD"
            },
            "mobile": {
                "type": "string",
                "description": "10 digit mobile number. If it has prefix '+91-' at start, then consider mobile number after prefix."
            },
            # "nationality": {
            #     "type": "string",
            #     "description": "Nationality of Person"
            # },
            "email": {
                "type": "string",
                "description": "Email address of Person"
            },
            "permanentAddressId": {
                "type": "string",
                "description": "Permanent address ID of the person"
            },
            "aadharCardNumber": {
                "type": "string",
                "description": "Aadhar card number (12 digits)"
            },
            "panCardNumber": {
                "type": "string",
                "description": "PAN card number"
            },
            # "mailingAddressId": {
            #     "type": "string",
            #     "description": "Mailing address ID of the person"
            # },
            # "currentAddressId": {
            #     "type": "string",
            #     "description": "Current address ID of the person"
            # },
            # "userPhotoLink": {
            #     "type": "string",
            #     "description": "Link to the user's photo"
            # },
            # "storePersonalData": {
            #     "type": "boolean",
            #     "description": "Consent to store personal data"
            # },
            # "consentForDigiform": {
            #     "type": "boolean",
            #     "description": "Consent for Digiform"
            # },
            # "notificationsAllowed": {
            #     "type": "boolean",
            #     "description": "Allow notifications"
            # }
        },
            "required": [  
                "firstName", "lastName", "fatherName", "gender", "maritalStatus",
                "dob", "mobile", "email", "permanentAddressId", "aadharCardNumber"
            ]
    }
    #     "required": [
    #         "user_id", "firstName", "lastName", "fatherName", "motherName", "gender", "maritalStatus",
    #         "dob", "mobile", "nationality", "email", "permanentAddressId", "mailingAddressId", 
    #         "currentAddressId", "userPhotoLink", "storePersonalData", "consentForDigiform", 
    #         "notificationsAllowed"
    #     ]
    # }
}
'''
get_personal_information = {
    "name": "get_personal_information",
    "description": "Get personal information including various ID numbers and their respective document links.",
    "parameters": {
        "type": "object",
        "properties": {
            "personal_data_id": {
                "type": "string",
                "description": "Unique ID for the personal data"
            },
            "user_id": {
                "type": "string",
                "description": "User ID linked to the personal data"
            },
            "aadharCardNumber": {
                "type": "string",
                "description": "Aadhar card number (12 digits)"
            },
            "panCardNumber": {
                "type": "string",
                "description": "PAN card number"
            },
            "drivingLicenseNumber": {
                "type": "string",
                "description": "Driving license number"
            },
            "voterIdNumber": {
                "type": "string",
                "description": "Voter ID number"
            },
            "rationCardNumber": {
                "type": "string",
                "description": "Ration card number"
            },
            "passportNumber": {
                "type": "string",
                "description": "Passport number"
            },
            "aadhaarCardLink": {
                "type": "string",
                "description": "Link to Aadhaar card"
            },
            "panCardLink": {
                "type": "string",
                "description": "Link to PAN card"
            },
            "drivingLicenseLink": {
                "type": "string",
                "description": "Link to driving license"
            },
            "voterIdLink": {
                "type": "string",
                "description": "Link to voter ID"
            },
            "rationCardLink": {
                "type": "string",
                "description": "Link to ration card"
            },
            "passportLink": {
                "type": "string",
                "description": "Link to passport"
            }
        },
        "required": [
            "personal_data_id", "user_id", "aadharCardNumber", "panCardNumber", "drivingLicenseNumber",
            "voterIdNumber", "rationCardNumber", "passportNumber", "aadhaarCardLink", "panCardLink",
            "drivingLicenseLink", "voterIdLink", "rationCardLink", "passportLink"
        ]
    }
}

get_address_information = {
    "name": "get_address_information",
    "description": "Get address information including address lines, city, state, country, and pincode.",
    "parameters": {
        "type": "object",
        "properties": {
            "address_id": {
                "type": "string",
                "description": "Unique ID of the address"
            },
            "addressLine1": {
                "type": "string",
                "description": "Address Line 1"
            },
            "addressLine2": {
                "type": "string",
                "description": "Address Line 2 (optional)"
            },
            "city": {
                "type": "string",
                "description": "City"
            },
            "state": {
                "type": "string",
                "description": "State"
            },
            "country": {
                "type": "string",
                "description": "Country"
            },
            "pincode": {
                "type": "integer",
                "description": "Pincode"
            },
            "isResidence": {
                "type": "boolean",
                "description": "Is the address a residence?"
            },
            "isPermanent": {
                "type": "boolean",
                "description": "Is the address permanent?"
            },
            "isMailing": {
                "type": "boolean",
                "description": "Is the address for mailing?"
            }
        },
        "required": [
            "address_id", "addressLine1", "city", "state", "country", "pincode", "isResidence", 
            "isPermanent", "isMailing"
        ]
    }
}
'''


def create_assistant(client, assistant_id):
    try:
        assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)
        return assistant
    except Exception as e:
        assistant = client.beta.assistants.create(
        name="AI Assistant",
        instructions=main_prompt,
        model=model_name,
        tools=[
                {
                    "type": "function",
                    "function": get_user_information # function_call = {'name': 'get_user_information'},
                },
                # {
                #     "type": "function",
                #     "function": get_personal_information # function_call = {'name': 'get_personal_information'},
                # },
                # {
                #     "type": "function",
                #     "function": get_address_information # function_call = {'name': 'get_address_information'},
                # }
                # {
                #     "type": "retrieval",
                #      instructions="You are a customer support chatbot. Use your knowledge base to best respond to customer queries.",
                # }
            ]
        )
        set_redis("assistant_id", assistant.id)
        return assistant

def create_thread(client):
    thread = client.beta.threads.create()
    return thread

def create_run(client, thread_id, assistant_id):
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )
    return run.id, run.status

def upload_message(client, thread_id, input_message, assistant_id):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=input_message
    )
    run_id, run_status = create_run(client, thread_id, assistant_id)
    return run_id, run_status

def get_run_status(client, thread_id, run_id):
    run = client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id
    )
    delay = 5
    try: 
        run_status = run.status
        print(f"run status inside method is {run_status}")
    except Exception as e:
        return None, None

    while run_status not in ["completed", "failed", "requires_action"]:
        time.sleep(delay)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id,
        )
        run_id = run.id
        run_status = run.status
        delay = 8 if run_status == "requires_action" else 5

    return run_id, run_status

def get_tools_to_call(client, thread_id, run_id):
    run = client.beta.threads.runs.retrieve(
        run_id=run_id,
        thread_id=thread_id
    )
    tools_to_call = run.required_action.submit_tool_outputs.tool_calls
    print(f"tools to call are {tools_to_call}")
    print()
    print(f"run id is {run_id}")
    print()
    print(f"thread id is {thread_id}")
    print()
    if tools_to_call is None:
        print("No tools to call")
    return tools_to_call, run.id, run.status

def get_assistant_message(client, thread_id):
    messages = client.beta.threads.messages.list(
        thread_id=thread_id,
    )
    return messages.data[0].content[0].text.value


def transcribe_audio(audio_file, client):
    transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
    )
    return transcript.text

def generate_audio(text, client):
    response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
    return response

def get_duration_pydub(file_path):
    try:
        audio_file = AudioSegment.from_file(file_path)
        duration = audio_file.duration_seconds
        return duration
    except Exception as e:
        print(f"Error occurred while getting duration: {e}")
        return None

def get_random_wait_messages(not_always=False, lang="en"):
    messages = [
        "Please wait",
        "I am processing your request",
        "Hold on",
        "I am on it",
        "I am working on it",
    ]
    if not_always:
        rand = random.randint(0, 2)
        if rand == 1:
            random_message = random.choice(messages)
            random_message = bhashini_translate(random_message, "en", lang)
        else:
            random_message = ""
    else:
        random_message = random.choice(messages)
        random_message = bhashini_translate(random_message, "en", lang)
    return random_message


# get_personal_details = {
#     "name": "get_personal_details",
#     "description": "Get user personal information including name, gender, marital status, date of birth, mobile number, nationality, and email.",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "firstName": {
#                 "type": "string",
#                 "description": "First Name of Person"
#             },
#             "lastName": {
#                 "type": "string",
#                 "description": "Last Name of Person"
#             },
#             "fatherName": {
#                 "type": "string",
#                 "description": "Father's Name of Person"
#             },
#             "motherName": {
#                 "type": "string",
#                 "description": "Mother's Name of Person"
#             },
#             "gender": {
#                 "type": "string",
#                 "description": "Gender of Person",
#                 "enum": ["Male", "Female", "Other"]
#             },
#             "maritalStatus": {
#                 "type": "string",
#                 "description": "Marital Status of Person",
#                 "enum": ["Unmarried", "Married"]
#             },
#             "dob": {
#                 "type": "string",
#                 "description": "Date of Birth of Person. Format is DD-MM-YYYY"
#             },
#             "mobile": {
#                 "type": "string",
#                 "description": "10 digit mobile number. If it has prefix '+91-' at start, then consider mobile number after prefix."
#             },
#             "nationality": {
#                 "type": "string",
#                 "description": "Nationality of Person"
#             },
#             "email": {
#                 "type": "string",
#                 "description": "Email address of Person"
#             }
#         },
#         "required": [
#             "firstName", "lastName", "fatherName", "motherName", "gender", "maritalStatus",
#             "dob", "mobile", "nationality", "email"
#         ]
#     }
# }

# # expermental address function (uses nested functions)
# get_address_details = {
#     "name": "get_address_details",
#     "description": "Get user address information including permanent address, mailing address, and current address.",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "permanentAddress": {
#                 "type": "object",
#                 "description": "Permanent Address of Person",
#                 "properties": {
#                     "addressLine1": {
#                         "type": "string",
#                         "description": "Address Line 1"
#                     },
#                     "addressLine2": {
#                         "type": "string",
#                         "description": "Address Line 2 (optional)"
#                     },
#                     "city": {
#                         "type": "string",
#                         "description": "City"
#                     },
#                     "state": {
#                         "type": "string",
#                         "description": "State"
#                     },
#                     "country": {
#                         "type": "string",
#                         "description": "Country"
#                     },
#                     "pincode": {
#                         "type": "string",
#                         "description": "Pincode"
#                     }
#                 },
#                 "required": ["addressLine1", "city", "state", "country", "pincode"]
#             },
#             "mailingAddress": {
#                 "type": "object",
#                 "description": "Mailing Address of Person",
#                 "properties": {
#                     "addressLine1": {
#                         "type": "string",
#                         "description": "Address Line 1"
#                     },
#                     "addressLine2": {
#                         "type": "string",
#                         "description": "Address Line 2 (optional)"
#                     },
#                     "city": {
#                         "type": "string",
#                         "description": "City"
#                     },
#                     "state": {
#                         "type": "string",
#                         "description": "State"
#                     },
#                     "country": {
#                         "type": "string",
#                         "description": "Country"
#                     },
#                     "pincode": {
#                         "type": "string",
#                         "description": "Pincode"
#                     }
#                 },
#                 "required": ["addressLine1", "city", "state", "country", "pincode"]
#             },
#             "currentAddress": {
#                 "type": "object",
#                 "description": "Current Address of Person",
#                 "properties": {
#                     "addressLine1": {
#                         "type": "string",
#                         "description": "Address Line 1"
#                     },
#                     "addressLine2": {
#                         "type": "string",
#                         "description": "Address Line 2 (optional)"
#                     },
#                     "city": {
#                         "type": "string",
#                         "description": "City"
#                     },
#                     "state": {
#                         "type": "string",
#                         "description": "State"
#                     },
#                     "country": {
#                         "type": "string",
#                         "description": "Country"
#                     },
#                     "pincode": {
#                         "type": "string",
#                         "description": "Pincode"
#                     }
#                 },
#                 "required": ["addressLine1", "city", "state", "country", "pincode"]
#             }
#         },
#         "required": ["permanentAddress", "mailingAddress", "currentAddress"]
#     }
# }

# get_consent_details = {
#     "name": "get_profile_details",
#     "description": "Get user profile details including photo link, consent for storing personal data, Digiform consent, and notification preferences.",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "userPhotoLink": {
#                 "type": "string",
#                 "description": "Link to the user's photo"
#             },
#             "storePersonalData": {
#                 "type": "boolean",
#                 "description": "Consent to store personal data"
#             },
#             "consentForDigiform": {
#                 "type": "boolean",
#                 "description": "Consent for Digiform"
#             },
#             "notificationsAllowed": {
#                 "type": "boolean",
#                 "description": "Allow notifications"
#             }
#         },
#         "required": ["userPhotoLink", "storePersonalData", "consentForDigiform", "notificationsAllowed"]
#     }
# }

# get_personal_documents = {
#     "name": "get_personal_documents",
#     "description": "Get user personal documents including document numbers and links.",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "aadharCardNumber": {
#                 "type": "string",
#                 "description": "Aadhar card number (12 digits)"
#             },
#             "panCardNumber": {
#                 "type": "string",
#                 "description": "PAN card number"
#             },
#             "drivingLicenseNumber": {
#                 "type": "string",
#                 "description": "Driving license number"
#             },
#             "voterIdNumber": {
#                 "type": "string",
#                 "description": "Voter ID number"
#             },
#             "rationCardNumber": {
#                 "type": "string",
#                 "description": "Ration card number"
#             },
#             "passportNumber": {
#                 "type": "string",
#                 "description": "Passport number"
#             },
#             "aadhaarCardLink": {
#                 "type": "string",
#                 "description": "Link to Aadhaar card"
#             },
#             "panCardLink": {
#                 "type": "string",
#                 "description": "Link to PAN card"
#             },
#             "drivingLicenseLink": {
#                 "type": "string",
#                 "description": "Link to driving license"
#             },
#             "voterIdLink": {
#                 "type": "string",
#                 "description": "Link to voter ID"
#             },
#             "rationCardLink": {
#                 "type": "string",
#                 "description": "Link to ration card"
#             },
#             "passportLink": {
#                 "type": "string",
#                 "description": "Link to passport"
#             }
#         },
#         "required": [
#             "aadharCardNumber", "panCardNumber", "drivingLicenseNumber", "voterIdNumber",
#             "rationCardNumber", "passportNumber", "aadhaarCardLink", "panCardLink",
#             "drivingLicenseLink", "voterIdLink", "rationCardLink", "passportLink"
#         ]
#     }
# }

'''
def run_with_streaming_responses(client, thread_id, assistant_id):
    # to add streaming responses
    from typing_extensions import override
    from openai import AssistantEventHandler
    # First, we create a EventHandler class to define
    # how we want to handle the events in the response stream.
    class EventHandler(AssistantEventHandler):    
        @override
        def on_text_created(self, text) -> None:
            print(f"\nassistant > ", end="", flush=True)
            
        @override
        def on_text_delta(self, delta, snapshot):
            print(delta.value, end="", flush=True)
        
        def on_tool_call_created(self, tool_call):
            print(f"\nassistant > {tool_call.type}\n", flush=True)
        
        def on_tool_call_delta(self, delta, snapshot):
            if delta.type == 'code_interpreter':
                if delta.code_interpreter.input:
                    print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)
    # Then, we use the `create_and_stream` SDK helper 
    # with the `EventHandler` class to create the Run 
    # and stream the response.
    with client.beta.threads.runs.create_and_stream(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions="Please address the user as Jane Doe. The user has a premium account.",
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()
'''
# raise_complaint ={
#     "name": "raise_complaint",
#     "description": "Raise complaint",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "description": {
#                 "type": "string",
#                 "description": "Detailed description of complaint"
#             },
#             "service_code": {
#                 "type": "string",
#                 "description": "service code of complaint extracted from description",
#                 "enum": [
#                     "GarbageNeedsTobeCleared", "NoStreetLight", "StreetLightNotWorking",
#                     "BurningOfGarbage", "OverflowingOrBlockedDrain", "illegalDischargeOfSewage",
#                     "BlockOrOverflowingSewage", "ShortageOfWater", "DirtyWaterSupply", "BrokenWaterPipeOrLeakage",
#                     "WaterPressureisVeryLess", "HowToPayPT", "WrongCalculationPT", "ReceiptNotGenerated",
#                     "DamagedRoad", "WaterLoggedRoad", "ManholeCoverMissingOrDamaged", "DamagedOrBlockedFootpath",
#                     "ConstructionMaterialLyingOntheRoad", "RequestSprayingOrFoggingOperation", "StrayAnimals", "DeadAnimals",
#                     "DirtyOrSmellyPublicToilets", "PublicToiletIsDamaged", "NoWaterOrElectricityinPublicToilet", "IllegalShopsOnFootPath",
#                     "IllegalConstructions", "IllegalParking"
#                 ]
#             },
#             "auth_token": {
#                 "type": "string",
#                 "description": "Authentication token of user"
#             },
#             "city": {
#                 "type": "string",
#                 "description": "City of the complaint"
#             },
#             "state": {
#                 "type": "string",
#                 "description": "State of the complaint"
#             },
#             "district": {
#                 "type": "string",
#                 "description": "district of the complaint"
#             },
#             "region": {
#                 "type": "string",
#                 "description": "region of the complaint"
#             },
#             "locality": {
#                 "type": "string",
#                 "description": "locality of the complaint"
#             },
#             "name": {
#                 "type": "string",
#                 "description": "name of the user"
#             },
#             "mobile_number": {
#                 "type": "string",
#                 "description": "mobile number of the user"
#             },
#         },
#         "required": [
#             "description",
#             "service_code",
#             "locality",
#             "city",
#             "name",
#             "mobile_number"
#         ]
#     },
# }