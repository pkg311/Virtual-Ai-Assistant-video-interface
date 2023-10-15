import threading
import os
import time
import pygame
import streamlit as st
import speech_recognition as sr
import openai
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.playback import play
from gtts import gTTS

# Set OpenAI API key
openai.api_key = '### Enter your open AI API KEY ####'

# Initialize Streamlit UI
st.title("Atech - Voice Assistant")
st.text("Welcome to Atech. How may I assist you? Say 'Hello' to start, and 'Goodbye' to end the conversation.")
lang = 'en' # select your language 
gender = 'female' # select Voice Gender
video_path = r"Video Path"  # Replace with the path to your video file

def generate_response(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=80
    )
    return response.choices[0].text.strip()

def take_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        r.pause_threshold = 3
        audio = r.listen(source)

    try:
        st.write("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        st.write(f"User said: {query}\n")
        return query
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.write("Say that again please...")
        return "None"

def display(response):
    converter = TextToVideoConverter(lang, gender)
    converter.combine_text_with_video(response, video_path)
    converter.clear_resources()

class TextToVideoConverter:
    def __init__(self, lang='en', gender='female'):
        self.lang = lang
        self.gender = gender
        self.engine = self.get_voice()
        pygame.init()

    def get_audio_duration(self, audio_path):
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0  # Convert duration to seconds

    def get_voice(self):
        voices = {
            'en': {
                'female': 'en'
            },
            # Add more languages and gender options as needed
        }
        lang_code = voices.get(self.lang, {}).get(self.gender, 'en')
        return lang_code

    def generate_audio_from_text(self, text, audio_output_path):
        if text:
            lang_code = self.get_voice()
            engine = gTTS(text=text, lang=lang_code, slow=False)
            engine.save(audio_output_path)

    def play_audio(self, audio_path, audio_duration, completion_event):
        audio = AudioSegment.from_file(audio_path)
        play(audio)
        time.sleep(audio_duration)
        completion_event.set()  # Set the completion event when audio playback is done

    def play_video(self, video_path, video_duration, completion_event):
        video = VideoFileClip(video_path)

        # Remove the video's audio
        video = video.set_audio(None)

        subclip = video.subclip(0, video_duration)  # Create a subclip matching audio duration
        try:
            subclip.preview()  # Play the subclip
        except Exception as e:
            print(f"Error playing video: {e}")
        finally:
            completion_event.set()  # Set the completion event when video playback is done
            video.close()  # Close the video reader

    def delete_audio_file(self, audio_path):
        os.remove(audio_path)

    def clear_resources(self):
        pygame.quit()  # Close the Pygame window

    def combine_text_with_video(self, text, video_path):
        audio_output_path = "output_audio.mp3"
        self.generate_audio_from_text(text, audio_output_path)

        audio_path = audio_output_path

        audio_duration = self.get_audio_duration(audio_path)
        video_duration = audio_duration  # Set video duration equal to audio duration

        audio_completion_event = threading.Event()
        video_completion_event = threading.Event()

        audio_thread = threading.Thread(target=self.play_audio,
                                        args=(audio_path, audio_duration, audio_completion_event))
        video_thread = threading.Thread(target=self.play_video,
                                        args=(video_path, video_duration, video_completion_event))

        audio_thread.start()
        video_thread.start()

        audio_thread.join()
        video_thread.join()

        # Delete the audio file after playback is completed
        self.delete_audio_file(audio_path)

a = False

while True:
    query = take_command().lower()
    if 'hello' in query:
        a = True
        response = generate_response(query)
        st.write(f"System response: {response}\n")
        display(response)

    while a:
        query = take_command().lower()
        if "thank you" in query or "goodbye" in query:
            display('Have a good day. Thank you for chatting with me.')
            a = False
            break
        else:
            response = generate_response(query)
            st.write(f"System response: {response}\n")
            display(response)
