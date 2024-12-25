import os
import streamlit as st
from azure.azure_variables import ow_db, blob_connection_string
from azure.owclasses import OWCollections, OWContainers
from azure.data_upload import upload_segmentation_items, upload_look_wardrobe
from azure.azure_blob_storage import generate_sas_token
from datetime import datetime
from custom_css import page_l_title, page_m_title

def look_wardrobe_page():
    page_l_title(f"Welcome to your Look Wardrobe, {st.session_state['user_name']}!")

    col1, col2, _ = st.columns([0.15, 0.15, 0.7])
    with col1:
        if st.button("View My Looks"):
            st.session_state["create_new_look_wardrobe"] = False
            st.session_state["view_look_wardrobes"] = not st.session_state.get("view_look_wardrobes", False)

    with col2:
        if st.button("Create New Look"):
            st.session_state["view_look_wardrobes"] = False
            st.session_state["view_look_wardrobe_items"] = False
            st.session_state["add_items_to_look_wardrobe"] = False
            st.session_state["create_new_look_wardrobe"] = not st.session_state.get("create_new_look_wardrobe", False)

    if st.session_state.get("view_look_wardrobes"): view_look_wardrobes()
    if st.session_state.get("create_new_look_wardrobe"): create_and_add_new_look_wardrobe()


def view_look_wardrobes():
    look_wardrobes = ow_db[OWCollections.LOOK_WARDROBE.value].find({"userId": st.session_state['user_id']})
    look_map = {look["name"]: look["_id"] for look in look_wardrobes}
    look_names = list(look_map.keys())
    selected_look_wardrobe = st.selectbox("Select a Look", look_names)
    st.session_state["look_wardrobe_id"] = look_map.get(selected_look_wardrobe)
    
    
    if selected_look_wardrobe:
        col1, col2, _ = st.columns([0.15, 0.2, 0.65])
            
        with col1:
            if st.button("View Look Items"):
                st.session_state["view_look_wardrobe_items"] = not st.session_state.get("view_look_wardrobe_items", False)

    if st.session_state.get("view_look_wardrobe_items"): 
        try:    view_look_wardrobe_items("look_wardrobe_id")
        except: st.warning("No Items available")


def view_look_wardrobe_items(look_wardrobe_id = None, segmentation_item_id = None, num_columns = 5):
    if look_wardrobe_id:
        items = ow_db[OWCollections.SEGMENTATION_ITEM.value].find(
            {
                "lookWardrobeId": st.session_state[look_wardrobe_id],
                "blobName": {
                    "$not": {
                        "$regex": "uploaded_image.*"
                    }
                }
            }
        )
        
        page_m_title("Uploaded Image:")
        uploaded_item = ow_db[OWCollections.SEGMENTATION_ITEM.value].find_one(
            {
                "lookWardrobeId": st.session_state[look_wardrobe_id],
                "blobName": {
                    "$regex": "uploaded_image.*",
                    "$not": {"$regex": "uploaded_image_rb.*"}
                }
            }
        )
        blob_url = generate_sas_token(blob_connection_string, OWContainers.SEGMENTATONITEM.value, uploaded_item['blobName'])
        st.image(blob_url, caption = str(uploaded_item["_id"]), width = 300)
    else:
        items = ow_db[OWCollections.SEGMENTATION_ITEM.value].find({"_id": segmentation_item_id})
    items_list = list(items)
    
    page_m_title("Segmented Items:")
    
    num_rows = -(-len(items_list) // num_columns)
    for i in range(num_rows):
        cols = st.columns(num_columns)
        for j in range(num_columns):
            index = i * num_columns + j
            if index < len(items_list):
                item = items_list[index]
                blob_url = generate_sas_token(blob_connection_string, OWContainers.SEGMENTATONITEM.value, item['blobName'])
                cols[j].image(blob_url, caption=f"{item['blobName'].split('.')[0]}\n{item['_id']}\n{item['itemCategory']}", width=150)


def create_and_add_new_look_wardrobe():
    st.text_input("Create New Look", key="new_look_wardrobe_name")
    st.text_input("Get URL", key="detect_segment_url")
    st.text_input("Get DEVICE", key="device")
    st.session_state['looks_file_upload'] = st.file_uploader("Upload an image")
    
    if st.button("Create"):
        wardrobe_name = st.session_state["new_look_wardrobe_name"]
        if wardrobe_name and st.session_state["detect_segment_url"] and st.session_state["device"] and st.session_state["looks_file_upload"]:
            file_extension = st.session_state['looks_file_upload'].name.split('.')[-1]
            current_time = str(datetime.now().timestamp()).replace('.', '')
            
            current_segmentation_folder = os.path.join(os.path.dirname(__file__), 'segmentation_image', current_time)
            os.makedirs(current_segmentation_folder, exist_ok=True)
            full_file_path = os.path.join(current_segmentation_folder, f'uploaded_image.{file_extension}')
            with open(full_file_path, "wb") as f:
                f.write(st.session_state['looks_file_upload'].getbuffer())

            upload_segmentation_items(st.session_state['detect_segment_url'], full_file_path, st.session_state['device'], st.session_state["user_id"], wardrobe_name)
            os.remove(full_file_path)
            st.success(f"Wardrobe '{wardrobe_name}' created and Items added successfully")
        else:
            st.warning("Please provide both image and a wardrobe name")