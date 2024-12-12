import json
import os
import requests
import time
from dotenv import load_dotenv
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from google.cloud import texttospeech
from faster_whisper import WhisperModel
from openai import OpenAI
# from aws import upload_audio_to_s3

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Twilio setup
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)
twilio_phone_number = client.incoming_phone_numbers.list()[0].phone_number

# Initialize ChatGPT API Key
openai_api_key = os.getenv("OPENAI_API_KEY")


# Initialize Google Text-to-Speech Client
GOOGLE_APPLICATION_CREDENTIALS = "key.json"
# tts_client = texttospeech.TextToSpeechClient()



@app.route("/voice", methods=["POST"])
def voice():
    """
    Respond to an incoming phone call with a language selection menu

    """
    # Create a VoiceResponse object to build the response
    response = VoiceResponse()

    # Prompt the caller to select a language

    response.play("https://limerick-toucan-5791.twil.io/assets/Menu.wav")

    # Gather the caller's language selection
    with response.gather(num_digits=1, action="/language-selected", method="POST") as gather:
        pass

    with response.gather(num_digits=2, action="/language-selected", method="POST") as gather:
        # gather.say("Please select your preferred language.")
        pass

    # Return the response as a string
    return str(response)

@app.route("/language-selected", methods=["POST"])
def language_selected():
    """ Respond to the caller's language selection"""

    # Create a VoiceResponse object to build the response
    response = VoiceResponse()

    # Retrieve the selected language from the request
    selected_language = request.form["Digits"]

    # Based on the selected language, provide the appropriate language prompt
    if selected_language == "1":
        response.play(r"https://limerick-toucan-5791.twil.io/assets/En%20option.wav")

        response.record(action="/process-recording", method="POST", timeout=2, max_length=30, speech_model="default")
        # response.record(max_length=30, transcribe=True, transcribe_callback='/message')

    elif selected_language == "2":
        response.play(r"https://limerick-toucan-5791.twil.io/assets/twi_opt_audio.wav")
        print("Recording")
        response.record(action="/twi-recording", method="POST", timeout=2,max_length=30, speech_model="default")
        
    # Return the response as a string
    return str(response)

def transcribe_whisperAI(audio):
    """
    Transcribe the audio using the WhisperAI model
    """
    transcibed_list = []
    model = WhisperModel("small")
    segments, info = model.transcribe(audio)
    language = info[0]
    segments = list(segments)
    for segment in segments:
       
        transcibed_list.append(segment.text)
    transcribed_text = " ".join(transcibed_list).strip()
    transcribed_text = " ".join(transcribed_text.split())
    return transcribed_text
 

client = OpenAI()

def call_chatgpt_api(transcribed_speech):
    # Call the ChatGPT API with the transcribed speech as the user message
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content":"You are a helpful assistant with expertise in farming and agriculture. Every response should relate to farming, agriculture, or rural life. Ensure that responses are concise and formatted as a single, clear and complete paragraph."},
            {"role": "user", "content": transcribed_speech}
        ],
        max_tokens=80  # Adjust this to control the approximate length (75 words is about 100 tokens)
    )
    
    return completion.choices[0].message.content



def synthesize_text_to_speech(generated_text, output_audio_file):
    """Convert text to speech using Google TTS and save it as an audio file."""
    
    # Create the TTS request and get the response
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=generated_text,
    )
    
    # Write the audio content to the output file
    with open(output_audio_file, "wb") as audio_file:
        for chunk in response.iter_bytes():
            audio_file.write(chunk)
    
    return output_audio_file



import boto3

# Initialize the S3 client with your credentials (ensure they're configured)
s3 = boto3.client('s3')

def upload_audio_to_s3(file_path, bucket_name, object_name):
    """
    Uploads an audio file to an S3 bucket and sets the content type for direct playback.
    """
    response = VoiceResponse()
    response.play(r"https://limerick-toucan-5791.twil.io/assets/On%20hold.wav")
    try:
        # Upload the file to S3 with Content-Type set as audio/mpeg
        s3.upload_file(
            file_path, 
            bucket_name, 
            object_name, 
            ExtraArgs={'ContentType': 'audio/mpeg'}
        )
        print(f"File {object_name} uploaded successfully to {bucket_name}.")
        
        # Construct the public URL for the uploaded file
        public_url = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
        print(public_url)
        return public_url
        
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None


