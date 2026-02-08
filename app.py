import streamlit as st
import easyocr
from PIL import Image, ImageOps
import pandas as pd
import os
import re
import numpy as np

# 1. CSS for a Visual Scanning Box (Overlay)
st.markdown("""
    <style>
    .scanner-box {
        border: 5px solid #00FF00;
        position: relative;
        width: 100%;
        height: 250px;
        margin-bottom: -250px;
        z-index: 10;
        pointer-events: none;
    }
    </style>
    <div class="scanner-box"></div>
""", unsafe_allow_html=True)

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'])
reader = load_reader()

st.title("📦 Inventory Tag Scanner")
st.write("Hold tag vertically; AI will rotate it automatically.")

img_file = st.camera_input("Capture Tag")

if img_file:
    # Open and prepare image
    img = Image.open(img_file)
    
    # ACTION: Rotate the portrait image to horizontal for the AI
    img = img.rotate(-90, expand=True) 
    st.image(img, caption="AI Viewing Angle (Rotated)", use_container_width=True)
    
    with st.spinner('🔍 Deep Scanning...'):
        # Convert to array for EasyOCR
        img_array = np.array(img)
        results = reader.readtext(img_array, detail=0)
        full_text = " ".join(results).upper() # Convert to uppercase for easier matching

    # 2. Advanced Extraction (Looking for your specific Tag labels)
    def extract(keywords, text):
        for word in keywords:
            # Look for the keyword and the first number/code following it
            pattern = rf"{word}.*?([\w\d/-]+)"
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""

    st.subheader("📝 Verification")
    
    # Searching for your specific tag fields
    tag_book = st.text_input("Book No", extract(["BOOK NO", "BOOK"], full_text))
    tag_sr = st.text_input("Tag Sr No", extract(["SR NO", "TAG SR"], full_text))
    part_no = st.text_input("Material No", extract(["MATERIAL NO", "MAT NO"], full_text))
    qty = st.text_input("Quantity", extract(["QUANTITY", "QTY"], full_text))
    loc = st.text_input("Location", extract(["LOCATION", "LOC"], full_text))

    if st.button("💾 SAVE TO EXCEL"):
        new_data = {"Book": tag_book, "Tag": tag_sr, "Part": part_no, "Qty": qty, "Location": loc}
        df = pd.DataFrame([new_data])
        
        if os.path.exists("inventory.xlsx"):
            old_df = pd.read_excel("inventory.xlsx")
            df = pd.concat([old_df, df], ignore_index=True)
        
        df.to_excel("inventory.xlsx", index=False)
        st.success("Saved!")

if os.path.exists("inventory.xlsx"):
    with open("inventory.xlsx", "rb") as f:
        st.sidebar.download_button("📥 Download Report", f, file_name="Inventory.xlsx")
        
