import os
import streamlit as st
from azure.azure_variables import ow_db, blob_connection_string
from azure.owclasses import OWCollections, OWContainers
from azure.azure_blob_storage import generate_sas_token
from azure.data_upload import upload_wardrobe_item, upload_wardrobe
from datetime import datetime
from custom_css import page_l_title

def wardrobe_page():
    page_l_title(f"Welcome to your Wardrobe, {st.session_state['user_name']}!")

    col1, col2, _ = st.columns([0.3, 0.3, 0.4])
    
    with col1:
        if st.button("View Wardrobes"):
            st.session_state["create_new_wardrobe"] = False
            st.session_state["view_wardrobes"] = not st.session_state.get("view_wardrobes", False)

    with col2:
        if st.button("Create New Wardrobe"):
            st.session_state["view_wardrobes"] = False
            st.session_state["view_wardrobe_items"] = False
            st.session_state["add_items_to_wardrobe"] = False
            st.session_state["create_new_wardrobe"] = not st.session_state.get("create_new_wardrobe", False)

    if st.session_state.get("view_wardrobes"): view_wardrobes()
    if st.session_state.get("create_new_wardrobe"): create_new_wardrobe()

def view_wardrobes():
    wardrobes = ow_db[OWCollections.WARDROBE.value].find({"userId": st.session_state['user_id']})
    wardrobe_map = {wardrobe["name"]: wardrobe["_id"] for wardrobe in wardrobes}
    wardrobe_names = list(wardrobe_map.keys())
    selected_wardrobe = st.selectbox("Select a Wardrobe", wardrobe_names)
    st.session_state["wardrobe_id"] = wardrobe_map.get(selected_wardrobe)
    
    
    if selected_wardrobe:
        col1, col2, _ = st.columns([0.3, 0.3, 0.4])
            
        with col1:
            if st.button("View Wardrobe Items"):
                st.session_state["add_items_to_wardrobe"] = False
                st.session_state["view_wardrobe_items"] = not st.session_state.get("view_wardrobe_items", False)

        with col2:
            if st.button("Add Items to Wardrobe"):
                st.session_state["view_wardrobe_items"] = False
                st.session_state["add_items_to_wardrobe"] = not st.session_state.get("add_items_to_wardrobe", False)


    if st.session_state.get("view_wardrobe_items"): view_wardrobe_items("wardrobe_id")
    if st.session_state.get("add_items_to_wardrobe"): add_items_to_wardrobe()


def view_wardrobe_items(wardrobe_id = None, wardrobe_item_ids = None, num_columns = 4):
    if wardrobe_item_ids is not None:
        items = [ow_db[OWCollections.WARDROBE_ITEM.value].find_one(id) for id in wardrobe_item_ids]
    elif wardrobe_id == 'All':
        items = ow_db[OWCollections.WARDROBE_ITEM.value].find()
    else:
        items = ow_db[OWCollections.WARDROBE_ITEM.value].find({"wardrobeId": st.session_state[wardrobe_id]})
    items_list = list(items)
    num_rows = -(-len(items_list) // num_columns)
    
    if num_rows == 0:   st.caption("No similarity results found.")
    
    for i in range(num_rows):
        cols = st.columns(num_columns)
        for j in range(num_columns):
            index = i * num_columns + j
            if index < len(items_list):
                item = items_list[index]
                blob_url = generate_sas_token(blob_connection_string, OWContainers.WARDROBEITEM.value, item['blobName'])
                cols[j].image(blob_url, caption=f"Image ID: {item['_id']}\n{item['itemCategory']}", width=150)


def add_items_to_wardrobe():
    st.session_state['wardrobe_file_upload'] = st.file_uploader("Upload an image")
    st.text_input(
        "Item Description", 
        st.session_state.get('wardrobe_item_description', ''),
        key='wardrobe_item_description'
    )
    
    st.text_input(
        "Item Category",
        st.session_state.get('wardrobe_item_category', ''),
        key='wardrobe_item_category'
    )
    
    if st.button("Upload"):
        if st.session_state['wardrobe_file_upload'] is not None and st.session_state['wardrobe_item_category']:
            file_extension = st.session_state['wardrobe_file_upload'].name.split('.')[-1]
            
            folder_path = f'{os.path.dirname(__file__)}/wardrobe_image'
            os.makedirs(folder_path, exist_ok=True)
            file_path = f"{folder_path}/uploaded_image_{str(datetime.now().timestamp()).replace('.','')}.{file_extension}"
            with open(file_path, "wb") as f:
                f.write(st.session_state['wardrobe_file_upload'].getbuffer())
            
            item_data = {
                "wardrobeId": st.session_state["wardrobe_id"],
                "jsonData": {"description": st.session_state['wardrobe_item_description']},
                "itemCategory": st.session_state['wardrobe_item_category']
            }
            
            upload_wardrobe_item(file_path, item_data)
            st.success("Item added successfully")
            os.remove(file_path)
        else:
            st.warning("Please provide both image and description")


def create_new_wardrobe():
    st.text_input("Create New Wardrobe", key="new_wardrobe_name")
    if st.button("Create"):
        wardrobe_name = st.session_state["new_wardrobe_name"]
        if wardrobe_name:
            wardrobe_data = {
                "userId": st.session_state["user_id"],
                "name": wardrobe_name,
                "userPermission": "Public"
            }
            
            upload_wardrobe(wardrobe_data)
            st.success(f"Wardrobe '{wardrobe_name}' created successfully")
        else:
            st.warning("Please enter a wardrobe name")