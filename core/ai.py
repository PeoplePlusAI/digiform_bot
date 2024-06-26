from openai import OpenAI
import numpy as np
import cv2
import pytesseract
import base64
import requests
# from utils.digit_utils import (
#     get_auth_token, 
#     file_complaint, 
#     search_complaint
# )
from utils.openai_utils import (
    create_run,
    create_thread,
    upload_message,
    get_run_status,
    get_assistant_message,
    create_assistant,
    transcribe_audio,
    generate_audio,
    get_tools_to_call
)
from utils.redis_utils import (
    get_redis_value,
    set_redis,
)

from utils.bhashini_utils import (
    bhashini_translate,
    bhashini_asr,
    bhashini_tts
)

from utils.profile import (
    profile_creation
)

import os
import json
import time
from dotenv import load_dotenv

load_dotenv(
    dotenv_path="ops/.env",
)

openai_api_key = os.getenv("OPENAI_API_KEY")

# USERNAME = os.getenv("USERNAME")
# PASSWORD = os.getenv("PASSWORD")

assistant_id = get_redis_value("assistant_id")

print(f"assistant id is {assistant_id}")

client = OpenAI(
    api_key=openai_api_key,
)

assistant = create_assistant(client, assistant_id)

assistant_id = assistant.id

def get_metadata(chat_id):
    """
    Get thread_id, run_id and status from redis
    """
    history = get_redis_value(chat_id)
    if history == None:
        history = {
            "thread_id": None,
            "run_id": None,
            "status": None,
        }
    else:
        history = json.loads(history)
    return history

def set_metadata(chat_id, history):
    """
    Set thread_id, run_id and status in redis
    """
    set_redis(chat_id, json.dumps(history))
    thread_id = history.get("thread_id")
    run_id = history.get("run_id")
    status = history.get("status")
    return thread_id, run_id, status

def get_or_create_thread_id(client, thread_id):
    """
    Get thread_id if exists else create a new thread
    using openAI assistant API
    """
    if thread_id:
        thread = client.beta.threads.retrieve(thread_id)
        thread_id = thread.id
    else:
        thread = create_thread(client)
        thread_id = thread.id
    return thread_id

def gather_user_details(input_message, history, assistant_id):
    """
    Converse with the user and gather details using 
    openAI assistant API
    """
    thread_id = history.get("thread_id")
    status = history.get("status")
    print(thread_id, input_message, assistant_id)
    run_id, status = upload_message(client, thread_id, input_message, assistant_id)
    print("run.status is", status)
    run_id, status = get_run_status(client, thread_id, run_id)
    print(f"input message is {input_message}")
    print(f"run status is {status}")
    if status == "completed":
        assistant_message = get_assistant_message(client, thread_id)
    else:
        assistant_message = "something went wrong please check the openAI API"
        # call the function

    print(f"assistant message is {assistant_message}")

    history = {
        "thread_id": thread_id,
        "run_id": run_id,
        "status": status,
    }
    return assistant_message, history


def digiform(parameters, tool_id, thread_id, run_id):
    """
    DigiForm API call
    """
    print(f"tool id is {tool_id}")
    print(f"thread id is {thread_id}")
    print(f"run id is {run_id}")
    print(f"parameters are {parameters}")
    
    # other_details = {"nationality": "Indian"}
    # parameters.update(other_details)
    
    tool_output_array = [
        {
            "tool_call_id": tool_id,
            "output": 
        }
    ]
    run = client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_output_array
    )
    run_id, status = get_run_status(client, thread_id, run.id)
    
    if status == "completed":
            assistant_message = get_assistant_message(client, thread_id)
    else:
        assistant_message = "something went wrong please check the openAI API"
    print(f"assistant message is {assistant_message}")

    history = {
        "thread_id": thread_id,
        "run_id": run_id,
        "status": status,
    }
    return assistant_message, history

