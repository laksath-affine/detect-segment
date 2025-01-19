from azure.azure_mongo import insert_one_into_collection
from azure.azure_blob_storage import is_image_url, upload_files_to_blob_subfolder
from azure.azure_embeddings import vectorize_image_with_filepath, vector_search
from azure.owclasses import OWCollections, OWContainers
from azure.gpt_gen import get_item_rankings
from azure.azure_variables import ow_db, blob_connection_string, vision_endpoint, vision_key
from bson import ObjectId
from datetime import datetime
from azure.azure_blob_storage import generate_sas_token
import requests
import os
import base64

def create_user(json_data):
    
    item_id = ObjectId()
    time_now = datetime.now()
    
    user_entry = {
        "_id": item_id,
        "profileName": json_data["profileName"],
        "userName": json_data["userName"],
        "email": json_data["email"],
        "password": json_data["password"],
        "gender": json_data["gender"],
        "isActive": True,
        "createdAt": time_now,
        "updatedAt": time_now
    }
    
    insert_one_into_collection(ow_db, OWCollections.USER.value, user_entry)
    
    return item_id

def upload_wardrobe(json_data):
    
    item_id = ObjectId()
    time_now = datetime.now()
    
    wardrobe_entry = {
        "_id": item_id,
        "userId": json_data["userId"],
        "name": json_data["name"],
        "userPermission": json_data["userPermission"],
        "isActive": True,
        "createdAt": time_now,
        "updatedAt": time_now
    }
    
    insert_one_into_collection(ow_db, OWCollections.WARDROBE.value, wardrobe_entry)
    
    return item_id


def upload_look_wardrobe(json_data):
    
    item_id = ObjectId()
    time_now = datetime.now()
    
    look_wardrobe_entry = {
        "_id": item_id,
        "userId": json_data["userId"],
        "name": json_data["name"],
        "isActive": True,
        "createdAt": time_now,
        "updatedAt": time_now
    }
    
    insert_one_into_collection(ow_db, OWCollections.LOOK_WARDROBE.value, look_wardrobe_entry)
    
    return item_id


def upload_wardrobe_item(filepath, json_data):
      
    if not is_image_url(filepath):
        print("Not an image upload")
        return False

    blob_names = upload_files_to_blob_subfolder(blob_connection_string, OWContainers.WARDROBEITEM.value, None, filepath, '')
    image_embeddings = vectorize_image_with_filepath(filepath, vision_endpoint, vision_key)
    
    print(blob_names)
    
    time_now = datetime.now()
    item_id = ObjectId()
    
    wardrobe_item_entry = {
        "_id": item_id,
        "wardrobeId": json_data["wardrobeId"],
        "jsonData": json_data["jsonData"],
        "blobName": blob_names[0],
        "imageEmbeddingIVF1": image_embeddings,
        "itemCategory": json_data["itemCategory"],
        "isActive": True,
        "createdAt": time_now,
        "updatedAt": time_now,
    }
    
    print(wardrobe_item_entry['blobName'])
    
    insert_one_into_collection(ow_db, OWCollections.WARDROBE_ITEM.value, wardrobe_item_entry)
    
    return item_id


def get_detect_segment_response(url, files, data):
    response = requests.post(url, files= files, data=data)
    if response.status_code == 200:
        print("Response received successfully")
        return response.json()  # To print the JSON response
    else:
        print(f"Failed with status code: {response.status_code}")
        return {}