@app.route("/process-recording", methods=["POST"])
def process_recording():
    """Process the recorded speech, send to ChatGPT, convert response to speech, and play back"""
    print("Processing recording...")
    response = VoiceResponse()
    
    recording_url = request.form.get("RecordingUrl")
    time.sleep(2)  # Allow the recording to save
    
    try:
        # Fetch audio recording
        remote_audio_file = requests.get(f'{recording_url}.mp3', auth=(account_sid, auth_token))

        print(f"recording: {recording_url}")

        if remote_audio_file.status_code != 200:
            raise Exception("Failed to fetch audio file")
        
        # Save recording locally
        recording_sid = request.form.get("RecordingSid")
        audio_file_path = f'voices/{recording_sid}.wav'
        with open(audio_file_path, 'wb') as f:
            f.write(remote_audio_file.content)

        # Transcribe the audio (assuming `transcribe_whisperAI` function is defined elsewhere)

        response.play(r"https://limerick-toucan-5791.twil.io/assets/On%20hold.wav")
        transcribed_speech = transcribe_whisperAI(audio_file_path)
        # transcribed_speech = "i want information on climate change"
        
        # response.play(r"https://limerick-toucan-5791.twil.io/assets/On%20hold.wav")
        # time.sleep(2)
        print(f"Transcribed Speech: {transcribed_speech}")
        chatgpt_response = call_chatgpt_api(transcribed_speech)
        # chatgpt_response = "Rising temperatures can affect crop yields. Some crops may thrive in warmer conditions, but many staple crops like wheat, rice, and corn are sensitive to temperature increases, which can result in decreased yields."
        print(f"ChatGPT Response: {chatgpt_response}")
         
        # response.say('done')
        # Convert ChatGPT response to audio
        response.play(r"https://limerick-toucan-5791.twil.io/assets/On%20hold.wav")
        audio_response_path = synthesize_text_to_speech(chatgpt_response, f'voices/response_{recording_sid}.mp3')
        print(f"Audio Response Path: {audio_response_path}")
        
        # time.sleep(3)

        # #upload recording to aws bucket
        response.play(r"https://limerick-toucan-5791.twil.io/assets/On%20hold.wav")
        print("Uploading audio to S3...")
        public_url = upload_audio_to_s3(audio_response_path, "farmtalker", audio_response_path)
        # # public_url = upload_audio_to_s3("voices/REed92fe8370564a1eb21163e328f89d34.wav", "farmtalker", "voices/REed92fe8370564a1eb21163e328f89d34.wav")
        response.play(public_url)
        
        # # Ask the user if they need more information
        
        response.play("https://limerick-toucan-5791.twil.io/assets/Extension1.wav")
        
        # Gather the response from the user
        with response.gather(num_digits=1, action="/check-follow-up", method="POST") as gather:
            pass

        return str(response)
        
    except Exception as e:
        print(f"Error processing recording: {e}")
        response.say("Sorry, there was an error processing your request.")
    
    return str(response)

@app.route("/check-follow-up", methods=["POST"])
def check_follow_up():
    """Handle follow-up responses to continue the conversation."""
    response = VoiceResponse()

    selected_option = request.form.get("Digits")
    if selected_option == "1":
        response.play(r"https://limerick-toucan-5791.twil.io/assets/On%20hold.wav")
        response.record(action="/process-recording", method="POST", timeout=3, max_length=15, speech_model="default")
    elif selected_option == "2":
        response.play(r"https://limerick-toucan-5791.twil.io/assets/Byeee.wav")
        response.hangup()

    return str(response)





"TWI PART"
import requests


def transcribe_audio_twi(audio_file_path):
    """
    Transcribe the given audio file in Twi
    Return: Twi Transcription
    """
    url = "https://translation-api.ghananlp.org/asr/v1/transcribe?language=tw"
    
    headers = {
        'Ocp-Apim-Subscription-Key': '4f00858473444353b3d414e568ec8a8e',
        'Content-Type': 'audio/wave'
    }

    with open(audio_file_path, 'rb') as file:
        payload = file.read()

    res = requests.post(url, headers=headers, data=payload)
    
    if res.status_code == 200:
        return res.text
    else:
        return f"Error: {res.status_code} - {res.text}"
    



