import streamlit as st

st.markdown(
    """
    <style>
    /* 데이터프레임 툴바 숨기기 */
    [data-testid="stElementToolbar"] {
        display: none !important;
    }
    /* 1. Canvas 기반 테이블 헤더(컬럼 제목) 가운데 정렬 */
    div[data-testid="stDataFrame"] [role="columnheader"] {
        justify-content: center !important;
        text-align: center !important;
    }

    /* 2. 일반 HTML Table 헤더 대응 */
    div[data-testid="stDataFrame"] th {
        text-align: center !important;
    }

    /* 3. Canvas 기반 데이터 셀(내용) 가운데 정렬 */
    div[data-testid="stDataFrame"] [role="gridcell"] {
        justify-content: center !important;
        text-align: center !important;
    }

    /* 4. 일반 HTML Table 데이터 셀 대응 */
    div[data-testid="stDataFrame"] td {
        text-align: center !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# --- [메인 화면 로직] ---
st.image(
    "images/technology-7111760_1920.jpg", width="stretch"
)
st.error(
    "⚠️ 로그인 정보가 없거나 열람 가능한 지점이 없습니다. 사이드바에서 먼저 로그인 해 주세요."
)

# 하단 푸터
st.caption("Copyright (R) Realtargeting All rights reserved.")

