import hashlib
import streamlit as st
from sqlalchemy import text


# ===================================================================
# Page & Layout Config
# ===================================================================
st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
        [data-testid="stSidebarHeader"] img {
            height: 100px !important;
            width: auto !important;
            max-width: 100% !important;
        }

        [data-testid="stSidebarHeader"] {
            padding-top: 40px !important;
            padding-bottom: 40px !important;
            padding-left: 0px !important;
        }

        div[data-testid="InputInstructions"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ===================================================================
# DB Connection
# ===================================================================
conn = st.connection("mysql", type="sql")


# ===================================================================
# Page Definition
# ===================================================================
main_page = st.Page(
    "views/main.py",
    title="   내 서비스",
    default=True,
)

guide_page = st.Page(
    "views/guide.py",
    title="   이용 가이드",
)

# 로그인 실패 페이지
# 사이드바에는 표시하지 않음
loginfail_page = st.Page(
    "views/loginfail.py",
    title="   로그인 실패",
    visibility="hidden",
)

pdfdown_page = st.Page(
    "views/dashboard_pdf.py",
    title="   PDF 다운",
    visibility="hidden",
)

today_page = st.Page(
    "views/today.py",
    title="   일일 모니터링",
)

dashboard_page = st.Page(
    "views/dashboard.py",
    title="   통합 대시보드",
)

today_car_page = st.Page(
    "views/today_car.py",
    title="   일일 모니터링(준비중)",
)

dashboard_car_page = st.Page(
    "views/dashboard_car.py",
    title="   통합 대시보드(준비중)",
)


# ===================================================================
# Multi-Page Navigation
# ===================================================================
pages = {
    "🏠홈": [
        main_page,
        guide_page,
    ],
    "👨‍👩‍👧‍👦방문자분석": [
        today_page,
        dashboard_page,
    ],
    "🚗차량분석": [
        today_car_page,
        dashboard_car_page,
    ],
    "": [
        loginfail_page,
        pdfdown_page,
    ],
}

pg = st.navigation(pages)


# ===================================================================
# Helper Functions
# ===================================================================
def hash_password(password: str) -> str:
    """비밀번호 SHA-256 해시 변환"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def authenticate_user(user_id: str, password_raw: str) -> dict:
    """
    계정 확인 및 열람 가능한 work_no 목록 조회
    """
    try:
        hashed_pw = hash_password(password_raw)

        # 1. 계정 검증
        user_sql = """
            SELECT
                user_id,
                user_name,
                company_name,
                is_password_changed,
                is_active
            FROM rt_collect_user
            WHERE user_id = :user_id
              AND password_hash = :password_hash
              AND is_active = 1
        """

        user_df = conn.query(
            user_sql,
            params={
                "user_id": user_id,
                "password_hash": hashed_pw,
            },
            ttl=0,
        )

        if user_df.empty:
            return {
                "success": False,
                "msg": "아이디 혹은 비밀번호가 올바르지 않습니다.",
            }

        user_info = user_df.iloc[0].to_dict()

        # 2. 열람 가능 지점 확인
        info_sql = """
            SELECT
                work_no,
                location,
                memo,
                user_company,
                view_start_date,
                view_end_date
            FROM rt_collect_info
            WHERE user_id = :user_id
              AND view_yn = 1
              AND DATE_FORMAT(NOW(), '%Y%m%d')
                  BETWEEN view_start_date AND view_end_date
        """

        info_df = conn.query(
            info_sql,
            params={"user_id": user_id},
            ttl=0,
        )

        if info_df.empty:
            return {
                "success": False,
                "msg": "열람 권한이 없거나 웹 열람 허용 기간이 아닙니다.",
            }

        user_info["work_list"] = info_df.to_dict(orient="records")
        user_info["success"] = True

        return user_info

    except Exception as e:
        st.error(f"DB 조회 중 오류가 발생했습니다: {e}")

        return {
            "success": False,
            "msg": "DB 처리 중 오류가 발생했습니다.",
        }


def update_user_password(
    user_id: str,
    new_password_raw: str
) -> bool:
    """비밀번호 변경"""

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
                {
                    "new_pw": new_hashed_pw,
                    "user_id": user_id,
                }
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

    result = authenticate_user(
        input_id,
        str(input_pw)
    )

    # 로그인 성공
    if result["success"]:

        st.session_state["user_id"] = result["user_id"]
        st.session_state["user_name"] = result["user_name"]
        st.session_state["company_name"] = result["company_name"]
        st.session_state["work_list"] = result["work_list"]
        st.session_state["is_password_changed"] = result[
            "is_password_changed"
        ]

        st.toast(
            "✔️ "
            + st.session_state["user_name"]
            + "님 로그인 되었습니다."
        )

        st.switch_page(main_page)

    # 로그인 실패
    else:

        st.toast(
            "⚠️ 로그인 정보가 없거나 열람 가능한 지점이 없습니다. "
            "사이드바에서 먼저 로그인해 주세요."
        )

        st.switch_page(loginfail_page)


def myclear():
    """로그아웃 / 세션 초기화"""

    st.session_state["user_id"] = None
    st.session_state["user_name"] = None
    st.session_state["company_name"] = None
    st.session_state["work_list"] = []
    st.session_state["is_password_changed"] = 1
    st.session_state["input_id_val"] = ""
    st.session_state["input_pw_val"] = ""

    st.toast("🧹 로그아웃 되었습니다.")


# ===================================================================
# Logo
# ===================================================================
st.logo(
    "images/logo_wide.png",
    size="large",
    link="https://realtargeting.streamlit.app",
)


# ===================================================================
# Sidebar Authentication
# ===================================================================
with st.sidebar:

    st.subheader("🔑 사용자 인증")

    is_authenticated = bool(
        st.session_state.get("user_id")
    )

    # ---------------------------------------------------------------
    # 로그인 상태
    # ---------------------------------------------------------------
    if is_authenticated:

        user_id = st.session_state["user_id"]

        company = (
            st.session_state.get("company_name")
            or "고객사"
        )

        user_name = (
            st.session_state.get("user_name")
            or "사용자"
        )

        work_count = len(
            st.session_state.get("work_list", [])
        )

        if st.session_state.pop(
            "pw_change_success",
            False
        ):
            st.toast(
                "✅ 비밀번호가 성공적으로 변경되었습니다!",
                icon="🎉"
            )
            st.success("비밀번호가 변경되었습니다.")

        st.markdown(
            f"""
            <div style="
                background-color: rgba(52, 168, 83, 0.15);
                border: 1px solid #34a853;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 12px;
            ">
                <div style="
                    font-weight: bold;
                    font-size: 14px;
                    margin-bottom: 4px;
                    color: #34a853;
                ">
                    ✅ 인증 완료
                </div>
                <div style="font-size: 13px;">
                    • 소속: <b>{company}</b>
                </div>
                <div style="font-size: 13px;">
                    • 사용자명: <b>{user_name}</b>
                </div>
                <div style="font-size: 13px;">
                    • ID: <b>{user_id}</b>
                </div>
                <div style="font-size: 13px;">
                    • 열람지점: <b>{work_count}개 보유</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 초기 비밀번호
        if st.session_state.get(
            "is_password_changed"
        ) == 0:

            st.warning(
                "⚠️ 초기 비밀번호 사용 중입니다. "
                "비밀번호를 변경해 주세요."
            )

        # 비밀번호 변경
        with st.expander("🔒 비밀번호 변경"):

            with st.form(
                key="change_pw_form",
                clear_on_submit=True
            ):

                new_pw = st.text_input(
                    "새 비밀번호",
                    type="password"
                )

                new_pw_confirm = st.text_input(
                    "비밀번호 확인",
                    type="password"
                )

                pw_submit = st.form_submit_button(
                    "비밀번호 변경",
                    width="stretch"
                )

                if pw_submit:

                    if not new_pw or len(new_pw) < 4:

                        st.error(
                            "비밀번호는 최소 4자리 이상 "
                            "입력해 주세요."
                        )

                    elif new_pw in ["1111", "notreal"]:

                        st.error(
                            "초기 비밀번호 외 다른 "
                            "비밀번호를 설정해 주세요."
                        )

                    elif new_pw != new_pw_confirm:

                        st.error(
                            "새 비밀번호가 서로 일치하지 않습니다."
                        )

                    else:

                        if update_user_password(
                            user_id,
                            new_pw
                        ):

                            st.session_state[
                                "is_password_changed"
                            ] = 1

                            st.session_state[
                                "pw_change_success"
                            ] = True

                            st.rerun()

        # 로그아웃
        st.button(
            "🚪 로그아웃",
            on_click=myclear,
            width="stretch",
            type="secondary",
        )

    # ---------------------------------------------------------------
    # 로그인 전 상태
    # ---------------------------------------------------------------
    else:

        with st.form(
            key="login_form",
            clear_on_submit=False
        ):

            st.text_input(
                "🆔 아이디",
                key="input_id_val"
            )

            st.text_input(
                "🔑 비밀번호",
                type="password",
                key="input_pw_val"
            )

            st.form_submit_button(
                "로그인",
                on_click=handle_submit,
                width="stretch"
            )


# ===================================================================
# Run Page
# ===================================================================
pg.run()

