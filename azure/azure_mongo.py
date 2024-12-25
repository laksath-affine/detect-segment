from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import json


def connect_mongo_client(uname, passwd, cluster):
	connection_string = f"mongodb+srv://{uname}:{passwd}@{cluster}/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000&serverSelectionTimeoutMS=45000"
	client = MongoClient(connection_string)
	if client.server_info():
		# print(client.server_info())
		# print("Valid server client")
		pass
	return client


def create_or_get_db(client, db_name):
	# Check if the database exists
	if db_name in client.list_database_names():
		# print(f"Using existing database: '{db_name}'.")
		pass
	else:
		# Create the database by inserting a dummy document
		db = client[db_name]
		collection_name = 'dummy_collection'
		collection = db[collection_name]
		collection.insert_one({"dummy_field": "dummy_value"})
		# print(f"Database '{db_name}' and collection '{collection_name}' created.")
		collection.drop()
		# print(f"Dummy collection '{collection_name}' dropped.")
	
	return client[db_name]


def create_or_get_collection(db, collection_name):
	# Check if the collection exists
	if collection_name not in db.list_collection_names():
		# Create the collection by performing an operation
		db.create_collection(collection_name)
		# print(f"Created collection '{collection_name}'.")
	else:
		# print(f"Using existing collection: '{collection_name}'.")
		pass

	return db[collection_name]


def insert_one_into_collection(db, collection_name, data):
	if db[collection_name].find_one({"_id": data["_id"]}) is not None:
		# print("Item already exists in collection")
		return False
	# print(f"Item added to collection: {collection_name}")
	db[collection_name].insert_one(data)


def insert_many_into_collection(db, collection_name, data):
	try:
		db[collection_name].insert_many(data)
		# print("Items added to collection: {collection_name}")
	except Exception as e:
		# print(f"An error occurred: {e}")
		pass
	

def custom_serializer(obj):
	if isinstance(obj, ObjectId):
		return str(obj)
	if isinstance(obj, datetime):
		return obj.isoformat()
	raise TypeError(f"Type {type(obj)} not serializable")


def get_all_collection_items(db, collection_name):
	for x in db[collection_name].find():
		print(json.dumps(x, default=custom_serializer, indent=4))


def delete_db(client, db_name):
	client.drop_database(db_name)
	# print(f"Database '{db_name}' has been deleted.")


def delete_collection(db, collection_name):
	if collection_name in db.list_collection_names():
		db[collection_name].drop()
		# print(f"Deleted collection: {collection_name}")
	else:
		# print(f"Collection {collection_name} never existed")
		pass


def delete_all_entries(db, collection_name):
	delete_result = db[collection_name].delete_many({})
	# print(f"Deleted {delete_result.deleted_count} documents from {collection_name} collection.")


def delete_user(db, username):
	user_to_delete = db['user'].find_one({"userName": username})

	if user_to_delete:
		# Delete the found user
		delete_result = db['user'].delete_one({"userName": username})
		# print(f"Deleted {delete_result.deleted_count} document with username: {username}")
	else:
		pass
		# print(f"No user found with username: {username}")


def create_vector_ivf_index(db, collection_name, field_name, numLists):
	db.command({
		"createIndexes": collection_name,
		"indexes": [
			{
				"name": "vectorSearchIndex",
				"key": {
					field_name: "cosmosSearch"
				},
				"cosmosSearchOptions": {
					"kind": "vector-ivf",
					"numLists": numLists,
					"similarity": "COS",
					"dimensions": 1024
				}
			}
		]
	})

	# print(f'created vector-ivf indices for db: {db} and collection: {collection_name}')


def delete_vector_index(db, collection_name, index_name):
    try:
        collection = db[collection_name]
        collection.drop_index(index_name)
        # print(f"Deleted index '{index_name}' from collection '{collection_name}'")
    except Exception as e:
        pass
        # print(f"An error occurred: {e}")


def read_from_json(file_path):
	try:
		with open(file_path, 'r') as file:
			data = json.load(file)
		# print("Data loaded successfully.")
	except FileNotFoundError:
		pass
		# print(f"The file {file_path} was not found.")
	except json.JSONDecodeError:
		pass
		# print(f"The file {file_path} does not contain valid JSON.")
		
	# print(data[0]['image'])
	return data
