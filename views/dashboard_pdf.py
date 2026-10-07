import datetime, base64, os
from typing import Any, Dict, List
import streamlit as st
from streamlit_echarts import st_echarts
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


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
        
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        header { display: none !important; }
        footer { display: none !important; }
        .main .block-container {
            max-width: 100% !important;
            padding: 1rem !important;
        }
        
    </style>
    """,
    unsafe_allow_html=True,
)

def get_image_base64(image_path: str) -> str:
    """이미지 파일을 HTML에 직접 매립하기 위한 Base64 인코딩 함수"""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
    return ""

def render_pdf_cover(selected_work_info: dict = None):
    """
    업로드된 완성형 A4 표지 레이아웃 렌더링 (Markdown 코드 블록 오류 방지 처리)
    """
    selected_work_no = selected_work_info.get("작업번호") or selected_work_info.get("work_no")

    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month
    current_day = datetime.datetime.now().day

    doc_no = f"발행일자 : {current_year}년 {current_month}월 {current_day}일"

    # 이미지 파일 경로 지정
    logo_b64 = get_image_base64("images/logo_wide.png")
    qr_b64 = get_image_base64("images/qr_chat.png")
    kakao_logo_b64 = get_image_base64("images/kakao_icon.png")

    # 태그 내부에 들어갈 이미지 HTML을 미리 완성 (f-string 중첩 에러 방지)
    qr_html = f"<img src='{qr_b64}' class='cover-qr-img'>" if qr_b64 else "<div style='width:110px; height:110px; background:#eee; display:flex; align-items:center; justify-content:center; font-size:11px;'>QR Image</div>"
    kakao_logo_html = f"<img src='{kakao_logo_b64}' class='cover-logo-img'>" if kakao_logo_b64 else ""
    logo_html = f"<img src='{logo_b64}' class='cover-logo-img'>" if logo_b64 else ""

    # 들여쓰기 공백 없이 좌측에 바짝 붙인 HTML 문자열
    cover_html = f"""<style>
@media print {{
    .pdf-cover-container {{
        page-break-after: always !important;
        break-after: page !important;
    }}
}}
.pdf-cover-container {{
    width: 100%;
    height: 1120px;
    background-color: #ffffff;
    position: relative;
    box-sizing: border-box;
    padding: 20px 40px;
    page-break-after: always;
    break-after: page;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}}
.cover-doc-no {{
    text-align: right;
    font-size: 16px;
    font-weight: 700;
    color: #333333;
    margin-bottom: 20px;
}}
.cover-main-wrapper {{
    width: 100%;
    height: 780px; /* A4 1페이지에 맞도록 높이 보정 */
    background-color: #f0f0f0;
    position: relative;
}}
.cover-blue-box {{
    width: 53%;
    height: 580px;
    background-color: #1565c0;
    padding: 48px 40px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}
.cover-title-kr {{
    color: #ffffff;
    font-size: 64px;
    font-weight: 800;
    line-height: 1.25;
    letter-spacing: -1px;
}}
.cover-title-en {{
    color: #90caf9;
    font-size: 44px;
    font-weight: 600;
    font-style: italic;
    line-height: 1.3;
    margin-top: 24px;
}}
.cover-footer-desc {{
    color: rgba(255, 255, 255, 0.9);
    font-size: 18px;
    line-height: 1.6;
}}
/* 담당자 인적사항 및 QR 우측 배치 */
.cover-bottom-wrapper {{
    margin-top: 200px; /* 오버플로우 방지를 위한 여백 보정 */
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding: 0 10px;
}}
.cover-info-list {{
    font-size: 18px;
    line-height: 1.9;
    color: #222222;
}}
.cover-info-list div {{
    display: flex;
}}
.cover-info-label {{
    font-weight: 800;
    width: 110px; /* 라벨 너비 확보 */
}}
.cover-info-val {{
    font-weight: 700;
}}
/* 우측 카카오톡 + QR 수직 정렬 컨테이너 */
.cover-qr-box {{
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}}
.cover-kakao-title {{
    font-size: 18px;
    font-weight: 800;
    color: #3c1e1e;
    margin: 4px 0 8px 0;
}}
.cover-qr-img {{
    width: 110px;
    height: 110px;
    object-fit: contain;
}}
/* 하단 로고 및 카피라이트 */
.cover-footer-logo-zone {{
    margin-top: 50px;
    text-align: center;
}}
.cover-logo-img {{
    height: 75px;
    object-fit: contain;
    margin-bottom: 12px;
}}
.cover-copyright {{
    font-size: 18px;
    font-weight: 700;
    color: #333333;
}}
.cover-qr-box {{
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}}

/* 🎯 로고와 텍스트를 좌우(가로)로 배치하는 헤더 박스 */
.cover-kakao-header {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px; /* 로고와 텍스트 사이 간격 */
    margin-bottom: 8px; /* QR 코드와의 간격 */
}}

