import datetime
import json
import os
import requests
import time
from dotenv import load_dotenv
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from dotenv import load_dotenv
from google.cloud import speech
from faster_whisper import WhisperModel

# from helper_func.twi_func import transcribe_audio_twi


os.environ['KMP_DUPLICATE_LIB_OK']='True'

# Load environment variables from .env file
load_dotenv()

# Load Twilio credentials from environment variables
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

# Initialize Twilio client
client = Client(account_sid, auth_token)

# Initialize OpenAi client
# openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get your Twilio phone number from the Twilio API
twilio_phone_number = client.incoming_phone_numbers.list()[0].phone_number
print(f"Twilio phone number: {twilio_phone_number}")


app = Flask(__name__)

#set up google cloud credentials
GOOGLE_APPLICATION_CREDENTIALS = "key.json"

#Initialize the google speech to text client
# g_client = speech_v1.SpeechClient()




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
        # gather.say("Please select your preferred language.")
        pass

    with response.gather(num_digits=2, action="/language-selected", method="POST") as gather:
        gather.say("Please select your preferred language.")

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

        response.record(action="/process-recording", method="POST", timeout=3, max_length=30, speech_model="default")
        # response.record(max_length=30, transcribe=True, transcribe_callback='/message')

    elif selected_language == "2":
        response.play(r"https://limerick-toucan-5791.twil.io/assets/twi_opt_audio.wav")
        response.record(action="/twi-recording", method="POST", timeout=3,max_length=15, speech_model="default")
        
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

#Storing keywords with their respective audios
audio_map= {'climate change': r"https://limerick-toucan-5791.twil.io/assets/Climate%20change.wav",
                'maize production': r"https://limerick-toucan-5791.twil.io/assets/Maize%20production.wav",
                'pest and disease management': r"https://limerick-toucan-5791.twil.io/assets/Pest%20and%20disease%20management.wav",
                'tips on sorghum farming': r"https://limerick-toucan-5791.twil.io/assets/Tips%20on%20sorghum%20farming.wav",
                'pest control': r"https://limerick-toucan-5791.twil.io/assets/Cultural%20methods%20for%20pest%20control.wav",
                'stages of post harvest farming': r"https://limerick-toucan-5791.twil.io/assets/Stages%20of%20post%20harvest.wav",
                'soil management and fertility': r"https://limerick-toucan-5791.twil.io/assets/Stages%20of%20post%20harvest.wav",
                'tips for diverse crops':r"https://limerick-toucan-5791.twil.io/assets/Tips%20for%20diverse%20crops.wav",
                'land prep for groundnut farming':r"https://limerick-toucan-5791.twil.io/assets/Land%20prep%20for%20groundnut%20farming.wav",
                'land prep for yam farming':r"https://limerick-toucan-5791.twil.io/assets/Land%20prep%20for%20yam%20farming.wav",
                'soybean planting':r"https://limerick-toucan-5791.twil.io/assets/Soybean%20planting.wav",
                'food safety': r"https://limerick-toucan-5791.twil.io/assets/Food%20safety.wav",
    }



            
def respond_to_user(transcribed_speech):
    """Respond to the user based on the transcribed speech."""
    speech_lower = transcribed_speech.lower().strip()  # Strip leading/trailing spaces
    response = VoiceResponse()

    print(f"Transcribed speech (lowercased): {speech_lower}")

    for keyword, audio_url in audio_map.items():
        if keyword in speech_lower:
            # Play the corresponding audio file
            print(f"Keyword '{keyword}' found, playing audio.")
            response.play(audio_url)

            # After playing the response, ask if they need more information
            response.pause(length=1)  # Adding a pause for a better user experience
            response.play(r'https://limerick-toucan-5791.twil.io/assets/Extension1.wav')
            
            # Gather the response from the user
            with response.gather(num_digits=1, action="/check-follow-up", method="POST") as gather:
                pass

            return str(response)  # Return the VoiceResponse as a string!

    # If no keyword is recognized, prompt the user to try again
    print("No keyword matched, giving user another chance to try.")
    response.play(r'https://limerick-toucan-5791.twil.io/assets/Retry.wav')

    # Gather the user's response for retry
    with response.gather(num_digits=1, action="/retry-or-end", method="POST") as gather:
        pass

    return str(response)

