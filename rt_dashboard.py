import streamlit as st

# 화면설정: wide
st.set_page_config(layout="wide")

# Streamlit DB 커넥션 선언 (.streamlit/secrets.toml 설정 참조)
conn = st.connection("mysql", type="sql")


def check_user_exists(user_id: str, work_no: int) -> bool:
    """st.connection을 활용하여 사용자 데이터 존재 여부 검증"""
    try:
        sql = """
            SELECT COUNT(1) AS cnt 
            FROM rt_collect_all 
            WHERE user_id = :user_id AND work_no = :work_no AND del_yn = 0
        """
        # 파라미터 바인딩을 통해 데이터 조회
        df = conn.query(sql, params={"user_id": user_id, "work_no": work_no}, ttl=0)

        if not df.empty:
            return df.iloc[0]["cnt"] > 0
        return False
    except Exception as e:
        st.error(f"DB 조회 중 오류가 발생했습니다: {e}")
        return False


# 세션 상태 초기화
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

if "user_re" not in st.session_state:
    st.session_state["user_re"] = None

# 좌측메뉴 세팅
pages = {
    "🏠홈": [
        st.Page("views/main.py", title="   메인화면", default=True),
        st.Page("views/guide.py", title="   이용 가이드"),
    ],
    "👨‍👩‍👧‍👦방문자분석": [
        st.Page("views/today.py", title="   일일 모니터링"),
        st.Page("views/dashboard.py", title="   대시보드"),
    ],
    "🚗차량분석": [
        st.Page("views/today_car.py", title="   일일 모니터링"),
        st.Page("views/dashboard_car.py", title="   대시보드"),
    ],
}

pg = st.navigation(pages)

# 로고 세팅
st.logo(
    "images/logo_wide.png",
    size="large",
    link="https://realtargeting.streamlit.app",
)


# 콜백 및 폼 제출 처리 함수
def handle_submit():
    input_id = st.session_state.get("input_id_val")
    input_re = st.session_state.get("input_re_val")

    if not input_id or not input_re:
        st.toast("⚠️ 아이디 및 등록번호를 입력하세요.")
        return

    # DB 조회 검증
    if check_user_exists(input_id, input_re):
        st.session_state["user_id"] = input_id
        st.session_state["user_re"] = input_re
        st.session_state["id"] = input_id
        st.session_state["re"] = input_re
        st.toast("✔️ 적용완료!")
    else:
        st.toast("⚠️ 아이디 혹은 등록번호를 다시 확인하시기 바랍니다.")


def myclear():
    # 세션값 초기화
    st.session_state.clear()
    st.toast("🧹 초기화되었습니다.")


# 회원정보 등록 (사이드바)
with st.sidebar:
    st.subheader("🔑 사용자 인증")

    # 인증 적용 여부 확인
    is_authenticated = bool(
        st.session_state.get("user_id") and st.session_state.get("user_re")
    )

    # 적용 상태 배너
    if is_authenticated:
        st.markdown(
            f"""
            <div style="
                background-color: #e6f4ea;
                border: 1px solid #34a853;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 15px;
                color: #137333;
            ">
                <div style="font-weight: bold; font-size: 14px; margin-bottom: 4px;">✅ 인증 적용 중</div>
                <div style="font-size: 12px;">• ID: <b>{st.session_state['user_id']}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("💡 아이디와 등록번호를 입력 후 적용해주세요.")

    # 1. 입력 및 적용 폼
    with st.form(key="login_form", clear_on_submit=False):
        default_id = st.session_state.get("user_id", "")
        default_re = st.session_state.get("user_re", None)

        st.text_input(
            "🆔 아이디",
            value=default_id if default_id else "",
            key="input_id_val",
            disabled=is_authenticated,
        )
        st.number_input(
            "🔑 등록번호",
            value=default_re if default_re else None,
            min_value=1,
            max_value=99999999,
            step=1,
            placeholder="12345678",
            key="input_re_val",
            disabled=is_authenticated,
        )

        st.form_submit_button(
            "적용",
            on_click=handle_submit,
            use_container_width=True,
            disabled=is_authenticated,
        )

    # 2. 초기화 버튼
    st.button("취소/초기화", on_click=myclear, use_container_width=True)

# 페이지 실행
pg.run()