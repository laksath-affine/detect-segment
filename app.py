import streamlit as st
from auth import login, signup
from home import home_page
from wardrobe import wardrobe_page
from look_wardrobe import look_wardrobe_page
from search_look_to_wardrobe import search_look_to_wardrobe
from custom_css import add_custom_css


def main():
    add_custom_css()

    st.sidebar.title("Navigation")
    
    pages = ["Home", "Login", "Signup"]
    if st.session_state.get("logged_in"):
        pages = pages+["Wardrobe", "Looks", "Search Look to Wardrobe"]
    page = st.sidebar.selectbox("Go to", pages)

    if page == "Home":
        home_page()
    elif page == "Wardrobe":
        if "logged_in" in st.session_state and st.session_state["logged_in"]:
            wardrobe_page()
        else:
            st.error("Please log in to access the Wardrobe page.")
    elif page == "Looks":
        if "logged_in" in st.session_state and st.session_state["logged_in"]:
            look_wardrobe_page()
        else:
            st.error("Please log in to access the Looks page.")
    elif page == "Search Look to Wardrobe":
        if "logged_in" in st.session_state and st.session_state["logged_in"]:
            search_look_to_wardrobe()
        else:
            st.error("Please log in to access the Search Look to Wardrobe page.")
    elif page == "Login":
        login()
    elif page == "Signup":
        signup()

if __name__ == '__main__':
    main()