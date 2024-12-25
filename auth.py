import streamlit as st
from azure.azure_variables import ow_db
from azure.owclasses import OWCollections
from azure.data_upload import create_user

def login():
    st.subheader("Login")
    user_name = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        user = ow_db[OWCollections.USER.value].find_one({"userName": user_name, "password": password})
        if user:
            st.session_state["logged_in"] = True
            st.session_state["user_name"] = user_name
            st.session_state['user_id'] = user["_id"]
            st.success(f"Logged in as {user_name}")
            st.rerun()
        else:
            st.error("Invalid username or password")

def signup():
    st.subheader("Signup")
    profile_name = st.text_input("Profile Name")
    user_name = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    password2 = st.text_input("Re-Type Password", type="password")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    
    if st.button("Signup"):
        if ow_db[OWCollections.USER.value].find_one({"userName": user_name}):
            st.warning("User already exists")
        elif ow_db[OWCollections.USER.value].find_one({"email": email}):
            st.warning("Email already exists")
        elif password != password2:
            st.warning("Passwords do not match")
        else:
            json_data = {
                "profileName": profile_name,
                "userName": user_name,
                "email": email,
                "password": password,
                "gender": gender
            }
            create_user(json_data)
            st.success("Account created successfully")
            st.write(f"Welcome {profile_name}, Please Login!")