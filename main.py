import os
import base64
import tempfile
import time
from typing import Union

import asyncio
import logging
import dotenv

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
    CallbackContext,
    CallbackQueryHandler,
)

from core.ai import (
    chat, 
    audio_chat, 
    bhashini_text_chat, 
    bhashini_audio_chat,
    parse_photo_text,
    process_image,
    imagegpt
)
from utils.redis_utils import set_redis
import pytesseract
from PIL import Image
import json
from utils.openai_utils import (
    get_duration_pydub, 
    get_random_wait_messages
)

dotenv.load_dotenv("ops/.env")

token = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
class BotInitializer:
    _instance = None
    run_once = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BotInitializer, cls).__new__(cls)
            cls.run_once = True
        return cls._instance

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    BotInitializer()  # To initialize only once

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Welcome to KYC Form Application. I am DigiForm. \n I will help you complete your KYC Form."
        # func to take consent from user to be added later
    )
    await relay_handler(update, context)

async def relay_handler(update: Update, context: CallbackContext):
    await language_handler(update, context)
    
async def language_handler(update: Update, context: CallbackContext):
    # Handle user's language selection
    keyboard = [
        [InlineKeyboardButton("English", callback_data='1')],
        [InlineKeyboardButton("हिंदी", callback_data='2')],
        # [InlineKeyboardButton("मराठी", callback_data='3')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Choose a Language:", 
        reply_markup=reply_markup
    )

async def preferred_language_callback(update: Update, context: CallbackContext):
    
    callback_query = update.callback_query
    languages = {"1": "en", "2": "hi"} # , "3": "mr"
    try:
        preferred_language = callback_query.data
        lang = languages.get(preferred_language)
        context.user_data['lang'] = lang
    except (AttributeError, ValueError):
        lang = 'en'
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="Error getting language! Setting default to English."
        )
    
    text_message = ""
    if lang == "en":
        text_message = "To get started, please provide your mobile number and email." # To get started, please upload your Aadhaar card.
    elif lang == "hi":
        text_message = "नमस्ते, आरंभ करने के लिए कृपया अपना मोबाइल नंबर और ईमेल प्रदान करें।"
        
    set_redis('lang', lang)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=text_message
    )

async def response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    upload_message = "please upload your Aadhaar card and PAN card"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=upload_message)
    
    await query_handler(update, context)

# def check_change_language_query(text):
#     return text.lower() in ["change language", "set language", "language"]

async def query_handler(update: Update, context: CallbackContext):

    lang = context.user_data.get('lang')
    if not lang:
        await language_handler(update, context)
        return

    if update.message.text:
        text = update.message.text
        print(f"text is {text}")
        # if check_change_language_query(text):
        #     await language_handler(update, context)
        #     return
        await chat_handler(update, context, text)
    elif update.message.voice:
        voice = await context.bot.get_file(update.message.voice.file_id)
        await talk_handler(update, context, voice)
    elif update.message.photo:
        photo = await context.bot.get_file(update.message.photo[-1].file_id) # update.message.photo[0].file_id
        # await photo_handler(update, context, photo)
        await photo_handler_1(update, context, photo)

async def photo_handler_1(update: Update, context: ContextTypes.DEFAULT_TYPE, photo):
    assistant_message = ""
    # chat_id = update.effective_chat.id
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=True) as temp_image_file:
        await photo.download_to_drive(custom_path=temp_image_file.name)
        chat_id = update.effective_chat.id
        lang = context.user_data.get('lang')

        wait_message = get_random_wait_messages(
                not_always=True,
                lang=lang
        )
        if wait_message:
            await context.bot.send_message(chat_id=chat_id, text=wait_message)

        try:
            with open(temp_image_file.name, "rb") as image_file: # Open the image file in binary mode
                # Function to encode the image in base64 format
                photo_data = base64.b64encode(image_file.read()).decode('utf-8')
                # photo_data = file.read()
                # using GPT4V 
                text = imagegpt(chat_id, photo_data)
                print(f"text is {text}")
                # Check if the text is in JSON format
                try:
                    data = json.loads(text)
                    # If it's valid JSON, load it as a string
                    text = json.dumps(data)
                except json.JSONDecodeError:
                    # If it's not valid JSON, continue with the original text
                    pass
                assistant_message, history = chat(chat_id, text)
                print(f"assistant_message is {assistant_message}")
                await context.bot.send_message(chat_id=chat_id, text=assistant_message)
                image_file.close()
        except Exception as e:
            print(f"Error in photo_handler_1: {e}")
            await context.bot.send_message(chat_id=chat_id, text="An error occurred. Please try again.")
            # return None
    
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, photo):
    '''
        # Get the file ID of the image
        # file_id = update.message.photo[-1].file_id
        
        # Download the image file
        # file = await context.bot.get_file(file_id)
        file_path = await context.bot.download_to_drive(photo.file_path) # 'current_image.jpg'
        text_1 = parse_photo_text(text)
        
        response = chat(chat_id, text_1)
        print(f"response is {response}")
        # Delete the downloaded image file
        os.remove(file_path)
        
        await context.bot.send_message(chat_id=update.effective_chat.id, text= response)
    '''
    """
    async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = update.message.from_user
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive("user_photo.jpg")
        logger.info("Photo of %s: %s", user.first_name, "user_photo.jpg")
        await update.message.reply_text(
            "Gorgeous! Now, send me your location please, or send /skip if you don't want to."
        )
    """
    assistant_message = ""
    chat_id = update.effective_chat.id
    lang = context.user_data.get('lang')
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=True) as temp_image_file:
        await photo.download_to_drive(custom_path=temp_image_file.name)
        chat_id = update.effective_chat.id

        wait_message = get_random_wait_messages(
                not_always=True,
                lang=lang
        )
        if wait_message:
            await context.bot.send_message(chat_id=chat_id, text=wait_message)

        with open(temp_image_file.name, "rb") as file: # Open the image file in binary mode
            photo_data = file.read()
            text = process_image(chat_id, photo_data) # file
            print(f"text is {text}")
            text_1 = parse_photo_text(text)
            assistant_message, history = chat(chat_id, text_1)
            print(f"assistant_message is {assistant_message}")
            print(type(assistant_message))
            # response_photo, assistant_message, history = parse_photo_text(
            #     chat_id, photo_file=open(temp_image_file.name, "rb")
            # )
            # response_photo.stream_to_file(temp_image_file.name)
            #duration = get_duration_pydub(temp_image_file.name)
            # await context.bot.send_photo(
            #     chat_id=chat_id, 
            #     #photo=open(temp_image_file.name, "rb"), 
            #     filename="response.jpg",
            #     performer="Yojana Didi",
            # )
            await context.bot.send_message(
                chat_id=chat_id, text=assistant_message # try adding [0] if it doesn't work
            )
            file.close()

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    response = ""
    chat_id = update.effective_chat.id
    lang = context.user_data.get('lang')
    wait_message = get_random_wait_messages(
        not_always=True,
        lang=lang
    )
    if wait_message:
        await context.bot.send_message(chat_id=chat_id, text=wait_message)
    if lang == 'en':
        response_en, history = chat(chat_id, text)
    else:
        response, response_en, history = bhashini_text_chat(chat_id,text, lang)
    if response:
        await context.bot.send_message(chat_id=chat_id, text=response)
    # set_redis(history, history)
    await context.bot.send_message(chat_id=chat_id, text=response_en)

