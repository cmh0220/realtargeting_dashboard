import hashlib
import streamlit as st

# ===================================================================
# Page & Layout Config
# ===================================================================
st.set_page_config(layout="wide")

# CSS Customization
st.markdown(
    """
    <style>
        /* st.logo 이미지 컨테이너 크기 확대 */
        [data-testid="stSidebarHeader"] img {
            height: 100px !important;
            width: auto !important;
            max-width: 100% !important;
        }
        /* 로고 영역 컨테이너 여백 조정 */
        [data-testid="stSidebarHeader"] {
            padding-top: 40px !important;
            padding-bottom: 40px !important;
            padding-left: 0px !important;
        }
        /* Form 하단의 "Press ↵ to submit form" 안내 문구 숨기기 */
        div[data-testid="InputInstructions"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Streamlit DB 커넥션 선언 (.streamlit/secrets.toml 설정 참조)
conn = st.connection("mysql", type="sql")


# ===================================================================
# Helper Functions (DB & Authentication)
# ===================================================================
def hash_password(password: str) -> str:
    """비밀번호 SHA-256 해시 변환"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def authenticate_user(user_id: str, password_raw: str) -> dict:
    """
    1. rt_collect_user 테이블에서 계정 정보 및 비밀번호 해시 검증
    2. rt_collect_info 테이블에서 현재 열람 가능한 work_no 목록 조회
    """
    try:
        hashed_pw = hash_password(password_raw)

        # 1. 계정 검증
        user_sql = """
            SELECT user_id, user_name, company_name, is_password_changed, is_active
            FROM rt_collect_user
            WHERE user_id = :user_id 
              AND password_hash = :password_hash
              AND is_active = 1
        """
        user_df = conn.query(
            user_sql,
            params={"user_id": user_id, "password_hash": hashed_pw},
            ttl=0,
        )

        if user_df.empty:
            return {"success": False, "msg": "아이디 혹은 비밀번호가 올바르지 않습니다."}

        user_info = user_df.iloc[0].to_dict()

        # 2. 열람 가능 지점(work_no) 목록 및 기간 검증
        info_sql = """
            SELECT work_no, location, memo, user_company, view_start_date, view_end_date
            FROM rt_collect_info
            WHERE user_id = :user_id
              AND view_yn = 1
              AND DATE_FORMAT(NOW(), '%Y%m%d') BETWEEN view_start_date AND view_end_date
        """
        info_df = conn.query(info_sql, params={"user_id": user_id}, ttl=0)

        if info_df.empty:
            return {
                "success": False,
                "msg": "열람 권한이 없거나 웹 열람 허용 기간이 아닙니다. 관리자에게 문의하세요.",
            }

        user_info["work_list"] = info_df.to_dict(orient="records")
        user_info["success"] = True
        return user_info

    except Exception as e:
        st.error(f"DB 조회 중 오류가 발생했습니다: {e}")
        return {"success": False, "msg": "DB 처리 중 오류가 발생했습니다."}


from sqlalchemy import text  # 1. sqlalchemy의 text 함수 임포트 필수


def update_user_password(user_id: str, new_password_raw: str) -> bool:
    """비밀번호 변경 및 is_password_changed 플래그 1로 업데이트"""
    try:
        new_hashed_pw = hash_password(new_password_raw)

        update_sql = text("""
            UPDATE rt_collect_user
            SET password_hash = :new_pw,
                is_password_changed = 1
            WHERE user_id = :user_id
        """)

        with conn.session as session:
            session.execute(
                update_sql,
                {"new_pw": new_hashed_pw, "user_id": user_id}
            )
            session.commit()

        return True
    except Exception as e:
        st.error(f"비밀번호 변경 실패: {e}")
        return False


# ===================================================================
# Session State Initialization
# ===================================================================
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None
if "company_name" not in st.session_state:
    st.session_state["company_name"] = None
if "work_list" not in st.session_state:
    st.session_state["work_list"] = []
if "is_password_changed" not in st.session_state:
    st.session_state["is_password_changed"] = 1

# 입력 필드용 위젯 키
if "input_id_val" not in st.session_state:
    st.session_state["input_id_val"] = ""
if "input_pw_val" not in st.session_state:
    st.session_state["input_pw_val"] = ""


# ===================================================================
# Callbacks
# ===================================================================
def handle_submit():
    input_id = st.session_state.get("input_id_val")
    input_pw = st.session_state.get("input_pw_val")

    if not input_id or not input_pw:
        st.toast("⚠️ 아이디 및 비밀번호를 입력하세요.")
        return

    result = authenticate_user(input_id, str(input_pw))

    if result["success"]:
        st.session_state["user_id"] = result["user_id"]
        st.session_state["user_name"] = result["user_name"]
        st.session_state["company_name"] = result["company_name"]
        st.session_state["work_list"] = result["work_list"]
        st.session_state["is_password_changed"] = result["is_password_changed"]
        st.toast("✔️ 로그인 성공!")

        # 로그인 성공 시 main.py 페이지로 바로 이동
        st.switch_page("views/main.py")
    else:
        st.toast(f"⚠️ {result['msg']}")


def myclear():
    """로그아웃 / 세션 초기화"""
    st.session_state["user_id"] = None
    st.session_state["user_name"] = None
    st.session_state["company_name"] = None
    st.session_state["work_list"] = []
    st.session_state["is_password_changed"] = 1
    st.session_state["input_id_val"] = ""
    st.session_state["input_pw_val"] = ""
    st.toast("🧹 로그아웃되었습니다.")


# ===================================================================
# Logo Setting
# ===================================================================
st.logo(
    "images/logo_wide.png",
    size="large",
    link="https://realtargeting.streamlit.app",
)


# ===================================================================
# Sidebar Authentication & Password Change UI
# ===================================================================
with st.sidebar:
    st.subheader("🔑 사용자 인증")

    is_authenticated = bool(st.session_state.get("user_id"))

    # 1. 인증 완료 상태 UI
    if is_authenticated:
        user_id = st.session_state["user_id"]
        company = st.session_state.get("company_name") or "고객사"
        user_name = st.session_state.get("user_name") or "사용자"
        work_count = len(st.session_state.get("work_list", []))

        # 비밀번호 변경 성공 플래그가 세션에 남아있으면 알림 출력 후 삭제
        if st.session_state.pop("pw_change_success", False):
            st.toast("✅ 비밀번호가 성공적으로 변경되었습니다!", icon="🎉")
            st.success("비밀번호가 변경되었습니다.")

        # 사용자 인증 배너
        st.markdown(
            f"""
            <div style="
                background-color: rgba(52, 168, 83, 0.15);
                border: 1px solid #34a853;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 12px;
            ">
                <div style="font-weight: bold; font-size: 14px; margin-bottom: 4px; color: #34a853;">✅ 인증 완료</div>
                <div style="font-size: 13px;">• 소속: <b>{company}</b></div>
                <div style="font-size: 13px;">• 사용자명: <b>{user_name}</b></div>
                <div style="font-size: 13px;">• ID: <b>{user_id}</b></div>
                <div style="font-size: 13px;">• 열람지점: <b>{work_count}개 보유</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 초기 비밀번호 상태인 경우 경고 문구 노출
        if st.session_state.get("is_password_changed") == 0:
            st.warning("⚠️ 초기 비밀번호 사용 중입니다. 비밀번호를 변경해 주세요.")

        # 비밀번호 변경 Expander
        with st.expander("🔒 비밀번호 변경"):
            with st.form(key="change_pw_form", clear_on_submit=True):
                new_pw = st.text_input("새 비밀번호", type="password")
                new_pw_confirm = st.text_input("비밀번호 확인", type="password")
                pw_submit = st.form_submit_button(
                    "비밀번호 변경", use_container_width="stretch"
                )

                if pw_submit:
                    if not new_pw or len(new_pw) < 4:
                        st.error("비밀번호는 최소 4자리 이상 입력해 주세요.")
                    elif new_pw == "1111" or new_pw == "notreal":
                        st.error("초기 비밀번호 외 다른 비밀번호를 설정해 주세요.")
                    elif new_pw != new_pw_confirm:
                        st.error("새 비밀번호가 서로 일치하지 않습니다.")
                    else:
                        if update_user_password(user_id, new_pw):
                            st.session_state["is_password_changed"] = 1
                            # 새로고침 후 성공 메시지를 띄우기 위한 플래그 설정
                            st.session_state["pw_change_success"] = True
                            st.rerun()

        # 🚪 로그아웃 버튼 
        st.button(
            "🚪 로그아웃",
            on_click=myclear,
            use_container_width="stretch",
            type="secondary",
        )
    # 2. 미인증 상태 UI (로그인 폼)
    else:
        with st.form(key="login_form", clear_on_submit=False):
            st.text_input("🆔 아이디", key="input_id_val")
            st.text_input("🔑 비밀번호", type="password", key="input_pw_val")

            st.form_submit_button(
                "로그인",
                on_click=handle_submit,
                use_container_width="stretch",
            )


# ===================================================================
# Multi-Page Navigation
# ===================================================================
pages = {
    "🏠홈": [
        st.Page("views/main.py", title="   내 서비스", default=True),
        st.Page("views/guide.py", title="   이용 가이드"),
    ],
    "👨‍👩‍👧‍👦방문자분석": [
        st.Page("views/today.py", title="   일일 모니터링"),
        st.Page("views/dashboard.py", title="   통합 대시보드"),
    ],
    "🚗차량분석": [
        st.Page("views/today_car.py", title="   일일 모니터링(준비중)"),
        st.Page("views/dashboard_car.py", title="   통합 대시보드(준비중)"),
    ],
}

pg = st.navigation(pages)
pg.run()