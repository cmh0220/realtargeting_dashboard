import streamlit as st

if 'id' not in st.session_state:
    st.session_state['id'] = None

if 're' not in st.session_state:
    st.session_state['re'] = None

st.subheader("리얼타겟팅 실시간 대시보드", divider="blue")
st.image("images/technology-7111760_1920.jpg")
st.write("Copyright (R)Realtargeting All right reserved.")


