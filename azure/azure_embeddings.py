import requests


def vectorize_image_with_filepath(
    image_filepath: str,
    endpoint: str,
    key: str,
):
    """
    Generates a vector embedding for a local image using Azure AI Vision 4.0
    (Vectorize Image API).

    :param image_filepath: The image filepath.
    :param endpoint: The endpoint of the Azure AI Vision resource.
    :param key: The access key of the Azure AI Vision resource.
    :param version: The version of the API.
    :return: The vector embedding of the image.
    """
    with open(image_filepath, "rb") as img:
        data = img.read()

    # Vectorize Image API
    version = f'?api-version=2024-02-01&model-version=2023-04-15'
    vision_api = endpoint + "retrieval:vectorizeImage" + version

    headers = {
        "Content-type": "application/octet-stream",
        "Ocp-Apim-Subscription-Key": key,
    }

    try:
        r = requests.post(vision_api, data=data, headers=headers)
        if r.status_code == 200:
            image_vector = r.json()["vector"]
            return image_vector
        else:
            print(
                f"An error occurred while processing {image_filepath}. "
                f"Error code: {r.status_code}."
            )
    except Exception as e:
        print(f"An error occurred while processing {image_filepath}: {e}")

    return None


def vectorize_image_with_url(
    image_url: str,
    endpoint: str,
    key: str,
):
    """
    Generates a vector embedding for a remote image using Azure AI Vision 4.0
    (Vectorize Image API).

    :param image_url: The URL of the image.
    :param endpoint: The endpoint of the Azure AI Vision resource.
    :param key: The access key of the Azure AI Vision resource.
    :param version: The version of the API.
    :return: The vector embedding of the image.
    """
    # Vectorize Image API
    version = f'?api-version=2024-02-01&model-version=2023-04-15'
    vision_api = endpoint + "retrieval:vectorizeImage" + version

    headers = {
        "Content-type": "application/json",
        "Ocp-Apim-Subscription-Key": key,
    }

    try:
        r = requests.post(vision_api, json={"url": image_url}, headers=headers)
        if r.status_code == 200:
            image_vector = r.json()["vector"]
            return image_vector
        else:
            print(
                f"An error occurred while processing {image_url}. "
                f"Error code: {r.status_code}."
            )
    except Exception as e:
        print(f"An error occurred while processing {image_url}: {e}")

    return None


def vector_search(collection, image_embedding, path_field, num_results=5):
    pipeline = []

    # Add the search stage
    
    search = {
        '$search': {
            "cosmosSearch": {
                "vector": image_embedding,
                "path": path_field,
                "k": num_results
            },
            "returnStoredSource": "true"
        }
    }
    pipeline.append(search)

    # Add the projection stage
    pipeline.append({
        '$project': {
            'similarityScore': { 
                '$meta': 'searchScore' 
            },
            'document': '$$ROOT'
        }
    })

    results = collection.aggregate(pipeline)
    return results


def vectorize_text(
    text: str,
    endpoint: str,
    key: str,
):
    """
    Generates a vector embedding for a text prompt using Azure AI Vision 4.0
    (Vectorize Text API).

    :param text: The text prompt.
    :param endpoint: The endpoint of the Azure AI Vision resource.
    :param key: The access key of the Azure AI Vision resource.
    :param version: The version of the API.
    :return: The vector embedding of the image.
    """
    # Vectorize Text API
    version = f'?api-version=2024-02-01&model-version=2023-04-15'
    vision_api = endpoint + "retrieval:vectorizeText" + version

    headers = {
        "Content-type": "application/json",
        "Ocp-Apim-Subscription-Key": key
    }

    try:
        r = requests.post(vision_api, json={"text": text}, headers=headers)
        if r.status_code == 200:
            text_vector = r.json()["vector"]
            return text_vector
        else:
            print(
                f"An error occurred while processing the prompt '{text}'. "
                f"Error code: {r.status_code}."
            )
    except Exception as e:
        print(f"An error occurred while processing the prompt '{text}': {e}")

    return None