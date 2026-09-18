import streamlit as st

# 세션 상태 초기화
if 'id' not in st.session_state:
    st.session_state['id'] = None
if 're' not in st.session_state:
    st.session_state['re'] = None

url_kakao = "https://pf.kakao.com/_vfxaZn"
url_homepage = "https://www.realtargeting.co.kr"

# CSS 커스텀 스타일링
st.markdown("""
    <style>
        /* st.logo 이미지 컨테이너 크기 확대 */
        [data-testid="stSidebarHeader"] img {
            height: 100px !important;
            width: auto !important;
            max-width: 100% !important;
        }
        [data-testid="stSidebarHeader"] {
            padding-top: 40px !important;
            padding-bottom: 1rem !important;
            padding-left: 0px !important;
        }
        /* 메인 카드 스타일 */
        .info-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 5px solid #1E88E5;
            margin-bottom: 20px;
        }
        .contact-box {
            background-color: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# 헤더 영역
st.title("💡 서비스 이용 가이드")
st.caption("리얼타겟팅 분석 솔루션을 효과적으로 활용하는 방법입니다.")
st.divider()

# 1. 이용방법 & 샘플조회 (2열 카드 레이아웃)
col1, col2 = st.columns([1.2, 0.8], gap="medium")

with col1:
    st.subheader("📌 이용 방법")
    st.info("""
    **Step 1.** 좌측 사이드바에 전달받으신 [아이디]와 [비밀번호]를 입력 후 [적용]을 클릭하세요.  
    **Step 2.** 조회할 분석 메뉴를 선택하여 데이터를 확인합니다.
    """)

with col2:
    st.subheader("🧪 샘플 계정")
    st.warning("""
    서비스를 미리 체험해보고 싶다면 아래 테스트 계정을 입력해보세요.

    * **아이디**: `real`
    * **등록번호**: `12345678`
    """)

st.write("")

# 2. 문의사항 & 고객지원
st.subheader("❓ 문의 사항")

contact_col1, contact_col2 = st.columns([1, 1], gap="medium")

with contact_col1:
    with st.container(border=True):
        st.markdown("#### 💬 카카오톡 1:1 상담")
        sub_col1, sub_col2 = st.columns([1, 2])
        with sub_col1:
            st.image("images/qr_카카오채널.png", use_container_width=True)
        with sub_col2:
            st.write("QR코드를 스캔하거나 아래 버튼을 클릭하여 상담을 시작하세요.")
            st.link_button("카카오톡 채널 바로가기", url_kakao, type="primary")

with contact_col2:
    with st.container(border=True):
        st.markdown("#### 📞 고객지원 센터")
        st.write(f"👉 **유선 연락처**: 010-4424-3291")
        st.write(f"👉 **이메일**: realtargeting@gmail.com")
        st.write(f"👉 **공식 홈페이지**: [{url_homepage}]({url_homepage})")

# 푸터
st.divider()
st.caption("Copyright © RealTargeting All rights reserved.", help="리얼타겟팅 지원센터")