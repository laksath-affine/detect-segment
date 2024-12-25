import streamlit as st
from azure.azure_variables import ow_db, blob_connection_string
from wardrobe import view_wardrobe_items
from look_wardrobe import view_look_wardrobe_items
from azure.owclasses import OWCollections, OWContainers
from azure.data_upload import upload_similarity_search_results, topN_results
from azure.azure_blob_storage import generate_sas_token
from custom_css import page_l_title, page_s_title
import time
from custom_css import button_style


def search_look_to_wardrobe():
    page_l_title("Find Similar Items From The Segmented Looks With Your Wardrobe Items")

    view_search_look_wardrobe('search_look_wardrobe_id', 'view_search_look_wardrobe_items')
    st.write("")
    
    if 'use_case_value' not in st.session_state:    st.session_state.use_case_value = 2
    use_case = st.radio("Select Use Case", ("Use Case 1", "Use Case 2"))
    if use_case == "Use Case 1":    st.session_state.use_case_value = 2
    else:   st.session_state.use_case_value = 3
    
    search_wardrobe_items()
    

def view_search_look_wardrobe(search_look_wardrobe_id_str, view_search_look_wardrobe_items_str):    
    look_wardrobes = ow_db[OWCollections.LOOK_WARDROBE.value].find({"userId": st.session_state['user_id']})
    
    look_map = {look["name"]: look["_id"] for look in look_wardrobes}
    
    look_names = list(look_map.keys())
    selected_look_wardrobe = st.selectbox("Select a Look", look_names)
    st.session_state[search_look_wardrobe_id_str] = look_map.get(selected_look_wardrobe)
    
    if st.session_state[search_look_wardrobe_id_str]:
        if st.button("View Look Items"):
            st.session_state[view_search_look_wardrobe_items_str] = \
                not st.session_state.get(view_search_look_wardrobe_items_str, False)

    if st.session_state.get(view_search_look_wardrobe_items_str):
        view_look_wardrobe_items(search_look_wardrobe_id_str)


def view_search_wardrobe(search_wardrobe_id_str, view_search_wardrobe_items_str):
    wardrobes = ow_db[OWCollections.WARDROBE.value].find({"userId": st.session_state['user_id']})
    
    wardrobe_map = {"All": "All"}
    for wardrobe in wardrobes:
        wardrobe_map[wardrobe["name"]] = wardrobe["_id"]
    wardrobe_names = list(wardrobe_map.keys())
    selected_wardrobe = st.selectbox("Select a Wardrobe", wardrobe_names)
    st.session_state[search_wardrobe_id_str] = wardrobe_map.get(selected_wardrobe)
    
    if st.button("View Wardrobe Items"):
        if st.session_state[search_wardrobe_id_str] or st.session_state[search_wardrobe_id_str] != 'All':
            st.session_state[view_search_wardrobe_items_str] = \
                not st.session_state.get(view_search_wardrobe_items_str, False)
    
    if st.session_state.get(view_search_wardrobe_items_str):
        view_wardrobe_items(search_wardrobe_id_str)


def get_search_items():
    search_item_ids = upload_similarity_search_results(
        st.session_state["search_look_wardrobe_id"], 
        st.session_state.get("search_wardrobe_id"),
        'imageEmbeddingIVF1'
    )
    search_items = [ow_db[OWCollections.SIMILARITY_SEARCH.value].find_one(id) for id in search_item_ids]
    return search_items


def vector_search_item(item):
    segmentation_item_id = item['similarityScoreIds']['segmentationItemId']
    segmentation_item = ow_db[OWCollections.SEGMENTATION_ITEM.value].find_one(segmentation_item_id)
    
    view_look_wardrobe_items(segmentation_item_id = segmentation_item_id, num_columns=1)
    wardrobe_item_ids = item['similarityScoreIds']['wardrobeItemIds']
    if wardrobe_item_ids:
        wardrobe_item_ids = item['similarityScoreIds']['wardrobeItemIds']
        similarity_scores = item['similarityScoreIds']['similarityScores']
        
        page_s_title("Vector Search Results:")
        view_wardrobe_items(wardrobe_item_ids = wardrobe_item_ids, num_columns=5)
        st.caption(f"Similarity Scores: {similarity_scores}")

        return [wardrobe_item_ids, similarity_scores, segmentation_item]
    
    return None


def category_filter_search_item(segmentation_item, wardrobe_item_ids, similarity_scores):
    filtered_wardrobe_item_ids = []
    filtered_similarity_scores = []
    
    for i in range(len(wardrobe_item_ids)):
        wardrobe_item_id = wardrobe_item_ids[i]
        if ow_db[OWCollections.WARDROBE_ITEM.value].find_one({'_id': wardrobe_item_id, 'itemCategory': segmentation_item['itemCategory']}):
            filtered_wardrobe_item_ids.append(wardrobe_item_id)
            filtered_similarity_scores.append(similarity_scores[i])
        
    page_s_title("Category Filter Search Results:")
    view_wardrobe_items(wardrobe_item_ids = filtered_wardrobe_item_ids, num_columns=5)
    st.caption(f"Similarity Scores: {filtered_similarity_scores}")
    
    return filtered_wardrobe_item_ids, filtered_similarity_scores


def gpt_filter_search_item(segmentation_item, wardrobe_item_ids, similarity_scores):
    image_url = generate_sas_token(blob_connection_string, OWContainers.SEGMENTATONITEM.value, segmentation_item['blobName'])
    
    wardrobe_ranked, similarity_ranked = topN_results(
        wardrobe_item_ids,
        similarity_scores,
        st.session_state.use_case_value,
        image_url = image_url
    )
    
    page_s_title("GPT Filter Search Results:")
    view_wardrobe_items(wardrobe_item_ids = wardrobe_ranked, num_columns=5)
    st.caption(f"Similarity Scores: {similarity_ranked}")
    
    return wardrobe_ranked, similarity_ranked


def filtered_search_results():
    search_items = get_search_items()
    for item in search_items:
        results = vector_search_item(item)
        if results is not None:
            wardrobe_item_ids, similarity_scores, segmentation_item = results
            wardrobe_item_ids, similarity_scores = category_filter_search_item(
                segmentation_item, 
                wardrobe_item_ids,
                similarity_scores
            )
            wardrobe_ranked, similarity_ranked = gpt_filter_search_item(
                segmentation_item, 
                wardrobe_item_ids, 
                similarity_scores
            )
        st.write("")
    
    return len(search_items)


def search_wardrobe_items():
    button_style()
    
    if st.button("Search Similar Items"):
        start_time = time.time()
        total_items = filtered_search_results()
        end_time = time.time()
        minutes, seconds = divmod(end_time - start_time, 60)

        print(f"Time taken for {total_items} image search: {minutes}m:{seconds}s.")