def upload_segmentation_items(url, filepath, device, user_id, look_wardrobe_name):
    wardrobe_data = {
        "userId": user_id,
        "name": look_wardrobe_name
    }
    look_wardrobe_id = upload_look_wardrobe(wardrobe_data)
            
    if not is_image_url(filepath):
        print("Not an image upload")
        return False
    
    files = {'file': open(filepath, 'rb')}
    data = {'device': device, 'resize': False}
    
    response = get_detect_segment_response(url, files, data)
    if response.get('res') is None:
        return []

    response = response['res']
    print(response['execution_time'])
    
    file_paths = [os.path.basename(path) for path in response['files']]
    base64_images = response['images']
    for i in range(len(base64_images)):
        image_data = base64.b64decode(base64_images[i])
        with open(file_paths[i], 'wb') as file:
            file.write(image_data)
    
    item_ids = []
    for i in range(len(file_paths)):
        time_now = datetime.now()
        item_ids.append(ObjectId())
        fp = file_paths[i]
        if i < len(file_paths)-2:
            image_type, image_description = response['item_classes'][i], response['item_names'][i]
        elif i == len(file_paths)-1:
            image_type, image_description = 'original', response['gpt_description']
        else:
            image_type, image_description = 'backgroundRemoved', response['gpt_description']

        blob_names = upload_files_to_blob_subfolder(blob_connection_string, OWContainers.SEGMENTATONITEM.value, None, fp, '')
        image_embeddings = vectorize_image_with_filepath(fp, vision_endpoint, vision_key)
        
        segmentation_item_entry = {
            '_id': item_ids[-1],
            'lookWardrobeId': look_wardrobe_id,
            'jsonData': {
                'imageDescription': image_description,
            },
            "blobName": blob_names[0],
            "imageEmbedding": image_embeddings,
            "isActive": True,
            "itemCategory": image_type,
            "createdAt": time_now,
            "updatedAt": time_now,
        }

        insert_one_into_collection(ow_db, OWCollections.SEGMENTATION_ITEM.value, segmentation_item_entry)
        os.remove(fp)
    return item_ids


def upload_similarity_search_results(look_wardrobe_id, wardrobe_id, indexer):
    segmentation_items = ow_db[OWCollections.SEGMENTATION_ITEM.value].find(
        {
            "lookWardrobeId": look_wardrobe_id,
            "blobName": {
                "$not": {
                    "$regex": "uploaded_image.*"
                }
            }
        }
    )
    wardrobe_id = wardrobe_id if wardrobe_id and wardrobe_id != 'All' else None

    solution = []
    for items in segmentation_items:
        item_id = ObjectId()
        time_now = datetime.now()
        agg_cursor = vector_search(ow_db[OWCollections.WARDROBE_ITEM.value], items['imageEmbedding'], indexer, 10)
        similarityScores = []
        wardrobeItemIds = []
        
        for doc in agg_cursor:
            similarityScores.append(doc['similarityScore'])
            wardrobeItemIds.append(doc['_id'])
        
        segmentation_item_entry = {
            "_id": item_id,
            "wardrobeId": wardrobe_id,
            "lookWardrobeId": items["lookWardrobeId"],
            "similarityScoreIds": {
                'segmentationItemId': items['_id'],
                'wardrobeItemIds': wardrobeItemIds,
                'similarityScores': similarityScores
            },
            "isActive": True,
            "createdAt": time_now,
            "updatedAt": time_now,
        }
        
        solution.append(item_id)
        
        insert_one_into_collection(ow_db, OWCollections.SIMILARITY_SEARCH.value, segmentation_item_entry)
    
    return solution

def upload_similarity_search_via_filepath(filepath, wardrobe_id, indexer):
    wardrobe_id = wardrobe_id if wardrobe_id and wardrobe_id != 'All' else None
    
    image_embeddings = vectorize_image_with_filepath(filepath, vision_endpoint, vision_key)
    
    agg_cursor = vector_search(ow_db[OWCollections.WARDROBE_ITEM.value], image_embeddings, indexer, 10)
    similarityScores = []
    wardrobeItemIds = []
        
    for doc in agg_cursor:
        similarityScores.append(doc['similarityScore'])
        wardrobeItemIds.append(doc['_id'])
    
    return [similarityScores, wardrobeItemIds]


def topN_results(wardrobe_item_ids, similarity_scores, limit, image_path = None, image_url = None):    
    image_urls = [generate_sas_token(
                    blob_connection_string, 
                    OWContainers.WARDROBEITEM.value, 
                    ow_db[OWCollections.WARDROBE_ITEM.value].find_one(id)['blobName']
                ) for id in wardrobe_item_ids]    
    try:
        rankings = get_item_rankings(image_urls, limit, image_path, image_url)
        wardrobe_ranked = [wardrobe_item_ids[rank] for rank in rankings]
        similarity_ranked = [similarity_scores[rank] for rank in rankings]
        return wardrobe_ranked, similarity_ranked
    except:
        return [], []
