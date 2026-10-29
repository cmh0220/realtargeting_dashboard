from datetime import datetime, date, timedelta
from typing import Any, Dict, List
import streamlit as st
from streamlit_echarts import st_echarts
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from playwright.sync_api import sync_playwright
import subprocess
import pandas as pd
import requests
import os


# 1. Playwright 크롬 브라우저 자동 설치 체크 함수
@st.cache_resource
def install_playwright_browser():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Playwright 브라우저 설치 실패: {e}")


# 앱 실행 시 1회 자동 설치
install_playwright_browser()


# 2. PDF 생성 핵심 함수
def get_pdf_bytes(user_id: str, work_no: str):
    base_url = os.getenv("STREAMLIT_BASE_URL", "http://localhost:8501")
    if base_url.startswith("http://"):
        clean_base = base_url
    else:
        clean_base = f"http://{base_url}"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )

        page = browser.new_page(
            viewport={'width': 1200, 'height': 1600},
            device_scale_factor=2
        )

        target_url = f"{clean_base}/dashboard_pdf?export_mode=true&user_id={user_id}&work_no={work_no}"

        # 💡 'networkidle' 대신 'domcontentloaded'로 변경 (웹소켓 통신 대기 방지)
        page.goto(target_url, wait_until='domcontentloaded', timeout=60000)

        # ECharts, Folium 등 차트가 완전히 그려질 수 있도록 충분히 대기 (7초)
        page.wait_for_timeout(7000)

        pdf_bytes = page.pdf(
            format='A4',
            print_background=True,
            margin={'top': '10mm', 'bottom': '10mm', 'left': '10mm', 'right': '10mm'}
        )
        browser.close()
        return pdf_bytes


# Helper 함수: YYYYMMDD -> YYYY-MM-DD
def format_date_str(date_str):
    if date_str and len(str(date_str)) == 8:
        s = str(date_str)
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return date_str or "-"

# Helper 함수: HH -> HH:00 또는 HHMM -> HH:MM
def format_time_str(time_str):
    if time_str:
        s = str(time_str).zfill(2)
        if len(s) == 2:
            return f"{s}:00"
        elif len(s) == 4:
            return f"{s[:2]}:{s[2:]}"
    return time_str or "-"

