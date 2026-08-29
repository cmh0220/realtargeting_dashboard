from typing import Any, Dict, List
import streamlit as st
from streamlit_echarts import st_echarts

# ------------------------------------------------------------------------------
# 1. 공통 차트 렌더러 (Chart Component Functions)
# ------------------------------------------------------------------------------


def render_metric_cards(df_h1, df_h2, df_h3, df_h4):
    """상단 주요 지표 카드를 출력합니다."""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "전체 누적 통행량",
        f"{format(round(int(df_h1.iloc[0, 0])), ',')}명",
        "1,200 명",
    )
    col2.metric(
        "일평균 통행량",
        f"{format(round(int(df_h2.iloc[0, 0])), ',')}명",
        "1,200 명",
    )
    col3.metric(
        "시간당 통행량",
        f"{format(round(int(df_h3.iloc[0, 0])), ',')}명",
        "1,200 명",
    )
    col4.metric(
        "분당 통행량",
        f"{format(round(int(df_h4.iloc[0, 0])), ',')}명",
        "-1,200 명",
    )


def render_chart_item(chart_info: Dict[str, Any]):
    """개별 차트 데이터를 받아 유형에 맞는 Streamlit 차트를 출력합니다."""
    title = chart_info.get("title", "")
    chart_type = chart_info.get("type", "bar")
    df = chart_info.get("df")

    st.write(f"😊{title}")
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
        # ECharts 데이터 변환 및 옵션 구성
        chart_data = [
            {"name": row["age"], "value": int(row["cnt"])}
            for _, row in df.iterrows()
        ]
        options = {
            "tooltip": {
                "trigger": "item",
                "formatter": "{b}: {c} ({d}%)",
            },
            "legend": {"bottom": "5%", "left": "center"},
            "series": [
                {
                    "name": title,
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "center": ["50%", "50%"],
                    "startAngle": 0,
                    "endAngle": 180,
                    "data": chart_data,
                }
            ],
        }
        st_echarts(options=options, height="300px")

    elif chart_type == "echarts_pie_gender":
        # 데이터프레임 컬럼명 유연하게 매핑 (기본값: age / cnt)
        name_col = chart_info.get("name_col", "age")
        val_col = chart_info.get("value_col", "cnt")

        chart_data = [
            {"name": row[name_col], "value": int(row[val_col])}
            for _, row in df.iterrows()
        ]

        # 제시해주신 ECharts 예제 옵션 적용
        options = {
            "tooltip": {
                "trigger": "item",
                "formatter": "{b}: {c} ({d}%)",
            },
            "legend": {"top": "5%", "left": "center"},
            "series": [
                {
                    "name": title,
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "center": ["50%", "50%"],
                    "startAngle": 180,
                    "endAngle": 360,
                    "data": chart_data,
                }
            ],
        }

        # 반원 차트 형태에 맞춰 높이를 조정하여 출력
        st_echarts(options=options, height="300px")


def render_chart_grid(
    charts: List[Dict[str, Any]],
    cols_per_row: int = 3,
    ratios: List[float] = None,
):
    """차트 리스트를 받아 지정한 열 개수(cols_per_row)나 비율(ratios)에 맞춰 자동으로 행을 나누어 배치합니다."""
    for i in range(0, len(charts), cols_per_row):
        row_charts = charts[i : i + cols_per_row]

        # 비율 지정이 있으면 사용하고, 없으면 균등 분hal
        if ratios and len(ratios) == len(row_charts):
            cols = st.columns(ratios, vertical_alignment="bottom")
        else:
            cols = st.columns(len(row_charts), vertical_alignment="bottom")

        for idx, chart in enumerate(row_charts):
            with cols[idx]:
                render_chart_item(chart)


# ------------------------------------------------------------------------------
# 2. 메인 페이지 로직
# ------------------------------------------------------------------------------

# 로고 설정
st.logo(
    "images/logo_wide.png",
    size="large",
    link="https://realtargeting.streamlit.app",
    # icon_image="images/단순창발효관광재단 로고.png",
)

conn = st.connection("mysql", type="sql")

if st.session_state.get("id") is None or st.session_state.get("re") is None:
    st.write("⚠️아이디 및 등록번호를 확인하세요.")
    st.toast("⚠️아이디 및 등록번호를 확인하세요.")
