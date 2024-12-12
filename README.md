# FarmTalker: Natural Language IVR System for Ghanaian Farmers

**FarmTalker** is an Interactive Voice Response (IVR) system designed to provide low-literate and low-tech farmers in Ghana with accurate and accessible agricultural information. The system uses advanced natural language processing (NLP) tools, machine learning models, and text-to-speech technologies to enable seamless communication in both English and Twi.

---

## Features

- **Language Support**:  
  Supports English and Twi (a major Ghanaian language) with transcription and translation through Ghana NLP.
  
- **Dynamic Query Responses**:  
  Uses ChatGPT to generate relevant and dynamic responses based on user queries.

- **Text-to-Speech Conversion**:  
  Converts text responses into audio using Whisper AI TTS for playback.

- **Scalable and Modular**:  
  Built on a microservice architecture, allowing flexibility and scalability.

- **Static and Dynamic Modes**:  
  - **Static Mode**: Key-value pairs for frequently asked queries mapped to pre-recorded audio.
  - **Dynamic Mode**: Real-time transcription, translation, and response generation.

---

## System Architecture

FarmTalker is designed using a **microservice architecture**. Key components include:
- **IVR Service**: Handles user interactions via Twilio.
- **Transcription Service**: Processes and transcribes user audio.
- **NLP Service**: Manages ChatGPT queries and Ghana NLP integrations.
- **Storage Service**: Handles audio storage and retrieval using Amazon S3.
- **TTS Service**: Converts text to audio for playback.

Refer to the system architecture diagram for more details.

---

## Technologies Used

- **Backend**:
  - Python with Flask Framework
  - Microservice architecture

- **Speech and Language Processing**:
  - Ghana NLP for Twi transcription and translation
  - ChatGPT for dynamic response generation
  - Whisper AI for text-to-speech conversion

- **Call Handling**:
  - Twilio for IVR integration and call workflows

- **Storage**:
  - Amazon S3 for managing audio recordings and responses

- **Development Tools**:
  - Ngrok for exposing local development environments to the internet
  - Boto3 for Amazon S3 integrations

---

## Installation and Setup

### Prerequisites
- Python 3.8+
- Ngrok for tunneling
- AWS credentials configured for Amazon S3
- Twilio Account
- Ghana NLP API Key
- OpenAI API Key

### Installation Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/Abigail-Owusu1/farmtalker.git
   cd farmtalker

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   
3. Configure environment variables:
```bash
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
OPENAI_API_KEY=your_openai_api_key
Ocp_Apim_Subscription_Key=your_ghana_nlp_api_key
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
NGROK_URL=your_ngrok_url
```
4. Run the application:
```bash
python app.py

```

5. Expose your local server using Ngrok:
```bash
ngrok http 5000
```
## Workflow

1. **Call Handling**:  
   Twilio answers the call and prompts the user to select a language.

2. **Audio Processing**:  
   The user's query is recorded and sent for transcription (using Whisper AI or Ghana NLP).

3. **Query Resolution**:  
   - **Static Mode**: If the query matches predefined keywords, a corresponding audio file is played.  
   - **Dynamic Mode**: The query is processed through ChatGPT for a response.

4. **Audio Response**:  
   The generated text response is converted into speech and played back to the user.

