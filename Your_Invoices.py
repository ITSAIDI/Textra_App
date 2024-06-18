import streamlit as st
from utilitis import Get_Data,Get_Files

def app():
    # st.title(f'Your Invoices: {st.session_state["handle_name"]}')  # You may need to uncomment this line
    _, _, storage = Get_Data()
    if st.session_state["Valid_user"] == False:
        st.sidebar.error("Please Login")
    else:
        Images_URLs,Number = Get_Files(st.session_state['user']['localId'], storage)
        for dic in Images_URLs:
            st.sidebar.markdown(f"**{dic['name']}**")
            st.sidebar.image(dic["url"], use_column_width=True, width=700)  # Set width as per your requirement
        st.write("<span style='color:#60b4ff;font-weight:bold;font-size:40px;'>{}</span>".format(Number), unsafe_allow_html=True)

