import streamlit as st
from utilitis import Draw,Change_Image,Update,Get_Data,Get_Bytes,save_json_to_file
from PIL import Image
import time 




def app():
    _,_,storage = Get_Data()
    st.title(f'Welcome to Textra :blue[{st.session_state["handle_name"]}]')
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
                return Draw(image)
            
            # Process the image and retrieve results
            image, Results,execution_time = process_image(uploaded_file)
            # Execution Time
            st.write(f"Execution Time: {execution_time:.2f} seconds")
            
            # Tools
            st.sidebar.title('Tools')
            Change_Image(image,image_initiale)
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
                storage.child(uid).child("Invoices").child(uploaded_file.name).put(Get_Bytes(image_initiale),st.session_state['user']['idToken'])
                storage.child(uid).child("Invoices").child("Annoutated_"+uploaded_file.name).put(Get_Bytes(image),st.session_state['user']['idToken'])
                              
                file_path = "data.json"
                save_json_to_file(New_results, file_path)
                storage.child(uid).child("Jsons").child(uploaded_file.name.split(".", 1)[0]+".json").put(file_path,st.session_state['user']['idToken'])
            