/* 카카오 로고 이미지 크기 (텍스트 2줄 높이에 맞춤) */
.cover-kakao-header img {{
    height: 36px; /* 텍스트 2줄 높이에 맞춘 36px */
    width: auto;
    object-fit: contain;
}}

/* 카카오톡 상담하기 2줄 텍스트 */
.cover-kakao-title {{
    font-size: 18px;
    font-weight: 800;
    color: #3c1e1e;
    line-height: 1.25; /* 2줄 텍스트 행간 고정 */
    text-align: left; /* 좌측 정렬 */
}}

.cover-qr-img {{
    width: 110px;
    height: 110px;
    object-fit: contain;
}}
</style>
<div class="pdf-cover-container">
    <div class="cover-doc-no">{doc_no}</div>
    <div class="cover-main-wrapper">
        <div class="cover-blue-box">
            <div>
                <div class="cover-title-kr">
                    AI 통행량<br>분석 보고서
                </div>
                <div class="cover-title-en">
                    AI Foot Traffic<br>Intelligence Report
                </div>
            </div>
            <div class="cover-footer-desc">
                본 보고서는 AI 통행량 분석 시스템을 기반으로 한<br>실제 데이터를 통해 작성 되었습니다.
            </div>
        </div>
    </div>
    <div class="cover-bottom-wrapper">
        <div class="cover-info-list">
            <div><span class="cover-info-label">담 당 자</span><span class="cover-info-val">채명훈</span></div>
            <div><span class="cover-info-label">연 락 처</span><span class="cover-info-val">010-4424-3291</span></div>
            <div><span class="cover-info-label">E-mail</span><span class="cover-info-val">realtargeting@gmail.com</span></div>
            <div><span class="cover-info-label">홈페이지</span><span class="cover-info-val">https://www.realtargeting.co.kr</span></div>
            <div style="margin-top: 4px;"><span class="cover-info-val">아이하우스(주)</span></div>
        </div>
        <div class="cover-qr-box">
            <div class="cover-kakao-header">
                {kakao_logo_html}
                <div class="cover-kakao-title">카카오톡<br>상담하기</div>
            </div>
            {qr_html}
        </div>       
    </div>
    <div class="cover-footer-logo-zone">
        {logo_html}
        <div class="cover-copyright">Copyright ® RealTargeting Allright Resolved.</div>
    </div>
