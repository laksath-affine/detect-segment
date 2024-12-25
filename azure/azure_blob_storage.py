import os
from datetime import datetime, timedelta
import requests
import io
import re
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContainerClient
from azure.core.exceptions import ResourceExistsError

image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff')

def sanitize_blob_name(blob_name):
    """
    Replaces any characters that are not valid in a blob name with underscores.
    """
    return re.sub(r'[^a-zA-Z0-9-./_]', '_', blob_name)

# create and retreive the container NOT THE BLOB (you do get_blob_client lol) (create_blob_client)
def create_container_if_not_exists(connection_string: str, container_name: str):
    """
    Creates and returns a container in Azure Blob Storage if it does not already exist.

    :param connection_string: The connection string to the Azure Storage Account.
    :param container_name: The name of the container to create.
    :return: The ContainerClient object.
    """
    # Create a BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # Get a ContainerClient
    container_client = blob_service_client.get_container_client(container_name)

    try:
        # Create the container if it does not exist
        container_client.create_container()
        # print(f"Container '{container_name}' created.")
    except ResourceExistsError:
        # Container already exists
        # print(f"Container '{container_name}' already exists.")
        pass
    
    # Return the ContainerClient object
    return container_client


def upload_files_to_blob_subfolder(connection_string: str, container_name: str, folder_path: str, file_path: str, custom_folder: str):
    """
    Uploads all files from a local folder to a specified subfolder in an Azure Blob Storage container.

    :param connection_string: The connection string to the Azure Storage Account.
    :param container_name: The name of the Azure Blob Storage container.
    :param folder_path: The local folder path containing the files to upload.
    :param custom_folder: The subfolder name in the blob container.
    """
    # Create a BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    # Get a ContainerClient
    container_client = blob_service_client.get_container_client(container_name)
    
    # List all files in the folder
    if folder_path is not None:
        file_names = os.listdir(folder_path)
    else:
        file_names = [file_path]

    uploaded_filenames = []
    
    for file_name in file_names:
        timestamp = str(datetime.now().timestamp()).replace('.','')
        file_base_name, file_extension = os.path.splitext(file_name)
        file_name_with_timestamp = file_base_name.split('/')[-1]+timestamp+file_extension
        
        file_full_path = os.path.join(folder_path, file_name) if folder_path else file_name
        
        blob_name = os.path.join(custom_folder, file_name_with_timestamp)
        blob_name = sanitize_blob_name(blob_name)

        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        with open(file_full_path, mode="rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        # print(f"Uploaded {file_name_with_timestamp} to '{custom_folder}' in container {container_name}.")
        
        uploaded_filenames.append(blob_name)
        
    return uploaded_filenames


def upload_files_from_urls_to_blob_subfolder(connection_string: str, container_name: str, file_urls: list, custom_folder: str):
    """
    Uploads all files from the provided URLs to a specified subfolder in an Azure Blob Storage container.

    :param connection_string: The connection string to the Azure Storage Account.
    :param container_name: The name of the Azure Blob Storage container.
    :param file_urls: List of URLs of the files to upload.
    :param custom_folder: The subfolder name in the blob container.
    """
    # Create a BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    # Get a ContainerClient
    container_client = blob_service_client.get_container_client(container_name)
    
    filenames = []
    
    for file_url in file_urls:
        timestamp = str(datetime.now().timestamp()).replace('.','')
        if file_url.lower().endswith(image_extensions):
            file_name = os.path.basename(file_url).split('.')[0]+timestamp+'.png'
        else:
            file_name = os.path.basename(file_url)+timestamp+'.png'
        blob_name = os.path.join(custom_folder, file_name)
        blob_name = sanitize_blob_name(blob_name)
        
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        # Download the file from the URL
        response = requests.get(file_url)
        response.raise_for_status()  # Ensure the request was successful
        
        # Upload the downloaded file content to blob
        blob_client.upload_blob(response.content, overwrite=True)
        
        # print(f"Uploaded {file_name} to {custom_folder} in container {container_name}.")
        
        filenames.append(blob_name)
    
    return filenames


def delete_blob(connection_string: str, container_name: str, blob_name: str):
    """
    Deletes a specified blob from an Azure Blob Storage container.

    :param connection_string: The connection string to the Azure Storage Account.
    :param container_name: The name of the Azure Blob Storage container.
    :param blob_name: The name of the blob to delete.
    """
    # Create a BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    # Get a BlobClient for the specified blob
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    
    # Delete the blob
    blob_client.delete_blob()
    # print(f"Deleted blob '{blob_name}' from container '{container_name}'.")


def delete_all_blobs_in_container(connection_string: str, container_name: str):
    """
    Lists and deletes all blobs in a specified Azure Blob Storage container.

    :param connection_string: The connection string to the Azure Storage Account.
    :param container_name: The name of the Azure Blob Storage container.
    """
    # Create a BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    # Get a ContainerClient for the specified container
    container_client = blob_service_client.get_container_client(container_name)
    
    # List and delete all blobs in the container
    blob_list = container_client.list_blobs()
    
    for blob in blob_list:
        # print(f"Deleting blob: {blob.name}")
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob.name)
        blob_client.delete_blob()
        # print(f"Deleted blob '{blob.name}' from container '{container_name}'.")
       
 
