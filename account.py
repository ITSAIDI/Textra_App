# Modules
import pyrebase
import streamlit as st
from datetime import datetime
import requests
from  utilitis import extract_error_message,Get_Data


    
def app():    
    db,auth,_ = Get_Data()
    
    col1, col2,col3 = st.columns([0.2, 0.6 , 0.2],gap="small")  
    with col2:
        st.write("                           ")
        st.write("                           ")

    with col2:
        with st.container():
            # Authentication
            choice = st.selectbox('login/Signup', ['Login', 'Sign up'])

            # Obtain User Input for email and password
            email = st.text_input('Please enter your email address')
            password = st.text_input('Please enter your password',type = 'password')

            # Sign up Block
            if choice == 'Sign up':
                handle = st.text_input('Please input your app handle name', value='Default')
                submit = st.button('Create my account')

                if submit:
                    # Create User
                    try:
                        user = auth.create_user_with_email_and_password(email, password)
                        db.child(user['localId']).child("Handle").set(handle)
                        db.child(user['localId']).child("email").set(email) 
                        db.child(user['localId']).child("Password").set(password)
                        st.success('Your account is created successfully!')
                    except requests.exceptions.HTTPError as e:
                        st.error(extract_error_message(str(e)))

            # Login Block
            if choice == 'Login':
                login = st.checkbox('Login')
                if login:
                    try:
                        user = auth.sign_in_with_email_and_password(email,password)
                        handle = db.child(user['localId']).child("Handle").get().val()
                        # primary key of the user (table call localId )
                        st.session_state['Valid_user'] = True
                        st.session_state['user'] = user
                        st.session_state['handle_name'] = handle
                        st.success('LogIn successfully!')
                    except requests.exceptions.HTTPError as e:
                        st.error(extract_error_message(str(e)))
        
