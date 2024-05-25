"""Main file for the Solo project"""
import os
from os import PathLike
from time import time
import asyncio
from typing import Union

from dotenv import load_dotenv
import openai
from deepgram import Deepgram
import pygame
from pygame import mixer
import elevenlabs
import pyttsx3

from record import speech_to_text

# Load API keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
elevenlabs.set_api_key(os.getenv("ELEVENLABS_API_KEY"))

# Initialize APIs
gpt_client = openai.Client(api_key=OPENAI_API_KEY)
deepgram = Deepgram(DEEPGRAM_API_KEY)
# mixer is a pygame module for playing audio
mixer.init()

# Change the context if you want to change Jarvis' personality
context = """You are Data Scientist Voice Assistant, your name is Solo. 
             You are human assistant in DataScience, Machine Learning, Neural Networks, DeepLearing,
             Programming, Python, ML fraimworks and other Technologies. 
             You are witty and full of personality. 
             Your answers should be limited to 2-8 short sentences."""

            #  for gpt-4o specific
            #  Your answers should be limited to 1-2 short sentences.
            #  When you reply do not send icons or other non-UTF-8 characters.

conversation = {"Conversation": []}
RECORDING_PATH = "audio/recording.wav"

# replace original text to wav
tts = pyttsx3.init()


def request_gpt(prompt: str) -> str:
    """
    Send a prompt to the GPT-3 API and return the response.

    Args:
        - state: The current state of the app.
        - prompt: The prompt to send to the API.

    Returns:
        The response from the API.
    """
    response = gpt_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"{prompt}",
            }
        ],
        model="gpt-3.5-turbo",
        # model="gpt-4o",
    )
    return response.choices[0].message.content


async def transcribe(
    file_name: Union[Union[str, bytes, PathLike[str], PathLike[bytes]], int]
):
    """
    Transcribe audio using Deepgram API.

    Args:
        - file_name: The name of the file to transcribe.

    Returns:
        The response from the API.
    """
    with open(file_name, "rb") as audio:
        source = {"buffer": audio, "mimetype": "audio/wav"}
        response = await deepgram.transcription.prerecorded(source)
        return response["results"]["channels"][0]["alternatives"][0]["words"]


def log(log: str):
    """
    Print and write to status.txt
    """
    print(log)
    with open("status.txt", "w") as f:
        f.write(log)


if __name__ == "__main__":

    voices = tts.getProperty('voices')
    for voice in voices:
        print('=======')
        print('Имя: %s' % voice.name)
        print('ID: %s' % voice.id)
        print('Язык(и): %s' % voice.languages)
        print('Пол: %s' % voice.gender)
        print('Возраст: %s' % voice.age)

    # Задать голос по умолчанию
    tts.setProperty('voice', 'ru') 

    # Попробовать установить предпочтительный голос
    for voice in voices:
        # if voice.name == 'Microsoft Irina Desktop - Russian':
        #     tts.setProperty('voice', voice.id)
        if voice.name == 'Microsoft Zira Desktop - English (United States)':
            tts.setProperty('voice', voice.id)

    while True:
        # Record audio
        log("Listening...")
        speech_to_text()
        log("Done listening")

        # Transcribe audio
        current_time = time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        words = loop.run_until_complete(transcribe(RECORDING_PATH))
        string_words = " ".join(
            word_dict.get("word") for word_dict in words if "word" in word_dict
        )
        with open("conv.txt", "a") as f:
            f.write(f"{string_words}\n")
        transcription_time = time() - current_time
        log(f"Finished transcribing in {transcription_time:.2f} seconds.")

        # Get response from GPT-3
        current_time = time()
        context += f"\nAlex: {string_words}\nStarovoytov: "
        response = request_gpt(context)
        context += response
        gpt_time = time() - current_time
        log(f"Finished generating response in {gpt_time:.2f} seconds.")

        # Convert response to audio
        current_time = time()
        # audio = elevenlabs.generate(
        #     text=response, voice="Adam", model="eleven_monolingual_v1"
        # )
        # elevenlabs.save(audio, "audio/response.wav")
        audio = tts.save_to_file(response, 'audio/response.wav')
        tts.runAndWait()
        audio_time = time() - current_time
        log(f"Finished generating audio in {audio_time:.2f} seconds.")

        # Play response
        log("Speaking...")
        sound = mixer.Sound("audio/response.wav")
        # Add response as a new line to conv.txt
        # with open("conv.txt", "a") as f:
        #     f.write(f"{response}\n")
        with open("conv.txt", "a", encoding="utf-8") as f:
            f.write(f"{response}\n")
        sound.play()
        pygame.time.wait(int(sound.get_length() * 1000))
        print(f"\n --- USER: {string_words}\n --- SOLO: {response}\n")
