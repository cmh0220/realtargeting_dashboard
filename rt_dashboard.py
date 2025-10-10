import streamlit as st

isReg = False

# 세션 세팅
if 'id' not in st.session_state:
    st.session_state['id'] = None

if 're' not in st.session_state:
    st.session_state['re'] = None

# 화면설정: wide
st.set_page_config(layout="wide")

# 좌측메뉴 세팅
pages = {
    "🏠홈": [
        st.Page("views/main.py", title = "   메인화면", default = True),
        st.Page("views/guide.py", title = "   이용 가이드"),
    ],
    "👨‍👩‍👧‍👦방문자분석": [
        st.Page("views/today.py", title = "   일일 모니터링"),
        st.Page("views/dashboard.py", title = "   대시보드"),
    ],
    "🚗차량분석": [
        st.Page("views/today_car.py", title="   일일 모니터링"),
        st.Page("views/dashboard_car.py", title="   대시보드"),
    ],
}

pg = st.navigation(pages)

# # Realtargeting 로고
st.logo("images/logo_wide.png", size="large", link="https://realtargeting.streamlit.app", icon_image="images/단순창발효관광재단 로고.png")
#
def button_clicked():

    if st.session_state['id'] == None or st.session_state['re'] == None:
        st.toast("⚠️아이디 및 등록번호를 확인하세요.")
    else:
        #세션 정보 저장
        st.session_state["id"] = input_id
        st.session_state["re"] = input_re

        with (st.sidebar):
            st.toast('✔️적용완료!')

def myclear():
    st.session_state.clear()

# 회원정보 등록
with st.sidebar:

    input_id = st.text_input("🆔아이디", key='id')
    input_re = st.number_input("🔑등록번호", key='re', min_value=1, max_value=99999999, step=None, placeholder="12345678")

    left, right = st.columns(2, gap="small", vertical_alignment="bottom")

    # 적용 버튼
    left.button("적용", on_click=button_clicked, use_container_width=True)
    right.button("취소", on_click=lambda: myclear(), use_container_width=True)

pg.run()