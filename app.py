import streamlit as st
import easyocr
from PIL import Image, ImageOps
import pandas as pd
import os
import numpy as np

# 1. Setup OCR
@st.cache_resource
def load_reader():
    # Adding 'hi' (Hindi) can sometimes help with number recognition in India
    return easyocr.Reader(['en']) 

reader = load_reader()

st.title("📦 Inventory Tag Scanner")

# 2. Camera Input
img_file = st.camera_input("Take a photo of the Tag")

if img_file:
    img = Image.open(img_file)
    # Fix orientation
    img = ImageOps.exif_transpose(img)
    st.image(img, caption="Uploaded Image", use_container_width=True)
    
    with st.spinner('Reading all text...'):
        # Get raw results
        img_array = np.array(img)
        raw_results = reader.readtext(img_array, detail=0)
        
    st.subheader("🔍 Scanned Text (Raw)")
    if not raw_results:
        st.error("AI couldn't see any text. Try moving closer or improving light.")
    else:
        # This shows you EXACTLY what the AI found so we can debug
        st.write("The AI found these pieces of text:", raw_results)
        
        st.divider()
        st.subheader("📝 Manual Entry (Correction)")
        
        # We will try to guess, but leave them editable
        # If the list is too short, we provide empty strings to avoid errors
        def get_val(index):
            return raw_results[index] if index < len(raw_results) else ""

        # Create the input boxes
        col1, col2 = st.columns(2)
        with col1:
            book_no = st.text_input("Book No", get_val(0))
            tag_no = st.text_input("Tag No", get_val(1))
        with col2:
            part_no = st.text_input("Material No", get_val(2))
            qty = st.text_input("Quantity", get_val(3))
        
        loc = st.text_input("Location", get_val(4))

        if st.button("💾 SAVE TO EXCEL"):
            new_data = {"Book": book_no, "Tag": tag_no, "Part": part_no, "Qty": qty, "Location": loc}
            df = pd.DataFrame([new_data])
            
            filename = "inventory.xlsx"
            if os.path.exists(filename):
                old_df = pd.read_excel(filename)
                df = pd.concat([old_df, df], ignore_index=True)
            
            df.to_excel(filename, index=False)
            st.success("Successfully saved to Excel!")

# Download button in sidebar
if os.path.exists("inventory.xlsx"):
    with open("inventory.xlsx", "rb") as f:
        st.sidebar.download_button("📥 Download Excel", f, file_name="Inventory.xlsx")
        