def render_section_header(icon: str, ko_title: str, en_title: str):
    """보고서 스타일의 일체형 섹션 헤더를 렌더링합니다."""
    st.markdown(
        f"""
        <div style="display: flex; align-items: baseline; gap: 12px; margin-top: 20px; margin-bottom: 16px;">
            <span style="font-size: 32px; line-height: 1;">{icon}</span>
            <div style="display: flex; align-items: baseline; gap: 12px;">
                <span style="font-size: 30px; font-weight: bold; color: #0f172a; letter-spacing: -0.5px;">{ko_title}</span>
                <span style="font-size: 24px; font-weight: 500; color: #94a3b8; font-family: sans-serif;">{en_title}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_info_footer(logo_path_or_url: str = None):
    """
    대시보드 하단 안내문 및 로고 레이아웃 렌더링 함수
    :param logo_path_or_url: 가운데 들어갈 로고 이미지 경로 또는 URL
    """

    # Custom CSS 적용
    st.markdown("""
    <style>
        .info-title {
            font-size: 20px;
            font-weight: 800;
            color: #1E293B;
            margin-bottom: 8px;
        }
        .info-divider {
            border-bottom: 3px solid #3B82F6;
            margin-bottom: 24px;
        }
        .info-list {
            font-size: 14.5px;
            line-height: 1.7;
            color: #334155;
            margin-bottom: 30px;
        }
        .info-list p {
            margin-bottom: 12px;
            word-break: keep-all;
        }

        /* 주의사항 박스 */
        .warning-box {
            background-color: #FEF9C3;
            border: 1px solid #FDE047;
            border-radius: 8px;
            padding: 30px 24px;
            margin-top: 35px;
            margin-bottom: 25px;
            color: #1E293B;
            font-size: 13.5px;
            line-height: 1.6;
        }
        .warning-header {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            font-weight: 700;
            font-size: 14px;
            margin-bottom: 12px;
            color: #854D0E;
        }
        .warning-list {
            margin-left: 28px;
            color: #334155;
        }
        .warning-list li {
            margin-bottom: 4px;
        }

        /* 저작권 표시 */
        .copyright {
            text-align: right;
            font-size: 13px;
            color: #64748B;
            font-weight: 600;
            margin-top: 15px;
        }
    </style>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # 1. 상단 타이틀 및 안내문
    # ----------------------------------------------------
    st.markdown('<div class="info-title">AI 통행량 분석 안내</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-divider"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-list">
        <p><b>1.</b> 통행량 데이터 수집 프로세스는 인공지능 기술을 이용하여 모든 과정이 자동으로 처리됩니다.</p>
        <p><b>2.</b> 수집된 정보는 모두 개인을 식별할 수 없는 메타데이터로 구성되어 있으며 파일 암호화 및 접근통제가 적용되어 있습니다.</p>
        <p><b>3.</b> 영상정보처리기기 운영 및 관리지침에 의해 관리되고 있으며, 통행량 데이터 수집시 영상을 녹화하거나 저장하지 않으며 개인정보보호법을 엄격히 준수합니다.</p>
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # 3. 하단 경고 및 안내 박스
    # ----------------------------------------------------
    st.markdown("""
    <div class="warning-box" style="margin-top: 35px;">
        <div class="warning-header">
            <span style="font-size: 20px;">⚠️</span>
            <div>
                본 보고서는 인공지능 AI 영상인식 기술을 활용하여 통행량을 분석하여 작성되었습니다.<br>
                상황에 따라 아래와 같이 일부 오탐지 되는 경우도 있는 점 미리 안내드립니다. 따라서 이 점 충분히 감안하여 상권분석에 활용하시기 바랍니다.
            </div>
        </div>
        <ol class="warning-list" type="1">
            <li>측정 순간 객체의 일부 혹은 전체가 가려진 경우(차량, 타 보행자) 누락 가능</li>
            <li>뛰어가거나 차량, 자전거, 오토바이에 탑승하여 빠르게 통과 하는 경우 누락 가능</li>
            <li>조명이 부족한 경우(새벽, 야간) 탐지 누락 가능</li>
            <li>사람이 봐도 성별 구분이 어려운 경우 성별 오탐지</li>
            <li>그 외 AI가 인식하지 못하는 경우 발생</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # 2. 중앙 로고 영역
    # ----------------------------------------------------
    if logo_path_or_url:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.image(logo_path_or_url, width='stretch')
    else:
        # 파일이 없을 때 보여주는 샘플 대용 박스 (실제 적용 시 삭제 가능)
        st.info("💡 여기에 로고 이미지(logo_path_or_url)를 지정해 주세요.")

    # ----------------------------------------------------
    # 4. 카피라이트 (Copyright)
    # ----------------------------------------------------
    st.markdown('<div style="text-align: right;" class="copyright">Copyright © 2026. All Rights Reserved.</div>', unsafe_allow_html=True)


# 1. 해당 작업(work_no)의 모든 코멘트를 한 번에 가져오는 함수
def fetch_all_comments(user_id: str, work_no: str):
    query = """
        SELECT com1, com2, com3, com4, com5, com6, com7, com8, com9 
        FROM rt_collect_comment 
        WHERE user_id = :user_id AND work_no = :work_no
    """
    try:
        # work_no가 숫자형 테이블 타입이라면 int()로 명시적 변환
        params = {"user_id": str(user_id), "work_no": int(work_no)}

        # 캐시 오버헤드를 줄이기 위해 ttl=0 제거
        df = conn.query(query, params=params)

        if df is not None and not df.empty:
            return df.iloc[0].to_dict()
    except Exception as e:
        print(f"Error fetching comments: {e}")

    return {}


# 2. 미리 조회해 둔 딕셔너리에서 특정 컬럼의 코멘트를 출력하는 함수
def render_comment_box(comments_dict: dict, comment_key: str = "com1"):
    comment_text = ""
    if comments_dict:
        val = comments_dict.get(comment_key)
        if val and str(val).strip() != "None" and str(val).strip() != "nan":
            comment_text = str(val)

    st.markdown(
        f"""
        <div style="            
            box-sizing: border-box;
            background-color: #f1f3f5;
            border-radius: 6px;
            padding: 20px;                      /* 🌟 상하좌우 모든 방향에 동일하게 4px 적용 */
            margein-left: 2px;
            font-size: 15px;
            color: #212529;
            line-height: 1.6;
            white-space: pre-line;
            word-break: keep-all;
        "><B>Comment</B><BR>
            {comment_text}
        </div>
        """,
        unsafe_allow_html=True
    )

# ------------------------------------------------------------------------------
# 1. 공통 차트 렌더러 (Chart Component Functions)
# ------------------------------------------------------------------------------
def render_location_map(selected_work_info: Dict[str, Any]):
    """왼쪽에는 측정 기본 정보 카드, 오른쪽(너비 50%)에는 지도를 배치합니다."""

    # 1. 컬럼 분할 (3:2 비율)
    col_info, col_map = st.columns([3, 2], gap="medium")

    # 2. [왼쪽 컬럼] 기본 정보 카드 렌더링
    with col_info:
        start_date = format_date_str(selected_work_info.get("시작일자") or selected_work_info.get("start_date"))
        end_date = format_date_str(selected_work_info.get("종료일자") or selected_work_info.get("end_date"))
        start_time = format_time_str(selected_work_info.get("시작시간") or selected_work_info.get("start_time"))
        end_time = format_time_str(selected_work_info.get("종료시간") or selected_work_info.get("end_time"))
        address = selected_work_info.get("주소") or selected_work_info.get("location", "-")
        memo = selected_work_info.get("측정지점") or selected_work_info.get(
            "memo") or f"지점 {selected_work_info.get('작업번호') or selected_work_info.get('work_no')}"

        st.markdown(
            f"""
            <div style="
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 16px 20px;
                height: 320px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <h4 style="margin-top: 0; margin-bottom: 12px; color: #1e293b; font-size: 17px; font-weight: bold;">
                    위치 : {memo}                    
                </h4>
                <h4 style="margin-top: 0; margin-bottom: 12px; color: #1e293b; font-size: 17px; font-weight: bold;">
                    주소 : {address}
                </h4>
                <hr style="margin: 8px 0 16px 0; border: none; border-top: 1px solid #e2e8f0;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div>
                        <span style="font-size: 17px; color: #64748b; display: block;">📅 측정 시작일자</span>
                        <span style="font-size: 17px; font-weight: 600; color: #0f172a; margin-left: 24px;">{start_date}</span>
                    </div>
                    <div>
                        <span style="font-size: 17px; color: #64748b; display: block;">📅 측정 종료일자</span>
                        <span style="font-size: 17px; font-weight: 600; color: #0f172a; margin-left: 24px;">{end_date}</span>
                    </div>
                    <div>
                        <span style="font-size: 17px; color: #64748b; display: block;">⏰ 측정 시작시간</span>
                        <span style="font-size: 17px; font-weight: 600; color: #2563eb; margin-left: 24px;">{start_time}</span>
                    </div>
                    <div>
                        <span style="font-size: 17px; color: #64748b; display: block;">⏰ 측정 종료시간</span>
                        <span style="font-size: 17px; font-weight: 600; color: #2563eb; margin-left: 24px;">{end_time}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. [오른쪽 컬럼] 지도 렌더링
    with col_map:
        lat = selected_work_info.get("위도") or selected_work_info.get("latitude")
        lng = selected_work_info.get("경도") or selected_work_info.get("longitude")

        if lat is None or lng is None:
            st.info("ℹ️ 해당 측정지점에 등록된 위도/경도 좌표 정보가 없습니다.")
            return

        try:
            lat = float(lat)
            lng = float(lng)
        except (ValueError, TypeError):
            st.warning("⚠️ 위도/경도 좌표 형식이 올바르지 않습니다.")
            return

        m = folium.Map(location=[lat, lng], zoom_start=17)

        popup_text = f"<b>{memo}</b><br>{address}" if address else f"<b>{memo}</b>"
        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=memo,
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(m)

        st_folium(
            m,
            width="100%",
            height=320,
            key=f"map_{selected_work_info.get('작업번호') or selected_work_info.get('work_no')}",
        )


def render_metric_cards(df_h1, df_h2, df_h3, df_h4, df_h5, df_h6, df_h7, df_h8):
    """상단 주요 지표 카드를 출력합니다."""
    col1, col2, col3, col4 = st.columns(4)
    col5, col6, col7, col8 = st.columns(4)

    def get_val_cnt(df, surfix):
        if df is not None and not df.empty and df.iloc[0, 0] is not None:
            return f"{int(round(float(df.iloc[0, 0]))):,}{surfix}"
        return f"0{surfix}"

    def get_val_sec(df, surfix):
        if df is not None and not df.empty and df.iloc[0, 0] is not None:
            return f"{float(df.iloc[0, 0]):,.1f}{surfix}"
        return f"0.0{surfix}"

    col1.metric("전체 누적 통행량", get_val_cnt(df_h1, "명"))
    col2.metric("일평균 통행량", get_val_cnt(df_h2, "명"))
    col3.metric("시간당 통행량", get_val_cnt(df_h3, "명"))
    col4.metric("분당 통행량", get_val_cnt(df_h4, "명"))
    col5.metric("주중 평균 통행량", get_val_cnt(df_h5, "명"))
    col6.metric("주말 평균 통행량", get_val_cnt(df_h6, "명"))
    col7.metric("전체 평균 체류시간", get_val_sec(df_h7, "초"))
    col8.metric("시간당 평균 체류시간", get_val_sec(df_h8, "초"))


def render_chart_item(chart_info: Dict[str, Any]):
    """개별 차트 데이터를 받아 유형에 맞는 Streamlit 차트를 출력합니다."""
    title = chart_info.get("title", "")
    chart_type = chart_info.get("type", "bar")
    df = chart_info.get("df")
    chart_id = chart_info.get("chart_id", "default_chart")

    comp_key = f"{chart_type}_{chart_id}"

    st.markdown(
        f"<h4 style='font-size: 20px; font-weight: bold; margin-bottom: 0px;'>{title}</h4>",
        unsafe_allow_html=True,
    )
    st.write(" ")

    if chart_type == "bar":
        x_col = chart_info.get("x")
        y_col = chart_info.get("y")
        x_label = chart_info.get("x_label", "")
        y_label = chart_info.get("y_label", "")

        x_data = df[x_col].astype(str).tolist() if x_col and x_col in df.columns else []

        if isinstance(y_col, list):
            series_data = [
                {"name": col, "type": "bar", "data": df[col].tolist()}
                for col in y_col if col in df.columns
            ]
        else:
            series_data = [
                {
                    "name": y_col or "",
                    "type": "bar",
                    "data": df[y_col].tolist() if y_col and y_col in df.columns else []
                }
            ]

        options = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"show": True if isinstance(y_col, list) and len(y_col) > 1 else False},
            "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": {"type": "category", "data": x_data, "name": x_label, "nameLocation": "middle", "nameGap": 30},
            "yAxis": {"type": "value", "name": y_label},
            "series": series_data
        }
        st_echarts(options=options, height="300px", key=comp_key)

    elif chart_type == "echarts_multi_bar_gender":
        index_col = chart_info.get("index_col", "collect_date")
        columns_col = chart_info.get("columns_col", "gender")
        values_col = chart_info.get("values_col", "cnt")
        y_name = chart_info.get("y_name", "통행량")
        is_stacked = chart_info.get("stacked", True)

        pivot_df = df.pivot(index=index_col, columns=columns_col, values=values_col).fillna(0)

        x_data = [str(idx) for idx in pivot_df.index]
        legend_keys = list(pivot_df.columns)

        color_map = {
            "남성": "#60A5FA",
            "여성": "#F472B6",
            "m": "#60A5FA",
            "w": "#F472B6",
            "왼쪽": "#A865B5",
            "오른쪽": "#9fcc4b"
        }

        series_list = []
        for key in legend_keys:
            series_item = {
                "name": str(key),
                "type": "bar",
                "stack": "total" if is_stacked else None,
                "data": pivot_df[key].round(1).tolist(),
            }
            # 정의된 색상이 있다면 적용
            if str(key) in color_map:
                series_item["itemStyle"] = {"color": color_map[str(key)]}

            series_list.append(series_item)

        options = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"top": "0%", "data": [str(k) for k in legend_keys]},
            "grid": {"top": "15%", "left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value", "name": y_name},
            "series": series_list,
        }
        st_echarts(options=options, height="400px", key=comp_key)

    elif chart_type == "echarts_multi_bar_age":
        # index_col: x축 기준 (예: 일자 또는 시간), columns_col: 그룹화할 기준 (예: 성별), values_col: 값
        index_col = chart_info.get("index_col", "collect_date")
        columns_col = chart_info.get("columns_col", "age")
        values_col = chart_info.get("values_col", "cnt")
        y_name = chart_info.get("y_name", "통행량")
        is_stacked = chart_info.get("stacked", True)  # 기본값: 누적 바 차트 (False면 그룹 바 차트)

        # 데이터 피벗 (없는 데이터는 0으로 채움)
        pivot_df = df.pivot(index=index_col, columns=columns_col, values=values_col).fillna(0)

        x_data = [str(idx) for idx in pivot_df.index]
        legend_keys = list(pivot_df.columns)

        # 🎨 성별/항목별 맞춤 색상 맵 정의 (원하시는 HEX 코드로 자유롭게 변경 가능합니다)
        color_map = {
            "남성": "#60A5FA",  # 파란 계열
            "여성": "#F472B6",  # 핑크 계열
            "m": "#60A5FA",  # 영문 키값이 'm'인 경우 대비
            "w": "#F472B6",  # 영문 키값이 'w'인 경우 대비
            "왼쪽": "#A865B5",  # 연한 보라색 계열 (예: Lavender)
            "오른쪽": "#9fcc4b"  # 연한 연두색 계열 (예: Light Mint/Green)
        }

        # 각 그룹별 시리즈 생성 (color 속성 추가)
        series_list = []
        for key in legend_keys:
            series_item = {
                "name": str(key),
                "type": "bar",
                "stack": "total" if is_stacked else None,
                "data": pivot_df[key].round(1).tolist(),
            }
            # 정의된 색상이 있다면 적용
            if str(key) in color_map:
                series_item["itemStyle"] = {"color": color_map[str(key)]}

            series_list.append(series_item)

        options = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"top": "0%", "data": [str(k) for k in legend_keys]},
            "grid": {"top": "15%", "left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value", "name": y_name},
            "series": series_list,
        }
        st_echarts(options=options, height="400px", key=comp_key)

    elif chart_type == "echarts_multi_bar_direction":
        # index_col: x축 기준 (예: 일자 또는 시간), columns_col: 그룹화할 기준 (예: 성별), values_col: 값
        index_col = chart_info.get("index_col", "collect_date")
        columns_col = chart_info.get("columns_col", "direction")
        values_col = chart_info.get("values_col", "cnt")
        y_name = chart_info.get("y_name", "통행량")
        is_stacked = chart_info.get("stacked", True)  # 기본값: 누적 바 차트 (False면 그룹 바 차트)

        # 데이터 피벗 (없는 데이터는 0으로 채움)
        pivot_df = df.pivot(index=index_col, columns=columns_col, values=values_col).fillna(0)

        x_data = [str(idx) for idx in pivot_df.index]
        legend_keys = list(pivot_df.columns)

        # 🎨 성별/항목별 맞춤 색상 맵 정의 (원하시는 HEX 코드로 자유롭게 변경 가능합니다)
        color_map = {
            "남성": "#60A5FA",  # 파란 계열
            "여성": "#F472B6",  # 핑크 계열
            "m": "#60A5FA",  # 영문 키값이 'm'인 경우 대비
            "w": "#F472B6",  # 영문 키값이 'w'인 경우 대비
            "왼쪽": "#A865B5",  # 연한 보라색 계열 (예: Lavender)
            "오른쪽": "#9fcc4b"  # 연한 연두색 계열 (예: Light Mint/Green)
        }

        # 각 그룹별 시리즈 생성 (color 속성 추가)
        series_list = []
        for key in legend_keys:
            series_item = {
                "name": str(key),
                "type": "bar",
                "stack": "total" if is_stacked else None,
                "data": pivot_df[key].round(1).tolist(),
            }
            # 정의된 색상이 있다면 적용
            if str(key) in color_map:
                series_item["itemStyle"] = {"color": color_map[str(key)]}

            series_list.append(series_item)

        options = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"top": "0%", "data": [str(k) for k in legend_keys]},
            "grid": {"top": "15%", "left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value", "name": y_name},
            "series": series_list,
        }
        st_echarts(options=options, height="400px", key=comp_key)

    elif chart_type == "echarts_pie":
        name_col = chart_info.get("name_col", "name")
        val_col = chart_info.get("value_col", "cnt")
        semi_pie = chart_info.get("semi_pie", None)

        # 🛡️ 방어 로직: 데이터 유무 및 컬럼 체크
        if df is None or df.empty:
            st.warning(f"⚠️ '{title}' 차트에 표시할 데이터가 없습니다.")
            return

        if name_col not in df.columns or val_col not in df.columns:
            st.error(f"⚠️ 차트 생성 오류: 데이터프레임에 [{name_col}, {val_col}] 컬럼이 존재하지 않습니다.")
            return

        start_angle = 90
        end_angle = 450

        if semi_pie == "up":
            start_angle = 180
            end_angle = 0

        # 🎨 성별 맞춤 색상 맵 정의
        color_map = {
            "남성": "#60A5FA",  # 파란 계열
            "여성": "#F472B6",  # 핑크 계열
            "남": "#60A5FA",
            "여": "#F472B6",
            "m": "#60A5FA",  # 영문 키값 대비
            "w": "#F472B6",
            "왼쪽": "#A865B5",  # 연한 보라색 계열 (예: Lavender)
            "오른쪽": "#9fcc4b"  # 연한 연두색 계열 (예: Light Mint/Green)
        }

        # 데이터 세팅 (성별일 경우 지정 색상 적용, 그 외는 ECharts 기본 색상)
        chart_data = []
        for _, row in df.iterrows():
            item_name = str(row[name_col])
            item_val = int(row[val_col]) if pd.notnull(row[val_col]) else 0
            item_dict = {
                "name": item_name,
                "value": item_val
            }

            # 키값이 color_map에 들어있으면 해당 색상 적용
            if item_name in color_map:
                item_dict["itemStyle"] = {"color": color_map[item_name]}

            chart_data.append(item_dict)

        options = {
            "tooltip": {"trigger": "item", "formatter": "{b}: {c:,}명 ({d}%)"},
            "legend": {"bottom": "5%", "left": "center"},
            "series": [
                {
                    "name": title,
                    "type": "pie",
                    "radius": chart_info.get("radius", ["40%", "70%"]),
                    "center": ["50%", "50%"],
                    "startAngle": start_angle,
                    "endAngle": end_angle,
                    "avoidLabelOverlap": True,
                    "data": chart_data,
                }
            ],
        }

        st_echarts(options=options, height=chart_info.get("height", "400px"), key=comp_key)

    elif chart_type == "echarts_line":
        x_col = chart_info.get("x_col", "collect_hour")
        y_col = chart_info.get("y_col", "cnt")
        x_data = df[x_col].astype(str).tolist()
        y_data = df[y_col].tolist()

        option = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value"},
            "series": [{"data": y_data, "type": "line", "areaStyle": {}}],
        }
        st_echarts(options=option, height="400px", key=comp_key)

    elif chart_type == "echarts_multi_line":
        index_col = chart_info.get("index_col", "collect_hour")
        columns_col = chart_info.get("columns_col", "collect_day")
        values_col = chart_info.get("values_col", "cnt")
        y_name = chart_info.get("y_name", "통행량")

        # 🛡️ 방어 로직: 데이터 유무 및 컬럼 체크

        if df is None or df.empty:
            st.warning(f"⚠️ '{title}' 차트에 표시할 데이터가 없습니다.")
            return

        missing_cols = [col for col in [index_col, columns_col, values_col] if col not in df.columns]

        if missing_cols:
            st.error(f"⚠️ 차트 생성 오류: 데이터프레임에 다음 컬럼이 존재하지 않습니다: {missing_cols}")

            return

        try:
            pivot_df = df.pivot(index=index_col, columns=columns_col, values=values_col).fillna(0)
            days_order = ['월', '화', '수', '목', '금', '토', '일']
            if any(col in days_order for col in pivot_df.columns):
                legend_keys = [d for d in days_order if d in pivot_df.columns]
            else:
                legend_keys = list(pivot_df.columns)

            x_data = [f"{int(h):02d}시" if str(h).isdigit() else str(h) for h in pivot_df.index]

            # 🎨 성별 맞춤 색상 맵 정의

            color_map = {
                "남성": "#60A5FA",  # 파란 계열
                "여성": "#F472B6",  # 핑크 계열
                "남": "#60A5FA",
                "여": "#F472B6",
                "m": "#60A5FA",
                "w": "#F472B6",
                "왼쪽": "#A865B5",  # 연한 보라색 계열 (예: Lavender)
                "오른쪽": "#9fcc4b"  # 연한 연두색 계열 (예: Light Mint/Green)
            }

            # 각 그룹별 시리즈 생성 (성별 색상 매핑 포함)
            series_list = []
            for key in legend_keys:
                series_item = {
                    "name": str(key),
                    "type": "line",
                    "data": pivot_df[key].round(1).tolist()
                }

                # 키가 성별 관련 단어일 경우 itemStyle 적용
                if str(key) in color_map:
                    series_item["itemStyle"] = {"color": color_map[str(key)]}
                    series_item["lineStyle"] = {"color": color_map[str(key)]}
                series_list.append(series_item)

            option = {
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
                "legend": {"top": "0%", "data": [str(k) for k in legend_keys]},
                "grid": {"top": "15%", "left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
                "xAxis": {"type": "category", "boundaryGap": False, "data": x_data},
                "yAxis": {"type": "value", "name": y_name},
                "series": series_list,
            }

            st_echarts(options=option, height="400px", key=comp_key)

        except Exception as e:
            st.error(f"⚠️ '{title}' 차트 렌더링 중 오류가 발생했습니다: {str(e)}")

    elif chart_type == "echarts_icon_bar":

        # 🛡️ 방어 로직: 데이터 유무 확인
        if df is None or df.empty:
            st.warning(f"⚠️ '{title}' 차트에 표시할 데이터가 없습니다.")
            return
        name_col = chart_info.get("name_col", "class")
        val_col = chart_info.get("value_col", "cnt")

        if name_col not in df.columns or val_col not in df.columns:
            st.error(f"⚠️ 차트 생성 오류: 데이터프레임에 [{name_col}, {val_col}] 컬럼이 존재하지 않습니다.")
            return
        y_categories = []
        chart_values = []
        # 이모지와 매핑된 디스플레이 이름
        display_map = {
            "bycicle": "🚲 자전거",
            "bicycle": "🚲 자전거",
            "stroller": "👶 유모차",
            "dog": "🐕 애완견"
        }

        for _, row in df.iterrows():
            cls_name = str(row[name_col]).lower()
            try:
                val = int(row[val_col]) if row[val_col] is not None else 0
            except (ValueError, TypeError):
                val = 0
            display_name = display_map.get(cls_name, str(row[name_col]))
            y_categories.append(display_name)
            chart_values.append(val)

        options = {
            "title": {"text": title, "textStyle": {"fontSize": 16}},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "grid": {"containLabel": True, "left": 10, "right": 30, "top": "15%", "bottom": "10%"},
            "xAxis": {
                "type": "value",
                "splitLine": {"show": False},
                "axisLabel": {"show": True},
            },
            "yAxis": {
                "type": "category",
                "data": y_categories,
                "inverse": True,
                "axisLine": {"show": True},
                "axisTick": {"show": False},
                "axisLabel": {"margin": 15, "fontSize": 14, "fontWeight": "bold"},
            },
            "series": [
                {
                    "type": "bar",
                    "data": chart_values,
                    "barWidth": "40%",
                    "label": {
                        "show": True,
                        "position": "right",
                        "formatter": "{c}",
                        "fontWeight": "bold",
                        "fontSize": 20
                    },
                    "itemStyle": {
                        "color": "#3B82F6",
                        "borderRadius": [0, 4, 4, 0]  # 막대 끝을 둥글게 처리
                    }
                }
            ],
        }

        st_echarts(options=options, height=chart_info.get("height", "350px"), key=comp_key)


def render_chart_grid(
        charts: List[Dict[str, Any]],
        cols_per_row: int = 3,
        ratios: List[float] = None,
):
    """차트 리스트를 받아 지정한 열 개수나 비율에 맞춰 자동으로 행을 나누어 배치합니다."""
    for i in range(0, len(charts), cols_per_row):
        row_charts = charts[i: i + cols_per_row]
        cols = st.columns(
            ratios if ratios and len(ratios) == len(row_charts) else len(row_charts),
            vertical_alignment="bottom"
        )
        for idx, chart in enumerate(row_charts):
            with cols[idx]:
                render_chart_item(chart)


# ------------------------------------------------------------------------------
# 2. 메인 페이지 로직
# ------------------------------------------------------------------------------

st.logo(
    "images/logo_wide.png",
    size="large",
    link="https://report.realtargeting.co.kr",
)

conn = st.connection("mysql", type="sql")

st.subheader("통합 보고서", divider="blue")

user_id = st.session_state.get("user_id")
work_list = st.session_state.get("work_list", [])

if not user_id or not work_list:
    st.error("⚠️ 로그인 정보가 없거나 열람 가능한 지점이 없습니다. 사이드바에서 먼저 로그인해 주세요.")
else:

    location_options = [
        item.get("측정지점") or item.get("memo") or item.get("주소") or item.get(
            "location") or f"지점 {item.get('작업번호', item.get('work_no'))}"
        for item in work_list
    ]

    default_work_no = st.session_state.get("selected_work_no")
    default_idx = 0

    if default_work_no is not None:
        for idx, item in enumerate(work_list):
            item_work_no = item.get("작업번호") or item.get("work_no")
            if str(item_work_no) == str(default_work_no):
                default_idx = idx
                break

    col1, col2 = st.columns([8, 2])

    with col1:
        selected_location = st.selectbox(
            "📍 측정지점 선택",
            options=location_options,
            index=default_idx,
            key="sb_dashboard_location"
        )

    selected_work_info = work_list[location_options.index(selected_location)]
    selected_work_no = selected_work_info.get("작업번호") or selected_work_info.get("work_no")

    if user_id in ['notreal', 'admin']:
        variables = {'work_no': selected_work_no}
        qr_special = """ select user_id from rt_collect_info where work_no = {work_no}"""
        user_id = conn.query(qr_special.format(**variables), ttl=0).iloc[0, 0]

    with col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)

        st.download_button(
            label="💾 PDF 다운로드",
            data=lambda: get_pdf_bytes(user_id, selected_work_no),
            file_name=f"리얼타겟팅 보고서_{user_id}_{selected_work_no}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
            disabled=False
        )

    st.session_state["selected_work_no"] = selected_work_no
    start_date_raw = format_date_str(selected_work_info.get("시작일자") or selected_work_info.get("start_date"))
    end_date_raw = format_date_str(selected_work_info.get("종료일자") or selected_work_info.get("end_date"))
    start_time_raw = format_time_str(selected_work_info.get("시작시간") or selected_work_info.get("start_time"))
    end_time_raw = format_time_str(selected_work_info.get("종료시간") or selected_work_info.get("end_time"))

    start_date_str = str(start_date_raw).replace("-", "").strip()
    end_date_str = str(end_date_raw).replace("-", "").strip()

    start_time_clean = str(start_time_raw).replace(":", "").strip()
    end_time_clean = str(end_time_raw).replace(":", "").strip()

    start_time_str = start_time_clean[:2].zfill(2) if start_time_clean else ""
    end_time_str = end_time_clean[:2].zfill(2) if end_time_clean else ""

    st.write(" ")

    # 지도 및 기본 정보 표시
    render_location_map(selected_work_info)
    st.write(" ")

    # ------------------------------------------------------------------------------
    # 🌟 [추가 기능] 측정 기간 일자별 날씨 정보 연동 영역
    # ------------------------------------------------------------------------------
    st.subheader("🌦️ 측정 기간 일자별 날씨 정보", divider="gray")
    st.write(" ")

    lat_val = selected_work_info.get("위도") or selected_work_info.get("latitude")
    lng_val = selected_work_info.get("경도") or selected_work_info.get("longitude")

    if lat_val is not None and lng_val is not None:
        try:
            lat_float = float(lat_val)
            lng_float = float(lng_val)

            if len(start_date_str) == 8 and len(end_date_str) == 8:
                api_start_date = f"{start_date_str[:4]}-{start_date_str[4:6]}-{start_date_str[6:]}"
                api_end_date = f"{end_date_str[:4]}-{end_date_str[4:6]}-{end_date_str[6:]}"

                # 종료일 미래 날짜 방지 로직
                max_available_date = date.today() - timedelta(days=1)
                max_available_date = str(max_available_date).replace("-", "").strip()

                try:

                    if end_date_str > max_available_date:
                        api_end_date = f"{max_available_date[:4]}-{max_available_date[4:6]}-{max_available_date[6:]}"

                        if start_date_str > max_available_date:
                            api_start_date = api_end_date

                except Exception:
                    pass

                # 3. Open-Meteo API 호출 함수
                @st.cache_data
                def fetch_weather_range(lat, lon, start, end):
                    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start}&end_date={end}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&timezone=Asia%2FSeoul"
                    try:
                        res = requests.get(url, timeout=10)
                        if res.status_code == 200:
                            return res.json()
                    except Exception:
                        pass
                    return None


                # WMO 날씨 코드를 아이콘 및 한글 상태로 매핑
                def get_weather_icon(code):
                    if code == 0:
                        return "☀️ 맑음"
                    elif code in [1, 2, 3]:
                        return "⛅ 구름/흐림"
                    elif code in [45, 48]:
                        return "🌫️ 안개"
                    elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67]:
                        return "🌧️ 비"
                    elif code in [71, 73, 75, 77, 85, 86]:
                        return "❄️ 눈"
                    elif code >= 95:
                        return "⛈️ 천둥번개"
                    else:
                        return "🌡️ 기타"

                weather_data = fetch_weather_range(lat_float, lng_float, api_start_date, api_end_date)

                if weather_data and "daily" in weather_data:
                    daily = weather_data["daily"]
                    weather_df = pd.DataFrame({
                        "날짜": daily["time"],
                        "최고기온": daily["temperature_2m_max"],
                        "최저기온": daily["temperature_2m_min"],
                        "강수량": daily["precipitation_sum"],
                        "날씨코드": daily["weathercode"]
                    })
                    weather_df["상태"] = weather_df["날씨코드"].apply(get_weather_icon)

                    # 일자별 카드 형태로 그리드 표시 (최대 7일씩 행 분할 등 처리)
                    # 일자별 카드 형태로 그리드 표시 (최대 7일씩 행 분할 등 처리)
                    num_days = len(weather_df)
                    if num_days > 0:
                        # 💡 st.expander를 활용해 기본적으로 접혀(expanded=False) 있도록 구현
                        with st.expander(f"📅 일자별 상세 날씨 정보 보기 (총 {num_days}일)", expanded=False):
                            # 화면 너비에 맞게 최대 7열씩 나누어 출력
                            cols = st.columns(min(num_days, 7))
                            for idx, row in weather_df.iterrows():
                                col_idx = idx % 7
                                if col_idx == 0 and idx > 0:
                                    cols = st.columns(min(num_days - idx, 7))

                                with cols[col_idx]:
                                    icon_part = row["상태"].split()[0]
                                    text_part = row["상태"].split()[1] if len(row["상태"].split()) > 1 else ""
                                    st.markdown(
                                        f"""
                                                        <div style="
                                                            background-color: #f8f9fa;
                                                            border: 1px solid #e2e8f0;
                                                            border-radius: 6px;
                                                            padding: 10px;
                                                            text-align: center;
                                                            margin-bottom: 10px;
                                                        ">
                                                            <div style="font-size: 13px; font-weight: bold; color: #475569;">{row['날짜']}</div>
                                                            <div style="font-size: 24px; margin: 4px 0;">{icon_part}</div>
                                                            <div style="font-size: 12px; color: #64748b; margin-bottom: 6px;">{text_part}</div>
                                                            <div style="font-size: 13px; color: #ef4444;">최고: {row['최고기온']}°C</div>
                                                            <div style="font-size: 13px; color: #3b82f6;">최저: {row['최저기온']}°C</div>
                                                            <div style="font-size: 12px; color: #0f172a; margin-top: 4px;">💧 {row['강수량']}mm</div>
                                                        </div>
                                                        """,
                                        unsafe_allow_html=True
                                    )

                        # 기온 변화 추이 시각화 차트 추가
                        st.write(" ")
                        # ------------------------------------------------------------------------------
                        # 📈 기온(선) 및 강수량(막대) 멀티 차트 렌더링 (ECharts 듀얼축 활용)
                        # ------------------------------------------------------------------------------
                        st.write(" ")

                        x_data = weather_df["날짜"].tolist()
                        max_temp = weather_df["최고기온"].tolist()
                        min_temp = weather_df["최저기온"].tolist()
                        precipitation = weather_df["강수량"].tolist()

                        weather_chart_options = {
                            "tooltip": {
                                "trigger": "axis",
                                "axisPointer": {"type": "cross"}
                            },
                            "legend": {
                                "data": ["최고기온", "최저기온", "강수량"],
                                "top": "0%"
                            },
                            "grid": {
                                "top": "18%",
                                "left": "5%",
                                "right": "5%",
                                "bottom": "10%",
                                "containLabel": True
                            },
                            "xAxis": [
                                {
                                    "type": "category",
                                    "data": x_data,
                                    "axisPointer": {"type": "shadow"}
                                }
                            ],
                            "yAxis": [
                                {
                                    "type": "value",
                                    "name": "기온 (°C)",
                                    "position": "left",
                                    "axisLabel": {"formatter": "{value} °C"}
                                },
                                {
                                    "type": "value",
                                    "name": "강수량 (mm)",
                                    "position": "right",
                                    "splitLine": {"show": False},  # 배경 격자선 중복 방지
                                    "axisLabel": {"formatter": "{value} mm"}
                                }
                            ],
                            "series": [
                                {
                                    "name": "최고기온",
                                    "type": "line",
                                    "data": max_temp,
                                    "itemStyle": {"color": "#ef4444"},  # 빨간 계열 (최고기온)
                                    "lineStyle": {"width": 2}
                                },
                                {
                                    "name": "최저기온",
                                    "type": "line",
                                    "data": min_temp,
                                    "itemStyle": {"color": "#3b82f6"},  # 파란 계열 (최저기온)
                                    "lineStyle": {"width": 2}
                                },
                                {
                                    "name": "강수량",
                                    "type": "bar",
                                    "yAxisIndex": 1,  # 우측 Y축 사용
                                    "data": precipitation,
                                    "itemStyle": {
                                        "color": "#93c5fd",  # 연한 하늘색 막대
                                        "borderRadius": [4, 4, 0, 0]
                                    },
                                    "barWidth": "35%"
                                }
                            ]
                        }

                        st_echarts(options=weather_chart_options, height="500px", key="weather_multi_chart")
                        # 📌 출처 및 면책 안내 문구 추가
                        st.markdown(
                            """
                            <div style="
                                font-size: 12px; 
                                color: #64748b; 
                                text-align: right; 
                                margin-top: 4px; 
                                margin-bottom: 16px;
                            ">
                                📊 <b>기상 데이터 출처:</b> Open-Meteo API (기상 재분석 모델)<br>
                                ⚠️ 본 기상 정보는 글로벌 기상 모델을 기반으로 산출된 값으로, 실제 기상청 공식 실측값과는 다소 차이가 있을 수 있습니다.
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.info("ℹ️ 해당 측정 기간 내 조회된 날씨 데이터가 없습니다.")
                else:
                    st.warning("⚠️ 지정된 날짜 및 위치의 기상 데이터를 불러오지 못했습니다.")
            else:
                st.info("ℹ️ 측정 시작일자 또는 종료일자 형식(YYYYMMDD)이 올바르지 않습니다.")
        except Exception as e:
            st.warning(f"⚠️ 날씨 정보를 불러오는 중 오류가 발생했습니다: {e}")
    else:
        st.info("ℹ️ 해당 지점의 위도/경도 정보가 없어 날씨 정보를 불러올 수 없습니다.")

    all_comments = fetch_all_comments(user_id, selected_work_no)

    st.write(" ")
    render_section_header("📅", "분석 요약", "Summary")
    st.write(" ")

    variables1 = {
        "id": user_id,
        "work_no": selected_work_no,
        "start_date_str": start_date_str,
        "end_date_str": end_date_str,
        "start_time_str": start_time_str,
        "end_time_str": end_time_str,
    }

    # --------------------------------------------------------------------------
    # A. Metric 상단 지표 조회 및 렌더링
    # --------------------------------------------------------------------------
    qr_h1 = """SELECT sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 """
    qr_h2 = """SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date) t1"""
    qr_h3 = """SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' and (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date, rca.collect_hour) t1"""
    qr_h4 = """SELECT round(avg(t1.cnt)/60) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date, rca.collect_hour) t1"""
    qr_h5 = """SELECT IFNULL(ROUND(AVG(t1.cnt)), 0) AS weekday_avg FROM (SELECT rca.collect_date AS collect_date, IFNULL(SUM(rca.collect_cnt), 0) AS cnt FROM rt_collect_summary rca JOIN rt_calendar c ON rca.collect_date = c.dt WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 AND c.anal_gubun = 'Weekday' GROUP BY rca.collect_date) t1"""
    qr_h6 = """SELECT IFNULL(ROUND(AVG(t1.cnt)), 0) AS weekend_avg FROM (SELECT rca.collect_date AS collect_date, IFNULL(SUM(rca.collect_cnt), 0) AS cnt FROM rt_collect_summary rca JOIN rt_calendar c ON rca.collect_date = c.dt WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 AND c.anal_gubun = 'Weekend' GROUP BY rca.collect_date) t1"""
    qr_h7 = """SELECT avg(rca.stay_time) as stay_time FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.stay_time <> 99999 AND rca.del_yn = 0 """
    qr_h8 = """SELECT AVG(t1.hourly_avg_stay) as stay_time FROM (SELECT rca.collect_hour, AVG(rca.stay_time) AS hourly_avg_stay FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') AND rca.stay_time <> 99999 AND rca.del_yn = 0 GROUP BY rca.collect_hour) t1;"""

    # 1. 단 1회 통합 조회 쿼리 실행
    qr_all = """
    SELECT 
        rca.collect_date, 
        rca.collect_hour, 
        rca.collect_cnt, 
        rca.stay_time,
        c.anal_gubun
    FROM rt_collect_summary rca 
    LEFT JOIN rt_calendar c ON rca.collect_date = c.dt
    WHERE rca.user_id = '{id}' 
      AND rca.work_no = {work_no} 
      AND rca.collect_date >= '{start_date_str}' 
      AND rca.collect_date <= '{end_date_str}' 
      AND rca.collect_hour >= '{start_time_str}' 
      AND rca.collect_hour < '{end_time_str}' 
      AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
      AND rca.del_yn = 0
    """

    df = conn.query(qr_all.format(**variables1), ttl=0)

    # 2. 데이터가 없을 경우 기본값 설정 및 Pandas 연산
    if df.empty:
        h1_cnt, h2_avg, h3_avg, h4_avg, h5_weekday, h6_weekend, h7_stay, h8_stay = 0, 0, 0, 0, 0, 0, 0.0, 0.0
        avg_daily_cnt = 0.0
    else:
        # [h1] 전체 총 통행량
        h1_cnt = int(df["collect_cnt"].sum())

        # [h2] 일평균 통행량 (등급 판정용 겸용)
        df_daily = df.groupby("collect_date")["collect_cnt"].sum().reset_index()
        avg_daily_cnt = float(df_daily["collect_cnt"].mean()) if not df_daily.empty else 0.0
        h2_avg = round(avg_daily_cnt)

        # [h3] 시간대별 일평균 통행량
        df_hourly = df.groupby(["collect_date", "collect_hour"])["collect_cnt"].sum().reset_index()
        h3_avg = round(df_hourly["collect_cnt"].mean()) if not df_hourly.empty else 0

        # [h4] 분당 통행량 평균
        h4_avg = round(h3_avg / 60) if h3_avg > 0 else 0

        # [h5] 평일 평균
        df_weekday = df[df["anal_gubun"] == "Weekday"]
        h5_weekday = round(
            df_weekday.groupby("collect_date")["collect_cnt"].sum().mean()) if not df_weekday.empty else 0

        # [h6] 주말 평균
        df_weekend = df[df["anal_gubun"] == "Weekend"]
        h6_weekend = round(
            df_weekend.groupby("collect_date")["collect_cnt"].sum().mean()) if not df_weekend.empty else 0

        # [h7] 체류시간 평균 (99999 제외)
        df_stay = df[df["stay_time"] != 99999]
        h7_stay = float(df_stay["stay_time"].mean()) if not df_stay.empty else 0.0

        # [h8] 시간당 체류시간 평균의 평균 (99999 제외)
        if not df_stay.empty:
            h8_stay = float(df_stay.groupby("collect_hour")["stay_time"].mean().mean()) if not df_stay.empty else 0.0
        else:
            h8_stay = 0.0

    # 2. 등급 판정 및 색상 설정 로직
    if avg_daily_cnt >= 10000:
        grade = "S"
        grade_color = "#FF4B4B"  # 빨강
    elif avg_daily_cnt >= 5000:
        grade = "A"
        grade_color = "#FF8C00"  # 주황
    elif avg_daily_cnt >= 1000:
        grade = "B"
        grade_color = "#FFD000"  # 황갈/골드
    elif avg_daily_cnt >= 500:
        grade = "C"
        grade_color = "#1E88E5"  # 파랑
    else:
        grade = "D"
        grade_color = "#8E44AD"  # 보라

    # 3. 등급 시각화 영역 (HTML/CSS로 색상 반영)
    col_g1, col_g2 = st.columns([1, 2.5])

    with col_g1:
        st.markdown(
            f"""
            <div style="
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 10px;
                padding: 12px;
                text-align: center;
                height: 150px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="text-align: left; font-size: 20px; color: #6c757d; font-weight: bold; margin-bottom: 2px; margin-left: 10px;">
                    트래픽 등급
                </div>      
                <div style="font-size: 50px; font-weight: 900; color: {grade_color}; line-height: 1.1;">
                    {grade}
                </div>          
            </div>            
            """,
            unsafe_allow_html=True,
        )

    with col_g2:
        st.markdown(
            """
            <div style="
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 10px;
                padding: 14px 18px;
                height: 150px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="text-align: right; font-size: 14px; font-weight: bold; color: #495057; margin-bottom: 8px;">
                    (기준 : 하루 평균)
                </div>                
                <div style="font-size: 20px; font-weight: 600; line-height: 1.6; text-align: center;">
                    <span style="color: #FF4B4B;">S</span> : 1만명 이상 &nbsp;&nbsp;|&nbsp;&nbsp;
                    <span style="color: #FF8C00;">A</span> : 5천명 이상 &nbsp;&nbsp;|&nbsp;&nbsp;
                    <span style="color: #FFD000;">B</span> : 1천명 이상 &nbsp;&nbsp;|&nbsp;&nbsp;
                    <span style="color: #1E88E5;">C</span> : 500명 이상 &nbsp;&nbsp;|&nbsp;&nbsp;
                    <span style="color: #8E44AD;">D</span> : 100명 이하
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write(" ")
    st.write(" ")
    st.write(" ")

    # 5. 기존 함수 규격에 맞게 1행짜리 DataFrame으로 포장해서 전달
    render_metric_cards(
        pd.DataFrame({"val": [h1_cnt]}),
        pd.DataFrame({"val": [h2_avg]}),
        pd.DataFrame({"val": [h3_avg]}),
        pd.DataFrame({"val": [h4_avg]}),
        pd.DataFrame({"val": [h5_weekday]}),
        pd.DataFrame({"val": [h6_weekend]}),
        pd.DataFrame({"val": [h7_stay]}),
        pd.DataFrame({"val": [h8_stay]})
    )
    st.write(" ")

    # ------------------------------------------------------------------------------
    # 1. 공통 데이터 단 2회 조회 (DB 부하 최소화)
    # ------------------------------------------------------------------------------

    # [데이터셋 1] 메트릭 및 대다수 차트용 공통 원본 데이터
    qr_base_all = """
    SELECT 
        rca.collect_date, 
        rca.collect_hour, 
        rca.collect_day,
        rca.gender, 
        rca.age, 
        rca.direction, 
        rca.class,
        rca.collect_cnt, 
        rca.stay_time,
        c.anal_gubun
    FROM rt_collect_summary rca 
    LEFT JOIN rt_calendar c ON rca.collect_date = c.dt
    WHERE rca.user_id = '{id}' 
      AND rca.work_no = {work_no} 
      AND rca.collect_date >= '{start_date_str}' 
      AND rca.collect_date <= '{end_date_str}' 
      AND rca.collect_hour >= '{start_time_str}' 
      AND rca.collect_hour < '{end_time_str}' 
      AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
      AND rca.del_yn = 0
    """

    # [데이터셋 2] 기타 객체(자전거, 유모차, 애완견) 전용 데이터
    qr_base_etc = """
    SELECT 
        rca.collect_date, 
        rca.collect_hour, 
        rca.class, 
        rca.collect_cnt, 
        rca.stay_time
    FROM rt_collect_summary rca 
    WHERE rca.user_id = '{id}' 
      AND rca.work_no = {work_no} 
      AND rca.collect_date >= '{start_date_str}' 
      AND rca.collect_date <= '{end_date_str}' 
      AND rca.collect_hour >= '{start_time_str}' 
      AND rca.collect_hour < '{end_time_str}' 
      AND rca.class IN ('bycicle', 'stroller', 'dog') 
      AND rca.del_yn = 0 
      AND rca.stay_time <> 99999
    """

    # DB 쿼리 실행 (총 2회)
    df_base = conn.query(qr_base_all.format(**variables1), ttl=0)
    df_etc = conn.query(qr_base_etc.format(**variables1), ttl=0)

    # ------------------------------------------------------------------------------
    # 2. 메트릭(Metric) 및 등급 판정 연산 (Pandas 활용)
    # ------------------------------------------------------------------------------
    if df_base.empty:
        h1_cnt, h2_avg, h3_avg, h4_avg, h5_weekday, h6_weekend, h7_stay, h8_stay = 0, 0, 0, 0, 0, 0, 0.0, 0.0
        avg_daily_cnt = 0.0
    else:
        h1_cnt = int(df_base["collect_cnt"].sum())

        # 일평균 통행량 (등급용)
        df_daily = df_base.groupby("collect_date")["collect_cnt"].sum().reset_index()
        avg_daily_cnt = float(df_daily["collect_cnt"].mean()) if not df_daily.empty else 0.0
        h2_avg = round(avg_daily_cnt)

        # 시간대별 일평균 통행량
        df_hourly = df_base.groupby(["collect_date", "collect_hour"])["collect_cnt"].sum().reset_index()
        h3_avg = round(df_hourly["collect_cnt"].mean()) if not df_hourly.empty else 0

        # 분당 통행량 평균
        h4_avg = round(h3_avg / 60) if h3_avg > 0 else 0

        # 평일/주말 평균
        df_weekday = df_base[df_base["anal_gubun"] == "Weekday"]
        h5_weekday = round(
            df_weekday.groupby("collect_date")["collect_cnt"].sum().mean()) if not df_weekday.empty else 0

        df_weekend = df_base[df_base["anal_gubun"] == "Weekend"]
        h6_weekend = round(
            df_weekend.groupby("collect_date")["collect_cnt"].sum().mean()) if not df_weekend.empty else 0

        # 체류시간 평균 (99999 제외)
        df_stay = df_base[df_base["stay_time"] != 99999]
        h7_stay = float(df_stay["stay_time"].mean()) if not df_stay.empty else 0.0
        h8_stay = float(df_stay.groupby("collect_hour")["stay_time"].mean().mean()) if not df_stay.empty else 0.0


    # ------------------------------------------------------------------------------
    # 3. 차트용 데이터프레임 가공 (Pandas)
    # ------------------------------------------------------------------------------
    def format_date_str(date_str):
        if pd.isna(date_str) or len(str(date_str)) != 8:
            return date_str
        return f"{date_str[4:6]}/{date_str[6:]}"


    df_base["formatted_date"] = df_base["collect_date"].apply(format_date_str)
    df_etc["formatted_date"] = df_etc["collect_date"].apply(format_date_str)
    df_stay_valid = df_base[df_base["stay_time"] != 99999].copy()

    # 1. 일자별 통행량
    df_date = df_base.groupby("formatted_date")["collect_cnt"].sum().reset_index()
    df_date.columns = ["collect_date", "cnt"]


    # 2. 시간대별 평균 통행량 (주중/주말/전체)
    def get_hourly_trend(subset_df):
        if subset_df.empty:
            return pd.DataFrame(columns=["collect_hour", "cnt"])
        t1 = subset_df.groupby(["collect_date", "collect_hour"])["collect_cnt"].sum().reset_index(name="cnt")
        return t1.groupby("collect_hour")["cnt"].mean().round().reset_index()


    df_w_trend = get_hourly_trend(df_base[df_base["anal_gubun"] == "Weekday"])
    df_w_trend["gubun"] = "주중"
    df_we_trend = get_hourly_trend(df_base[df_base["anal_gubun"] == "Weekend"])
    df_we_trend["gubun"] = "주말"
    df_tot_trend = get_hourly_trend(df_base)
    df_tot_trend["gubun"] = "전체"
    df_hour_ww = pd.concat([df_w_trend, df_we_trend, df_tot_trend], ignore_index=True)

    # 3. 일자별 평균 체류시간
    df_date_stay = df_stay_valid.groupby("formatted_date")["stay_time"].mean().reset_index()
    df_date_stay.columns = ["collect_date", "cnt"]

    # 4. 요일별/시간대별 통행량 및 체류시간
    day_map = {'Sun': '일', 'Mon': '월', 'Tue': '화', 'Wed': '수', 'Thu': '목', 'Fri': '금', 'Sat': '토'}
    day_order = {'일': 1, '월': 2, '화': 3, '수': 4, '목': 5, '금': 6, '토': 7}
    df_base['collect_day_kr'] = df_base['collect_day'].map(day_map)
    df_stay_valid['collect_day_kr'] = df_stay_valid['collect_day'].map(day_map)

    df_day_hour = df_base.groupby(["collect_hour", "collect_day_kr"], as_index=False)["collect_cnt"].mean()
    df_day_hour.columns = ["collect_hour", "collect_day", "cnt"]

    df_dh_stay = df_stay_valid.groupby(["collect_hour", "collect_day_kr"], as_index=False)["stay_time"].mean()
    df_dh_stay["stay_time"] = df_dh_stay["stay_time"].round(1)
    df_dh_stay.columns = ["collect_hour", "collect_day", "stay_time"]

    # 5. 성별 관련 차트 데이터
    df_base_gender = df_stay_valid.copy()
    df_base_gender["gender_kr"] = df_base_gender["gender"].map({"male": "남성", "female": "여성"})

    df_gender_day = df_base_gender.groupby(["formatted_date", "gender_kr"], as_index=False)["collect_cnt"].sum()
    df_gender_day.columns = ["collect_date", "gender", "cnt"]

    df_gender_pie = df_base.groupby("gender")["collect_cnt"].sum().reset_index()
    df_gender_pie["gender"] = df_gender_pie["gender"].map({"male": "남성", "female": "여성"})
    df_gender_pie.columns = ["gender", "cnt"]

    df_gender_hour = df_base.groupby(["collect_hour", "gender"], as_index=False)["collect_cnt"].mean()
    df_gender_hour.columns = ["collect_hour", "gender", "cnt"]  # 먼저 컬럼명을 'cnt'로 변경
    df_gender_hour["cnt"] = df_gender_hour["cnt"].round()  # 그 후 반올림 수행
    df_gender_hour["gender"] = df_gender_hour["gender"].map({"male": "남성", "female": "여성"})

    df_gender_hour_stay = df_stay_valid.groupby(["collect_hour", "gender"], as_index=False)["stay_time"].mean()
    df_gender_hour_stay["stay_time"] = df_gender_hour_stay["stay_time"].round(1)
    df_gender_hour_stay["gender"] = df_gender_hour_stay["gender"].map({"male": "남성", "female": "여성"})
    df_gender_hour_stay.columns = ["collect_hour", "gender", "stay_time"]

    # 6. 연령대 관련 차트 데이터 수정
    df_age_day = df_base_gender.groupby(["formatted_date", "age"], as_index=False)["collect_cnt"].sum()
    df_age_day.columns = ["collect_date", "age", "cnt"]  # 컬럼명 확실하게 고정

    df_age_pie = df_base.groupby("age", as_index=False)["collect_cnt"].sum()
    df_age_pie.columns = ["age", "cnt"]  # [age, cnt] 보장

    df_age_hour = df_base.groupby(["collect_hour", "age"], as_index=False)["collect_cnt"].sum()
    df_age_hour.columns = ["hour", "age", "cnt"]

    df_age_hour_stay = df_stay_valid.groupby(["collect_hour", "age"], as_index=False)["stay_time"].mean()
    df_age_hour_stay["stay_time"] = df_age_hour_stay["stay_time"].round(1)
    df_age_hour_stay.columns = ["hour", "age", "stay_time"]

    # 6. 방향별 관련 차트 데이터 수정
    df_dir_day = df_base_gender.groupby(["formatted_date", "direction"], as_index=False)["collect_cnt"].sum()
    df_dir_day.columns = ["collect_date", "direction", "cnt"]

    df_dir_pie = df_base.groupby("direction", as_index=False)["collect_cnt"].sum()
    df_dir_pie.columns = ["direction", "cnt"]  # [direction, cnt] 보장

    df_dir_hour = df_base.groupby(["collect_hour", "direction"], as_index=False)["collect_cnt"].sum()
    df_dir_hour.columns = ["collect_hour", "direction", "cnt"]

    # 7. 기타 객체(자전거, 유모차, 애완견) 차트 데이터 수정
    df_etc_pie = df_etc.groupby("class", as_index=False)["collect_cnt"].sum()
    df_etc_pie.columns = ["class", "cnt"]  # [class, cnt] 보장
    # 대소문자 매핑 (필요시)
    df_etc_pie["class"] = df_etc_pie["class"].map({"bycicle": "bycicle", "stroller": "stroller", "dog": "dog"})

    df_etc_hour = df_etc.groupby(["collect_hour", "class"], as_index=False)["collect_cnt"].sum()
    df_etc_hour.columns = ["collect_hour", "class", "cnt"]
    df_etc_hour["class"] = df_etc_hour["class"].map({"bycicle": "Bycicle", "stroller": "Stroller", "dog": "Dog"})

    # ------------------------------------------------------------------------------
    # 4. 차트 딕셔너리 정의 (가공된 DataFrame 주입)
    # ------------------------------------------------------------------------------
    chart_date = {"chart_id": "date_traffic", "title": "일자별 통행량", "type": "bar", "df": df_date, "x": "collect_date",
                  "y": "cnt", "x_label": "일자", "y_label": "통행량"}
    chart_hour_weekday_weekend = {"chart_id": "hour_weekday_weekend", "title": "시간대별 평균 통행량",
                                  "type": "echarts_multi_line", "df": df_hour_ww, "index_col": "collect_hour",
                                  "columns_col": "gubun", "values_col": "cnt", "y_name": "통행량"}
    chart_date_stay = {"chart_id": "date_stay", "title": "일자별 평균 체류시간", "type": "bar", "df": df_date_stay,
                       "x": "collect_date", "y": "cnt", "x_label": "일자", "y_label": "평균 체류시간"}
    chart_day_hour = {"chart_id": "day_hour_traffic", "title": "요일별/시간대별 평균 통행량", "type": "echarts_multi_line",
                      "df": df_day_hour, "index_col": "collect_hour", "columns_col": "collect_day", "values_col": "cnt",
                      "y_name": "통행량"}
    chart_day_hour_stay_time = {"chart_id": "day_hour_stay", "title": "요일별/시간대별 평균 체류시간", "type": "echarts_multi_line",
                                "df": df_dh_stay, "index_col": "collect_hour", "columns_col": "collect_day",
                                "values_col": "stay_time", "y_name": "체류시간(초)"}

    chart_gender_day = {"title": "일자별 성별 통행량 분석", "type": "echarts_multi_bar_gender", "df": df_gender_day,
                        "index_col": "collect_date", "columns_col": "gender", "values_col": "cnt", "y_name": "통행량(명)",
                        "stacked": True}
    chart_gender = {"chart_id": "gender_pie", "title": "성별 통행량", "type": "echarts_pie", "df": df_gender_pie,
                    "name_col": "gender", "value_col": "cnt", "semi_pie": None}
    chart_gender_hour = {"chart_id": "gender_hour", "title": "성별/시간대별 평균 통행량", "type": "echarts_multi_line",
                         "df": df_gender_hour, "index_col": "collect_hour", "columns_col": "gender",
                         "values_col": "cnt", "y_name": "통행량"}
    chart_gender_hour_stay = {"chart_id": "gender_hour_stay", "title": "성별/시간대별 평균 체류시간", "type": "echarts_multi_line",
                              "df": df_gender_hour_stay, "index_col": "collect_hour", "columns_col": "gender",
                              "values_col": "stay_time", "y_name": "체류시간"}

    chart_age_day = {"title": "일자별 연령별 통행량 분석", "type": "echarts_multi_bar_age", "df": df_age_day,
                     "index_col": "collect_date", "columns_col": "age", "values_col": "cnt", "y_name": "통행량(명)",
                     "stacked": True}
    chart_age = {"chart_id": "age_pie", "title": "연령별 통행량", "type": "echarts_pie", "df": df_age_pie, "name_col": "age",
                 "value_col": "cnt", "semi_pie": None}
    chart_age_hour = {"chart_id": "age_hour", "title": "연령별(시간대) 평균 통행량", "type": "echarts_multi_line",
                      "df": df_age_hour, "index_col": "hour", "columns_col": "age", "values_col": "cnt",
                      "y_name": "통행량"}
    chart_age_hour_stay = {"chart_id": "age_hour_stay", "title": "연령별(시간대) 평균 체류시간", "type": "echarts_multi_line",
                           "df": df_age_hour_stay, "index_col": "hour", "columns_col": "age", "values_col": "stay_time",
                           "y_name": "체류시간"}

    chart_direction_day = {"title": "일자별 방향별 통행량 분석", "type": "echarts_multi_bar_direction", "df": df_dir_day,
                           "index_col": "collect_date", "columns_col": "direction", "values_col": "cnt",
                           "y_name": "통행량(명)", "stacked": True}
    chart_direction = {"chart_id": "direction_pie", "title": "방향별 통행량", "type": "echarts_pie", "df": df_dir_pie,
                       "name_col": "direction", "value_col": "cnt", "semi_pie": None}
    chart_dir_hour = {"chart_id": "dir_hour", "title": "방향별(시간대) 평균 통행량", "type": "echarts_multi_line",
                      "df": df_dir_hour, "index_col": "collect_hour", "columns_col": "direction", "values_col": "cnt",
                      "y_name": "통행량"}

    chart_pictorial = {"chart_id": "pictorial_features", "title": "기타 객체 통행량 분석", "type": "echarts_icon_bar",
                       "df": df_etc_pie, "name_col": "class", "value_col": "cnt"}
    chart_etc_hour = {"chart_id": "etc_hour", "title": "기타 객체(시간대) 평균 통행량", "type": "echarts_multi_line",
                      "df": df_etc_hour, "index_col": "collect_hour", "columns_col": "class", "values_col": "cnt",
                      "y_name": "통행량"}

    # ------------------------------------------------------------------------------
    # 5. 대시보드 레이아웃 구성
    # ------------------------------------------------------------------------------
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_date], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    render_section_header("🕒", "시간대 분석", "Timeline Analysis")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_hour_weekday_weekend], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    render_comment_box(all_comments, comment_key="com1")
    st.write(" ")
    st.write(" ")
    render_section_header("🗓️", "요일 분석", "Week Analysis")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_day_hour], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    render_comment_box(all_comments, comment_key="com2")
    st.write(" ")
    st.write(" ")
    render_section_header("⏱️", "체류시간 분석", "Stay Time Analysis")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_date_stay], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_day_hour_stay_time], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    render_comment_box(all_comments, comment_key="com3")
    st.write(" ")
    st.write(" ")
    render_section_header("🚻", "성별 분석", "Gender Analysis")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_gender_day], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_gender, chart_gender_hour], cols_per_row=2)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_gender_hour_stay], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    render_comment_box(all_comments, comment_key="com4")
    st.write(" ")
    st.write(" ")
    render_section_header("👥", "연령대 분석", "Age Analysis")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_age_day], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_age, chart_age_hour], cols_per_row=2)
    st.write(" ")
    st.write(" ")
    render_comment_box(all_comments, comment_key="com5")
    st.write(" ")
    st.write(" ")
    render_section_header("🚲", "기타 분석", "Additional Analysis")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_direction_day], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_direction, chart_dir_hour], cols_per_row=2)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_pictorial, chart_etc_hour], cols_per_row=2)
    render_comment_box(all_comments, comment_key="com6")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_info_footer(logo_path_or_url="images/logo_wide.png")

    # # --------------------------------------------------------------------------
    # # B. 차트 설정 메타데이터 정의
    # # --------------------------------------------------------------------------
    #
    # # 1. 날짜별 통행량
    # qr1 = "SELECT DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, SUM(rca.collect_cnt) AS cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') ORDER BY MIN(STR_TO_DATE(rca.collect_date, '%Y%m%d'));"
    # chart_date = {
    #     "chart_id": "date_traffic",
    #     "title": "일자별 통행량",
    #     "type": "bar",
    #     "df": conn.query(qr1.format(**variables1), ttl=0),
    #     "x": "collect_date",
    #     "y": "cnt",
    #     "x_label": "일자",
    #     "y_label": "통행량",
    # }
    #
    # # 2. 시간대별 통행량 (주중/주말)
    # qr3_combined = """
    #     -- 1. 주중 (Weekday)
    #     SELECT '주중' AS gubun, tt1.collect_hour, SUM(tt1.cnt) AS cnt
    #     FROM (
    #         SELECT t1.collect_hour, ROUND(AVG(t1.cnt)) AS cnt
    #         FROM (
    #             SELECT rca.collect_hour, rca.collect_date, SUM(rca.collect_cnt) AS cnt
    #             FROM rt_collect_summary rca
    #             JOIN rt_calendar c ON rca.collect_date = c.dt
    #             WHERE rca.user_id = '{id}' AND rca.work_no = {work_no}
    #               AND rca.collect_date >= '{start_date_str}' AND rca.collect_date <= '{end_date_str}'
    #               AND rca.collect_hour >= '{start_time_str}' AND rca.collect_hour < '{end_time_str}'
    #               AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%')
    #               AND rca.del_yn = 0 AND c.anal_gubun = 'Weekday'
    #             GROUP BY rca.collect_hour, rca.collect_date
    #         ) t1 GROUP BY t1.collect_hour
    #     ) tt1 GROUP BY tt1.collect_hour
    #
    #     UNION ALL
    #
    #     -- 2. 주말 (Weekend)
    #     SELECT '주말' AS gubun, tt1.collect_hour, SUM(tt1.cnt) AS cnt
    #     FROM (
    #         SELECT t1.collect_hour, ROUND(AVG(t1.cnt)) AS cnt
    #         FROM (
    #             SELECT rca.collect_hour, rca.collect_date, SUM(rca.collect_cnt) AS cnt
    #             FROM rt_collect_summary rca
    #             JOIN rt_calendar c ON rca.collect_date = c.dt
    #             WHERE rca.user_id = '{id}' AND rca.work_no = {work_no}
    #               AND rca.collect_date >= '{start_date_str}' AND rca.collect_date <= '{end_date_str}'
    #               AND rca.collect_hour >= '{start_time_str}' AND rca.collect_hour < '{end_time_str}'
    #               AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%')
    #               AND rca.del_yn = 0 AND c.anal_gubun = 'Weekend'
    #             GROUP BY rca.collect_hour, rca.collect_date
    #         ) t1 GROUP BY t1.collect_hour
    #     ) tt1 GROUP BY tt1.collect_hour
    #
    #     UNION ALL
    #
    #     -- 3. 전체 (Total - 평일+주말 구분 없는 전체 기준)
    #     SELECT '전체' AS gubun, tt1.collect_hour, SUM(tt1.cnt) AS cnt
    #     FROM (
    #         SELECT t1.collect_hour, ROUND(AVG(t1.cnt)) AS cnt
    #         FROM (
    #             SELECT rca.collect_hour, rca.collect_date, SUM(rca.collect_cnt) AS cnt
    #             FROM rt_collect_summary rca
    #             WHERE rca.user_id = '{id}' AND rca.work_no = {work_no}
    #               AND rca.collect_date >= '{start_date_str}' AND rca.collect_date <= '{end_date_str}'
    #               AND rca.collect_hour >= '{start_time_str}' AND rca.collect_hour < '{end_time_str}'
    #               AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%')
    #               AND rca.del_yn = 0
    #             GROUP BY rca.collect_hour, rca.collect_date
    #         ) t1 GROUP BY t1.collect_hour
    #     ) tt1 GROUP BY tt1.collect_hour
    #
    #     ORDER BY collect_hour, gubun
    # """
    #
    # chart_hour_weekday_weekend = {
    #     "chart_id": "hour_weekday_weekend",
    #     "title": "시간대별 평균 통행량",
    #     "type": "echarts_multi_line",
    #     "df": conn.query(qr3_combined.format(**variables1), ttl=0),
    #     "index_col": "collect_hour",
    #     "columns_col": "gubun",
    #     "values_col": "cnt",
    #     "y_name": "통행량",
    # }
    #
    # # 1. 날짜별 평균 체류시간
    # qr1_stay_perday = "SELECT DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, AVG(rca.stay_time) AS cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') ORDER BY MIN(STR_TO_DATE(rca.collect_date, '%Y%m%d'));"
    # chart_date_stay = {
    #     "chart_id": "date_stay",
    #     "title": "일자별 평균 체류시간",
    #     "type": "bar",
    #     "df": conn.query(qr1_stay_perday.format(**variables1), ttl=0),
    #     "x": "collect_date",
    #     "y": "cnt",
    #     "x_label": "일자",
    #     "y_label": "평균 체류시간",
    # }
    #
    # # 3. 요일/시간대별 통행량 및 체류시간
    # qr2 = "SELECT t1.collect_hour, t1.collect_day, t1.collect_order, avg(t1.cnt) as cnt FROM (SELECT (CASE WHEN rca.collect_day = 'Sun' THEN '일' WHEN rca.collect_day = 'Mon' THEN '월' WHEN rca.collect_day = 'Tue' THEN '화' WHEN rca.collect_day = 'Wed' THEN '수' WHEN rca.collect_day = 'Thu' THEN '목' WHEN rca.collect_day = 'Fri' THEN '금' WHEN rca.collect_day = 'Sat' THEN '토' END) as collect_day, (CASE WHEN rca.collect_day = 'Sun' THEN 1 WHEN rca.collect_day = 'Mon' THEN 2 WHEN rca.collect_day = 'Tue' THEN 3 WHEN rca.collect_day = 'Wed' THEN 4 WHEN rca.collect_day = 'Thu' THEN 5 WHEN rca.collect_day = 'Fri' THEN 6 WHEN rca.collect_day = 'Sat' THEN 7 END) as collect_order, rca.collect_hour, rca.collect_date, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY collect_day, collect_order, rca.collect_hour, rca.collect_date) t1 GROUP BY t1.collect_hour, t1.collect_day, t1.collect_order ORDER BY t1.collect_hour, t1.collect_day, t1.collect_order"
    # chart_day_hour = {
    #     "chart_id": "day_hour_traffic",
    #     "title": "요일별/시간대별 평균 통행량",
    #     "type": "echarts_multi_line",
    #     "df": conn.query(qr2.format(**variables1), ttl=0),
    #     "index_col": "collect_hour",
    #     "columns_col": "collect_day",
    #     "values_col": "cnt",
    #     "y_name": "통행량",
    # }
    #
    # qr20 = "SELECT t1.collect_hour, t1.collect_day, t1.collect_order, round(avg(t1.stay_time), 1) as stay_time FROM (SELECT (CASE WHEN rca.collect_day = 'Sun' THEN '일' WHEN rca.collect_day = 'Mon' THEN '월' WHEN rca.collect_day = 'Tue' THEN '화' WHEN rca.collect_day = 'Wed' THEN '수' WHEN rca.collect_day = 'Thu' THEN '목' WHEN rca.collect_day = 'Fri' THEN '금' WHEN rca.collect_day = 'Sat' THEN '토' END) as collect_day, (CASE WHEN rca.collect_day = 'Sun' THEN 1 WHEN rca.collect_day = 'Mon' THEN 2 WHEN rca.collect_day = 'Tue' THEN 3 WHEN rca.collect_day = 'Wed' THEN 4 WHEN rca.collect_day = 'Thu' THEN 5 WHEN rca.collect_day = 'Fri' THEN 6 WHEN rca.collect_day = 'Sat' THEN 7 END) as collect_order, rca.collect_hour, rca.collect_date, avg(rca.stay_time) as stay_time FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 AND rca.stay_time <> 99999 GROUP BY collect_day, collect_order, rca.collect_hour, rca.collect_date) t1 GROUP BY t1.collect_hour, t1.collect_day, t1.collect_order ORDER BY t1.collect_hour, t1.collect_day, t1.collect_order"
    # chart_day_hour_stay_time = {
    #     "chart_id": "day_hour_stay",
    #     "title": "요일별/시간대별 평균 체류시간",
    #     "type": "echarts_multi_line",
    #     "df": conn.query(qr20.format(**variables1), ttl=0),
    #     "index_col": "collect_hour",
    #     "columns_col": "collect_day",
    #     "values_col": "stay_time",
    #     "y_name": "체류시간(초)",
    # }
    #
    # # 4. 성별 일자별 차트
    # qr20_1 = """select (CASE WHEN rca.gender = 'male' THEN '남성' WHEN rca.gender = 'female' THEN '여성' END) as gender, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, sum(rca.collect_cnt) as cnt
    #               from rt_collect_summary rca
    #                 WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}'
    #                     and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
    #                     AND (rca.class like 'm%' OR rca.class like 'w%')
    #                     AND rca.del_yn = 0
    #                     AND rca.stay_time <> 99999
    #               group by (CASE WHEN rca.gender = 'male' THEN '남성' WHEN rca.gender = 'female' THEN '여성' END), DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d')"""
    #
    # chart_gender_day = {
    #     "title": "일자별 성별 통행량 분석",
    #     "type": "echarts_multi_bar_gender",
    #     "df": conn.query(qr20_1.format(**variables1), ttl=0),
    #     "index_col": "collect_date",  # X축이 될 열 이름 (예: 일자)
    #     "columns_col": "gender",  # 범례(남/여)로 분리할 열 이름
    #     "values_col": "cnt",  # 수치 값이 들어있는 열 이름
    #     "y_name": "통행량(명)",
    #     "stacked": True  # True면 누적 바 차트, False면 나란히 배치되는 그룹 바 차트
    # }
    #
    #
    # qr21 = "SELECT (CASE WHEN rca.gender = 'male' THEN '남성' WHEN rca.gender = 'female' THEN '여성' END) as gender, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY (CASE WHEN rca.gender = 'male' THEN '남성' WHEN rca.gender = 'female' THEN '여성' END)"
    # chart_gender = {
    #     "chart_id": "gender_pie",
    #     "title": "성별 통행량",
    #     "type": "echarts_pie",
    #     "df": conn.query(qr21.format(**variables1), ttl=0),
    #     "name_col": "gender",
    #     "value_col": "cnt",
    #     "semi_pie": None
    # }
    #
    # qr22 = """
    #     SELECT
    #         t1.collect_hour AS collect_hour,
    #         (CASE WHEN t1.gender_code = 'male' THEN '남성'
    #               WHEN t1.gender_code = 'female' THEN '여성' END) AS gender,
    #         ROUND(AVG(t1.cnt)) AS cnt
    #     FROM (
    #         SELECT
    #             rca.collect_hour AS collect_hour,
    #             rca.gender AS gender_code,
    #             rca.collect_date AS collect_date,
    #             SUM(rca.collect_cnt) AS cnt
    #         FROM rt_collect_summary rca
    #         WHERE rca.user_id = '{id}'
    #           AND rca.work_no = {work_no}
    #           and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
    #           AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%')
    #           AND rca.del_yn = 0
    #         GROUP BY rca.collect_hour, rca.gender, rca.collect_date
    #     ) t1
    #     GROUP BY t1.collect_hour, t1.gender_code
    #     ORDER BY t1.collect_hour
    # """
    #
    # chart_gender_hour = {
    #     "chart_id": "gender_hour",
    #     "title": "성별/시간대별 평균 통행량",
    #     "type": "echarts_multi_line",
    #     "df": conn.query(qr22.format(**variables1), ttl=0),
    #     "index_col": "collect_hour",
    #     "columns_col": "gender",
    #     "values_col": "cnt",
    #     "y_name": "통행량",
    # }
    #
    # qr25 = """
    #         SELECT
    #             t1.collect_hour AS collect_hour,
    #             (CASE WHEN t1.gender_code = 'male' THEN '남성'
    #                   WHEN t1.gender_code = 'female' THEN '여성' END) AS gender,
    #             ROUND(AVG(t1.stay_time),1) AS stay_time
    #         FROM (
    #             SELECT
    #                 rca.collect_hour AS collect_hour,
    #                 rca.gender AS gender_code,
    #                 rca.collect_date AS collect_date,
    #                 AVG(rca.stay_time) AS stay_time
    #             FROM rt_collect_summary rca
    #             WHERE rca.user_id = '{id}'
    #               AND rca.work_no = {work_no}
    #               and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
    #               AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%')
    #               AND rca.del_yn = 0
    #             GROUP BY rca.collect_hour, rca.gender, rca.collect_date
    #         ) t1
    #         GROUP BY t1.collect_hour, t1.gender_code
    #         ORDER BY t1.collect_hour
    #     """
    #
    # chart_gender_hour_stay = {
    #     "chart_id": "gender_hour_stay",
    #     "title": "성별/시간대별 평균 체류시간",
    #     "type": "echarts_multi_line",
    #     "df": conn.query(qr25.format(**variables1), ttl=0),
    #     "index_col": "collect_hour",
    #     "columns_col": "gender",
    #     "values_col": "stay_time",
    #     "y_name": "체류시간",
    # }
    #
    # # 5. 연령별 일자별 차트
    # qr23_1 = """select rca.age as age, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, sum(rca.collect_cnt) as cnt
    #                   from rt_collect_summary rca
    #                     WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}'
    #                         and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
    #                         AND (rca.class like 'm%' OR rca.class like 'w%')
    #                         AND rca.del_yn = 0
    #                         AND rca.stay_time <> 99999
    #                   group by rca.age, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d')"""
    #
    # chart_age_day = {
    #     "title": "일자별 연령별 통행량 분석",
    #     "type": "echarts_multi_bar_age",
    #     "df": conn.query(qr23_1.format(**variables1), ttl=0),
    #     "index_col": "collect_date",  # X축이 될 열 이름 (예: 일자)
    #     "columns_col": "age",  # 연령대
    #     "values_col": "cnt",  # 수치 값이 들어있는 열 이름
    #     "y_name": "통행량(명)",
    #     "stacked": True  # True면 누적 바 차트, False면 나란히 배치되는 그룹 바 차트
    # }
    #
    # # 5. 연령별 차트
    # qr23 = "SELECT t1.age as age, (CASE WHEN t1.age = '10대 이하' THEN 1 WHEN t1.age = '20~30대' THEN 2 WHEN t1.age = '40~50대' THEN 3 WHEN t1.age = '60~70대' THEN 4 END) as age_order, sum(t1.cnt) as cnt FROM (SELECT rca.age as age, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.age UNION ALL SELECT age, cnt FROM rt_dummy_age2) t1 GROUP BY t1.age ORDER BY age_order"
    # chart_age = {
    #     "chart_id": "age_pie",
    #     "title": "연령별 통행량",
    #     "type": "echarts_pie",
    #     "df": conn.query(qr23.format(**variables1), ttl=0),
    #     "name_col": "age",
    #     "value_col": "cnt",
    #     "semi_pie": None
    # }
    #
    # qr24 = "SELECT t1.collect_hour as hour, t1.age as age, sum(t1.cnt) as cnt FROM (SELECT rca.collect_hour as collect_hour, rca.age as age, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') and rca.del_yn = 0 GROUP BY rca.collect_hour, rca.age) t1 GROUP BY t1.collect_hour, t1.age"
    # chart_age_hour = {
    #     "chart_id": "age_hour",
    #     "title": "연령별(시간대) 평균 통행량",
    #     "type": "echarts_multi_line",
    #     "df": conn.query(qr24.format(**variables1), ttl=0),
    #     "index_col": "hour",
    #     "columns_col": "age",
    #     "values_col": "cnt",
    #     "y_name": "통행량",
    # }
    #
    # # 연령별 체류시간
    # qr24 = "SELECT t1.collect_hour as hour, t1.age as age, ROUND(AVG(t1.stay_time),1) as stay_time FROM (SELECT rca.collect_hour as collect_hour, rca.age as age, avg(rca.stay_time) as stay_time FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') and rca.del_yn = 0 GROUP BY rca.collect_hour, rca.age) t1 GROUP BY t1.collect_hour, t1.age"
    # chart_age_hour = {
    #     "chart_id": "age_hour_stay",
    #     "title": "연령별(시간대) 평균 체류시간",
    #     "type": "echarts_multi_line",
    #     "df": conn.query(qr24.format(**variables1), ttl=0),
    #     "index_col": "hour",
    #     "columns_col": "age",
    #     "values_col": "stay_time",
    #     "y_name": "체류시간",
    # }
    #
    # # 5. 연령별 일자별 차트
    # qr30 = """select rca.direction as direction, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, sum(rca.collect_cnt) as cnt
    #                       from rt_collect_summary rca
    #                         WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}'
    #                             and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
    #                             AND (rca.class like 'm%' OR rca.class like 'w%')
    #                             AND rca.del_yn = 0
    #                             AND rca.stay_time <> 99999
    #                       group by rca.direction, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d')"""
    #
    # chart_direction_day = {
    #     "title": "일자별 방향별 통행량 분석",
    #     "type": "echarts_multi_bar_direction",
    #     "df": conn.query(qr30.format(**variables1), ttl=0),
    #     "index_col": "collect_date",  # X축이 될 열 이름 (예: 일자)
    #     "columns_col": "direction",  # 방향
    #     "values_col": "cnt",  # 수치 값이 들어있는 열 이름
    #     "y_name": "통행량(명)",
    #     "stacked": True  # True면 누적 바 차트, False면 나란히 배치되는 그룹 바 차트
    # }
    #
    # # 6. 방향별 차트
    # qr31 = "SELECT rca.direction as direction, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.direction"
    # chart_direction = {
    #     "chart_id": "direction_pie",
    #     "title": "방향별 통행량",
    #     "type": "echarts_pie",
    #     "df": conn.query(qr31.format(**variables1), ttl=0),
    #     "name_col": "direction",
    #     "value_col": "cnt",
    #     "semi_pie": None
    # }
    #
    # qr32 = "SELECT rca.collect_hour as collect_hour, rca.direction as direction, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_hour, rca.direction"
    # chart_dir_hour = {
    #     "chart_id": "dir_hour",
    #     "title": "방향별(시간대) 평균 통행량",
    #     "type": "echarts_multi_line",
    #     "df": conn.query(qr32.format(**variables1), ttl=0),
    #     "index_col": "collect_hour",
    #     "columns_col": "direction",
    #     "values_col": "cnt",
    #     "y_name": "통행량",
    # }
    #
    # # 자전거, 유모차, 애완견 통행량 쿼리
    # qr_pictorial = """
    #         SELECT (CASE WHEN rca.class = 'bycicle' THEN 'bycicle'
    #                      WHEN rca.class = 'stroller' THEN 'stroller'
    #                      WHEN rca.class = 'dog' THEN 'dog' END) AS class,
    #                SUM(rca.collect_cnt) AS cnt
    #           FROM rt_collect_summary rca
    #          WHERE rca.user_id = '{id}' AND rca.work_no = {work_no}
    #            AND rca.collect_date >= '{start_date_str}' AND rca.collect_date <= '{end_date_str}'
    #            AND rca.collect_hour >= '{start_time_str}' AND rca.collect_hour < '{end_time_str}'
    #            AND rca.class IN ('bycicle', 'stroller', 'dog')
    #            AND rca.del_yn = 0
    #            AND rca.stay_time <> 99999
    #          GROUP BY class
    #     """
    #
    # chart_pictorial = {
    #     "chart_id": "pictorial_features",
    #     "title": "기타 객체 통행량 분석",
    #     "type": "echarts_icon_bar",  # 👈 타입 변경
    #     "df": conn.query(qr_pictorial.format(**variables1), ttl=0),
    #     "name_col": "class",
    #     "value_col": "cnt",
    # }
    #
    # qr99 = """
    #             select t1.collect_hour as collect_hour
    #             , (CASE WHEN t1.class = 'bycicle' THEN 'Bycicle'
    #                     WHEN t1.class = 'stroller' THEN 'Stroller'
    #                     WHEN t1.class = 'dog' THEN 'Dog' END) as class
    #             , (CASE WHEN t1.class = 'bycicle' THEN 1
    #                     WHEN t1.class = 'stroller' THEN 2
    #                     WHEN t1.class = 'dog' THEN 3 END) as class_order
    #                 , sum(t1.cnt) as cnt
    #         from (
    #             select rca.collect_hour as collect_hour, rca.class as class, sum(rca.collect_cnt) as cnt
    #               from rt_collect_summary rca
    #              WHERE rca.user_id = '{id}' AND rca.work_no = {work_no}
    #                AND rca.collect_date >= '{start_date_str}' AND rca.collect_date <= '{end_date_str}'
    #                AND rca.collect_hour >= '{start_time_str}' AND rca.collect_hour < '{end_time_str}'
    #                AND rca.class IN ('bycicle', 'stroller', 'dog')
    #                AND rca.del_yn = 0
    #                AND rca.stay_time <> 99999
    #               group by rca.collect_hour, rca.class) t1
    #         group by t1.collect_hour, t1.class
    #         """
    # chart_etc_hour = {
    #     "chart_id": "etc_hour",
    #     "title": "기타 객체(시간대) 평균 통행량",
    #     "type": "echarts_multi_line",
    #     "df": conn.query(qr99.format(**variables1), ttl=0),
    #     "index_col": "collect_hour",
    #     "columns_col": "class",
    #     "values_col": "cnt",
    #     "y_name": "통행량",
    # }
    #
    # # --------------------------------------------------------------------------
    # # C. 대시보드 레이아웃 구성
    # # --------------------------------------------------------------------------
    # st.write(" ")
    # st.write(" ")
    # render_chart_grid([chart_date], cols_per_row=1)
    # st.write(" ")
    # st.write(" ")
    # render_section_header("🕒", "시간대 분석", "Timeline Analysis")
    # st.write(" ")
    # st.write(" ")
    # render_chart_grid([chart_hour_weekday_weekend], cols_per_row=1)
    # st.write(" ")
    # st.write(" ")
    # render_comment_box(all_comments, comment_key="com1")
    # st.write(" ")
    # st.write(" ")
    # render_section_header("🗓️", "요일 분석", "Week Analysis")
    # st.write(" ")
    # st.write(" ")
    # render_chart_grid([chart_day_hour], cols_per_row=1)
    # st.write(" ")
    # st.write(" ")
    # render_comment_box(all_comments, comment_key="com2")
    # st.write(" ")
    # st.write(" ")
    # render_section_header("⏱️", "체류시간 분석", "Stay Time Analysis")
    # st.write(" ")
    # st.write(" ")
    # render_chart_grid([chart_date_stay], cols_per_row=1)
    # st.write(" ")
    # st.write(" ")
    # st.write(" ")
    # st.write(" ")
    # render_chart_grid([chart_day_hour_stay_time], cols_per_row=1)
    # st.write(" ")
    # st.write(" ")
    # render_comment_box(all_comments, comment_key="com3")
    # st.write(" ")
    # st.write(" ")
    # render_section_header("🚻", "성별 분석", "Gender Analysis")
    # st.write(" ")
    # st.write(" ")
    # render_chart_grid([chart_gender_day], cols_per_row=1)
    # st.write(" ")
    # st.write(" ")
    # st.write(" ")
    # st.write(" ")
    # render_chart_grid([chart_gender, chart_gender_hour], cols_per_row=2)
    # st.write(" ")
    # st.write(" ")
    # st.write(" ")
    # st.write(" ")
    # render_chart_grid([chart_gender_hour_stay], cols_per_row=1)
    # st.write(" ")
    # st.write(" ")
    # render_comment_box(all_comments, comment_key="com4")
    # st.write(" ")
    # st.write(" ")
    # render_section_header("👥", "연령대 분석", "Age Analysis")
    # st.write(" ")
    # st.write(" ")
    # render_chart_grid([chart_age_day], cols_per_row=1)
    # st.write(" ")
    # st.write(" ")
    # st.write(" ")
    # st.write(" ")
    # render_chart_grid([chart_age, chart_age_hour], cols_per_row=2)
    # st.write(" ")
    # st.write(" ")
    # render_comment_box(all_comments, comment_key="com5")
    # st.write(" ")
    # st.write(" ")
    # render_section_header("🚲", "기타 분석", "Additional Analysis")
    # st.write(" ")
    # st.write(" ")
    # render_chart_grid([chart_direction_day], cols_per_row=1)
    # st.write(" ")
    # st.write(" ")
    # st.write(" ")
    # st.write(" ")
    # render_chart_grid([chart_direction, chart_dir_hour], cols_per_row=2)
    # st.write(" ")
    # st.write(" ")
    # st.write(" ")
    # st.write(" ")
    # render_chart_grid([chart_pictorial, chart_etc_hour], cols_per_row=2)
    # render_comment_box(all_comments, comment_key="com6")
    # st.write(" ")
    # st.write(" ")
    # st.write(" ")
    # st.write(" ")
    # render_info_footer(logo_path_or_url="images/logo_wide.png")