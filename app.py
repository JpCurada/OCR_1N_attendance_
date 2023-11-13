import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
from thefuzz import process
import numpy as np
import io


buffer = io.BytesIO()

# Function to check if a string is a full name
def is_full_name(input_str):
    return len(input_str.split()) >= 2 and not any(char.isdigit() or char in set("!@#$%^&*()-+=<>?") for char in input_str)

# Read CSV file
section_data = pd.read_csv("attendance_1n.csv")

# Streamlit app header and description
st.header("BSCS 1-1N Automated Attendance")
st.caption("This online tool simplifies the process of recording attendance for BSCS 1-1N classes.")

# Streamlit columns for subject selection and date input
col1, col2 = st.columns(2)
subject = col1.selectbox('Choose a Subject: ', ("COMPROG", "MMW", "FILIPINOLOHIYA", "PATHFIT", "COMPUTING", "COMMUNICATION"))
date = col2.date_input("Class Date", value=None)

# Streamlit file uploader
uploaded_files = st.file_uploader("Upload the meetings' screenshots", type=['png', 'jpeg', 'jpg'], accept_multiple_files=True)

# Process uploaded files
if uploaded_files is not None:
    names_detected = []
    for screenshot in uploaded_files:
        image = Image.open(screenshot)
        data = pytesseract.image_to_string(image=image)
        dataList = data.split("\n")  # Split text into lines
        names_detected.extend([name for name in dataList if is_full_name(name)])

    # Create a DataFrame from the detected names
    image_names_df = pd.DataFrame(np.unique(np.array(names_detected)), columns=['Names'])

    # Update names in the DataFrame based on similarity with section_data
    image_names_df['Names'] = image_names_df['Names'].apply(
        lambda name: process.extractOne(name, section_data['1Nnovators Name'])[0]
    )
    
    present_indicator = "PRESENT"
    absent_indicator = "ABSENT"

    section_data[f"{subject}_{date}"] = section_data["1Nnovators Name"].isin(image_names_df["Names"]).map({True: present_indicator, False: absent_indicator})

    # Display metrics and the DataFrame
    if not image_names_df.empty:

        num_present_students = len(section_data[section_data[f"{subject}_{date}"] == "PRESENT"].values)
        num_absent_students = len(section_data[section_data[f"{subject}_{date}"] == "ABSENT"].values)

        st.subheader(f"There are {num_present_students} students present \
                   in {subject} class for {date}")

        # Display the merged DataFrame
        st.data_editor(section_data[section_data[f"{subject}_{date}"] == "PRESENT"], use_container_width=True)

        if num_absent_students != 0:
            st.write(f"There are {num_absent_students} students who did not attend the {subject} class. Message them to verify.")
            st.data_editor(section_data[section_data[f"{subject}_{date}"] == "ABSENT"], use_container_width=True)
  
        # Download as CSV
        @st.cache_data
        def convert_to_csv(df):
            # IMPORTANT: Cache the conversion to prevent computation on every rerun
            return df.to_csv(index=False).encode('utf-8')

        csv = convert_to_csv(section_data)

        # download button to download dataframe as csv
        download = st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f"{subject}{date}_attendance.csv",
            mime='text/csv'
        )
