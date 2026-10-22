import datetime
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
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )

        page = browser.new_page(
            viewport={'width': 1200, 'height': 1600},
            device_scale_factor=2
        )

        # 🎯 export_mode=true, user_id, work_no 3개 파라미터를 URL에 같이 주입
        target_url = f"http://localhost:8501/dashboard_pdf?export_mode=true&user_id={user_id}&work_no={work_no}"
        page.goto(target_url, wait_until='networkidle', timeout=60000)

        # ECharts 및 Folium 렌더링 완성 대기 (2초)
        page.wait_for_timeout(2000)

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

# ------------------------------------------------------------------------------
# Page CSS Customization
# ------------------------------------------------------------------------------
st.markdown(
    """
    <style>
        /* st.logo 이미지 컨테이너 크기 확대 */
        [data-testid="stSidebarHeader"] img {
            height: 100px !important;   /* 원하는 높이로 조절 */
            width: auto !important;
            max-width: 100% !important;
        }
        /* 로고 영역 컨테이너 여백 조정 */
        [data-testid="stSidebarHeader"] {
            padding-top: 40px !important;
            padding-bottom: 40px !important;
            padding-left: 0px !important;
        }

        /* 💡 셀렉트박스 입력창 커서 숨김, 입력 차단 및 선택 불가 처리 */
        div[data-baseweb="select"] input {
            caret-color: transparent !important; /* 깜빡이는 커서 숨김 */
            user-select: none !important;        /* 텍스트 드래그 및 선택 방지 */
        }

        /* 셀렉트박스 전체에 클릭만 허용하고 텍스트 커서 모양(I-beam) 방지 */
        div[data-baseweb="select"] {
            cursor: pointer !important;
        }

        div[data-baseweb="select"] * {
            cursor: pointer !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
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
        memo = selected_work_info.get("측정지점") or selected_work_info.get("memo") or f"지점 {selected_work_info.get('작업번호') or selected_work_info.get('work_no')}"

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
                    📌 {memo}
                </h4>
                <p style="margin-bottom: 25px; color: #64748b; font-size: 13px; line-height: 1.4;">
                    <b>주소:</b> {address}
                </p>
                <hr style="margin: 8px 0 16px 0; border: none; border-top: 1px solid #e2e8f0;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div>
                        <span style="font-size: 15px; color: #64748b; display: block;">📅 측정 시작일자</span>
                        <span style="font-size: 15px; font-weight: 600; color: #0f172a; margin-left: 24px;">{start_date}</span>
                    </div>
                    <div>
                        <span style="font-size: 15px; color: #64748b; display: block;">📅 측정 종료일자</span>
                        <span style="font-size: 15px; font-weight: 600; color: #0f172a; margin-left: 24px;">{end_date}</span>
                    </div>
                    <div>
                        <span style="font-size: 15px; color: #64748b; display: block;">⏰ 측정 시작시간</span>
                        <span style="font-size: 15px; font-weight: 600; color: #2563eb; margin-left: 24px;">{start_time}</span>
                    </div>
                    <div>
                        <span style="font-size: 15px; color: #64748b; display: block;">⏰ 측정 종료시간</span>
                        <span style="font-size: 15px; font-weight: 600; color: #2563eb; margin-left: 24px;">{end_time}</span>
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
        f"<h4 style='font-size: 20px; font-weight: bold; margin-bottom: 10px;'>{title}</h4>",
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
        # index_col: x축 기준 (예: 일자 또는 시간), columns_col: 그룹화할 기준 (예: 성별), values_col: 값
        index_col = chart_info.get("index_col", "collect_date")
        columns_col = chart_info.get("columns_col", "gender")
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
    link="https://realtargeting.streamlit.app",
)

conn = st.connection("mysql", type="sql")

st.subheader("통합 대시보드", divider="blue")

user_id = st.session_state.get("user_id")
work_list = st.session_state.get("work_list", [])

if not user_id or not work_list:
    st.error("⚠️ 로그인 정보가 없거나 열람 가능한 지점이 없습니다. 사이드바에서 먼저 로그인해 주세요.")
else:

    # 한글/영문 Key 모도 호환 가능한 옵션 텍스트 매핑
    location_options = [
        item.get("측정지점") or item.get("memo") or item.get("주소") or item.get("location") or f"지점 {item.get('작업번호', item.get('work_no'))}"
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

    # 8:2 비율로 컬럼 나누기
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

    with col2:
        # selectbox의 상단 라벨 높이에 맞춰 버튼 위치를 내리기 위한 여백 처리
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)

        # PDF 다운로드 버튼 (일반 화면에서만 노출)
        st.download_button(
            label="💾 PDF 다운로드",
            data=lambda: get_pdf_bytes(user_id, selected_work_no),
            file_name=f"리얼타겟팅 보고서_{user_id}_{selected_work_no}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

    # 선택된 work_no 세션 반영
    st.session_state["selected_work_no"] = selected_work_no
    start_date_raw = format_date_str(selected_work_info.get("시작일자") or selected_work_info.get("start_date"))
    end_date_raw = format_date_str(selected_work_info.get("종료일자") or selected_work_info.get("end_date"))
    start_time_raw = format_time_str(selected_work_info.get("시작시간") or selected_work_info.get("start_time"))
    end_time_raw = format_time_str(selected_work_info.get("종료시간") or selected_work_info.get("end_time"))

    # 1. 날짜에서 '-' 제거하여 YYYYMMDD 형태로 변환
    start_date_str = str(start_date_raw).replace("-", "").strip()
    end_date_str = str(end_date_raw).replace("-", "").strip()

    # 2. 시간에서 ':'를 제거하고 HH (시) 2자리만 추출
    start_time_clean = str(start_time_raw).replace(":", "").strip()
    end_time_clean = str(end_time_raw).replace(":", "").strip()

    start_time_str = start_time_clean[:2].zfill(2) if start_time_clean else ""
    end_time_str = end_time_clean[:2].zfill(2) if end_time_clean else ""

    st.write(" ")

    # 지도 및 기본 정보 표시
    render_location_map(selected_work_info)
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
    qr_h2 = """SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND rca.class IN ('m01', 'm23', 'm45', 'm67', 'w01', 'w23', 'w45', 'w67', 'unknown') AND rca.del_yn = 0 GROUP BY rca.collect_date) t1"""
    qr_h3 = """SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' and (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date, rca.collect_hour) t1"""
    qr_h4 = """SELECT round(avg(t1.cnt)/60) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date, rca.collect_hour) t1"""
    qr_h5 = """SELECT IFNULL(ROUND(AVG(t1.cnt)), 0) AS weekday_avg FROM (SELECT rca.collect_date AS collect_date, IFNULL(SUM(rca.collect_cnt), 0) AS cnt FROM rt_collect_summary rca JOIN rt_calendar c ON rca.collect_date = c.dt WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND rca.class IN ('m01', 'm23', 'm45', 'm67', 'w01', 'w23', 'w45', 'w67', 'unknown') AND rca.del_yn = 0 AND c.anal_gubun = 'Weekday' GROUP BY rca.collect_date) t1"""
    qr_h6 = """SELECT IFNULL(ROUND(AVG(t1.cnt)), 0) AS weekend_avg FROM (SELECT rca.collect_date AS collect_date, IFNULL(SUM(rca.collect_cnt), 0) AS cnt FROM rt_collect_summary rca JOIN rt_calendar c ON rca.collect_date = c.dt WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND rca.class IN ('m01', 'm23', 'm45', 'm67', 'w01', 'w23', 'w45', 'w67', 'unknown') AND rca.del_yn = 0 AND c.anal_gubun = 'Weekend' GROUP BY rca.collect_date) t1"""
    qr_h7 = """SELECT avg(rca.stay_time) as stay_time FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.stay_time <> 99999 AND rca.del_yn = 0 """
    qr_h8 = """SELECT AVG(t1.hourly_avg_stay) as stay_time FROM (SELECT rca.collect_hour, AVG(rca.stay_time) AS hourly_avg_stay FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') AND rca.stay_time <> 99999 AND rca.del_yn = 0 GROUP BY rca.collect_hour) t1;"""

    render_metric_cards(
        conn.query(qr_h1.format(**variables1), ttl=600),
        conn.query(qr_h2.format(**variables1), ttl=600),
        conn.query(qr_h3.format(**variables1), ttl=600),
        conn.query(qr_h4.format(**variables1), ttl=600),
        conn.query(qr_h5.format(**variables1), ttl=600),
        conn.query(qr_h6.format(**variables1), ttl=600),
        conn.query(qr_h7.format(**variables1), ttl=600),
        conn.query(qr_h8.format(**variables1), ttl=600),
    )
    st.write(" ")

    # --------------------------------------------------------------------------
    # B. 차트 설정 메타데이터 정의
    # --------------------------------------------------------------------------

    # 1. 날짜별 통행량
    qr1 = "SELECT DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, SUM(rca.collect_cnt) AS cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') ORDER BY MIN(STR_TO_DATE(rca.collect_date, '%Y%m%d'));"
    chart_date = {
        "chart_id": "date_traffic",
        "title": "일자별 통행량",
        "type": "bar",
        "df": conn.query(qr1.format(**variables1), ttl=600),
        "x": "collect_date",
        "y": "cnt",
        "x_label": "일자",
        "y_label": "통행량",
    }

    # 2. 시간대별 통행량 (주중/주말)
    qr3_combined = """
    SELECT '주중' AS gubun, tt1.collect_hour, SUM(tt1.cnt) AS cnt 
    FROM (
        SELECT t1.collect_hour, ROUND(AVG(t1.cnt)) AS cnt 
        FROM (
            SELECT rca.collect_hour, rca.collect_date, SUM(rca.collect_cnt) AS cnt 
            FROM rt_collect_summary rca 
            JOIN rt_calendar c ON rca.collect_date = c.dt 
            WHERE rca.user_id = '{id}' AND rca.work_no = {work_no}
              and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' 
              AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
              AND rca.del_yn = 0 AND c.anal_gubun = 'Weekday' 
            GROUP BY rca.collect_hour, rca.collect_date
        ) t1 GROUP BY t1.collect_hour
    ) tt1 GROUP BY tt1.collect_hour

    UNION ALL

    SELECT '주말' AS gubun, tt1.collect_hour, SUM(tt1.cnt) AS cnt 
    FROM (
        SELECT t1.collect_hour, ROUND(AVG(t1.cnt)) AS cnt 
        FROM (
            SELECT rca.collect_hour, rca.collect_date, SUM(rca.collect_cnt) AS cnt 
            FROM rt_collect_summary rca 
            JOIN rt_calendar c ON rca.collect_date = c.dt 
            WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} 
              and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
              AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
              AND rca.del_yn = 0 AND c.anal_gubun = 'Weekend' 
            GROUP BY rca.collect_hour, rca.collect_date
        ) t1 GROUP BY t1.collect_hour
    ) tt1 GROUP BY tt1.collect_hour
    ORDER BY collect_hour
    """

    chart_hour_weekday_weekend = {
        "chart_id": "hour_weekday_weekend",
        "title": "주중/주말 시간대별 평균 통행량",
        "type": "echarts_multi_line",
        "df": conn.query(qr3_combined.format(**variables1), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "gubun",
        "values_col": "cnt",
        "y_name": "통행량",
    }

    # 1. 날짜별 평균 체류시간
    qr1_stay_perday = "SELECT DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, AVG(rca.stay_time) AS cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') ORDER BY MIN(STR_TO_DATE(rca.collect_date, '%Y%m%d'));"
    chart_date_stay = {
        "chart_id": "date_stay",
        "title": "일자별 평균 체류시간",
        "type": "bar",
        "df": conn.query(qr1_stay_perday.format(**variables1), ttl=600),
        "x": "collect_date",
        "y": "cnt",
        "x_label": "일자",
        "y_label": "평균 체류시간",
    }

    # 3. 요일/시간대별 통행량 및 체류시간
    qr2 = "SELECT t1.collect_hour, t1.collect_day, t1.collect_order, avg(t1.cnt) as cnt FROM (SELECT (CASE WHEN rca.collect_day = 'Sun' THEN '일' WHEN rca.collect_day = 'Mon' THEN '월' WHEN rca.collect_day = 'Tue' THEN '화' WHEN rca.collect_day = 'Wed' THEN '수' WHEN rca.collect_day = 'Thu' THEN '목' WHEN rca.collect_day = 'Fri' THEN '금' WHEN rca.collect_day = 'Sat' THEN '토' END) as collect_day, (CASE WHEN rca.collect_day = 'Sun' THEN 1 WHEN rca.collect_day = 'Mon' THEN 2 WHEN rca.collect_day = 'Tue' THEN 3 WHEN rca.collect_day = 'Wed' THEN 4 WHEN rca.collect_day = 'Thu' THEN 5 WHEN rca.collect_day = 'Fri' THEN 6 WHEN rca.collect_day = 'Sat' THEN 7 END) as collect_order, rca.collect_hour, rca.collect_date, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY collect_day, collect_order, rca.collect_hour, rca.collect_date) t1 GROUP BY t1.collect_hour, t1.collect_day, t1.collect_order ORDER BY t1.collect_hour, t1.collect_day, t1.collect_order"
    chart_day_hour = {
        "chart_id": "day_hour_traffic",
        "title": "요일별/시간대별 평균 통행량",
        "type": "echarts_multi_line",
        "df": conn.query(qr2.format(**variables1), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "collect_day",
        "values_col": "cnt",
        "y_name": "통행량",
    }

    qr20 = "SELECT t1.collect_hour, t1.collect_day, t1.collect_order, round(avg(t1.stay_time), 1) as stay_time FROM (SELECT (CASE WHEN rca.collect_day = 'Sun' THEN '일' WHEN rca.collect_day = 'Mon' THEN '월' WHEN rca.collect_day = 'Tue' THEN '화' WHEN rca.collect_day = 'Wed' THEN '수' WHEN rca.collect_day = 'Thu' THEN '목' WHEN rca.collect_day = 'Fri' THEN '금' WHEN rca.collect_day = 'Sat' THEN '토' END) as collect_day, (CASE WHEN rca.collect_day = 'Sun' THEN 1 WHEN rca.collect_day = 'Mon' THEN 2 WHEN rca.collect_day = 'Tue' THEN 3 WHEN rca.collect_day = 'Wed' THEN 4 WHEN rca.collect_day = 'Thu' THEN 5 WHEN rca.collect_day = 'Fri' THEN 6 WHEN rca.collect_day = 'Sat' THEN 7 END) as collect_order, rca.collect_hour, rca.collect_date, avg(rca.stay_time) as stay_time FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 AND rca.stay_time <> 99999 GROUP BY collect_day, collect_order, rca.collect_hour, rca.collect_date) t1 GROUP BY t1.collect_hour, t1.collect_day, t1.collect_order ORDER BY t1.collect_hour, t1.collect_day, t1.collect_order"
    chart_day_hour_stay_time = {
        "chart_id": "day_hour_stay",
        "title": "요일별/시간대별 평균 체류시간",
        "type": "echarts_multi_line",
        "df": conn.query(qr20.format(**variables1), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "collect_day",
        "values_col": "stay_time",
        "y_name": "체류시간(초)",
    }

    # 4. 성별 일자별 차트
    qr20_1 = """select (CASE WHEN rca.gender = 'male' THEN '남성' WHEN rca.gender = 'female' THEN '여성' END) as gender, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, sum(rca.collect_cnt) as cnt
                  from rt_collect_summary rca 
                    WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' 
                        and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' 
                        AND (rca.class like 'm%' OR rca.class like 'w%') 
                        AND rca.del_yn = 0 
                        AND rca.stay_time <> 99999        
                  group by (CASE WHEN rca.gender = 'male' THEN '남성' WHEN rca.gender = 'female' THEN '여성' END), DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d')"""

    chart_gender_day = {
        "title": "일자별 성별 통행량 분석",
        "type": "echarts_multi_bar_gender",
        "df": conn.query(qr20_1.format(**variables1), ttl=600),
        "index_col": "collect_date",  # X축이 될 열 이름 (예: 일자)
        "columns_col": "gender",  # 범례(남/여)로 분리할 열 이름
        "values_col": "cnt",  # 수치 값이 들어있는 열 이름
        "y_name": "통행량(명)",
        "stacked": True  # True면 누적 바 차트, False면 나란히 배치되는 그룹 바 차트
    }


    qr21 = "SELECT (CASE WHEN rca.gender = 'male' THEN '남성' WHEN rca.gender = 'female' THEN '여성' END) as gender, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY (CASE WHEN rca.gender = 'male' THEN '남성' WHEN rca.gender = 'female' THEN '여성' END)"
    chart_gender = {
        "chart_id": "gender_pie",
        "title": "성별 통행량",
        "type": "echarts_pie",
        "df": conn.query(qr21.format(**variables1), ttl=600),
        "name_col": "gender",
        "value_col": "cnt",
        "semi_pie": None
    }

    qr22 = """
        SELECT 
            t1.collect_hour AS collect_hour, 
            (CASE WHEN t1.gender_code = 'male' THEN '남성' 
                  WHEN t1.gender_code = 'female' THEN '여성' END) AS gender, 
            ROUND(AVG(t1.cnt)) AS cnt 
        FROM (
            SELECT 
                rca.collect_hour AS collect_hour, 
                rca.gender AS gender_code, 
                rca.collect_date AS collect_date, 
                SUM(rca.collect_cnt) AS cnt
            FROM rt_collect_summary rca 
            WHERE rca.user_id = '{id}' 
              AND rca.work_no = {work_no} 
              and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
              AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
              AND rca.del_yn = 0 
            GROUP BY rca.collect_hour, rca.gender, rca.collect_date
        ) t1 
        GROUP BY t1.collect_hour, t1.gender_code
        ORDER BY t1.collect_hour
    """

    chart_gender_hour = {
        "chart_id": "gender_hour",
        "title": "성별/시간대별 평균 통행량",
        "type": "echarts_multi_line",
        "df": conn.query(qr22.format(**variables1), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "gender",
        "values_col": "cnt",
        "y_name": "통행량",
    }

    qr25 = """
            SELECT 
                t1.collect_hour AS collect_hour, 
                (CASE WHEN t1.gender_code = 'male' THEN '남성' 
                      WHEN t1.gender_code = 'female' THEN '여성' END) AS gender, 
                ROUND(AVG(t1.stay_time),1) AS stay_time 
            FROM (
                SELECT 
                    rca.collect_hour AS collect_hour, 
                    rca.gender AS gender_code, 
                    rca.collect_date AS collect_date, 
                    AVG(rca.stay_time) AS stay_time
                FROM rt_collect_summary rca 
                WHERE rca.user_id = '{id}' 
                  AND rca.work_no = {work_no} 
                  and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
                  AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
                  AND rca.del_yn = 0 
                GROUP BY rca.collect_hour, rca.gender, rca.collect_date
            ) t1 
            GROUP BY t1.collect_hour, t1.gender_code
            ORDER BY t1.collect_hour
        """

    chart_gender_hour_stay = {
        "chart_id": "gender_hour_stay",
        "title": "성별/시간대별 평균 체류시간",
        "type": "echarts_multi_line",
        "df": conn.query(qr25.format(**variables1), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "gender",
        "values_col": "stay_time",
        "y_name": "체류시간",
    }

    # 5. 연령별 일자별 차트
    qr23_1 = """select rca.age as age, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, sum(rca.collect_cnt) as cnt
                      from rt_collect_summary rca 
                        WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' 
                            and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' 
                            AND (rca.class like 'm%' OR rca.class like 'w%') 
                            AND rca.del_yn = 0 
                            AND rca.stay_time <> 99999        
                      group by rca.age, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d')"""

    chart_age_day = {
        "title": "일자별 연령별 통행량 분석",
        "type": "echarts_multi_bar_age",
        "df": conn.query(qr23_1.format(**variables1), ttl=600),
        "index_col": "collect_date",  # X축이 될 열 이름 (예: 일자)
        "columns_col": "age",  # 연령대
        "values_col": "cnt",  # 수치 값이 들어있는 열 이름
        "y_name": "통행량(명)",
        "stacked": True  # True면 누적 바 차트, False면 나란히 배치되는 그룹 바 차트
    }

    # 5. 연령별 차트
    qr23 = "SELECT t1.age as age, (CASE WHEN t1.age = '10대 이하' THEN 1 WHEN t1.age = '20~30대' THEN 2 WHEN t1.age = '40~50대' THEN 3 WHEN t1.age = '60~70대' THEN 4 END) as age_order, sum(t1.cnt) as cnt FROM (SELECT rca.age as age, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.age UNION ALL SELECT age, cnt FROM rt_dummy_age2) t1 GROUP BY t1.age ORDER BY age_order"
    chart_age = {
        "chart_id": "age_pie",
        "title": "연령별 통행량",
        "type": "echarts_pie",
        "df": conn.query(qr23.format(**variables1), ttl=600),
        "name_col": "age",
        "value_col": "cnt",
        "semi_pie": None
    }

    qr24 = "SELECT t1.collect_hour as hour, t1.age as age, sum(t1.cnt) as cnt FROM (SELECT rca.collect_hour as collect_hour, rca.age as age, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') and rca.del_yn = 0 GROUP BY rca.collect_hour, rca.age) t1 GROUP BY t1.collect_hour, t1.age"
    chart_age_hour = {
        "chart_id": "age_hour",
        "title": "연령별(시간대) 평균 통행량",
        "type": "echarts_multi_line",
        "df": conn.query(qr24.format(**variables1), ttl=600),
        "index_col": "hour",
        "columns_col": "age",
        "values_col": "cnt",
        "y_name": "통행량",
    }

    # 연령별 체류시간
    qr24 = "SELECT t1.collect_hour as hour, t1.age as age, ROUND(AVG(t1.stay_time),1) as stay_time FROM (SELECT rca.collect_hour as collect_hour, rca.age as age, avg(rca.stay_time) as stay_time FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') and rca.del_yn = 0 GROUP BY rca.collect_hour, rca.age) t1 GROUP BY t1.collect_hour, t1.age"
    chart_age_hour = {
        "chart_id": "age_hour_stay",
        "title": "연령별(시간대) 평균 체류시간",
        "type": "echarts_multi_line",
        "df": conn.query(qr24.format(**variables1), ttl=600),
        "index_col": "hour",
        "columns_col": "age",
        "values_col": "stay_time",
        "y_name": "체류시간",
    }

    # 5. 연령별 일자별 차트
    qr30 = """select rca.direction as direction, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, sum(rca.collect_cnt) as cnt
                          from rt_collect_summary rca 
                            WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' 
                                and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' 
                                AND (rca.class like 'm%' OR rca.class like 'w%') 
                                AND rca.del_yn = 0 
                                AND rca.stay_time <> 99999        
                          group by rca.direction, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d')"""

    chart_direction_day = {
        "title": "일자별 방향별 통행량 분석",
        "type": "echarts_multi_bar_direction",
        "df": conn.query(qr30.format(**variables1), ttl=600),
        "index_col": "collect_date",  # X축이 될 열 이름 (예: 일자)
        "columns_col": "direction",  # 방향
        "values_col": "cnt",  # 수치 값이 들어있는 열 이름
        "y_name": "통행량(명)",
        "stacked": True  # True면 누적 바 차트, False면 나란히 배치되는 그룹 바 차트
    }

    # 6. 방향별 차트
    qr31 = "SELECT rca.direction as direction, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.direction"
    chart_direction = {
        "chart_id": "direction_pie",
        "title": "방향별 통행량",
        "type": "echarts_pie",
        "df": conn.query(qr31.format(**variables1), ttl=600),
        "name_col": "direction",
        "value_col": "cnt",
        "semi_pie": None
    }

    qr32 = "SELECT rca.collect_hour as collect_hour, rca.direction as direction, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_hour, rca.direction"
    chart_dir_hour = {
        "chart_id": "dir_hour",
        "title": "방향별(시간대) 평균 통행량",
        "type": "echarts_multi_line",
        "df": conn.query(qr32.format(**variables1), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "direction",
        "values_col": "cnt",
        "y_name": "통행량",
    }

    # 자전거, 유모차, 애완견 통행량 쿼리
    qr_pictorial = """
            SELECT (CASE WHEN rca.class = 'bycicle' THEN 'bycicle'
                         WHEN rca.class = 'stroller' THEN 'stroller'
                         WHEN rca.class = 'dog' THEN 'dog' END) AS class,
                   SUM(rca.collect_cnt) AS cnt
              FROM rt_collect_summary rca 
             WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} 
               AND rca.collect_date >= '{start_date_str}' AND rca.collect_date <= '{end_date_str}' 
               AND rca.collect_hour >= '{start_time_str}' AND rca.collect_hour < '{end_time_str}' 
               AND rca.class IN ('bycicle', 'stroller', 'dog') 
               AND rca.del_yn = 0 
               AND rca.stay_time <> 99999        
             GROUP BY class
        """

    chart_pictorial = {
        "chart_id": "pictorial_features",
        "title": "기타 객체 통행량 분석",
        "type": "echarts_icon_bar",  # 👈 타입 변경
        "df": conn.query(qr_pictorial.format(**variables1), ttl=600),
        "name_col": "class",
        "value_col": "cnt",
    }

    qr99 = """
                select t1.collect_hour as collect_hour
                , (CASE WHEN t1.class = 'bycicle' THEN 'Bycicle'
                        WHEN t1.class = 'stroller' THEN 'Stroller'
                        WHEN t1.class = 'dog' THEN 'Dog' END) as class
                , (CASE WHEN t1.class = 'bycicle' THEN 1
                        WHEN t1.class = 'stroller' THEN 2
                        WHEN t1.class = 'dog' THEN 3 END) as class_order
                    , sum(t1.cnt) as cnt
            from (
                select rca.collect_hour as collect_hour, rca.class as class, sum(rca.collect_cnt) as cnt
                  from rt_collect_summary rca 
                 WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} 
                   AND rca.collect_date >= '{start_date_str}' AND rca.collect_date <= '{end_date_str}' 
                   AND rca.collect_hour >= '{start_time_str}' AND rca.collect_hour < '{end_time_str}' 
                   AND rca.class IN ('bycicle', 'stroller', 'dog') 
                   AND rca.del_yn = 0 
                   AND rca.stay_time <> 99999
                  group by rca.collect_hour, rca.class) t1
            group by t1.collect_hour, t1.class
            """
    chart_etc_hour = {
        "chart_id": "etc_hour",
        "title": "기타 객체(시간대) 평균 통행량",
        "type": "echarts_multi_line",
        "df": conn.query(qr99.format(**variables1), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "class",
        "values_col": "cnt",
        "y_name": "통행량",
    }

    # --------------------------------------------------------------------------
    # C. 대시보드 레이아웃 구성
    # --------------------------------------------------------------------------
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_date], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_hour_weekday_weekend], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_day_hour], cols_per_row=1)
    st.write(" ")
    st.write(" ")
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