from openai import AzureOpenAI
import os
import base64
import requests
import re
import streamlit as st

def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


def url_to_base64(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        base64_image = base64.b64encode(response.content).decode('utf-8')
        return base64_image
    else:
        raise Exception(f"Failed to retrieve image. Status code: {response.status_code}")


def get_text_api_result(image_description, base64_images):
    completion_client = AzureOpenAI(
        azure_endpoint = st.secrets['AZURE_OPENAI_OPEN_WARDROBE_ENDPOINT'],
        api_key = st.secrets['AZURE_OPENAI_OPEN_WARDROBE_API_KEY'],
        api_version = st.secrets['AZURE_OPENAI_AI_VERSION']
    )

    if base64_images:
        attachments = [{"type": "text", "text": image_description}]
        for base64_image in base64_images:
            attachments.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            )
        completion = completion_client.chat.completions.create(
        model = st.secrets['AZURE_OPENAI_OPEN_WARDROBE_NAME'],
        messages=[
                {
                    "role": "user",
                    "content": attachments
                }
            ]
        )
    else:
        completion = completion_client.chat.completions.create(
        model = st.secrets['AZURE_OPENAI_OPEN_WARDROBE_NAME'],
        messages=[
                {
                    "role": "user",
                    "content": image_description
                }
            ]
        )
    
    return completion.choices[0].message.content


def extract_numbers(input_string):
    numbers = re.findall(r'\d+', input_string)
    result = ''.join(numbers)
    return result

def get_item_rankings(image_urls, limit, image_path = None, image_url = None):   
    if image_path:  base64_image =  encode_image(image_path)
    else:   base64_image = url_to_base64(image_url)
    
    b64s = [base64_image]
    for url in image_urls:  b64s.append(url_to_base64(url))
    
    prompt = f'Compared to the first image, is there any other image that has a high resemblence to it? There is a very good chance that we find the exact product but in a different alignment in the other images. Pay attention to the primary and seconday colors, pattern details, materials and texture, design and style. If yes, What looks exact or most similar to the first image? Return only the names (ImageN, where N is the Nth image in the sequence of attachments) of the matching images in a comma-separated format. The number of results cannot be more than {limit}. Do not return anything if there are no similar results.'
    try:
        result = get_text_api_result(prompt, b64s)
        results = result.split(',')
        results = [int(extract_numbers(result))-2 for result in results]
    except:
        results = []
    
    return results
