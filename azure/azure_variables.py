import os
from urllib.parse import quote_plus
from azure.azure_mongo import connect_mongo_client, create_or_get_db
import warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
import streamlit as st
load_dotenv() # Load .env file

blob_connection_string = st.secrets['BLOB_CONNECTION_STRING']


uname = quote_plus(st.secrets['MONGO_USERNAME'])
passwd = quote_plus(st.secrets['MONGO_PASSWORD'])
cluster = quote_plus(st.secrets['MONGO_HOST'])


vision_endpoint = st.secrets['VISION_ENDPOINT'] + 'computervision/'
vision_key = st.secrets['VISION_SUBSCRIPTION_KEY']
vision_api_version = st.secrets['VISION_VERSION']
vectorize_img_url = vision_endpoint + 'retrieval:vectorizeImage' + vision_api_version


client = connect_mongo_client(uname, passwd, cluster)
ow_db = create_or_get_db(client, 'OpenWardrobe')