</div>"""

    st.markdown(cover_html, unsafe_allow_html=True)


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
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    col5, col6 = st.columns(2)
    col7, col8 = st.columns(2)

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


    st.subheader(title, divider="blue")
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

    elif chart_type == "area":
        st.area_chart(
            df,
            x=chart_info.get("x"),
            y=chart_info.get("y"),
            color=chart_info.get("color"),
            x_label=chart_info.get("x_label", ""),
            y_label=chart_info.get("y_label", ""),
            height=300,
        )

    elif chart_type == "echarts_pie":
        name_col = chart_info.get("name_col", "name")
        val_col = chart_info.get("value_col", "cnt")
        semi_pie = chart_info.get("semi_pie", None)

        start_angle = 90
        end_angle = 450
        if semi_pie == "up":
            start_angle = 180
            end_angle = 0

        chart_data = [
            {"name": str(row[name_col]), "value": int(row[val_col])}
            for _, row in df.iterrows()
        ]

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

        pivot_df = df.pivot(index=index_col, columns=columns_col, values=values_col).fillna(0)

        days_order = ['월', '화', '수', '목', '금', '토', '일']
        if any(col in days_order for col in pivot_df.columns):
            legend_keys = [d for d in days_order if d in pivot_df.columns]
        else:
            legend_keys = list(pivot_df.columns)

        x_data = [f"{int(h):02d}시" if str(h).isdigit() else str(h) for h in pivot_df.index]
        series_list = [
            {"name": str(key), "type": "line", "data": pivot_df[key].round(1).tolist()}
            for key in legend_keys
        ]

        option = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
            "legend": {"top": "0%", "data": [str(k) for k in legend_keys]},
            "grid": {"top": "15%", "left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": {"type": "category", "boundaryGap": False, "data": x_data},
            "yAxis": {"type": "value", "name": y_name},
            "series": series_list,
        }
        st_echarts(options=option, height="400px", key=comp_key)


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

conn = st.connection("mysql", type="sql")

# 1. URL Query Parameter 확인 (Playwright 백엔드 접속 체크)
# 2. URL Query Parameter 파싱
query_params = st.query_params.to_dict() if hasattr(st.query_params, "to_dict") else dict(st.query_params)

param_user_id = query_params.get("user_id")
if isinstance(param_user_id, list): param_user_id = param_user_id[0]

param_work_no = query_params.get("work_no")
if isinstance(param_work_no, list): param_work_no = param_work_no[0]

selected_work_info = None

# DB에서 해당 work_no의 시작/종료 일자 및 정보 조회
work_query = f"""
        SELECT * 
        FROM rt_collect_info 
        WHERE user_id = '{param_user_id}' AND work_no = {param_work_no}
        LIMIT 1
    """
try:
    df_work = conn.query(work_query, ttl=0)
    if not df_work.empty:
        selected_work_info = df_work.to_dict(orient="records")[0]
    else:
        # rt_work 테이블 정보가 없을 경우 기본값 세팅 (필요 시 테이블명 수정)
        selected_work_info = {
            "work_no": param_work_no,
            "작업번호": param_work_no,
            "start_date": "20200101",
            "end_date": "20991231",
            "start_time": "00",
            "end_time": "24"
        }
except Exception as e:
    st.error(f"지점 정보 조회 실패: {e}")


# 선택된 work_no 세션 반영
st.session_state["selected_work_no"] = param_work_no
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

# 2. PDF 출력 모드 시 전용 스타일 적용 (사이드바, 헤더, 로고 완벽 제거)
st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        header { display: none !important; }
        footer { display: none !important; }
        .main .block-container {
            max-width: 100% !important;
            padding: 1rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# 3. user_id 및 work_list(작업 정보) 결정 분기
# 🎯 Playwright 접속 시: URL 파라미터 기반으로 user_id 및 단일 work_info 구성
if not param_user_id:
    st.error("⚠️ 로그인 정보가 없거나 열람 가능한 지점이 없습니다. 사이드바에서 먼저 로그인해 주세요.")
else:

    # 1. 표지 렌더링
    render_pdf_cover(selected_work_info)

    st.subheader("분석요약", divider="blue")

    st.write(" ")

    # 지도 및 기본 정보 표시
    render_location_map(selected_work_info)
    st.write(" ")
    st.write(" ")
    st.write(" ")

    variables1 = {
        "id": param_user_id,
        "work_no": param_work_no,
        "start_date_str": start_date_str,
        "end_date_str": end_date_str,
        "start_time_str": start_time_str,
        "end_time_str": end_time_str,
    }

    # --------------------------------------------------------------------------
    # A. Metric 상단 지표 조회 및 렌더링
    # --------------------------------------------------------------------------
    qr_h1 = """SELECT sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 """
    qr_h2 = """SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND rca.class IN ('m01', 'm23', 'm45', 'm67', 'w01', 'w23', 'w45', 'w67', 'unknown') AND rca.del_yn = 0 GROUP BY rca.collect_date) t1"""
    qr_h3 = """SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' and (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date, rca.collect_hour) t1"""
    qr_h4 = """SELECT round(avg(t1.cnt)/60) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date, rca.collect_hour) t1"""
    qr_h5 = """SELECT IFNULL(ROUND(AVG(t1.cnt)), 0) AS weekday_avg FROM (SELECT rca.collect_date AS collect_date, IFNULL(SUM(rca.collect_cnt), 0) AS cnt FROM rt_collect_all rca JOIN rt_calendar c ON rca.collect_date = c.dt WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND rca.class IN ('m01', 'm23', 'm45', 'm67', 'w01', 'w23', 'w45', 'w67', 'unknown') AND rca.del_yn = 0 AND c.anal_gubun = 'Weekday' GROUP BY rca.collect_date) t1"""
    qr_h6 = """SELECT IFNULL(ROUND(AVG(t1.cnt)), 0) AS weekend_avg FROM (SELECT rca.collect_date AS collect_date, IFNULL(SUM(rca.collect_cnt), 0) AS cnt FROM rt_collect_all rca JOIN rt_calendar c ON rca.collect_date = c.dt WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND rca.class IN ('m01', 'm23', 'm45', 'm67', 'w01', 'w23', 'w45', 'w67', 'unknown') AND rca.del_yn = 0 AND c.anal_gubun = 'Weekend' GROUP BY rca.collect_date) t1"""
    qr_h7 = """SELECT avg(rca.stay_time) as stay_time FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.stay_time <> 99999 AND rca.del_yn = 0 """
    qr_h8 = """SELECT AVG(t1.hourly_avg_stay) as stay_time FROM (SELECT rca.collect_hour, AVG(rca.stay_time) AS hourly_avg_stay FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') AND rca.stay_time <> 99999 AND rca.del_yn = 0 GROUP BY rca.collect_hour) t1;"""

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
    qr1 = "SELECT DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, SUM(rca.collect_cnt) AS cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') ORDER BY MIN(STR_TO_DATE(rca.collect_date, '%Y%m%d'));"
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
            FROM rt_collect_all rca 
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
            FROM rt_collect_all rca 
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

    # 3. 요일/시간대별 통행량 및 체류시간
    qr2 = "SELECT t1.collect_hour, t1.collect_day, t1.collect_order, avg(t1.cnt) as cnt FROM (SELECT (CASE WHEN rca.collect_day = 'Sun' THEN '일' WHEN rca.collect_day = 'Mon' THEN '월' WHEN rca.collect_day = 'Tue' THEN '화' WHEN rca.collect_day = 'Wed' THEN '수' WHEN rca.collect_day = 'Thu' THEN '목' WHEN rca.collect_day = 'Fri' THEN '금' WHEN rca.collect_day = 'Sat' THEN '토' END) as collect_day, (CASE WHEN rca.collect_day = 'Sun' THEN 1 WHEN rca.collect_day = 'Mon' THEN 2 WHEN rca.collect_day = 'Tue' THEN 3 WHEN rca.collect_day = 'Wed' THEN 4 WHEN rca.collect_day = 'Thu' THEN 5 WHEN rca.collect_day = 'Fri' THEN 6 WHEN rca.collect_day = 'Sat' THEN 7 END) as collect_order, rca.collect_hour, rca.collect_date, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY collect_day, collect_order, rca.collect_hour, rca.collect_date) t1 GROUP BY t1.collect_hour, t1.collect_day, t1.collect_order ORDER BY t1.collect_hour, t1.collect_day, t1.collect_order"
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

    qr20 = "SELECT t1.collect_hour, t1.collect_day, t1.collect_order, round(avg(t1.stay_time), 1) as stay_time FROM (SELECT (CASE WHEN rca.collect_day = 'Sun' THEN '일' WHEN rca.collect_day = 'Mon' THEN '월' WHEN rca.collect_day = 'Tue' THEN '화' WHEN rca.collect_day = 'Wed' THEN '수' WHEN rca.collect_day = 'Thu' THEN '목' WHEN rca.collect_day = 'Fri' THEN '금' WHEN rca.collect_day = 'Sat' THEN '토' END) as collect_day, (CASE WHEN rca.collect_day = 'Sun' THEN 1 WHEN rca.collect_day = 'Mon' THEN 2 WHEN rca.collect_day = 'Tue' THEN 3 WHEN rca.collect_day = 'Wed' THEN 4 WHEN rca.collect_day = 'Thu' THEN 5 WHEN rca.collect_day = 'Fri' THEN 6 WHEN rca.collect_day = 'Sat' THEN 7 END) as collect_order, rca.collect_hour, rca.collect_date, avg(rca.stay_time) as stay_time FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 AND rca.stay_time <> 99999 GROUP BY collect_day, collect_order, rca.collect_hour, rca.collect_date) t1 GROUP BY t1.collect_hour, t1.collect_day, t1.collect_order ORDER BY t1.collect_hour, t1.collect_day, t1.collect_order"
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

    # 4. 성별 차트
    qr21 = "SELECT (CASE WHEN rca.gender = 'male' THEN '남성' WHEN rca.gender = 'female' THEN '여성' END) as gender, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY (CASE WHEN rca.gender = 'male' THEN '남성' WHEN rca.gender = 'female' THEN '여성' END)"
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
            FROM rt_collect_all rca 
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

    # 5. 연령별 차트
    qr23 = "SELECT t1.age as age, (CASE WHEN t1.age = '10대 이하' THEN 1 WHEN t1.age = '20~30대' THEN 2 WHEN t1.age = '40~50대' THEN 3 WHEN t1.age = '60~70대' THEN 4 END) as age_order, sum(t1.cnt) as cnt FROM (SELECT rca.age as age, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.age UNION ALL SELECT age, cnt FROM rt_dummy_age2) t1 GROUP BY t1.age ORDER BY age_order"
    chart_age = {
        "chart_id": "age_pie",
        "title": "연령별 통행량",
        "type": "echarts_pie",
        "df": conn.query(qr23.format(**variables1), ttl=600),
        "name_col": "age",
        "value_col": "cnt",
        "semi_pie": None
    }

    qr24 = "SELECT t1.collect_hour as hour, t1.age as age, sum(t1.cnt) as cnt FROM (SELECT rca.collect_hour as collect_hour, rca.age as age, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') and rca.del_yn = 0 GROUP BY rca.collect_hour, rca.age) t1 GROUP BY t1.collect_hour, t1.age"
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

    # 6. 방향별 차트
    qr31 = "SELECT rca.direction as direction, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.direction"
    chart_direction = {
        "chart_id": "direction_pie",
        "title": "방향별 통행량",
        "type": "echarts_pie",
        "df": conn.query(qr31.format(**variables1), ttl=600),
        "name_col": "direction",
        "value_col": "cnt",
        "semi_pie": None
    }

    qr32 = "SELECT rca.collect_hour as collect_hour, rca.direction as direction, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_hour, rca.direction"
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

    # --------------------------------------------------------------------------
    # C. 대시보드 레이아웃 구성
    # --------------------------------------------------------------------------
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_date], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_hour_weekday_weekend], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_day_hour], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_day_hour_stay_time], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_gender, chart_gender_hour], cols_per_row=2)
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_age, chart_age_hour], cols_per_row=2)
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_direction, chart_dir_hour], cols_per_row=2)