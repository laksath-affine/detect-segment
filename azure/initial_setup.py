from concurrent.futures import ThreadPoolExecutor
from azure.azure_mongo import insert_one_into_collection, read_from_json,\
    create_vector_ivf_index, delete_collection, create_or_get_collection
from azure.azure_blob_storage import is_image_url, upload_files_from_urls_to_blob_subfolder,\
    delete_all_blobs_in_container, create_container_if_not_exists
from azure.azure_embeddings import vectorize_image_with_url
from azure.owclasses import OWCollections, OWContainers
from azure.azure_variables import ow_db, blob_connection_string, \
    vision_endpoint, vision_key, vision_api_version
from datetime import datetime
from bson import ObjectId

def sample_user_entry():
    time_now = datetime.now()
    user_entry = {
		'_id': ObjectId('610711b2f1f8b200209834ab'),
		'profileName': 'affine',
		'userName': 'affine',
		'email': 'affine@gmail.com',
		'password': 'affine',
		'gender': 'male',
		'isActive': True,
		'createdAt': time_now,
		'updatedAt': time_now
	}
    
    insert_one_into_collection(ow_db, OWCollections.USER.value, user_entry)
    
def sample_wardrobe_entry():
    	
	if ow_db['wardrobe'].find_one({"name": "affine"}) is None:
		time_now = datetime.now()
		wardrobe_entry = {
			'_id': ObjectId(),
			'userId': ow_db['user'].find_one({"userName": "affine"})["_id"],
			'name': 'affine',
			'userPermission': 'Public',
			'isActive': True,
			'createdAt': time_now,
			'updatedAt': time_now
		}

		insert_one_into_collection(ow_db, OWCollections.WARDROBE.value, wardrobe_entry)


def upload_wardrobe_item(json_data, blob_name, image_embeddings):
    if ow_db["wardrobeItem"].find_one({"blobName": blob_name}) is None:
        time_now = datetime.now()

        try:    description = json_data["jsonData"]
        except Exception as e:  description = {}

        wardrobe_item_entry = {
            "_id": ObjectId(json_data["_id"]),
            "wardrobeId": ow_db["wardrobe"].find_one({"name": "affine"})["_id"],
            "jsonData": description,
            "blobName": blob_name,
            "imageEmbeddingIVF1": image_embeddings,
            "isActive": True,
            "itemCategory": json_data["itemCategory"],
            "createdAt": time_now,
            "updatedAt": time_now,
        }

        insert_one_into_collection(ow_db, OWCollections.WARDROBE_ITEM.value, wardrobe_item_entry)


def process_wardrobe_item(json_data):
    image_url = json_data["image"]
    if is_image_url(image_url):
        blob_names = upload_files_from_urls_to_blob_subfolder(blob_connection_string, "wardrobe-item", [image_url], "")
        image_embeddings = vectorize_image_with_url(image_url, vision_endpoint, vision_key)
        upload_wardrobe_item(json_data, blob_names[0], image_embeddings)

        
def upload_wardrobe_items_from_json(file_path):  
    data = read_from_json(file_path)
    with ThreadPoolExecutor() as executor:
        executor.map(process_wardrobe_item, data)


def create_initial_setup():
    for collection in OWCollections:
        delete_collection(ow_db, collection.value)
    create_or_get_collection(ow_db, collection.value)


    for container in OWContainers:
        delete_all_blobs_in_container(blob_connection_string, container.value)
        create_container_if_not_exists(blob_connection_string, container.value)


    create_vector_ivf_index(ow_db, OWCollections.WARDROBE_ITEM.value, 'imageEmbeddingIVF1', 1)

    sample_user_entry()
    sample_wardrobe_entry()
    upload_wardrobe_items_from_json('json_data/items.json')