def translate(text,input_lang,target_language):

    """
    Translate the given text from an input language to the specified language.
    Return: Translated Text
    """

    target_lang_dict = {
        "english":"en",
        "twi":"tw",
        "ewe": "ee",
        "ga": "gaa",
        "fante": "fat"}
        
    # Define the API endpoint
    url = "https://translation-api.ghananlp.org/v1/translate"

    payload = json.dumps({
        "in": text,
        "lang": f'{target_lang_dict[input_lang]}-{target_lang_dict[target_language]}',
        # "lang": "en-tw",
    })
    # Define the request headers
    headers = {
        'Ocp-Apim-Subscription-Key': os.getenv("Ocp-Apim-Subscription-Key"),
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    translate = response.text
    return translate


def text_to_speech(input, lang, voice_name):
    """
    Convert the given text to speech in the specified language.
    Return: The URL to the audio file or an error message.
    """
    
    target_lang_dict = {
        "english":"en",
        "twi":"tw",
        "ewe": "ee",
        "ga": "gaa",
        "fante": "fat"}
    # Define the API endpoint
    url = "https://translation-api.ghananlp.org/tts/v1/tts"
    
    # Load the subscription key from environment variables
    api_key = os.getenv("Ocp_Apim_Subscription_Key")
    
    # Prepare the payload
    payload = json.dumps({
        "text": input,
        "language": f'{target_lang_dict[lang]}',
    })
    
    # Define the request headers
    headers = {
        'Ocp-Apim-Subscription-Key': '4f00858473444353b3d414e568ec8a8e',
        'Content-Type': 'application/json'
    }
    
    # Send the POST request
    response = requests.post(url, headers=headers, data=payload)
    
    # Return the result
    if response.status_code == 200:
        print("works")
        # Save audio content to a file
        audio_file_path = f"twi_responses/response_{voice_name}.wav"
        with open(audio_file_path, 'wb') as file:
            file.write(response.content)

        # Return the URL to the audio file
        return audio_file_path
    else:
        return f"Error: {response.status_code} - {response.text}"



@app.route("/twi-recording", methods=["POST"])
def twi_recording():
    """Process the recorded Twi speech and provide a response"""
    # print("Twi Recording Processing")
    response = VoiceResponse()
    time.sleep(2)
    recording_url = request.form.get("RecordingUrl")

    try:
        # remote_audio_file = requests.get(f'{recording_url}.mp3')
        # Request to get Audio file
        remote_audio_file = requests.get(f'{recording_url}.mp3', auth=(account_sid, auth_token))
        print(f"HTTP status code: {remote_audio_file.status_code}")
        
        if remote_audio_file.status_code != 200:
            raise Exception(f"Failed to fetch the audio file: {remote_audio_file.status_code}")
        
        recording_sid = request.form.get("RecordingSid")
        audio_file_path = f'twi_audios/{recording_sid}.wav'

        with open(audio_file_path, 'wb') as file:
            file.write(remote_audio_file.content)

        # Transcribe the saved Twi audio file
        transcription = transcribe_audio_twi(audio_file_path)
        
        print(f"Twi transcription: {transcription}")

        # translate the transcription to English
        # translated_transcription = translate(transcription, "twi", "english")
        translated_transcription = "I want information on crop diversification"
        print(f"Translated transcription: {translated_transcription}")

        response.play(r"https://limerick-toucan-5791.twil.io/assets/On%20hold.wav")

        # pass through chat gpt
        chatgpt_response = call_chatgpt_api(translated_transcription)
        print(f"ChatGPT Response: {chatgpt_response}")
         
        # Convert ChatGPT response to audio
        response.play(r"https://limerick-toucan-5791.twil.io/assets/On%20hold.wav")
        
        # convert to twi
        convert_twi = translate(chatgpt_response, "english", "twi") 
        audio_response_path = text_to_speech(convert_twi, "twi", recording_sid)
        print(f"Audio Response Path: {audio_response_path}")

        response.play(audio_response_path)

        
        # time.sleep(3)

        #upload recording to aws bucket
        response.play(r"https://limerick-toucan-5791.twil.io/assets/On%20hold.wav")
        print("Uploading audio to S3...")
        public_url = upload_audio_to_s3(audio_response_path, "farmtalker", audio_response_path)
        response.play(public_url)


        
    except Exception as e:
        print(f"Error processing recordingg: {e}")
        response.say("Sorry, there was an error processing your request.")
    
    return str(response)



if __name__ == "__main__":
    app.run(debug=True)

    # print(transcript)

