import streamlit as st
from streamlit_modal import Modal
import requests
from pymongo import MongoClient
from streamlit_extras.switch_page_button import switch_page
from pathlib import Path
import json
from streamlit.source_util import _on_pages_changed, get_pages

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["recruiter_ai"]
collection = db["job_descriptions"]



# Define modal
modal = Modal("Job Description", key="Job_Description", max_width=1000, padding=20)

# Function to get all pages
def get_all_pages():
    default_pages = get_pages("home.py")
    pages_path = Path("pages.json")

    if pages_path.exists():
        saved_default_pages = json.loads(pages_path.read_text())
    else:
        saved_default_pages = default_pages.copy()
        pages_path.write_text(json.dumps(default_pages, indent=4))

    return saved_default_pages

# Function to clear all but the first page
def clear_all_but_first_page():
    current_pages = get_pages("home.py")

    if len(current_pages.keys()) == 1:
        return

    get_all_pages()

    key, val = list(current_pages.items())[0]
    current_pages.clear()
    current_pages[key] = val

    _on_pages_changed.send()

# Function to show all pages
def show_all_pages():
    current_pages = get_pages("home.py")
    saved_pages = get_all_pages()

    for key in saved_pages:
        if key not in current_pages:
            current_pages[key] = saved_pages[key]

    _on_pages_changed.send()

# Function to hide a specific page
def hide_page(name: str):
    current_pages = get_pages("login.py")

    for key, val in current_pages.items():
        if val["page_name"] == name:
            del current_pages[key]
            _on_pages_changed.send()
            break

# Clear all pages but the first (login) page on load
clear_all_but_first_page()

# Check for user authentication
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    switch_page("login")

# If logged in, show the home page
st.title("HR Recruiter AI")

# Initialize session state variables
if 'current_job_description' not in st.session_state:
    st.session_state['current_job_description'] = ""
if 'selected_job_id' not in st.session_state:
    st.session_state['selected_job_id'] = None
if 'modal_open' not in st.session_state:
    st.session_state['modal_open'] = False
if 'modal_content' not in st.session_state:
    st.session_state['modal_content'] = ""
if 'job_submitted' not in st.session_state:
    st.session_state['job_submitted'] = False
if 'job_updated' not in st.session_state:
    st.session_state['job_updated'] = False
if 'success_flag' not in st.session_state:
    st.session_state['success_flag'] = False

# Alert boxes
if st.session_state['success_flag']:
    st.success("Job description created successfully!")
    st.session_state['success_flag'] = False

# Function to fetch job descriptions from MongoDB
def fetch_job_descriptions():
    return list(collection.find({}, {"_id": 1, "prompt": 1, "job_description": 1}))

# Function to handle New Job Description button
def new_job_description():
    st.session_state['current_job_description'] = ""
    st.session_state['selected_job_id'] = None
    st.session_state['job_submitted'] = False
    st.session_state['job_updated'] = False

# Function to handle logout
def logout():
    st.session_state.logged_in = False
    st.session_state['current_job_description'] = ""
    st.session_state['selected_job_id'] = None
    st.session_state['modal_open'] = False
    st.session_state['modal_content'] = ""
    st.session_state['job_submitted'] = False
    st.session_state['job_updated'] = False
    switch_page("login")

# Sidebar
with st.sidebar:
    job_descriptions = fetch_job_descriptions()

    st.sidebar.button("New Job Description", on_click=new_job_description)
    st.sidebar.button("Logout", on_click=logout)

    st.sidebar.markdown("---")  # Separator

    st.sidebar.markdown("### Job Id's")
    for job in job_descriptions:
        if st.sidebar.button(f"Job ID: {job['_id']}", key=f"job_{job['_id']}"):
            st.session_state['selected_job_id'] = job['_id']
            st.session_state['current_job_description'] = job.get('prompt', '')
            st.session_state['job_submitted'] = True
            st.session_state['job_updated'] = False

# Job description input
job_description = st.text_area("Describe the Job Profile", value=st.session_state['current_job_description'])

# Create columns for buttons
col1, col2 = st.columns(2)

with col1:
    submit_disabled = st.session_state['selected_job_id'] is not None
    if st.button("Submit", disabled=submit_disabled):
        if job_description:
            api_url = "http://localhost:8081/api/v1/jd"
            payload = {"prompt": job_description}
            response = requests.post(api_url, json=payload)

            if response.status_code == 201:
                jd_response = response.json()
                job_id = jd_response.get("id")
                prompt_saved = job_description
                job_description_created = jd_response.get("job_description")

                if job_id and job_description_created:
                    collection.insert_one({"_id": job_id, "prompt": prompt_saved, "job_description": job_description_created})
                    st.session_state['selected_job_id'] = job_id
                    st.session_state['current_job_description'] = prompt_saved
                    st.session_state['job_submitted'] = True
                    st.session_state['success_flag'] = True
                    st.experimental_rerun()
                else:
                    st.error("Failed to retrieve job ID or job description from response.")
            else:
                st.error("Failed to create job description. Please try again.")
        else:
            st.warning("Please enter a job description before submitting.")

with col2:
    if st.session_state['job_submitted']:
        open_modal = st.button("View Job Description")
        if open_modal:
            modal.open()

# Modal logic

if modal.is_open():
    with modal.container():
        if st.session_state['selected_job_id'] is not None:
            api_url = f"http://localhost:8081/api/v1/jd/{st.session_state['selected_job_id']}"
            response = requests.get(api_url)

            if response.status_code == 200:
                jd_response = response.json()
                if 'job_description' in jd_response:
                    job_description = st.text_area("Job Description", value=jd_response['job_description'], disabled=not st.session_state['job_updated'])
                else:
                    st.error("Job description field not found in the response.")

                col1, col2 = st.columns(2)

                with col1:
                    if not st.session_state['job_updated']:
                        edit_button = st.button("Edit")
                        if edit_button:
                            st.session_state['job_updated'] = True

                with col2:
                    if st.session_state['job_updated']:
                        update_button = st.button("Update")
                        if update_button:
                            update_url = api_url
                            payload = {"job_description": job_description}
                            update_response = requests.put(update_url, json=payload)

                            if update_response.status_code == 200:
                                st.success("Job description updated successfully.")
                                st.session_state['job_updated'] = False
                                st.experimental_rerun()
                            else:
                                st.error("Failed to update job description. Please try again.")
            else:
                st.error("Failed to fetch job description. Please try again.")
        else:
            st.warning("No job description selected.")
