import streamlit as st
import requests
import json
from pathlib import Path
from streamlit_extras.switch_page_button import switch_page
from streamlit.source_util import _on_pages_changed, get_pages

st.set_page_config(layout="wide")

# Function to get all pages
def get_all_pages():
    default_pages = get_pages("signup.py")

    pages_path = Path("pages.json")

    if pages_path.exists():
        saved_default_pages = json.loads(pages_path.read_text())
    else:
        saved_default_pages = default_pages.copy()
        pages_path.write_text(json.dumps(default_pages, indent=4))

    return saved_default_pages

# Function to clear all pages but the first one
def clear_all_but_first_page():
    current_pages = get_pages("signup.py")

    if len(current_pages.keys()) == 1:
        return

    get_all_pages()

    # Remove all but the first page
    key, val = list(current_pages.items())[0]
    current_pages.clear()
    current_pages[key] = val

    _on_pages_changed.send()

# Function to show all pages
def show_all_pages():
    current_pages = get_pages("signup.py")

    saved_pages = get_all_pages()

    # Replace all the missing pages
    for key in saved_pages:
        if key not in current_pages:
            current_pages[key] = saved_pages[key]

    _on_pages_changed.send()

# Function to hide a specific page
def hide_page(name: str):
    current_pages = get_pages("signup.py")

    for key, val in current_pages.items():
        if val["page_name"] == name:
            del current_pages[key]
            _on_pages_changed.send()
            break

# Clear all pages but the first one
clear_all_but_first_page()

# Signup function
def signup(username, email, mobile_number, location, password):
    url = "http://localhost:8083/api/v1/user/"
    payload = {
        "name": username,
        "email": email,
        "mobile_number": mobile_number,
        "location": location,
        "password": password
    }
    response = requests.post(url, json=payload)
    return response

# Streamlit signup page
st.title("Sign Up")

username = st.text_input("Username")
email = st.text_input("Email")
mobile_number = st.text_input("Mobile Number")
location = st.text_input("Location")
password = st.text_input("Password", type="password")

if st.button("Sign Up"):
    response = signup(username, email, mobile_number, location, password)
    if response.status_code == 201:
        st.success("Sign up successful")
        # Redirect to login page with a success message
        st.experimental_set_query_params(signup_success="true")
        
        switch_page("login")
    else:
        st.error("Sign up failed. Please try again.")

# Add a button to navigate to the login page
if st.button("Login"):
    switch_page("login")
