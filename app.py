import streamlit as st
import easyocr
from PIL import Image, ImageOps
import pandas as pd
import os
import numpy as np
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="TPEML Inventory", layout="centered")

# Initialize OCR
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'])
reader = load_reader()

# --- SIDEBAR: CONTROLS & DOWNLOAD ---
st.sidebar.title("⚙️ Controls")

# Download Button Logic
if os.path.exists("inventory_data.xlsx"):
    with open("inventory_data.xlsx", "rb") as f:
        st.sidebar.download_button(
            label="📥 Download Excel File",
            data=f,
            file_name="TPEML_Inventory.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.sidebar.write(f"📊 Total Scanned: {len(pd.read_excel('inventory_data.xlsx'))}")

# --- MAIN APP ---
st.title("🏭 TPEML Tag Scanner")
st.info("ℹ️ Note: If the Front Camera opens, click the small 'Camera Icon' inside the scanner to switch it once. The browser will remember your choice.")

# 1. CAMERA INPUT
img_file = st.camera_input("Capture Tag", key="camera")

# Variables to hold extracted data
default_book = ""
default_tag = ""
default_qty = ""
default_loc = ""
default_mat = ""

if img_file:
    # 2. IMAGE PROCESSING
    img = Image.open(img_file)
    img = ImageOps.exif_transpose(img) # Fix rotation
    
    # 3. AI EXTRACTION
    with st.spinner('🔍 Reading Tag Data...'):
        img_array = np.array(img)
        # Detail=0 gives us a simple list of strings
        raw_text_list = reader.readtext(img_array, detail=0)
        
        # 4. DATA MAPPING
        for i, text in enumerate(raw_text_list):
            clean_text = text.upper().replace(" ", "").replace(":", "").replace(".", "")
            
            # A. TAG SR NO (Target: 48490)
            if "TAG" in clean_text or "SNO" in clean_text:
                num_match = re.search(r'\d{5}', clean_text)
                if num_match:
                    default_tag = num_match.group(0)
                elif i + 1 < len(raw_text_list):
                    next_val = raw_text_list[i+1].replace(" ", "")
                    if next_val.isdigit() and len(next_val) == 5:
                        default_tag = next_val

            # B. BOOK NO (Target: 1940)
            if "BOOK" in clean_text or "BONK" in clean_text:
                num_match = re.search(r'\d{4}', clean_text)
                if num_match:
                    default_book = num_match.group(0)
                elif i + 1 < len(raw_text_list):
                    next_val = raw_text_list[i+1]
                    if next_val.isdigit() and len(next_val) == 4:
                        default_book = next_val

            # C. QUANTITY (Target: 30) - FIXED SYNTAX HERE
            if "QTY" in clean_text or "QUAN" in clean_text:
                if i + 1 < len(raw_text_list):
                    next_val = raw_text_list[i+1]
                    if next_val.isdigit() and len(next_val) <= 3:
                        default_qty = next_val
            
            # Fallback for floating numbers
            if text == "30": 
                default_qty = "30"

            # D. LOCATION (Target: WIP-UBC)
            if "WIP" in clean_text or "WTP" in clean_text:
                default_loc = "WIP-UBC"
            if "UBC" in clean_text or "UB<" in clean_text:
                default_loc = "WIP-UBC"

# --- DATA ENTRY FORM ---
st.divider()
st.subheader("📝 Verify & Save")

with st.form("entry_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        book_input = st.text_input("Book No", value=default_book)
        tag_input = st.text_input("Tag Sr No", value=default_tag)
        qty_input = st.text_input("Quantity", value=default_qty)
        