def process_creating_profile_action(parameters, tool_id, thread_id, run_id):
    """
    Creates the citizen profile and get the person_id when the action required is profile_creation
    """
    id = profile_creation(parameters) # id is int
    if id != 0:
        person_id = str(id)
        tool_output_array = [
            {
                "tool_call_id": tool_id,
                "output": person_id
            }
        ]
        run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_output_array
        )
        run_id, status = get_run_status(client, thread_id, run.id)

        if status == "completed":
            assistant_message = get_assistant_message(client, thread_id)
        else:
            assistant_message = "something went wrong please check the openAI API"
        print(f"assistant message is {assistant_message}")

        history = {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": status,
        }
        return assistant_message, history
    else:
        error = "Profile creation failed. Please try again later."
        history = {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": "failed",
        }
        return error, history
    
def compose_function_call_params(func_name, arguments):
    """
    Compose function call parameters based on the args
    provided by openAI function calling API
    """
    # auth_token = get_auth_token(
    #         {
    #             "username": USERNAME,
    #             "password": PASSWORD
    #         }
    # )
    print(f"function name is {func_name}")
    try:
        parameters = json.loads(arguments)
    except:
        if isinstance(parameters, dict):
            print("Already a JSON")
    # parameters["auth_token"] = auth_token
    # parameters["username"] = username
    return parameters


def process_function_calls(tools_to_call, thread_id, run_id):
    """
    Method to manage all function calls using openAI
    """
    for tool in tools_to_call:
        func_name = tool.function.name
        print(f"function name is {func_name}")
        parameters = compose_function_call_params(
            func_name, tool.function.arguments
        )
        if func_name == "get_user_details":
            assistant_message, history = digiform(
                parameters, tool.id, thread_id, run_id
            )
        # elif func_name == "search_complaint":
        #     assistant_message, history = process_search_complaint_action(
        #         parameters, tool.id, thread_id, run_id
        #     )
        else:
            assistant_message = "This functionality is not supported yet. Please try again later."
            history = {
                "thread_id": thread_id,
                "run_id": run_id,
                "status": "requires_action",
            }
    return assistant_message, history

def chat(chat_id, input_message, client=client, assistant_id=assistant_id):
    """
    Main chat logic using OpenAI assistant API and function calling API
    """
    # setting default assistant_message
    assistant_message = "Something went wrong. Please try again later."    
    history = get_metadata(chat_id)
    print(history)
    thread_id = history.get("thread_id")
    run_id = history.get("run_id")
    status = history.get("status")
    thread_id = get_or_create_thread_id(client, thread_id)
    history["thread_id"] = thread_id
    print(f"thread id is {thread_id}")
    if status == "failed":
        run = client.beta.threads.runs.cancel(
                thread_id=thread_id,
                run_id=run_id
        )
        status = None
    if status == "completed" or status == None:
        assistant_message, history = gather_user_details(
            input_message, history, assistant_id
        )      
        thread_id, run_id, status = set_metadata(chat_id, history)
        history = {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": status,
        }
    if status == "requires_action":
        tools_to_call, run_id, status = get_tools_to_call(
            client, thread_id, run_id
        )
        assistant_message, history = process_function_calls(
            tools_to_call, thread_id, run_id
        )
        thread_id, run_id, status = set_metadata(chat_id, history)

    return assistant_message, history

def audio_chat(chat_id, audio_file):
    """
    Audio chat logic using OpenAI tts and stt
    """
    input_message = transcribe_audio(audio_file, client)
    assistant_message, history =  chat(chat_id, input_message)
    response_audio = generate_audio(assistant_message, client)
    return response_audio, assistant_message, history

def bhashini_text_chat(chat_id, text, lang): 
    """
    bhashini text chat logic
    """
    input_message = bhashini_translate(text, lang, "en")
    response_en, history = chat(chat_id, input_message)
    response = bhashini_translate(response_en, "en", lang)
    return response, response_en, history

def bhashini_audio_chat(chat_id, audio_file, lang):
    """
    bhashini voice chat logic
    """
    input_message = bhashini_asr(audio_file, lang, "en")
    response, history = chat(chat_id, input_message)
    response = bhashini_translate(response, "en", lang)
    audio_content = bhashini_tts(response, lang)
    return audio_content, response, history


