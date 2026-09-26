import datetime
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
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------------------
# 1. 공통 차트 렌더러 (Chart Component Functions)
# ------------------------------------------------------------------------------
def render_location_map(selected_work_info: Dict[str, Any]):
    """왼쪽에는 측정 기본 정보 카드, 오른쪽(너비 50%)에는 지도를 배치합니다."""

    # --------------------------------------------------------------------------
    # 1. 컬럼 분할 (1:1 비율로 나눔 -> 우측 지도가 50% 너비 차지)
    # --------------------------------------------------------------------------
    col_info, col_map = st.columns([3, 2], gap="medium")

    # --------------------------------------------------------------------------
    # 2. [왼쪽 컬럼] 기본 정보 카드 렌더링
    # --------------------------------------------------------------------------
    with col_info:
        start_date = format_date_str(selected_work_info.get("start_date"))
        end_date = format_date_str(selected_work_info.get("end_date"))
        start_time = format_time_str(selected_work_info.get("start_time"))
        end_time = format_time_str(selected_work_info.get("end_time"))
        address = selected_work_info.get("location") or selected_work_info.get("주소", "-")
        memo = selected_work_info.get("memo") or f"지점 {selected_work_info.get('work_no')}"

        # CSS 스타일링이 적용된 기본정보 박스
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
                    <b>     주소:</b> {address}
                </p>
                <hr style="margin: 8px 0 16px 0; border: none; border-top: 1px solid #e2e8f0;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div>
                                <span style="font-size: 15px; color: #64748b; display: block;">📅 측정 시작일자</span>
                                <span style="font-size: 15px; font-weight: 600; color: #0f172a; margin-left: 24px;">   {start_date}</span>
                            </div>
                            <div>
                                <span style="font-size: 15px; color: #64748b; display: block;">📅 측정 종료일자</span>
                                <span style="font-size: 15px; font-weight: 600; color: #0f172a; margin-left: 24px;">   {end_date}</span>
                            </div>
                            <div>
                                <span style="font-size: 15px; color: #64748b; display: block;">⏰ 측정 시작시간</span>
                                <span style="font-size: 15px; font-weight: 600; color: #2563eb; margin-left: 24px;">   {start_time}</span>
                            </div>
                            <div>
                                <span style="font-size: 15px; color: #64748b; display: block;">⏰ 측정 종료시간</span>
                                <span style="font-size: 15px; font-weight: 600; color: #2563eb; margin-left: 24px;">   {end_time}</span>
                            </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------------------------
    # 3. [오른쪽 컬럼] 지도 렌더링
    # --------------------------------------------------------------------------
    with col_map:
        lat = selected_work_info.get("latitude")
        lng = selected_work_info.get("longitude")

        # 좌표 데이터 유효성 검증
        if lat is None or lng is None:
            st.info("ℹ️ 해당 측정지점에 등록된 위도/경도(latitude, longitude) 좌표 정보가 없습니다.")
            return

        try:
            lat = float(lat)
            lng = float(lng)
        except (ValueError, TypeError):
            st.warning("⚠️ 위도/경도 좌표 형식이 올바르지 않습니다.")
            return

        # Folium 지도 생성
        m = folium.Map(location=[lat, lng], zoom_start=22)

        # 핀 마커 추가
        popup_text = f"<b>{memo}</b><br>{address}" if address else f"<b>{memo}</b>"
        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=memo,
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(m)

        # Streamlit 지도 렌더링 (col_map 내부에 위치하므로 전체 화면 기준 50% 영역 차지)
        st_folium(
            m,
            width="100%",
            height=320,
            key=f"map_{selected_work_info.get('work_no')}",
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

    # 공통 component key 생성 규칙
    comp_key = f"{chart_type}_{chart_id}"

    st.markdown(
        f"<h4 style='font-size: 20px; font-weight: bold; margin-bottom: 10px;'>{title}</h4>",
        unsafe_allow_html=True,
    )
    st.write(" ")

    # 1. 기본 Streamlit 차트
    if chart_type == "bar":
        st.bar_chart(
            df,
            x=chart_info.get("x"),
            y=chart_info.get("y"),
            x_label=chart_info.get("x_label", ""),
            y_label=chart_info.get("y_label", ""),
            height=300,
        )
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
        # 1. 컬럼명 지정 (기본값 설정)
        name_col = chart_info.get("name_col", "name")
        val_col = chart_info.get("value_col", "cnt")
        # 2. 반원(up) / 온원(전체) 옵션 및 범례 위치 처리
        semi_pie = chart_info.get("semi_pie", None)
        start_angle = 90
        end_angle = 450
        center = ["50%", "50%"]
        legend_pos = {"bottom": "5%", "left": "center"}  # 온원 기본값 (상단)
        default_radius = ["40%", "70%"]

        # 3. 데이터 구성
        chart_data = [
            {"name": str(row[name_col]), "value": int(row[val_col])}
            for _, row in df.iterrows()
        ]

        # 4. 차트 옵션 구성
        options = {
            "tooltip": {
                "trigger": "item",
                "formatter": "{b}: {c:,}명 ({d}%)"
            },
            "legend": legend_pos,
            "series": [
                {
                    "name": title,
                    "type": "pie",
                    "radius": chart_info.get("radius", default_radius),
                    "center": center,
                    "startAngle": start_angle,
                    "endAngle": end_angle,
                    "avoidLabelOverlap": True,
                    "data": chart_data,
                }
            ],
        }

        st_echarts(options=options, height=chart_info.get("height", "400px"), key=comp_key)

    # 4. ECharts 단일 라인 차트 (시간대별 통행량 등)
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

    # 5. ECharts 통합 범용 멀티 라인 차트 (요일별/성별 등 다중 라인 차트 일체)
    elif chart_type == "echarts_multi_line":
        index_col = chart_info.get("index_col", "collect_hour")
        columns_col = chart_info.get("columns_col", "collect_day")
        values_col = chart_info.get("values_col", "cnt")
        y_name = chart_info.get("y_name", "통행량")

        pivot_df = df.pivot(index=index_col, columns=columns_col, values=values_col).fillna(0)

        # 컬럼 순서 정렬 (요일 컬럼인 경우 월~일 우선 배치, 그 외는 데이터 컬럼 사용)
        days_order = ['월', '화', '수', '목', '금', '토', '일']
        if any(col in days_order for col in pivot_df.columns):
            legend_keys = [d for d in days_order if d in pivot_df.columns]
        else:
            legend_keys = list(pivot_df.columns)

        x_data = [f"{int(h):02d}시" for h in pivot_df.index]
        series_list = [
            {"name": key, "type": "line", "data": pivot_df[key].round(1).tolist()}
            for key in legend_keys
        ]

        option = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
            "legend": {"top": "0%", "data": legend_keys},
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
        cols = st.columns(ratios if ratios and len(ratios) == len(row_charts) else len(row_charts),
                          vertical_alignment="bottom")
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

# 인증 확인 및 로그인 계정의 전체 권한 지점 목록 가져오기
user_id = st.session_state.get("user_id")
work_list = st.session_state.get("work_list", [])  # 로그인 시 저장된 전체 지점 리스트 참조

if not user_id or not work_list:
    st.error("⚠️ 로그인 정보가 없거나 열람 가능한 지점이 없습니다. 사이드바에서 먼저 로그인해 주세요.")
else:
    # --------------------------------------------------------------------------
    # 상단 컨트롤러 (측정지점 선택 드롭다운)
    # --------------------------------------------------------------------------
    # 라벨 표시용 목록 (memo가 비어있으면 location 사용)
    location_options = [w.get("memo") or w.get("location", f"지점 {w['work_no']}") for w in work_list]

    # main.py 등에서 넘겨받은 단일 선택 지점 ID 확인
    default_work_no = st.session_state.get("selected_work_no")
    default_idx = 0

    if default_work_no is not None:
        for idx, item in enumerate(work_list):
            if str(item["work_no"]) == str(default_work_no):
                default_idx = idx
                break

    selected_location = st.selectbox(
        "📍 측정지점 선택",
        options=location_options,
        index=default_idx,
        key="sb_dashboard_location"
    )

    # 선택된 지명의 work_no 매핑
    selected_work_info = work_list[location_options.index(selected_location)]
    selected_work_no = selected_work_info["work_no"]

    st.write(" ")

    # 지도 표기
    render_location_map(selected_work_info)
    st.write(" ")

    # DB 바인딩 파라미터 생성
    variables1 = {
        "id": user_id,
        "work_no": selected_work_no,
    }

    # --------------------------------------------------------------------------
    # A. Metric 상단 지표 조회 및 렌더링
    # --------------------------------------------------------------------------
    qr_h1 = """SELECT sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 """
    qr_h2 = """SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND rca.class IN ('m01', 'm23', 'm45', 'm67', 'w01', 'w23', 'w45', 'w67', 'unknown') AND rca.del_yn = 0 GROUP BY rca.collect_date) t1"""
    qr_h3 = """SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date, rca.collect_hour) t1"""
    qr_h4 = """SELECT round(avg(t1.cnt)/60) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date, rca.collect_hour) t1"""
    qr_h5 = """SELECT IFNULL(ROUND(AVG(t1.cnt)), 0) AS weekday_avg FROM (SELECT rca.collect_date AS collect_date, IFNULL(SUM(rca.collect_cnt), 0) AS cnt FROM rt_collect_all rca JOIN rt_calendar c ON rca.collect_date = c.dt WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND rca.class IN ('m01', 'm23', 'm45', 'm67', 'w01', 'w23', 'w45', 'w67', 'unknown') AND rca.del_yn = 0 AND c.anal_gubun = 'Weekday' GROUP BY rca.collect_date) t1"""
    qr_h6 = """SELECT IFNULL(ROUND(AVG(t1.cnt)), 0) AS weekend_avg FROM (SELECT rca.collect_date AS collect_date, IFNULL(SUM(rca.collect_cnt), 0) AS cnt FROM rt_collect_all rca JOIN rt_calendar c ON rca.collect_date = c.dt WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND rca.class IN ('m01', 'm23', 'm45', 'm67', 'w01', 'w23', 'w45', 'w67', 'unknown') AND rca.del_yn = 0 AND c.anal_gubun = 'Weekend' GROUP BY rca.collect_date) t1"""
    qr_h7 = """SELECT avg(rca.stay_time) as stay_time FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.stay_time <> 99999 AND rca.del_yn = 0 """
    qr_h8 = """SELECT AVG(t1.hourly_avg_stay) as stay_time FROM (SELECT rca.collect_hour, AVG(rca.stay_time) AS hourly_avg_stay FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') AND rca.stay_time <> 99999 AND rca.del_yn = 0 GROUP BY rca.collect_hour) t1;"""

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
    # B. 차트 설정 메타데이터 정의 (통합된 type 및 깔끔한 chart_id 적용)
    # --------------------------------------------------------------------------

    # 1. 날짜별 통행량
    qr1 = "SELECT DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, SUM(rca.collect_cnt) AS cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') ORDER BY MIN(STR_TO_DATE(rca.collect_date, '%Y%m%d'));"
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

    # 3. 요일/시간대별 통행량 및 체류시간 (멀티 라인)
    qr2 = "SELECT t1.collect_hour, t1.collect_day, t1.collect_order, avg(t1.cnt) as cnt FROM (SELECT (CASE WHEN rca.collect_day = 'Sun' THEN '일' WHEN rca.collect_day = 'Mon' THEN '월' WHEN rca.collect_day = 'Tue' THEN '화' WHEN rca.collect_day = 'Wed' THEN '수' WHEN rca.collect_day = 'Thu' THEN '목' WHEN rca.collect_day = 'Fri' THEN '금' WHEN rca.collect_day = 'Sat' THEN '토' END) as collect_day, (CASE WHEN rca.collect_day = 'Sun' THEN 1 WHEN rca.collect_day = 'Mon' THEN 2 WHEN rca.collect_day = 'Tue' THEN 3 WHEN rca.collect_day = 'Wed' THEN 4 WHEN rca.collect_day = 'Thu' THEN 5 WHEN rca.collect_day = 'Fri' THEN 6 WHEN rca.collect_day = 'Sat' THEN 7 END) as collect_order, rca.collect_hour, rca.collect_date, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY collect_day, collect_order, rca.collect_hour, rca.collect_date) t1 GROUP BY t1.collect_hour, t1.collect_day, t1.collect_order ORDER BY t1.collect_hour, t1.collect_day, t1.collect_order"
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

    qr20 = "SELECT t1.collect_hour, t1.collect_day, t1.collect_order, round(avg(t1.stay_time), 1) as stay_time FROM (SELECT (CASE WHEN rca.collect_day = 'Sun' THEN '일' WHEN rca.collect_day = 'Mon' THEN '월' WHEN rca.collect_day = 'Tue' THEN '화' WHEN rca.collect_day = 'Wed' THEN '수' WHEN rca.collect_day = 'Thu' THEN '목' WHEN rca.collect_day = 'Fri' THEN '금' WHEN rca.collect_day = 'Sat' THEN '토' END) as collect_day, (CASE WHEN rca.collect_day = 'Sun' THEN 1 WHEN rca.collect_day = 'Mon' THEN 2 WHEN rca.collect_day = 'Tue' THEN 3 WHEN rca.collect_day = 'Wed' THEN 4 WHEN rca.collect_day = 'Thu' THEN 5 WHEN rca.collect_day = 'Fri' THEN 6 WHEN rca.collect_day = 'Sat' THEN 7 END) as collect_order, rca.collect_hour, rca.collect_date, avg(rca.stay_time) as stay_time FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 AND rca.stay_time <> 99999 GROUP BY collect_day, collect_order, rca.collect_hour, rca.collect_date) t1 GROUP BY t1.collect_hour, t1.collect_day, t1.collect_order ORDER BY t1.collect_hour, t1.collect_day, t1.collect_order"
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
    qr21 = "SELECT (CASE WHEN substring(rca.class,1,1) = 'm' THEN '남성' WHEN substring(rca.class,1,1) = 'w' THEN '여성' END) as gender, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY (CASE WHEN substring(rca.class,1,1) = 'm' THEN '남성' WHEN substring(rca.class,1,1) = 'w' THEN '여성' END)"
    # chart_gender = {
    #     "chart_id": "gender_ratio",
    #     "title": "성별 통행량",
    #     "type": "echarts_pie_gender",
    #     "df": conn.query(qr21.format(**variables1), ttl=600),
    #     "name_col": "gender",
    #     "value_col": "cnt",
    # }

    chart_gender = {
        "chart_id": "gender_pie",
        "title": "성별 통행량",
        "type": "echarts_pie",
        "df": conn.query(qr21.format(**variables1), ttl=600),
        "name_col": "gender",
        "value_col": "cnt",
        "semi_pie": "up"
    }

    qr22 = """
        SELECT 
            t1.collect_hour AS collect_hour, 
            (CASE WHEN t1.gender_code = 'm' THEN '남성' 
                  WHEN t1.gender_code = 'w' THEN '여성' END) AS gender, 
            ROUND(AVG(t1.cnt)) AS cnt 
        FROM (
            SELECT 
                rca.collect_hour AS collect_hour, 
                SUBSTRING(rca.class, 1, 1) AS gender_code, 
                rca.collect_date AS collect_date, 
                SUM(rca.collect_cnt) AS cnt
            FROM rt_collect_all rca 
            WHERE rca.user_id = '{id}' 
              AND rca.work_no = {work_no} 
              AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
              AND rca.del_yn = 0 
            GROUP BY rca.collect_hour, SUBSTRING(rca.class, 1, 1), rca.collect_date
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
    qr23 = "SELECT (CASE WHEN t1.age = '01' THEN '10대 이하' WHEN t1.age = '23' THEN '20~30대' WHEN t1.age = '45' THEN '40~50대' WHEN t1.age = '67' THEN '60대 이상' END) as age, (CASE WHEN t1.age = '01' THEN 1 WHEN t1.age = '23' THEN 2 WHEN t1.age = '45' THEN 3 WHEN t1.age = '67' THEN 4 END) as age_order, sum(t1.cnt) as cnt FROM (SELECT substring(rca.class, 2, 2) as age, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY substring(rca.class, 2, 2) UNION ALL SELECT age, cnt FROM rt_dummy_age) t1 GROUP BY t1.age ORDER BY age_order"
    # chart_age = {
    #     "chart_id": "age_ratio",
    #     "title": "연령별 통행량",
    #     "type": "echarts_pie",
    #     "df": conn.query(qr23.format(**variables1), ttl=600),
    # }

    chart_age = {
        "chart_id": "age_pie",
        "title": "연령별 통행량",
        "type": "echarts_pie",
        "df": conn.query(qr23.format(**variables1), ttl=600),
        "name_col": "age",
        "value_col": "cnt",
        "semi_pie": "down"
    }

    qr24 = "SELECT t1.collect_hour as hour, (CASE WHEN t1.age = '01' THEN '10대 이하' WHEN t1.age = '23' THEN '20~30대' WHEN t1.age = '45' THEN '40~50대' WHEN t1.age = '67' THEN '60대 이상' END) as age, sum(t1.cnt) as cnt FROM (SELECT rca.collect_hour as collect_hour, substring(rca.class, 2, 2) as age, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND (rca.class like 'm%' OR rca.class like 'w%') and rca.del_yn = 0 GROUP BY rca.collect_hour, substring(rca.class, 2, 2)) t1 GROUP BY t1.collect_hour, t1.age"
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
    qr31 = "SELECT rca.direction as direction, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.direction"
    # chart_dir = {
    #     "chart_id": "dir_bar",
    #     "title": "방향별 통행량",
    #     "type": "bar",
    #     "df": conn.query(qr31.format(**variables1), ttl=600),
    #     "x": "direction",
    #     "y": "cnt",
    #     "x_label": "방향별",
    #     "y_label": "통행량",
    # }

    # chart_dir = {
    #     "chart_id": "dir_ratio",
    #     "title": "방향별 통행량",
    #     "type": "echarts_pie",
    #     "df": conn.query(qr31.format(**variables1), ttl=600),
    # }

    chart_direction = {
        "chart_id": "direction_pie",
        "title": "방향별 통행량",
        "type": "echarts_pie",
        "df": conn.query(qr31.format(**variables1), ttl=600),
        "name_col": "direction",
        "value_col": "cnt",
        "semi_pie": "up"
    }

    qr32 = "SELECT rca.collect_hour as collect_hour, rca.direction as direction, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_hour, rca.direction"
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