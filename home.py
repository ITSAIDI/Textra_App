import streamlit as st

def app():
    st.title("Textra")
    st.write("This project integrates Optical Character Recognition (OCR) technology with Language Models (LM) to enhance the extraction of text from French invoices. By leveraging the capabilities of OCR to capture text from scanned documents and the contextual understanding provided by Language Models")
    image_path = '/teamspace/studios/this_studio/Textra_App/images/Last.png'
    image = open(image_path, 'rb').read()
    st.image(image,width=1000)