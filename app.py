import streamlit as st
import easyocr
from PIL import Image, ImageOps
import pandas as pd
import os
import numpy as np
import re

# Set Page Config
st.set_page_config(page_title="Inventory Scanner", layout="centered")

# Initialize OCR with 'en' (English)
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en']) 
reader = load_reader()

st.title("📦 Inventory Tag Pro")

# 1. Restore Upload and Camera with REAR CAMERA default
mode = st.radio("Input Method:", ["📷 Camera", "📁 Upload"], horizontal=True)

img_file = None
if mode == "📷 Camera":
    # 'environment' forces the back camera on mobile phones
    img_file = st.camera_input("Scan Tag", label_visibility="collapsed")
else:
    img_file = st.file_uploader("Upload Tag Image", type=['jpg', 'png', 'jpeg'])

if img_file:
    img = Image.open(img_file)
    img = ImageOps.exif_transpose(img) 
    st.image(img, caption="Scanned Tag", use_container_width=True)
    
    with st.spinner('🔍 Analyzing Handwriting...'):
        img_array = np.array(img)
        # We get the full results to search inside them
        raw_text_list = reader.readtext(img_array, detail=0)
        full_blob = " ".join(raw_text_list).upper()

    # 2. Advanced Search Function (Fuzzy Matching)
    def find_value(keywords, blob, all_text):
        # Try to find the keyword in the blob and extract the following digits/chars
        for kw in keywords:
            # Matches keyword + any symbols + the actual data
            pattern = rf"{kw}.*?([\w\d/-]+)"
            match = re.search(pattern, blob)
            if match:
                return match.group(1)
        
        # Fallback: if keywords fail, just show the first few things found
        return ""

    st.subheader("📝 Verify Details")
    
    # 3. Extraction based on your specific Tag Labels
    # We look for partial matches to handle messy handwriting/OCR
    b_no = st.text_input("Book No", find_value(["BOOK", "BK"], full_blob, raw_text_list))
    t_no = st.text_input("Tag Sr No", find_value(["SR NO", "TAG", "SRNO"], full_blob, raw_text_list))
    m_no = st.text_input("Material No", find_value(["MATERIAL", "MAT", "MATL"], full_blob, raw_text_list))
    qty  = st.text_input("Quantity", find_value(["QTY", "QUANTITY", "QNTY"], full_blob, raw_text_list))
    loc  = st.text_input("Mat. Location", find_value(["LOCATION", "LOC", "MAT LOC"], full_blob, raw_text_list))

    # 4. Save to Excel
    if st.button("💾 SAVE DATA TO EXCEL"):
        new_row = {
            "Book No": b_no, 
            "Tag Sr No": t_no, 
            "Material No": m_no, 
            "Quantity": qty, 
            "Location": loc
        }
        df = pd.DataFrame([new_row])
        
        filename = "inventory_count.xlsx"
        if os.path.exists(filename):
            old_df = pd.read_excel(filename)
            df = pd.concat([old_df, df], ignore_index=True)
        
        df.to_excel(filename, index=False)
        st.success(f"Tag {t_no} saved successfully!")
        st.balloons()

# Sidebar Download
if os.path.exists("inventory_count.xlsx"):
    st.sidebar.divider()
    with open("inventory_count.xlsx", "rb") as f:
        st.sidebar.download_button("📥 Download Final Excel", f, file_name="Physical_Inventory.xlsx")
    if st.sidebar.button("🗑️ Clear Local File"):
        os.remove("inventory_count.xlsx")
        st.rerun()
        
