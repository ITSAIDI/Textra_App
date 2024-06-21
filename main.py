import streamlit as st
from streamlit_option_menu import option_menu
import home, account, Your_Invoices,Use,Chat
import subprocess


st.set_page_config(
        page_title="Textra",
        page_icon=":bar_chart:",
        layout="wide"        
)



# Session State Tres importante !!
if 'Valid_user' not in st.session_state:
    st.session_state['Valid_user'] = False
    
if 'handle_name' not in st.session_state:
    st.session_state['handle_name'] = ''

if 'Ollama' not in st.session_state:
    subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True)
    st.session_state['Ollama']  = True


# Set CSS style to remove padding/margin
css = """
    <style>
        .main > div {
            padding-left: 2rem;
            padding-right: 2rem;
            padding-top: 0rem;
        }
        MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        body {
            background-color: #0E0E0E;
            color: #FAFAFA;
        }
      
    </style>
"""

st.markdown(css, unsafe_allow_html=True)

video_html = """
		<style>

		#myVideo {
		  position: fixed;
		  right: 0;
		  bottom: 0;
		  min-width: 100%; 
		  min-height: 100%;
		}

		.content {
		  position: fixed;
		  bottom: 0;
		  background: rgba(0, 0, 0, 0.5);
		  color: #f1f1f1;
		  width: 100%;
		  padding: 20px;
		}

		</style>	
		<video autoplay muted loop id="myVideo">
		  <source src="https://static.streamlit.io/examples/star.mp4")>
		  Your browser does not support HTML5 video.
		</video>
        """

#st.markdown(video_html, unsafe_allow_html=True)

app = option_menu(
menu_title=None,
options=['Home','Account','Use','Chat','Your Invoices'],
icons=['house-fill','person-circle','gear-fill','chat-dots-fill','trophy-fill'],
orientation= "horizontal",
styles={
    "nav-link-selected": {"background-color": "#3A7FFF"}
} 
)


# Logic

if app == "Home":
  home.app()
if app == "Account":
   account.app()
if app == 'Use':
   Use.app()  
if app == 'Chat':
   Chat.app()        
if app == 'Your Invoices':
   Your_Invoices.app()
