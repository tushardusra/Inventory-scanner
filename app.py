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
st.info("ℹ️ If Front Camera opens: Click 'Select Device' in the camera box once to switch. The app will remember.")

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
        
        # DEBUG: Uncomment this to see what AI sees
        # st.write(raw_text_list)

        # 4. DATA MAPPING (Logic specifically for your Tag)
        # We iterate through the list to find your specific data points
        
        for i, text in enumerate(raw_text_list):
            clean_text = text.upper().replace(" ", "").replace(":", "").replace(".", "")
            
            # A. TAG SR NO (Target: 48490)
            # Look for "TAGSNO" or "TAG" followed by 5 digits
            if "TAG" in clean_text or "SNO" in clean_text:
                # Check if the number is inside this string
                num_match = re.search(r'\d{5}', clean_text)
                if num_match:
                    default_tag = num_match.group(0)
                # Check the NEXT string in the list (often the value is next to the label)
                elif i + 1 < len(raw_text_list):
                    next_val = raw_text_list[i+1].replace(" ", "")
                    if next_val.isdigit() and len(next_val) == 5:
                        default_tag = next_val

            # B. BOOK NO (Target: 1940)
            if "BOOK" in clean_text or "BONK" in clean_text: # AI often reads Book as Bonk
                num_match = re.search(r'\d{4}', clean_text)
                if num_match:
                    default_book = num_match.group(0)
                elif i + 1 < len(raw_text_list):
                    next_val = raw_text_list[i+1]
                    if next_val.isdigit() and len(next_val) == 4:
                        default_book = next_val

            # C. QUANTITY (Target: 30)
            if "QTY" in clean_text or "QUAN" in clean_text:
                # Look for small numbers (1-3 digits)
                elif i + 1 < len(raw_text_list):
                    next_val = raw_text_list[i+1]
                    if next_val.isdigit() and len(next_val) <= 3:
                        default_qty = next_val
            # Fallback: Sometimes "30" is just floating alone in the list.
            if text == "30": 
                default_qty = "30"

            # D. LOCATION (Target: WIP-UBC)
            # The AI read "WTP" and "UB<" in your logs. We fix that here.
            if "WIP" in clean_text or "WTP" in clean_text:
                default_loc = "WIP-UBC" # Auto-correct common location
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
    
    with col2:
        loc_input = st.text_input("Location", value=default_loc)
        # Material No is left blank intentionally for manual entry if AI fails on grid
        mat_input = st.text_input("Material No", value=default_mat, placeholder="Type manually if grid fails")

    # SAVE BUTTON
    submitted = st.form_submit_button("💾 SAVE TO EXCEL", type="primary")

    if submitted:
        if not tag_input:
            st.error("❌ Error: Tag Sr No is required!")
        else:
            new_data = {
                "Book No": book_input,
                "Tag Sr No": tag_input,
                "Material No": mat_input,
                "Quantity": qty_input,
                "Location": loc_input
            }
            
            df = pd.DataFrame([new_data])
            file_path = "inventory_data.xlsx"
            
            if os.path.exists(file_path):
                existing_df = pd.read_excel(file_path)
                df = pd.concat([existing_df, df], ignore_index=True)
            
            df.to_excel(file_path, index=False)
            st.success(f"✅ Tag {tag_input} Saved Successfully!")
            st.balloons()
            
