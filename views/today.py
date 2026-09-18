import datetime
from typing import Any, Dict, List
import streamlit as st
from streamlit_echarts import st_echarts


# ------------------------------------------------------------------------------
# 1. 공통 차트 렌더러 (Chart Component Functions)
# ------------------------------------------------------------------------------
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

    # 공통 component key 생성
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

    # 2. ECharts 원형/반원 차트 (성별, 연령, 방향 등)
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

    # 3. ECharts 단일 라인/영역 차트
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

    # 4. ECharts 통합 멀티 라인 차트 (성별/연령, 요일별 등)
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
        row_charts = charts[i : i + cols_per_row]
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
st.write(" ")

user_id = st.session_state.get("id") or st.session_state.get("user_id")
user_re = st.session_state.get("re") or st.session_state.get("user_re")

if not user_id or not user_re:
    st.write("⚠️아이디 및 비밀번호를 확인하세요.")
else:
    cond_date = st.date_input("📆조회일자를 선택하세요.", datetime.date.today(), min_value=datetime.date(2024, 7, 1))
    target_date_str = cond_date.strftime("%Y%m%d")
    st.write(" ")

    variables = {
        "id": user_id,
        "re": user_re,
        "today": target_date_str,
    }


    # --------------------------------------------------------------------------
    # A. Metric 상단 지표 조회 및 렌더링
    # --------------------------------------------------------------------------
    qr_h2 = """SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND rca.collect_date = {today} and rca.class IN ('m01', 'm23', 'm45', 'm67', 'w01', 'w23', 'w45', 'w67', 'unknown') AND rca.del_yn = 0 GROUP BY rca.collect_date) t1"""
    qr_h3 = """SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND rca.collect_date = {today} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date, rca.collect_hour) t1"""
    qr_h4 = """SELECT round(avg(t1.cnt)/60) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND rca.collect_date = {today} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date, rca.collect_hour) t1"""
    qr_h7 = """SELECT avg(rca.stay_time) as stay_time FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND rca.collect_date = {today} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.stay_time <> 99999 AND rca.del_yn = 0 """

    render_metric_cards(
        conn.query(qr_h2.format(**variables), ttl=600),
        conn.query(qr_h3.format(**variables), ttl=600),
        conn.query(qr_h4.format(**variables), ttl=600),
        conn.query(qr_h7.format(**variables), ttl=600),
    )
    st.write(" ")

    # --------------------------------------------------------------------------
    # A. 차트 데이터 메타데이터 정의
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
                  AND rca.work_no = {re}
                  AND rca.collect_date = '{today}'
                  AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%')
                  AND rca.del_yn = 0
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
            (CASE WHEN SUBSTRING(rca.class, 1, 1) = 'm' THEN '남성' 
                  WHEN SUBSTRING(rca.class, 1, 1) = 'w' THEN '여성' END) AS gender,
            SUM(rca.collect_cnt) AS cnt 
        FROM rt_collect_all rca 
        WHERE rca.user_id = '{id}' 
          AND rca.work_no = {re} 
          AND rca.collect_date = '{today}'
          AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
          AND rca.del_yn = 0 
        GROUP BY (CASE WHEN SUBSTRING(rca.class, 1, 1) = 'm' THEN '남성' 
                       WHEN SUBSTRING(rca.class, 1, 1) = 'w' THEN '여성' END)
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
            (CASE WHEN SUBSTRING(rca.class, 1, 1) = 'm' THEN '남성' 
                  WHEN SUBSTRING(rca.class, 1, 1) = 'w' THEN '여성' END) AS gender, 
            SUM(rca.collect_cnt) AS cnt 
        FROM rt_collect_all rca 
        WHERE rca.user_id = '{id}' 
          AND rca.work_no = {re} 
          AND rca.collect_date = '{today}'
          AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
          AND rca.del_yn = 0 
        GROUP BY rca.collect_hour, SUBSTRING(rca.class, 1, 1)
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
            (CASE WHEN SUBSTRING(rca.class, 2, 2) = '01' THEN '10대 이하' 
                  WHEN SUBSTRING(rca.class, 2, 2) = '23' THEN '20~30대' 
                  WHEN SUBSTRING(rca.class, 2, 2) = '45' THEN '40~50대' 
                  WHEN SUBSTRING(rca.class, 2, 2) = '67' THEN '60대 이상' END) AS age, 
            SUM(rca.collect_cnt) AS cnt 
        FROM rt_collect_all rca 
        WHERE rca.user_id = '{id}' 
          AND rca.work_no = {re} 
          AND rca.collect_date = '{today}'
          AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
          AND rca.del_yn = 0 
        GROUP BY SUBSTRING(rca.class, 2, 2)
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
            (CASE WHEN SUBSTRING(rca.class, 2, 2) = '01' THEN '10대 이하' 
                  WHEN SUBSTRING(rca.class, 2, 2) = '23' THEN '20~30대' 
                  WHEN SUBSTRING(rca.class, 2, 2) = '45' THEN '40~50대' 
                  WHEN SUBSTRING(rca.class, 2, 2) = '67' THEN '60대 이상' END) AS age, 
            SUM(rca.collect_cnt) AS cnt 
        FROM rt_collect_all rca 
        WHERE rca.user_id = '{id}' 
          AND rca.work_no = {re} 
          AND rca.collect_date = '{today}'
          AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
          AND rca.del_yn = 0 
        GROUP BY rca.collect_hour, SUBSTRING(rca.class, 2, 2)
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
    # B. 대시보드 레이아웃 구성
    # --------------------------------------------------------------------------
    render_chart_grid([chart_hour], cols_per_row=1)
    render_chart_grid([chart_stay_time], cols_per_row=1)
    render_chart_grid([chart_gender, chart_gender_hour], cols_per_row=2)
    render_chart_grid([chart_age, chart_age_hour], cols_per_row=2)