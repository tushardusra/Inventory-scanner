import streamlit as st
import easyocr
from PIL import Image, ImageOps
import pandas as pd
import os
import re

# 1. Page Configuration
st.set_page_config(page_title="Pro Inventory Scanner", layout="centered")

# 2. CSS for the Green "Horizontal" Border & Camera UI
st.markdown("""
    <style>
    /* Creates a green scanning guide over the camera */
    .viewport-guide {
        border: 4px dashed #00FF00;
        border-radius: 15px;
        position: absolute;
        top: 10%;
        left: 5%;
        right: 5%;
        bottom: 10%;
        z-index: 99;
        pointer-events: none;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .viewport-guide::after {
        content: "PLACE TAG HORIZONTALLY HERE";
        color: #00FF00;
        font-weight: bold;
        font-size: 14px;
        background: rgba(0,0,0,0.4);
        padding: 5px;
    }
    /* Style the buttons */
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #00FF00; color: black; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 3. Load OCR Model
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'])
reader = load_reader()

st.title("📦 Inventory Pro Scanner")

# 4. Mode Selection: Camera or Upload
mode = st.radio("Select Input Method:", ["📷 Live Camera", "📁 Upload Image"], horizontal=True)

img_file = None
if mode == "📷 Live Camera":
    st.info("💡 Turn phone sideways (Landscape) for best results!")
    # Show the guide
    st.markdown('<div class="viewport-guide"></div>', unsafe_allow_html=True)
    img_file = st.camera_input("Scanner")
else:
    img_file = st.file_uploader("Upload Tag Photo", type=['jpg', 'png', 'jpeg'])

# 5. Processing Logic
if img_file:
    # Open image and fix orientation (Auto-rotate if phone was tilted)
    img = Image.open(img_file)
    img = ImageOps.exif_transpose(img) 
    
    st.image(img, caption="Processing...", use_container_width=True)
    
    with st.spinner('🔍 AI Reading Handwriting...'):
        results = reader.readtext(img_file.getvalue(), detail=0)
        full_text = " ".join(results)

    # Smart Search Patterns (Regex)
    def find(pattern, text):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    st.divider()
    st.subheader("📝 Verify & Correct")
    
    # Columns for easier editing on mobile
    col1, col2 = st.columns(2)
    with col1:
        book_no = st.text_input("Book No", find(r"Book\s*No[:\.]?\s*(\d+)", full_text))
        tag_no = st.text_input("Tag No", find(r"Tag\s*No[:\.]?\s*(\d+)", full_text))
    with col2:
        qty = st.text_input("Quantity", find(r"Qty[:\.]?\s*(\d+)", full_text))
        part_no = st.text_input("Material No", find(r"Material\s*No[:\.]?\s*([A-Z0-9-]+)", full_text))
    
    location = st.text_input("Location", find(r"Loc[:\.]?\s*([\w\d-]+)", full_text))

    if st.button("💾 SAVE TAG DATA"):
        # Save logic (local Excel for now)
        new_row = {"Book": book_no, "Tag": tag_no, "Part": part_no, "Qty": qty, "Location": location}
        df = pd.DataFrame([new_row])
        
        filename = "inventory.xlsx"
        if os.path.exists(filename):
            old_df = pd.read_excel(filename)
            df = pd.concat([old_df, df], ignore_index=True)
        
        df.to_excel(filename, index=False)
        st.success(f"Success! Tag #{tag_no} saved.")
        st.balloons()

# 6. Persistent Download Link
if os.path.exists("inventory.xlsx"):
    st.sidebar.markdown("---")
    with open("inventory.xlsx", "rb") as f:
        st.sidebar.download_button("📥 Download Excel Report", f, file_name="Inventory_Scan_Results.xlsx")


