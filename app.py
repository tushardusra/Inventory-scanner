import streamlit as st
import easyocr
from PIL import Image, ImageOps
import pandas as pd
import os
import numpy as np
import re

# Page Config
st.set_page_config(page_title="TPEML Scanner", layout="centered")

# 1. Load Reader (English)
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'])
reader = load_reader()

st.title("🏭 TPEML Tag Scanner")

# 2. Camera Setup (Request Rear Camera)
# We use a unique key to try and force a fresh camera instance
img_file = st.camera_input("Scan Tag (Landscape Mode Recommended)", key="rear_cam")

# 3. Processing
if img_file:
    # Open & Rotate
    img = Image.open(img_file)
    img = ImageOps.exif_transpose(img) 
    st.image(img, caption="Captured Image", use_container_width=True)
    
    with st.spinner('⏳ Decoding Handwritten Grid...'):
        img_array = np.array(img)
        # We read as a paragraph to try and group the grid numbers
        raw_text_list = reader.readtext(img_array, detail=0)
        # Join into one big search block
        full_text = " ".join(raw_text_list)
        
        # Debug: Print what AI actually sees to the console
        print(f"DEBUG RAW: {full_text}")

    # 4. "Smart Fix" Logic for your Specific Tag
    def smart_parse(text):
        data = {}
        
        # A. BOOK NO: Look for 4 digits (e.g., 1940)
        # The AI often sees "Bonk Ho" or "Book No" followed by 4 digits
        book_match = re.search(r'(?:Book|Bonk|Bk).*?(\d{4})', text, re.IGNORECASE)
        data['Book'] = book_match.group(1) if book_match else ""
        
        # B. TAG SR NO: Look for 5 digits (e.g., 48490)
        # It usually appears after "Tag" or "SNo"
        tag_match = re.search(r'(?:Tag|SNo).*?(\d{5})', text, re.IGNORECASE)
        data['Tag'] = tag_match.group(1) if tag_match else ""

        # C. QUANTITY: Look for a 1-3 digit number (e.g., 30) 
        # often floating near "Quantity" or "Qty"
        qty_match = re.search(r'(?:Quantity|Qty)\D*(\d{1,4})', text, re.IGNORECASE)
        data['Qty'] = qty_match.group(1) if qty_match else ""

        # D. LOCATION: Look for "WIP" or "UBC"
        loc_match = re.search(r'(WIP.*?UBC|WIP\s*-\s*\w+)', text, re.IGNORECASE)
        # Fallback: if it reads "WTP" instead of "WIP"
        if not loc_match:
             loc_match = re.search(r'(WTP.*?UB)', text, re.IGNORECASE)
        data['Loc'] = loc_match.group(1).replace("WTP", "WIP") if loc_match else ""

        # E. MATERIAL NO: The Hardest Part (Grid)
        # We look for a long sequence of digits/chars. 
        # If the grid lines break it, we might need manual entry.
        # This regex looks for 10+ characters that are uppercase or digits
        mat_match = re.search(r'([A-Z0-9]{10,15})', text)
        data['Mat'] = mat_match.group(1) if mat_match else ""
        
        return data

    extracted = smart_parse(full_text)

    # 5. Form Display
    st.subheader("📝 Verify & Save")
    
    col1, col2 = st.columns(2)
    with col1:
        # We prioritize the extracted data, but leave it editable
        b_val = st.text_input("Book No (4 Digits)", extracted['Book'])
        t_val = st.text_input("Tag Sr No (5 Digits)", extracted['Tag'])
    with col2:
        q_val = st.text_input("Quantity", extracted['Qty'])
        
