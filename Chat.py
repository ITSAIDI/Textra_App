import streamlit as st
from utilitis import Update,Get_Data,Get_Bytes,save_json_to_file
from utilitis1 import Run_llama3_Custom,interact_with_model,Run_ocr
from PIL import Image
import time 



def app():
    _,_,storage = Get_Data()
    st.title(f'Welcome to Textra ChatBot :blue[{st.session_state["handle_name"]}]')
    if st.session_state['Valid_user'] :
            
        st.markdown("### Drag and Drop votre facture ici:")
        st.write("(PNG, JPG, JPEG)")
        uploaded_file = st.file_uploader("Ou selectioner une image:", type=["png", "jpg", "jpeg"], accept_multiple_files=False)

        if uploaded_file is not None:
            image_initiale = Image.open(uploaded_file)
            image_initiale = image_initiale.convert("RGB")
            @st.cache_data
            def process_image(uploaded_file):
                image = Image.open(uploaded_file)
                image = image.convert("RGB")
                return Run_llama3_Custom(image)
            
            # Process the image and retrieve results
            Results,execution_time,Raw_Text = process_image(uploaded_file)
            # Execution Time
            st.write(f"Execution Time: {execution_time:.2f} seconds")
            st.image(image_initiale, caption='Output', use_column_width=True)
            st.subheader("Extracted Invoice Information")
            st.write(Results)

            # Chat interface
            st.subheader("Interact with Llama3")
            user_input = st.text_input("Ask for more details or clarification:")

            if user_input:
                response = interact_with_model(user_input+" "+Raw_Text)
                st.write(response)
            
            # Tools
            st.sidebar.title('Tools')
            sauvgarder_button = st.sidebar.empty()
            success_message = st.sidebar.empty()
            
            # Coin
            st.sidebar.title('Coin')
            Coin = st.sidebar.selectbox(
            'Choisissez une classe monétaire :',
            ('Dh', '$', '€')
            ) 
            # Results
            st.sidebar.title('Results')
            # Get Track of User Modeifications :
            New_results = Update(Results,Coin)
  
                    
            if sauvgarder_button.button("Sauvegarder"):
                success_message.success("Les résultats ont été sauvegardés avec succès !")
                time.sleep(1)
                success_message.empty()
                st.write(New_results)
                # Save the Image in the Storage
                uid = st.session_state['user']['localId']
                storage.child(uid).child("Invoices").child( uploaded_file.name).put(Get_Bytes(image_initiale),st.session_state['user']['idToken'])
                storage.child(uid).child("Invoices").child( "Annoutated_"+uploaded_file.name).put(Get_Bytes(image_initiale),st.session_state['user']['idToken'])
                              
                file_path = "data.json"
                save_json_to_file(New_results, file_path)
                storage.child(uid).child("Jsons").child( uploaded_file.name.split(".", 1)[0]+".json").put(file_path,st.session_state['user']['idToken'])
            

