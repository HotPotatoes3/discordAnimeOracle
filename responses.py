import requests
import os
import google.generativeai as genai

TOKEN2 = os.environ['TOKEN2']

TOKEN3 = os.environ['TOKEN3']
genai.configure(api_key=TOKEN3)

model = genai.GenerativeModel('gemini-pro')


def makeMALCall(url):
    # Set your API client ID in the X-MAL-CLIENT-ID header
    headers = {
        'X-MAL-CLIENT-ID': TOKEN2
    }

    # Make the API request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code} - {response.text}")



def ai_response(type, input, image):
    if type == 'askgojo':
        try:
            while True:
                response = model.generate_content(
                                'Answer the following question/statement as if you are the character Gojo Satoru from the anime "Jujutsu Kaisen" in less than 2000 characters (try to include a reference from the show in your response): ' + input,
                                safety_settings={'HARM_CATEGORY_HARASSMENT': 'block_none', 'HARM_CATEGORY_HATE_SPEECH': 'block_none',
                                                 'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'block_none',
                                                 'HARM_CATEGORY_DANGEROUS_CONTENT': 'block_none'})

                peterResponse = response.text
                if len(peterResponse) < 2000:
                    break
            return peterResponse
        except Exception as e:
            print(e)
            return "An error occured"
