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

        /* 셀렉트박스 입력창 커서 숨김, 입력 차단 및 선택 불가 처리 */
        div[data-baseweb="select"] input {
            caret-color: transparent !important;
            user-select: none !important;
        }

        div[data-baseweb="select"], div[data-baseweb="select"] * {
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

    col_info, col_map = st.columns([3, 2], gap="medium")

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


def render_metric_cards(df_h2, df_h3, df_h4, df_h7):
    """상단 주요 지표 카드를 출력합니다."""
    col1, col2, col3, col4 = st.columns(4)

    def get_val_cnt(df, surfix):
        if df is not None and not df.empty and df.iloc[0, 0] is not None:
            return f"{int(round(float(df.iloc[0, 0]))):,}{surfix}"
        return f"0{surfix}"

    def get_val_sec(df, surfix):
        if df is not None and not df.empty and df.iloc[0, 0] is not None:
            return f"{float(df.iloc[0, 0]):,.1f}{surfix}"
        return f"0.0{surfix}"

    col1.metric("총 통행량", get_val_cnt(df_h2, "명"))
    col2.metric("시간당 통행량", get_val_cnt(df_h3, "명"))
    col3.metric("분당 통행량", get_val_cnt(df_h4, "명"))
    col4.metric("평균 체류시간", get_val_sec(df_h7, "초"))


def render_chart_item(chart_info: Dict[str, Any]):
    """개별 차트 데이터를 받아 유형에 맞는 Streamlit/ECharts 차트를 출력합니다."""
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
            "tooltip": {
                "trigger": "item",
                "formatter": "{b}: {c:,}명 ({d}%)"
            },
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
        st_echarts(options=options, height=chart_info.get("height", "350px"), key=comp_key)

    elif chart_type == "echarts_line":
        x_col = chart_info.get("x_col", "collect_hour")
        y_col = chart_info.get("y_col", "cnt")

        x_data = [f"{int(h):02d}시" if str(h).isdigit() else str(h) for h in df[x_col].tolist()]
        y_data = df[y_col].tolist()

        option = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value", "name": chart_info.get("y_name", "통행량")},
            "series": [{"data": y_data, "type": "line", "areaStyle": {}}],
            "grid": {"top": "15%", "left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        }
        st_echarts(options=option, height=chart_info.get("height", "350px"), key=comp_key)

    elif chart_type == "echarts_multi_line":
        index_col = chart_info.get("index_col", "collect_hour")
        columns_col = chart_info.get("columns_col", "gender_age")
        values_col = chart_info.get("values_col", "cnt")
        y_name = chart_info.get("y_name", "통행량")

        pivot_df = df.pivot(index=index_col, columns=columns_col, values=values_col).fillna(0)
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
        st_echarts(options=option, height=chart_info.get("height", "400px"), key=comp_key)


def render_chart_grid(
        charts: List[Dict[str, Any]],
        cols_per_row: int = 3,
        ratios: List[float] = None,
):
    """차트 리스트를 받아 지정한 열 개수나 비율에 맞춰 그리드로 배치합니다."""
    for i in range(0, len(charts), cols_per_row):
        row_charts = charts[i: i + cols_per_row]
        cols = st.columns(
            ratios if ratios and len(ratios) == len(row_charts) else len(row_charts),
            vertical_alignment="bottom",
        )
        for idx, chart in enumerate(row_charts):
            with cols[idx]:
                render_chart_item(chart)


# ------------------------------------------------------------------------------
# 2. 메인 페이지 로직
# ------------------------------------------------------------------------------

st.logo("images/logo_wide.png", size="large", link="https://realtargeting.streamlit.app")

conn = st.connection("mysql", type="sql")

st.subheader("일일 모니터링", divider="blue")

# 인증 확인 및 로그인 계정의 전체 권한 지점 목록 가져오기
user_id = st.session_state.get("user_id")
work_list = st.session_state.get("work_list", [])

if not user_id or not work_list:
    st.error("⚠️ 로그인 정보가 없거나 열람 가능한 지점이 없습니다. 사이드바에서 먼저 로그인해 주세요.")
    st.stop()
else:

    # 1. 메인 화면에서 전달된 기본 선택 지점(work_no) 확인
    default_work_no = st.session_state.get("selected_work_no")

    # 2. 셀렉트박스 옵션 구성 (한글/영문 Key 호환 대응)
    location_options = [
        item.get("측정지점") or item.get("memo") or item.get("주소") or item.get(
            "location") or f"지점 {item.get('작업번호', item.get('work_no'))}"
        for item in work_list
    ]

    # 3. default_idx 계산
    default_idx = 0
    if default_work_no is not None:
        for idx, item in enumerate(work_list):
            item_work_no = item.get("작업번호") or item.get("work_no")
            if str(item_work_no) == str(default_work_no):
                default_idx = idx
                break

    # 4. 상단 컨트롤러 레이아웃 (지점 선택 + 날짜 선택)
    ctrl_col1, ctrl_col2 = st.columns([3, 2])

    with ctrl_col1:
        selected_location = st.selectbox(
            "📍 측정지점 선택",
            options=location_options,
            index=default_idx,
            key="sb_monitoring_location"
        )

    with ctrl_col2:
        cond_date = st.date_input(
            "📆 조회일자 선택",
            datetime.date.today(),
            min_value=datetime.date(2024, 7, 1)
        )

    # 5. 선택된 지점 상세 데이터 추출
    selected_work_info = work_list[location_options.index(selected_location)]
    selected_work_no = selected_work_info.get("작업번호") or selected_work_info.get("work_no")

    # 세션 정보 최신화
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

    # 6. 기본정보 및 지도 표시
    render_location_map(selected_work_info)
    st.write(" ")

    target_date_str = cond_date.strftime("%Y%m%d")

    # DB 바인딩 파라미터 생성
    variables = {
        "id": user_id,
        "work_no": selected_work_no,
        "today": target_date_str,
        "start_date_str": start_date_str,
        "end_date_str": end_date_str,
        "start_time_str": start_time_str,
        "end_time_str": end_time_str,
    }

    # --------------------------------------------------------------------------
    # A. Metric 상단 지표 조회 및 렌더링
    # --------------------------------------------------------------------------
    qr_h2 = """SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = '{work_no}' AND rca.collect_date = '{today}' and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' and rca.class IN ('m01', 'm23', 'm45', 'm67', 'w01', 'w23', 'w45', 'w67', 'unknown') AND rca.del_yn = 0 GROUP BY rca.collect_date) t1"""

    qr_h3 = """SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND rca.collect_date = '{today}' and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date, rca.collect_hour) t1"""

    qr_h4 = """SELECT round(avg(t1.cnt)/60) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND rca.collect_date = '{today}' and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date, rca.collect_hour) t1"""

    qr_h7 = """SELECT avg(rca.stay_time) as stay_time FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND rca.collect_date = '{today}' AND rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' and (rca.class like 'm%' OR rca.class like 'w%') AND rca.stay_time <> 99999 AND rca.del_yn = 0 """

    render_metric_cards(
        conn.query(qr_h2.format(**variables), ttl=600),
        conn.query(qr_h3.format(**variables), ttl=600),
        conn.query(qr_h4.format(**variables), ttl=600),
        conn.query(qr_h7.format(**variables), ttl=600),
    )
    st.write(" ")

    # --------------------------------------------------------------------------
    # B. 차트 데이터 메타데이터 정의 및 조회
    # --------------------------------------------------------------------------

    # 1. 당일 시간대별 통행량
    qr_hour = """
        SELECT tt1.collect_hour, SUM(tt1.cnt) AS cnt, SUM(tt1.stay_time) as stay_time
        FROM (
            SELECT t1.collect_hour, ROUND(AVG(t1.cnt)) AS cnt, AVG(t1.stay_time) AS stay_time
            FROM (
                SELECT rca.collect_hour AS collect_hour, rca.collect_date AS collect_date, SUM(rca.collect_cnt) AS cnt, avg(rca.stay_time) as stay_time   
                FROM rt_collect_all rca 
                WHERE rca.user_id = '{id}'
                  AND rca.work_no = {work_no}
                  AND rca.collect_date = '{today}'
                  and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
                  AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%')
                  AND rca.del_yn = 0
                  AND rca.stay_time <> 99999
                GROUP BY rca.collect_hour, rca.collect_date
            ) t1
            GROUP BY t1.collect_hour
            UNION ALL 
            SELECT d.collect_hour, d.cnt, 0 as stay_time
            FROM rt_dummy_hour d
        ) tt1
        GROUP BY tt1.collect_hour
        ORDER BY tt1.collect_hour
    """

    chart_hour = {
        "chart_id": "daily_hour_traffic",
        "title": "시간대별 통행량",
        "type": "echarts_line",
        "df": conn.query(qr_hour.format(**variables), ttl=600),
        "x_col": "collect_hour",
        "y_col": "cnt",
        "y_name": "통행량",
    }

    chart_stay_time = {
        "chart_id": "daily_hour_stay_time",
        "title": "시간대별 체류시간",
        "type": "echarts_line",
        "df": conn.query(qr_hour.format(**variables), ttl=600),
        "x_col": "collect_hour",
        "y_col": "stay_time",
        "y_name": "체류시간",
    }

    # 2. 당일 성별 통행량 (파이 차트)
    qr_gender = """
        SELECT 
            (CASE WHEN rca.gender = 'male' THEN '남성' 
                  WHEN rca.gender = 'female' THEN '여성' END) AS gender,
            SUM(rca.collect_cnt) AS cnt 
        FROM rt_collect_all rca 
        WHERE rca.user_id = '{id}' 
          AND rca.work_no = {work_no} 
          AND rca.collect_date = '{today}'
          and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
          AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
          AND rca.del_yn = 0 
        GROUP BY (CASE WHEN rca.gender = 'male' THEN '남성' 
                       WHEN rca.gender = 'female' THEN '여성' END)
    """

    chart_gender = {
        "chart_id": "daily_gender_pie",
        "title": "성별 통행량 비율",
        "type": "echarts_pie",
        "df": conn.query(qr_gender.format(**variables), ttl=600),
        "name_col": "gender",
        "value_col": "cnt",
        "semi_pie": "up",
    }

    # 3. 당일 성별/시간대별 통행량 (멀티 라인)
    qr_gender_hour = """
        SELECT 
            rca.collect_hour AS collect_hour, 
            (CASE WHEN rca.gender = 'male' THEN '남성' 
                  WHEN rca.gender = 'female' THEN '여성' END) AS gender, 
            SUM(rca.collect_cnt) AS cnt 
        FROM rt_collect_all rca 
        WHERE rca.user_id = '{id}' 
          AND rca.work_no = {work_no} 
          AND rca.collect_date = '{today}'
          and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
          AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
          AND rca.del_yn = 0 
        GROUP BY rca.collect_hour, (CASE WHEN rca.gender = 'male' THEN '남성' 
                  WHEN rca.gender = 'female' THEN '여성' END)
        ORDER BY rca.collect_hour
    """

    chart_gender_hour = {
        "chart_id": "daily_gender_hour",
        "title": "성별/시간대별 통행량",
        "type": "echarts_multi_line",
        "df": conn.query(qr_gender_hour.format(**variables), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "gender",
        "values_col": "cnt",
        "y_name": "통행량",
    }

    # 4. 당일 연령별 통행량 (파이 차트)
    qr_age = """
        SELECT 
            rca.age AS age, 
            SUM(rca.collect_cnt) AS cnt 
        FROM rt_collect_all rca 
        WHERE rca.user_id = '{id}' 
          AND rca.work_no = {work_no} 
          AND rca.collect_date = '{today}'
          and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
          AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
          AND rca.del_yn = 0 
        GROUP BY rca.age
    """

    chart_age = {
        "chart_id": "daily_age_pie",
        "title": "연령별 통행량 비율",
        "type": "echarts_pie",
        "df": conn.query(qr_age.format(**variables), ttl=600),
        "name_col": "age",
        "value_col": "cnt",
    }

    # 5. 당일 연령별/시간대별 통행량 (멀티 라인)
    qr_age_hour = """
        SELECT 
            rca.collect_hour AS collect_hour, 
            rca.age AS age, 
            SUM(rca.collect_cnt) AS cnt 
        FROM rt_collect_all rca 
        WHERE rca.user_id = '{id}' 
          AND rca.work_no = {work_no} 
          AND rca.collect_date = '{today}'
          and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
          AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
          AND rca.del_yn = 0 
        GROUP BY rca.collect_hour, rca.age
        ORDER BY rca.collect_hour
    """

    chart_age_hour = {
        "chart_id": "daily_age_hour",
        "title": "연령별/시간대별 통행량",
        "type": "echarts_multi_line",
        "df": conn.query(qr_age_hour.format(**variables), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "age",
        "values_col": "cnt",
        "y_name": "통행량",
    }

    # --------------------------------------------------------------------------
    # C. 대시보드 레이아웃 구성
    # --------------------------------------------------------------------------
    render_chart_grid([chart_hour], cols_per_row=1)
    render_chart_grid([chart_stay_time], cols_per_row=1)
    render_chart_grid([chart_gender, chart_gender_hour], cols_per_row=2)
    render_chart_grid([chart_age, chart_age_hour], cols_per_row=2)