@app.route("/retry-or-end", methods=["POST"])
def retry_or_end():
    """Handle user's decision to retry or end the call."""
    response = VoiceResponse()
    selected_option = request.form["Digits"]

    if selected_option == "1":
        # If the user wants to try again, redirect them to record again
        response.play(r'https://limerick-toucan-5791.twil.io/assets/Extension%202.wav')
        response.record(action="/process-recording", method="POST", timeout=3,max_length=15, speech_model="default")

    elif selected_option == "2":
        # If the user wants to end the call
        response.play(r'https://limerick-toucan-5791.twil.io/assets/Goodbye.wav')
        response.hangup()

    return str(response)


    
@app.route("/process-recording", methods=["POST"])
def process_recording():
    """Process the recorded speech and provide a response"""
    response = VoiceResponse()

    # Wait for 2 seconds to allow the recording to be saved
    time.sleep(2)
    recording_url = request.form.get("RecordingUrl")

    try:
        # Request to get the audio file
        remote_audio_file = requests.get(f'{recording_url}.mp3', auth=(account_sid, auth_token))
        print(f"HTTP status code: {remote_audio_file.status_code}")
        
        if remote_audio_file.status_code != 200:
            raise Exception(f"Failed to fetch the audio file: {remote_audio_file.status_code}")
        
        recording_sid = request.form.get("RecordingSid")
        audio_file_path = f'voices/{recording_sid}.wav'

        with open(audio_file_path, 'wb') as file:
            file.write(remote_audio_file.content)

        print(f"Audio file saved: {audio_file_path}")

        # Transcribe the saved audio file using Whisper AI
        transcribed_speech = transcribe_whisperAI(audio_file_path)
        print(f"Transcription: {transcribed_speech}")

        # Use respond_to_user to generate the response based on the transcription
        user_response = respond_to_user(transcribed_speech=transcribed_speech)

        if user_response:
            # Play the user response (this will include playing any audio from the keyword)
            return user_response  # Return the VoiceResponse directly to Twilio

    except Exception as e:
        print(f"Error processing recording: {e}")
        response.say("Sorry, there was an error processing your request.")
    
    return str(response)


@app.route("/check-follow-up", methods=["POST"])
def check_follow_up():
    """Handle follow-up responses to continue the conversation."""
    response = VoiceResponse()

    # Get the user's response (1 for more information, 2 for ending the call)
    selected_option = request.form.get("Digits")

    if selected_option == "1":
        # If the user needs more information, ask them for the new question
        response.play(r"https://limerick-toucan-5791.twil.io/assets/On%20hold.wav")
        response.record(action="/process-recording", method="POST",timeout=3, max_length=15, speech_model="default")

    elif selected_option == "2":
        # If the user is satisfied, end the call politely
        response.play(r"https://limerick-toucan-5791.twil.io/assets/Byeee.wav")
        response.hangup()

    return str(response)

import requests
# def transcribe_audio_twi(audio_file_path):
#     """
#     Transcribe the given audio file in Twi
#     Return: Twi Transcription
#     """
#     response = VoiceResponse()
#     # URL for the Twi transcription API by GhnanaNLP
#     url = "https://translation-api.ghananlp.org/asr/v1/transcribe?language=tw"
    
#     headers = {
#     'Ocp-Apim-Subscription-Key': '4f00858473444353b3d414e568ec8a8e',
#     'Content-Type': 'audio/wave'
#     } 

#     with open(audio_file_path, 'rb') as file:
#         payload = file.read()

#     res = requests.request("POST", url, headers=headers, data=payload)

