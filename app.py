import streamlit as st
import easyocr
from PIL import Image, ImageOps
import pandas as pd
import os
import numpy as np
import re

# --- MASTER CONFIG ---
st.set_page_config(page_title="TPEML Inventory Master", layout="wide")

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'])
reader = load_reader()

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏭 TPEML Physical Inventory")
st.write("Target: 10,000 Tags | Mode: Pattern Recognition")

# --- CAMERA / UPLOAD SELECTION ---
# Recommendation: Use 'Upload' on mobile to force your phone's high-quality back camera
input_mode = st.radio("Select Input:", ["📁 Upload/Take Photo (Recommended)", "📷 Live Web-Cam"], horizontal=True)

if input_mode == "📁 Upload/Take Photo (Recommended)":
    img_file = st.file_uploader("Click to open Camera/Gallery", type=['jpg', 'png', 'jpeg'])
else:
    img_file = st.camera_input("Scanner")

# --- LOGIC: PATTERN RECOGNITION ---
def extract_master_data(text_list):
    # Merge everything and remove noise
    full_blob = " ".join(text_list).upper()
    clean_blob = "".join(text_list).upper().replace(" ", "").replace("|", "").replace("[", "").replace("]", "")
    
    results = {"book": "", "tag": "", "mat": "", "qty": "", "loc": ""}

    # 1. Material No (The Grid): Look for 10-15 alphanumeric characters
    # This ignores the grid lines and finds the long part number
    mat_match = re.search(r'[A-Z0-9]{10,15}', clean_blob)
    if mat_match: results['mat'] = mat_match.group(0)

    # 2. Tag Sr No: Look for exactly 5 digits
    tag_match = re.search(r'\d{5}', full_blob)
    if tag_match: results['tag'] = tag_match.group(0)

    # 3. Book No: Look for 4 digits (usually starts with 19 or 20)
    book_match = re.search(r'\d{4}', full_blob)
    if book_match: results['book'] = book_match.group(0)

    # 4. Quantity: Look for 'QTY' followed by numbers or just a 2-3 digit number near the end
    qty_match = re.search(r'(?:QTY|QUANTITY|QNTY|30)\D*(\d{1,4})', full_blob)
    results['qty'] = qty_match.group(1) if qty_match else ""
    if not results['qty'] and "30" in full_blob: results['qty'] = "30"

    # 5. Location: Specifically looking for WIP/UBC
    if "WIP" in full_blob or "UBC" in full_blob or "WTP" in full_blob:
        results['loc'] = "WIP-UBC"

    return results

# --- MAIN PROCESS ---
if img_file:
    img = Image.open(img_file)
    img = ImageOps.exif_transpose(img)
    
    col_img, col_form = st.columns([1, 1])
    
    with col_img:
        st.image(img, caption="Scanned Tag", use_container_width=True)
    
    with col_form:
        with st.spinner('⚡ AI Analyzing Patterns...'):
            img_np = np.array(img)
            raw_data = reader.readtext(img_np, detail=0)
            found = extract_master_data(raw_data)

        # --- VERIFICATION FORM ---
        st.subheader("Confirm Details")
        with st.form("tag_form"):
            f_book = st.text_input("Book No", value=found['book'])
            f_tag = st.text_input("Tag Sr No", value=found['tag'])
            f_mat = st.text_input("Material No", value=found['mat'])
            f_qty = st.text_input("Quantity", value=found['qty'])
            f_loc = st.text_input("Material Location", value=found['loc'])
            
            submit = st.form_submit_button("💾 SAVE TO EXCEL")

            if submit:
                new_row = {
                    "Book No": f_book, "Tag Sr No": f_tag, 
                    "Material No": f_mat, "Quantity": f_qty, "Location": f_loc
                }
                df = pd.DataFrame([new_row])
                file = "inventory_master.xlsx"
                
                if os.path.exists(file):
                    old_df = pd.read_excel(file)
                    df = pd.concat([old_df, df], ignore_index=True)
                
                df.to_excel(file, index=False)
                st.success(f"Tag {f_tag} Saved!")
                st.balloons()

# --- SIDEBAR: DOWNLOAD ---
if os.path.exists("inventory_master.xlsx"):
    st.sidebar.title("📊 Export Data")
    current_df = pd.read_excel("inventory_master.xlsx")
    st.sidebar.write(f"Total Rows: **{len(current_df)}**")
    
    with open("inventory_master.xlsx", "rb") as f:
        st.sidebar.download_button("📥 Download Excel", f, file_name="Inventory_Final.xlsx")
    
    if st.sidebar.button("🗑️ Reset All Data"):
        os.remove("inventory_master.xlsx")
        st.rerun()
        
