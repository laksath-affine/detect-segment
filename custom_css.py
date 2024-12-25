import streamlit as st

def add_custom_css():
    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 70%;
            margin: auto;
            margin-top:0px;
            padding-top: 50px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def page_l_title(header):
    st.markdown(f'''<h2 style="font-size:28px; font-weight: bold;">{header}</h2>''', unsafe_allow_html=True)


def page_m_title(header):
    st.markdown(f'''<h3 style="font-size:24px; font-weight: bold;">{header}</h3>''', unsafe_allow_html=True)
    

def page_s_title(header):
    st.markdown(f'''<h4 style="font-size:18px; font-weight: bold;">{header}</h4>''', unsafe_allow_html=True)


def button_style():
    button_css = """
        <style>
        .stButton button {
            height: 50px;
            width: 100%;
        }
        </style>
    """
    st.markdown(button_css, unsafe_allow_html=True)
