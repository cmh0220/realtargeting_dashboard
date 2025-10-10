import streamlit as st

if 'id' not in st.session_state:
    st.session_state['id'] = None

if 're' not in st.session_state:
    st.session_state['re'] = None

url = "https://pf.kakao.com/_vfxaZn"
url2 = "https://realtargeting.imweb.me"

st.subheader("이용 가이드", divider="blue")
st.write("🔎**이용방법**")
st.write("Step1. 사전 안내드린 :blue[아이디]와 :blue[등록번호]를 좌측에 입력 후 :red[적용]버튼 클릭합니다.")
st.write("Step2. 좌측의 각 분석메뉴를 클릭하여 조회합니다.")
st.write(" ")
st.write(" ")
st.write("👍**샘플조회**")
st.write("아이디 : real  등록번호 : 12345678")
st.write(" ")
st.write(" ")
st.write("❓**문의사항**")
st.write("이용에 궁금한 사항은 아래 카카오채널로 언제든지 연락주세요.😊")
st.write(" ")
left, right, edge = st.columns([0.1,0.1,0.8])
left.image("images/free-icon-kakao-talk-3991999.png", width=100)
right.image("images/qr_카카오채널.png", width=100)
edge.write(" ")
st.write("💬카카오 채널 : [바로가기](%s)" % url)
st.write("📞유선 연락처 : 010-4424-3291")
st.write("📨메일 : realtargeting@gmail.com")
st.write("🏠홈페이지 : [바로가기](%s)" % url2)
st.write(" ")
st.write("Copyright (R)Realtargeting All right reserved.")
