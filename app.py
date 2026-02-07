import streamlit as st
import easyocr
from PIL import Image
import pandas as pd
import os

# Initialize the OCR reader (This stays in memory)
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'])

reader = load_reader()

st.title("📦 Inventory Tag Scanner")
st.write("Take a photo of the tag to sync with Excel.")

# 1. Image Input
img_file = st.camera_input("Scan Tag") # This opens the camera on mobile

if img_file:
    img = Image.open(img_file)
    st.image(img, caption="Scanned Tag", width=300)
    
    with st.spinner('Extracting text...'):
        # Convert image to bytes for EasyOCR
        results = reader.readtext(img_file.getvalue(), detail=0)
        
    st.subheader("Verify Data")
    
    # We try to guess which text is what based on the order
    # You will likely need to adjust these indices based on your tag layout
    tag_book = st.text_input("Tag Book No", results[0] if len(results) > 0 else "")
    tag_no = st.text_input("Tag No", results[1] if len(results) > 1 else "")
    part_no = st.text_input("Part No", results[2] if len(results) > 2 else "")
    qty = st.text_input("Quantity", results[3] if len(results) > 3 else "")
    location = st.text_input("Location", results[4] if len(results) > 4 else "")

    if st.button("✅ Save to Excel"):
        new_data = {
            "Book No": [tag_book],
            "Tag No": [tag_no],
            "Part No": [part_no],
            "Qty": [qty],
            "Location": [location]
        }
        df_new = pd.DataFrame(new_data)
        
        file_name = "physical_inventory.xlsx"
        
        if os.path.exists(file_name):
            df_old = pd.read_excel(file_name)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = df_new
            
        df_final.to_excel(file_name, index=False)
        st.success(f"Saved! Total tags in Excel: {len(df_final)}")

# 2. Download Option
if os.path.exists("physical_inventory.xlsx"):
    with open("physical_inventory.xlsx", "rb") as f:
        st.download_button("📂 Download Excel File", f, file_name="inventory_count.xlsx")
      