#     twi_transcription= res.text
#     # return f'Twi Transciption: {twi_transcription}'
#     print(f"Transcription_twi: {twi_transcription}")
#     print("working")
#     if "nnɔbae ahorow" in twi_transcription or "nɔbaeɛ ahohorɔ" in twi_transcription or "nnɔbaeɛ ahohoro" in twi_transcription:
#         #assuming we got info from chat gpt
#         #translate the eng to twi
#         info_from_chatgpt = "Crop diversification involves growing a variety of crops within a farming system rather than relying on a single crop. This practice enhances resilience against pests, diseases, and market fluctuations, as it reduces the risk associated with crop failure. Diversifying crops can also improve soil health by encouraging nutrient cycling and preventing soil depletion, especially when combined with crop rotation. Additionally, it can lead to better use of available resources (like water and land) and increase overall farm productivity and income stability, as farmers can tap into multiple markets and adapt to changing environmental conditions."
#         translated_info = translate(info_from_chatgpt, "english", "twi")
#         text_to_speech(translated_info, "twi")
#         response.say("I have some information for you")
#     else:
#         print("No information found")
#         response.say("I don't have any information for you")

# def translate(text,input_lang,target_language):

#     """
#     Translate the given text from an input language to the specified language.
#     Return: Translated Text
#     """

#     target_lang_dict = {
#         "english":"en",
#         "twi":"tw",
#         "ewe": "ee",
#         "ga": "gaa",
#         "fante": "fat"}
        
#     # Define the API endpoint
#     url = "https://translation-api.ghananlp.org/translation/v1/translate"

#     payload = json.dumps({
#         "in": text,
#         "lang": f'{target_lang_dict[input_lang]}-{target_lang_dict[target_language]}',
#     })
#     # Define the request headers
#     headers = {
#         'Ocp-Apim-Subscription-Key': '4f00858473444353b3d414e568ec8a8e',
#         'Content-Type': 'application/json'
#     }

#     response = requests.request("POST", url, headers=headers, data=payload)

#     translate = response.text
#     return f'Translated Text from {input_lang} to {target_language}: {translate}'

    
# def text_to_speech(input, lang):
#     """
#     Convert the given text to speech in the specified language.
#     Return: The URL to the audio file or an error message.
#     """

#     target_lang_dict = {
#         "english":"en",
#         "twi":"tw",
#         "ewe": "ee",
#         "ga": "gaa",
#         "fante": "fat"}
#     # Define the API endpoint
#     url = "https://translation-api.ghananlp.org/tts/v1/tts"
    
#     # Load the subscription key from environment variables
#     api_key = os.getenv("Ocp_Apim_Subscription_Key")
    
#     # Prepare the payload
#     payload = json.dumps({
#         "text": input,
#         "language": f'{target_lang_dict[lang]}',
#     })
    
#     # Define the request headers
#     headers = {
#         'Ocp-Apim-Subscription-Key': '4f00858473444353b3d414e568ec8a8e',
#         'Content-Type': 'application/json'
#     }
    
#     # Send the POST request
#     response = requests.post(url, headers=headers, data=payload)
    
#     # Return the result
#     if response.status_code == 200:
#         print("works")
#         # Save audio content to a file
#         audio_file_path = "twi_audios/output_audio.wav"
#         with open(audio_file_path, 'wb') as file:
#             file.write(response.content)
#     else:
#         return f"Error: {response.status_code} - {response.text}"

# @app.route("/twi-recording", methods=["POST"])
# def twi_recording():
#     """Process the recorded Twi speech and provide a response"""
#     response = VoiceResponse()

#     # Wait for 2 seconds to allow the recording to be saved
#     time.sleep(2)
#     recording_url = request.form.get("RecordingUrl")

#     # Print recording URL for debugging
#     print(f"Recording URL: {recording_url}")

#     try:
#         # Request to get Audio file
#         remote_audio_file = requests.get(f'{recording_url}.mp3', auth=(account_sid, auth_token))
#         print(f"HTTP status code: {remote_audio_file.status_code}")
        
#         if remote_audio_file.status_code != 200:
#             raise Exception(f"Failed to fetch the audio file: {remote_audio_file.status_code}")
        