else:
    variables1 = {"id": st.session_state["id"], "re": st.session_state["re"]}

    # --------------------------------------------------------------------------
    # A. Metric 상단 지표 조회 및 렌더링
    # --------------------------------------------------------------------------
    qr_h1 = "SELECT sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND rca.del_yn = 0"
    qr_h2 = "SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND rca.collect_hour >= '07' GROUP BY rca.collect_date) t1"
    qr_h3 = "SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND rca.collect_hour >= '07' GROUP BY rca.collect_date, rca.collect_hour) t1"
    qr_h4 = "SELECT round(avg(t1.cnt)/60) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND rca.collect_hour >= '07' GROUP BY rca.collect_date, rca.collect_hour) t1"

    df_h1 = conn.query(qr_h1.format(**variables1), ttl=600)
    df_h2 = conn.query(qr_h2.format(**variables1), ttl=600)
    df_h3 = conn.query(qr_h3.format(**variables1), ttl=600)
    df_h4 = conn.query(qr_h4.format(**variables1), ttl=600)

    render_metric_cards(df_h1, df_h2, df_h3, df_h4)
    st.write(" ")

    # --------------------------------------------------------------------------
    # B. 데이터 조회 및 차트 메타데이터 정의
    # --------------------------------------------------------------------------

    # 1. 날짜별 통행량
    qr1 = """
        SELECT DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, SUM(rca.collect_cnt) AS cnt, SUM(rca.collect_cnt * 1000) AS amt 
        FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND rca.del_yn = 0 
        GROUP BY DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') ORDER BY MIN(STR_TO_DATE(rca.collect_date, '%Y%m%d'));
    """
    chart_date = {
        "title": "날짜별 통행량",
        "type": "bar",
        "df": conn.query(qr1.format(**variables1), ttl=600),
        "x": "collect_date",
        "y": "cnt",
        "x_label": "일자",
        "y_label": "통행량",
    }

    # 2. 시간대별 통행량
    qr3 = """
        SELECT tt1.collect_hour, sum(tt1.cnt) as cnt FROM (
            SELECT t1.collect_hour, round(avg(t1.cnt)) as cnt FROM (
                SELECT rca.collect_hour as collect_hour, rca.collect_date as collect_date, sum(rca.collect_cnt) as cnt   
                FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} GROUP BY rca.collect_hour, rca.collect_date
            ) t1 GROUP BY t1.collect_hour
            UNION ALL 
            SELECT d.collect_hour, d.cnt FROM rt_dummy_hour d
        ) tt1 GROUP BY tt1.collect_hour ORDER BY tt1.collect_hour
    """
    chart_hour = {
        "title": "시간대별 통행량",
        "type": "area",
        "df": conn.query(qr3.format(**variables1), ttl=600),
        "x": "collect_hour",
        "y": "cnt",
        "x_label": "시간",
        "y_label": "통행량",
    }

    # 3. 요일별(시간대) 평균 통행량
    qr2 = """
        SELECT t1.collect_hour, t1.collect_day, t1.collect_order, avg(t1.cnt) as cnt FROM (
            SELECT 
                (CASE WHEN rca.collect_day = 'Sun' THEN '일' WHEN rca.collect_day = 'Mon' THEN '월' WHEN rca.collect_day = 'Tue' THEN '화' WHEN rca.collect_day = 'Wed' THEN '수' WHEN rca.collect_day = 'Thu' THEN '목' WHEN rca.collect_day = 'Fri' THEN '금' WHEN rca.collect_day = 'Sat' THEN '토' END) as collect_day,
                (CASE WHEN rca.collect_day = 'Sun' THEN 1 WHEN rca.collect_day = 'Mon' THEN 2 WHEN rca.collect_day = 'Tue' THEN 3 WHEN rca.collect_day = 'Wed' THEN 4 WHEN rca.collect_day = 'Thu' THEN 5 WHEN rca.collect_day = 'Fri' THEN 6 WHEN rca.collect_day = 'Sat' THEN 7 END) as collect_order,
                rca.collect_hour as collect_hour, rca.collect_date as collect_date, sum(rca.collect_cnt) as cnt
            FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re}
            GROUP BY collect_day, collect_order, rca.collect_hour, rca.collect_date
        ) t1 GROUP BY t1.collect_hour, t1.collect_day, t1.collect_order ORDER BY t1.collect_hour, t1.collect_day, t1.collect_order
    """
    chart_day_hour = {
        "title": "요일별(시간대) 평균 통행량",
        "type": "area",
        "df": conn.query(qr2.format(**variables1), ttl=600),
        "x": "collect_hour",
        "y": "cnt",
        "color": "collect_day",
        "x_label": "요일",
        "y_label": "통행량",
    }

    # 4. 성별 통행량
    qr21 = """
        SELECT 
            (CASE WHEN substring(rca.class,1,1) = 'm' THEN '남성' 
                  WHEN substring(rca.class,1,1) = 'w' THEN '여성' END) as gender, 
            sum(rca.collect_cnt) as cnt
        FROM rt_collect_all rca 
        WHERE rca.user_id = '{id}' 
          AND rca.work_no = {re} 
          AND (rca.class like 'm%' OR rca.class like 'w%')
        GROUP BY gender
    """

    chart_gender = {
        "title": "성별 통행량",
        "type": "echarts_pie_gender",
        "df": conn.query(qr21.format(**variables1), ttl=600),
        "name_col": "gender",  # 범례/라벨로 사용할 컬럼명
        "value_col": "cnt",  # 수치로 사용할 컬럼명
    }

    # 5. 성별(시간대) 평균 통행량
    qr22 = """
        SELECT t1.collect_hour as hour, substring(t1.gender,1,1) as gender, round(avg(t1.cnt)) as cnt FROM (
            SELECT rca.collect_hour as collect_hour, rca.class as gender, rca.collect_date as collect_date, sum(rca.collect_cnt) as cnt
            FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND (rca.class like 'm%' OR rca.class like 'w%')
            GROUP BY rca.collect_hour, rca.class, rca.collect_date
        ) t1 GROUP BY t1.collect_hour, substring(t1.gender,1,1)
    """
    chart_gender_hour = {
        "title": "성별(시간대) 평균 통행량",
        "type": "area",
        "df": conn.query(qr22.format(**variables1), ttl=600),
        "x": "hour",
        "y": "cnt",
        "color": "gender",
        "x_label": "시간대",
        "y_label": "통행량",
    }

    # 6. 연령별 통행량 (ECharts)
    qr23 = """
        SELECT (CASE WHEN t1.age = '01' THEN '10대 이하' WHEN t1.age = '23' THEN '20~30대' WHEN t1.age = '45' THEN '40~50대' WHEN t1.age = '67' THEN '60대 이상' END) as age,
               (CASE WHEN t1.age = '01' THEN 1 WHEN t1.age = '23' THEN 2 WHEN t1.age = '45' THEN 3 WHEN t1.age = '67' THEN 4 END) as age_order, sum(t1.cnt) as cnt
        FROM (
            SELECT substring(rca.class, 2, 2) as age, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY substring(rca.class, 2, 2)
            UNION ALL SELECT age, cnt FROM rt_dummy_age
        ) t1 GROUP BY t1.age ORDER BY age_order
    """
    chart_age = {
        "title": "연령별 통행량",
        "type": "echarts_pie",
        "df": conn.query(qr23.format(**variables1), ttl=600),
    }

    # 7. 연령별(시간대) 평균 통행량
    qr24 = """
        SELECT t1.collect_hour as hour,
               (CASE WHEN t1.age = '01' THEN '10대 이하' WHEN t1.age = '23' THEN '20~30대' WHEN t1.age = '45' THEN '40~50대' WHEN t1.age = '67' THEN '60대 이상' END) as age,
               sum(t1.cnt) as cnt
        FROM (
            SELECT rca.collect_hour as collect_hour, substring(rca.class, 2, 2) as age, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND (rca.class like 'm%' OR rca.class like 'w%') GROUP BY rca.collect_hour, substring(rca.class, 2, 2)
        ) t1 GROUP BY t1.collect_hour, t1.age
    """
    chart_age_hour = {
        "title": "연령별(시간대) 평균 통행량",
        "type": "area",
        "df": conn.query(qr24.format(**variables1), ttl=600),
        "x": "hour",
        "y": "cnt",
        "color": "age",
        "x_label": "시간대",
        "y_label": "통행량",
    }

    # 8. 방향별 통행량
    qr31 = "SELECT rca.direction as direction, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} GROUP BY rca.direction"
    chart_dir = {
        "title": "방향별 통행량",
        "type": "bar",
        "df": conn.query(qr31.format(**variables1), ttl=600),
        "x": "direction",
        "y": "cnt",
        "x_label": "방향별",
        "y_label": "통행량",
    }

    # 9. 방향별(시간대) 평균 통행량
    qr32 = "SELECT rca.collect_hour as collect_hour, rca.direction as direction, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} GROUP BY rca.collect_hour, rca.direction"
    chart_dir_hour = {
        "title": "방향별(시간대) 평균 통행량",
        "type": "area",
        "df": conn.query(qr32.format(**variables1), ttl=600),
        "x": "collect_hour",
        "y": "cnt",
        "color": "direction",
        "x_label": "시간대",
        "y_label": "통행량",
    }

    # --------------------------------------------------------------------------
    # C. 대시보드 레이아웃 구성 (배치 변경이 필요할 때 여기만 수정)
    # --------------------------------------------------------------------------

    # Row 1
    render_chart_grid(
        [chart_date], cols_per_row=1
    )

    # Row 2
    render_chart_grid(
        [chart_hour, chart_day_hour], cols_per_row=2
    )

    # Row 3
    render_chart_grid(
        [chart_gender, chart_gender_hour],
        cols_per_row=2
    )

    # Row 4
    render_chart_grid(
        [chart_age, chart_age_hour],
        cols_per_row=2
    )

    # Row 5
    render_chart_grid(
        [chart_dir, chart_dir_hour], cols_per_row=2, ratios=[0.2, 0.8]
    )