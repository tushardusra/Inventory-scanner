import streamlit as st
import easyocr
from PIL import Image, ImageOps
import pandas as pd
import os
import numpy as np
import re

# Setup OCR
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en']) 
reader = load_reader()

st.title("📦 Inventory Tag Scanner")

# 1. Restore Input Options
mode = st.radio("Choose Input:", ["📷 Camera", "📁 Upload Image"], horizontal=True)

if mode == "📷 Camera":
    img_file = st.camera_input("Scan Tag")
else:
    img_file = st.file_uploader("Upload Tag Image", type=['jpg', 'png', 'jpeg'])

if img_file:
    img = Image.open(img_file)
    img = ImageOps.exif_transpose(img) # Keeps image right-side up
    st.image(img, caption="Current Tag", width=400)
    
    with st.spinner('🔍 Extracting Details...'):
        img_array = np.array(img)
        # detail=0 returns just the strings
        raw_text = reader.readtext(img_array, detail=0)
        # Combine everything into one string for searching
        full_blob = " ".join(raw_text).upper()

    # 2. Smart Extraction Logic
    def get_data(patterns, text_list):
        # Look for labels and get the next item in the list
        for i, word in enumerate(text_list):
            clean_word = word.upper()
            if any(p in clean_word for p in patterns):
                if i + 1 < len(text_list):
                    return text_list[i+1]
        return ""

    st.subheader("📝 Verification")
    
    # We look for your specific labels on the tag
    col1, col2 = st.columns(2)
    with col1:
        f_book = st.text_input("Book No", get_data(["BOOK", "BK"], raw_text))
        f_tag = st.text_input("Tag Sr No", get_data(["SR NO", "TAG"], raw_text))
    with col2:
        f_mat = st.text_input("Material No", get_data(["MATERIAL", "MAT NO"], raw_text))
        f_qty = st.text_input("Quantity", get_data(["QUANTITY", "QTY"], raw_text))
    
    f_loc = st.text_input("Mat. Location", get_data(["LOCATION", "LOC"], raw_text))

    # 3. Save Logic
    if st.button("💾 SAVE TO EXCEL"):
        new_row = {"Book No": f_book, "Tag Sr No": f_tag, "Material No": f_mat, "Quantity": f_qty, "Location": f_loc}
        df = pd.DataFrame([new_row])
        
        filename = "inventory.xlsx"
        if os.path.exists(filename):
            old_df = pd.read_excel(filename)
            df = pd.concat([old_df, df], ignore_index=True)
        
        df.to_excel(filename, index=False)
        st.success(f"Tag {f_tag} saved! Total rows: {len(df)}")

    # 4. Debugging (Hidden by default)
    with st.expander("Show Raw Scanned Text (If data is missing)"):
        st.write(raw_text)

# Download Sidebar
if os.path.exists("inventory.xlsx"):
    with open("inventory.xlsx", "rb") as f:
        st.sidebar.download_button("📥 Download Excel", f, file_name="Inventory_Data.xlsx")
        