#         recording_sid = request.form.get("RecordingSid")
#         audio_file_path = f'twi_audios/{recording_sid}.wav'

#         with open(audio_file_path, 'wb') as file:
#             file.write(remote_audio_file.content)

#         print(f"Audio file saved: {audio_file_path}")

#         # Transcribe the saved twi audio file
#         transcribe_audio_twi(audio_file_path)
        



#     except Exception as e:
#         print(f"Error processing recording: {e}")
#         response.say("Sorry, there was an error processing your request.")    

#     return str(response)


def text_to_speech(input_text, lang, file_name=None):
    """
    Convert the given text to speech in the specified language.
    Save the audio to a file with a unique name.
    Return: Path to the saved audio file or an error message.
    """
    target_lang_dict = {
        "english": "en",
        "twi": "tw",
        "ewe": "ee",
        "ga": "gaa",
        "fante": "fat"
    }

    # Define the API endpoint
    url = "https://translation-api.ghananlp.org/tts/v1/tts"
    
    # Load the subscription key from environment variables
    # api_key = os.getenv("Ocp_Apim_Subscription_Key")
    
    # Prepare the payload
    payload = json.dumps({
        "text": input_text,
        "language": f'{target_lang_dict[lang]}',
    })
    
    # Define the request headers
    headers = {
        'Ocp-Apim-Subscription-Key': '4f00858473444353b3d414e568ec8a8e',
        'Content-Type': 'application/json'
    }
    
    # Send the POST request
    res = requests.post(url, headers=headers, data=payload)
    # response = VoiceResponse()
    
    # Return the result
    if res.status_code == 200:
        # Generate a unique file name if not provided
        # if file_name is None:
        #     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"output_2.wav"

        audio_file_path = os.path.join("twi_audios", file_name)
        with open(audio_file_path, 'wb') as file:
            file.write(res.content)
        print(f"Audio file saved: {audio_file_path}")
        return "https://limerick-toucan-5791.twil.io/assets/output_audio.wav"
    else:
        return f"Error: {res.status_code} - {res.text}"
    # return str(response)


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
        'Ocp-Apim-Subscription-Key': '4f00858473444353b3d414e568ec8a8e',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    translate = response.text
    return translate


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
    
twi_maps = {
    "Wim nsakraeɛ": r"https://limerick-toucan-5791.twil.io/assets/climate_change.wav",
    "aburoo": r"https://limerick-toucan-5791.twil.io/assets/maize_farming.wav",
    "ahobammɔ": r"https://limerick-toucan-5791.twil.io/assets/food%20safety.wav",
    "mmoawammoawa ne nyarewa": r"https://limerick-toucan-5791.twil.io/assets/pest%20and%20disease.wav",
    "sorghum kuayɛ": r"https://limerick-toucan-5791.twil.io/assets/Sorghum%20farming.wav",
    "asase sohwɛ": r"https://limerick-toucan-5791.twil.io/assets/soil%20management.wav",


}

@app.route("/twi-recording", methods=["POST"])
def twi_recording():
    """Process the recorded Twi speech and provide a response"""
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
        
        # Check for keywords and generate a response
        
        for keyword, audio_url in twi_maps.items():
            if keyword in transcription:
                # Play the corresponding audio file
                print(f"Keyword '{keyword}' found, playing audio.")
                response.play(audio_url)

                # After playing the response, ask if they need more information
                response.pause(length=1)  # Adding a pause for a better user experience
                response.play(r'https://limerick-toucan-5791.twil.io/assets/Extension1.wav')
                
                # Gather the response from the user
                with response.gather(num_digits=1, action="/check-follow-up", method="POST") as gather:
                    pass

                return str(response)  # Return the VoiceResponse as a string!
        else:
            response.say("I don't have any information for you.")
        
    except Exception as e:
        print(f"Error processing recordingg: {e}")
        response.say("Sorry, there was an error processing your request.")
    
    return str(response)


if __name__ == "__main__":
    app.run(debug=True)

    # print(transcript)