def parse_photo_text(photo_text):
    """
    Method to parse text from a photo
    """
    prompt = '''
    You are a helpful assistant that reads extracted text data from an image. the image data is read using opencv and pytesseract, so they are slightly jumbled together. 
    Your task is to read the given text and identitfy entites like first name, last name, mobile number, gender, marital status, and date of birth (dob). If some details are not possible, ask the user to input it as text.  
    Whatever entites you're able to identify, try to organize this information into a structured JSON string with the following format:
    {
    "firstName": <value>,
    "lastName": <value>,
    "mobile": <value>,
    "gender": <value>,
    "maritalStatus": <value>,
    "dob": <value>,
    }
    '''
    response = ""
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt.replace('\n', ' ')},
            {"role": "user", "content": photo_text}
        ]
    )

    try:
        print(f"completion is {completion}\n\n")
        # print("completion is", completion, "\n\n")
        response = completion.choices[0].message.content
        print(f"response_text is {response}")
        print(type(response))
        #response = json.loads(response)
    except Exception as e:
        print(e)
        response = "Cannot read image. Input all details as text"
    return response

def process_image(chat_id, image_data):
    """
    Process the uploaded image and extract text using OCR.

    Parameters:
    - chat_id (int): The ID of the chat.
    - image_data (str): Binary data of the uploaded image.

    Returns:
    - text (str): The extracted text from the image.
    """
    # Process the uploaded image as needed
    # Decode the image from binary data
    image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
    
    image = cv2.resize(image, None, fx=2, fy=2,interpolation=cv2.INTER_CUBIC) # remove this if isn't working

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    '''
    var = cv2.Laplacian(img, cv2.CV_64F).var()
    if var < 50:
        print("Image is Too Blurry....")
        k= input('Press Enter to Exit.')
        exit(1)
    '''

    # Apply thresholding to preprocess the image
    threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # Set the path to the Tesseract executable
    pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'

    # Perform text extraction using pytesseract
    text = pytesseract.image_to_string(threshold)
    print(f"text from inside the func is {text}")

    return text

def imagegpt(chat_id, image_data):
    prompt = '''
    You are a helpful assistant that reads extracted text data from Indian Aadhaar Card.
    Your task is to accepts ID documents to visually understands the data inside them and identitfy entites like the following:
    1. First Name: Identify patterns that suggest the user's first name.
    2. Last Name: Identify patterns that suggest the user's last name.
    3. Father's Name: Identify the user's father's name. It'll usually begin with S/O <Father's name>
    4. Gender: Detect mentions or indicators of gender, recognizing common terms for male, female, other gender identities (Options: Male, Female, Other)
    5. Date of Birth: Identify dates that could represent the user's birth date, keeping an eye out for various date formats. (Format: DD-MM-YYYY)
    6. Permanent Address: Identify patterns that suggest the user's permanent address. It'll be in this format: address_line1, address_line2, City/town/village, State, Country (India), Pin Code 
    7. Aadhaar Number: Identify the user's 12 digit Aadhaar number.
    
    Whatever entites you're able to identify, try to organize this information into JSON string with the following format:
    {
    "first_name": <value>,
    "last_name": <value>,
    "father_name": <value>,
    "gender": <value>,
    "dob": <value>,
    "permanentAddressId": <value>,
    "aadhaar_number": <value>
    }
    
    These are the steps you need to follow: 
    1. On receiving the photo, read back their name, address, mobile, gender and Aadhaar card number. If their address or mobile number was not provided, ask them to send a photo of the back of their Aadhaar card. 
    2. Ask one question at a time until you've collected answers to complete the JSON data above. Assume today is June 15, 2024 and use this date to calculate their age if you know their DOB.

    Guidelines:
    - Avoid answering questions beyond Aadhaar card and form filling in India. 
    - Respond without emojis, bulleted lists or special symbols (e.g. “*”)
    - Respond in the same language as the user. e.g. if they ask a question in Hindi, reply in Hindi. 
    - Use simple, direct language.
    '''
    # 5. Marital Status: Detect keywords or phrases that indicate marital status, such as unmarried or married. (Options: Unmarried, Married)
    # 9. Nationality: Indian
    
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_data}"},
            },
        ],
        }
    ],
    max_tokens=300,
    )
    
    res = response.choices[0].message.content
    print(res)
    print()
    return res
