from openai import OpenAI

client = OpenAI()

def generate_response(transcribed_speech):
    # Call the ChatGPT API with the transcribed speech as the user message
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant who provides concise responses of about 100 words."},
            {"role": "user", "content": transcribed_speech}
        ],
        max_tokens=150  # Adjust this to control the approximate length (100 words is about 150 tokens)
    )
    
    return completion.choices[0].message.content

    # Example usage:
transcribed_speech = "Talk about Halloween"
response = generate_response(transcribed_speech)
print(response)