def delete_all_blobs_from_folder(connection_string: str, container_name: str, folder_name: str):
    """
    Deletes all blobs from a specified folder in an Azure Blob Storage container.

    :param connection_string: The connection string to the Azure Storage Account.
    :param container_name: The name of the Azure Blob Storage container.
    :param folder_name: The name of the folder to delete blobs from.
    """
    # Create a BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    # Get a ContainerClient
    container_client = blob_service_client.get_container_client(container_name)
    
    # List all blobs in the specified folder
    blobs = container_client.list_blobs(name_starts_with=folder_name)
    
    for blob in blobs:
        blob_client = container_client.get_blob_client(blob=blob.name)
        blob_client.delete_blob()
        # print(f"Deleted blob '{blob.name}' from container '{container_name}'.")


def get_blob_url(connection_string: str, container_name: str, blob_name: str):
    """
    Gets the URL of a specified blob in an Azure Blob Storage container.

    :param connection_string: The connection string to the Azure Storage Account.
    :param container_name: The name of the Azure Blob Storage container.
    :param blob_name: The name of the blob to get the URL for.
    :return: The URL of the blob.
    """

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    
    # Get the blob URL
    blob_url = blob_client.url
    # print(f"Blob URL: {blob_url}")
    return blob_url


def generate_sas_token(connection_string: str, container_name: str, blob_name: str):
    """
    Generates a SAS token for a specified blob in an Azure Blob Storage container.

    :param connection_string: The connection string to the Azure Storage Account.
    :param container_name: The name of the Azure Blob Storage container.
    :param blob_name: The name of the blob to generate the SAS token for.
    :return: The SAS URL of the blob.
    """
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now() + timedelta(hours=1)  # Token valid for 1 hour
    )
    
    sas_url = f"{blob_client.url}?{sas_token}"
    return sas_url


def list_blob_urls_from_folder(connection_string: str, container_name: str, folder_name: str):
    """
    Lists all blob URLs from a specified folder in an Azure Blob Storage container.

    :param connection_string: The connection string to the Azure Storage Account.
    :param container_name: The name of the Azure Blob Storage container.
    :param folder_name: The name of the folder to list blobs from.
    :return: A list of blob URLs.
    """

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    
    # List all blobs in the specified folder
    blob_urls = []
    blobs = container_client.list_blobs(name_starts_with=folder_name)
    
    for blob in blobs:
        blob_url = get_blob_url(connection_string, container_name, blob.name)
        blob_urls.append(blob_url)
    
    return blob_urls


def list_blob_sas_urls_from_folder(connection_string: str, container_name: str, folder_name: str):
    """
    Lists all blob SAS URLs from a specified folder in an Azure Blob Storage container.

    :param connection_string: The connection string to the Azure Storage Account.
    :param container_name: The name of the Azure Blob Storage container.
    :param folder_name: The name of the folder to list blobs from.
    :return: A list of blob SAS URLs.
    """
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    
    sas_urls = []
    blobs = container_client.list_blobs(name_starts_with=folder_name)
    
    for blob in blobs:
        sas_url = generate_sas_token(connection_string, container_name, blob.name)
        sas_urls.append(sas_url)
    
    return sas_urls


def list_child_folders(connection_string: str, container_name: str, parent_folder: str = ''):
    """
    Lists all unique child folder names (prefixes) in a specified container or folder in Azure Blob Storage.

    :param connection_string: The connection string to the Azure Storage Account.
    :param container_name: The name of the Azure Blob Storage container.
    :param parent_folder: The parent folder to list child folders from. Default is the root of the container.
    :return: A list of unique child folder names.
    """
    # Create a BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    
    # Get a ContainerClient
    container_client = blob_service_client.get_container_client(container_name)
    
    # List all blobs with the specified parent folder prefix
    blob_list = container_client.list_blobs(name_starts_with=parent_folder)
    
    # Extract unique folder names
    folder_names = set()
    for blob in blob_list:
        # Split the blob name to get the folder name
        parts = blob.name[len(parent_folder):].split('/')
        if len(parts) > 1:
            folder_names.add(parts[0])
    
    return list(folder_names)


def is_image_url(url):
    
    # Check the file extension first
    if url.lower().endswith(image_extensions):
        return True
    
    # Check the MIME type
    try:
        response = requests.head(url, allow_redirects=True)
        content_type = response.headers.get('Content-Type')
        if content_type and content_type.startswith('image/'):
            return True
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
    
    return False


def download_blob(image_filename, connection_string, container_name):
    """
    Downloads an image from Azure Blob Storage and stores it in a binary stream.

    :param image_filename: The filename of the image.
    :param container_client: A `ContainerClient` object.
    :return: The image file as a binary stream.
    """
    
    container_client = ContainerClient.from_connection_string(connection_string, container_name)
    blob_client = container_client.get_blob_client(image_filename)
    blob_image = blob_client.download_blob().readall()

    image_stream = io.BytesIO(blob_image)
    with open(image_filename, "wb") as f:
        f.write(image_stream.getvalue())