async def talk_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, voice):    
    lang = context.user_data.get('lang')
    # getting audio file
    audio_file = voice
    # audio_file = await context.bot.get_file(update.message.voice.file_id)

    if lang == 'en':
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_audio_file:
            await audio_file.download_to_drive(custom_path=temp_audio_file.name)
            chat_id = update.effective_chat.id

            wait_message = get_random_wait_messages(
                not_always=True,
                lang=lang
        )
            if wait_message:
                await context.bot.send_message(chat_id=chat_id, text=wait_message)

            with open(temp_audio_file.name, "rb") as file:
                audio_data = file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')

                response_audio, assistant_message, history = audio_chat(
                    chat_id, audio_file=open(temp_audio_file.name, "rb")
                )
                response_audio.stream_to_file(temp_audio_file.name)
                # fix this error "raise JSONDecodeError("Expecting value", s, err.value) from None" here
                # duration = get_duration_pydub(temp_audio_file.name)
                await context.bot.send_audio(
                    chat_id=chat_id, 
                    audio=open(temp_audio_file.name, "rb"), 
                    #duration=duration, 
                    filename="response.wav",
                    performer="Digiform",
                )
                await context.bot.send_message(
                    chat_id=chat_id, text=assistant_message
                )
                file.close()
    else:
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=True) as temp_audio_file: # suffix='.wav'
            await audio_file.download_to_drive(custom_path=temp_audio_file.name)
            chat_id = update.effective_chat.id

            wait_message = get_random_wait_messages(
                    not_always=True,
                    lang=lang
            )
            if wait_message:
                await context.bot.send_message(chat_id=chat_id, text=wait_message)

            with open(temp_audio_file.name, "rb") as file:
                audio_data = file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                response_audio, response, history = bhashini_audio_chat(
                    chat_id, 
                    audio_file=audio_base64, 
                    lang=lang
                )
                file_ = open(temp_audio_file.name, "wb")
                file_.write(response_audio.content)
                file_.close()
                with open(temp_audio_file.name, "rb") as file:
                    duration = get_duration_pydub(temp_audio_file.name)
                    await context.bot.send_audio(
                        chat_id=chat_id, 
                        audio=open(temp_audio_file.name, "rb"), 
                        duration=duration, 
                        filename="response.mp3",
                        performer="Yojana Didi",
                    )
                await context.bot.send_message(
                    chat_id=chat_id, text=response
                )
                file_.close()

if __name__ == '__main__':
    application = ApplicationBuilder().token(
        token
    ).read_timeout(30).write_timeout(30).build()
    start_handler = CommandHandler('start', start)
    language_handler_ = CommandHandler('set_language', language_handler)
    chosen_language = CallbackQueryHandler(preferred_language_callback, pattern='[1-3]')
    application.add_handler(start_handler)
    application.add_handler(language_handler_)
    application.add_handler(chosen_language)
    application.add_handler(
        MessageHandler(
            (filters.TEXT & (~filters.COMMAND)) | (filters.VOICE & (~filters.COMMAND)) | (filters.PHOTO & (~filters.COMMAND)), 
            response_handler
        )
    )
    application.run_polling()
