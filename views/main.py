import pandas as pd
from sqlalchemy import text
import streamlit as st

# Streamlit DB 커넥션 설정
conn = st.connection("mysql", type="sql")

# Session State 초기화
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

if "id" not in st.session_state:
    st.session_state["id"] = None

if "re" not in st.session_state:
    st.session_state["re"] = None

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


# --- [DB 조회 함수: 측정 정보 데이터 로드] ---
def get_collect_info_list(user_id: str):
    """사용자 권한/ID에 따른 측정지점(rt_collect_info) 리스트 조회"""
    try:
        if user_id in ["notreal", "admin"]:
            query = text("""
                SELECT 
                    work_no as '작업번호',
                    memo as '측정지점',
                    location as '주소',
                    device_no as '장비번호',
                    status as '진행상태',
                    start_date as '시작일자',
                    end_date as '종료일자',
                    view_start_date as '열람시작일자',
                    view_end_date as '열람종료일자',
                    start_time as '시작시간',
                    end_time as '종료시간', 
                    latitude as '위도',
                    longitude as '경도'                    
                FROM rt_collect_info
                ORDER BY work_no ASC
            """)
            params = {}
        else:
            query = text("""
                SELECT 
                    work_no as '작업번호',
                    memo as '측정지점',
                    location as '주소',                    
                    status as '진행상태',
                    start_date as '시작일자',
                    end_date as '종료일자',                    
                    start_time as '시작시간',
                    end_time as '종료시간', 
                    latitude as '위도',
                    longitude as '경도' 
                FROM rt_collect_info
                WHERE user_id = :user_id
                  AND view_yn = 1
                AND view_start_date <= CURDATE()
                AND view_end_date >= CURDATE() 
                ORDER BY work_no ASC
            """)
            params = {"user_id": user_id}

        with conn.session as session:
            result = session.execute(query, params)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
    except Exception as e:
        st.error(f"측정지점 데이터 조회 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()


# --- [메인 화면 로직] ---

user_id = st.session_state.get("user_id")

if not user_id:
    # 1. 미로그인 상태
    st.image(
        "images/technology-7111760_1920.jpg", width="stretch"
    )
    st.info(
        "👋 좌측 사이드바에서 로그인 후 측정지점 리스트 및 통행량 분석 정보를 확인하세요."
    )
else:
    # 2. 로그인 완료 상태
    company_name = st.session_state.get("company_name", "고객사")
    user_name = st.session_state.get("user_name", "고객명")
    st.subheader(
        f"📊 {user_name}님[{company_name}] 서비스 현황", divider="blue"
    )

    df_info = get_collect_info_list(user_id)

    if df_info.empty:
        st.warning("등록된 측정지점 정보가 없습니다.")
    else:
        # 💡 최신 조회 결과를 session_state["work_list"]에 갱신 (latitude, longitude 포함됨)
        st.session_state["work_list"] = df_info.to_dict(orient="records")

        # 요약 메트릭 카드
        total_cnt = len(df_info)

        # 💡 'status' 또는 '상태' 컬럼 모두 대응 가능하도록 안전하게 체크
        status_col = "status" if "status" in df_info.columns else ("진행상태" if "진행상태" in df_info.columns else None)

        if status_col:
            active_cnt = len(df_info[df_info[status_col] == "완료"])
        else:
            active_cnt = total_cnt

        st.divider()

        # --- [1. 세션에서 테이블 선택 상태 추출] ---
        table_state = st.session_state.get("collect_table_selection", {})
        selected_rows = table_state.get("selection", {}).get("rows", [])
        selected_count = len(selected_rows)

        # 1-1. 상단 안내 메시지
        if selected_count == 0:
            st.info("💡 아래 목록에서 분석할 지점(행)을 선택해 주세요.")
        elif selected_count == 1:
            st.success("✅ 1개 지점 선택됨: [일일 모니터링] 또는 [통합 대시보드] 이동 가능")
        elif 2 <= selected_count <= 4:
            st.success(f"✅ {selected_count}개 지점 선택됨: [다중 분석] 이동 가능")
        else:
            st.error("⚠️ 다중 분석은 최대 4개 지점까지만 선택 가능합니다.")

        is_single_valid = selected_count == 1
        is_multi_valid = 2 <= selected_count <= 4

        # 1-2. 검색창 & 버튼 수평 레이아웃
        col_search, btn_col1, btn_col2, btn_col3 = st.columns([5, 1.5, 1.5, 1.5])

        with col_search:
            search_kw = st.text_input(
                "🔍 검색",
                placeholder="측정지점명 또는 주소 검색...",
                label_visibility="collapsed",
            )

        with btn_col1:
            btn_daily = st.button(
                "📈 일일 모니터링",
                disabled=not is_single_valid,
                width="stretch",
                type="primary" if is_single_valid else "secondary",
            )

        with btn_col2:
            btn_dashboard = st.button(
                "📊 통합 대시보드",
                disabled=not is_single_valid,
                width="stretch",
                type="primary" if is_single_valid else "secondary",
            )

        with btn_col3:
            btn_multi = st.button(
                f"🔀 다중 분석 ({selected_count}/4)",
                disabled=not is_multi_valid,
                width="stretch",
                type="primary" if is_multi_valid else "secondary",
            )

        # 검색 키워드 필터링 적용
        filtered_df = df_info.copy()
        if search_kw:
            filtered_df = filtered_df[
                filtered_df["측정지점"]
                .astype(str)
                .str.contains(search_kw, case=False, na=False)
                | filtered_df["주소"]
                .astype(str)
                .str.contains(search_kw, case=False, na=False)
            ]

        column_config = {
            col: st.column_config.Column(alignment="center")
            for col in filtered_df.columns
        }

        # --- [2. 측정지점 리스트 테이블] ---
        st.dataframe(
            filtered_df,
            width="stretch",
            hide_index=True,
            height=300,
            on_select="rerun",
            selection_mode=["multi-row"],
            key="collect_table_selection",
            column_config=column_config,
        )

        # --- [3. 페이지 이동 및 데이터 전달 로직] ---
        if btn_daily or btn_dashboard:
            # 선택된 행의 데이터 추출
            selected_row_data = filtered_df.iloc[selected_rows[0]]

            # 단일 선택된 지점의 work_no 및 memo/location 저장
            st.session_state["selected_work_no"] = selected_row_data["작업번호"]
            st.session_state["selected_location"] = selected_row_data.get("측정지점", selected_row_data.get("주소", ""))
            st.session_state["selected_start_date"] = selected_row_data["시작일자"]
            st.session_state["selected_end_date"] = selected_row_data["종료일자"]
            st.session_state["selected_start_time"] = selected_row_data["시작시간"]
            st.session_state["selected_end_time"] = selected_row_data["종료시간"]
            st.session_state["selected_latitude"] = selected_row_data["위도"]
            st.session_state["selected_longitude"] = selected_row_data["경도"]

            if btn_daily:
                st.switch_page("views/today.py")
            elif btn_dashboard:
                st.switch_page("views/dashboard.py")

        if btn_multi:
            selected_data = filtered_df.iloc[selected_rows]
            st.session_state["selected_work_nos"] = selected_data["작업번호"].tolist()
            st.session_state["selected_memos"] = selected_data[
                "측정지점"].tolist() if "측정지점" in selected_data.columns else []
            st.switch_page("views/multi_analysis.py")

# 하단 푸터
st.caption("Copyright (R) Realtargeting All rights reserved.")

