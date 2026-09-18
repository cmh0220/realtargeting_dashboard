from typing import Any, Dict, List
import streamlit as st
from streamlit_echarts import st_echarts, JsCode
import datetime

# ------------------------------------------------------------------------------
# 1. 공통 차트 렌더러 (Chart Component Functions)
# ------------------------------------------------------------------------------

def render_chart_item(chart_info: Dict[str, Any]):
    """개별 차트 데이터를 받아 유형에 맞는 Streamlit 차트를 출력합니다."""
    title = chart_info.get("title", "")
    chart_type = chart_info.get("type", "bar")
    df = chart_info.get("df")
    # 고유 key 생성을 위한 chart_id 식별자 추출
    chart_id = chart_info.get("chart_id", "default_chart")

    # 20px 굵은 글씨 스타일 적용
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
            "legend": {"top": "5%", "left": "center"},
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
        st_echarts(options=options, height="300px", key=f"echarts_pie_{chart_id}")

    elif chart_type == "echarts_line":
        # 지정된 X축/Y축 컬럼 읽기
        x_col = chart_info.get("x_col", "collect_hour")
        y_col = chart_info.get("y_col", "cnt")

        x_data = df[x_col].astype(str).tolist()
        y_data = df[y_col].tolist()

        option = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {
                "type": "category",
                "data": x_data,
            },
            "yAxis": {"type": "value"},
            "series": [
                {
                    "data": y_data,
                    "type": "line",
                    "areaStyle": {},
                }
            ],
        }

        st_echarts(options=option, height="300px", key=f"echarts_line_{chart_id}")



    elif chart_type == "echarts_pie_gender":

        name_col = chart_info.get("name_col", "age")

        val_col = chart_info.get("value_col", "cnt")

        chart_data = [

            {"name": row[name_col], "value": int(row[val_col])}

            for _, row in df.iterrows()

        ]

        options = {

            "tooltip": {

                "trigger": "item",

                # ECharts 5.x 이상 지원 기본 툴팁 포맷터 (천 단위 쉼표 적용)

                "valueFormatter": "{value:,}",

            },

            "legend": {"top": "5%", "left": "center"},

            "series": [

                {

                    "name": title,

                    "type": "pie",

                    "radius": ["40%", "70%"],

                    "center": ["50%", "50%"],

                    "startAngle": 90,

                    "endAngle": 270,

                    "data": chart_data,

                }

            ],

        }

        st_echarts(options=options, height="300px", key=f"echarts_gender_{chart_id}")

    elif chart_type == "echarts_multi_line_day_hour":
        # 1. 쿼리 결과(df)를 시간대(행) x 요일(열) 형태의 피벗 테이블로 변환
        # collect_order 순서(월~일)를 유지하기 위해 정렬 보장
        pivot_df = df.pivot(index="collect_hour", columns="collect_day", values="cnt").fillna(0)

        # 요일 순서 고정 (월, 화, 수, 목, 금, 토, 일)
        days_order = ['월', '화', '수', '목', '금', '토', '일']
        existing_days = [day for day in days_order if day in pivot_df.columns]

        # 2. X축(시간대 00~23) 및 시리즈 데이터 구성
        x_data = [f"{int(h):02d}시" for h in pivot_df.index]

        series_list = []
        for day in existing_days:
            series_list.append({
                "name": day,
                "type": "line",
                "data": pivot_df[day].round(1).tolist(),
            })

        # 3. ECharts 옵션 작성
        option = {
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "cross"},
            },
            "legend": {
                "top": "0%",
                "data": existing_days,
            },
            "grid": {
                "top": "15%",
                "left": "3%",
                "right": "4%",
                "bottom": "3%",
                "containLabel": True,
            },
            "xAxis": {
                "type": "category",
                "boundaryGap": False,
                "data": x_data,
            },
            "yAxis": {
                "type": "value",
                "name": "통행량",
            },
            "series": series_list,
        }

        st_echarts(options=option, height="400px", key=f"echarts_day_hour_{chart_id}")

    elif chart_type == "echarts_multi_line_day_hour_gender_age":
        # 1. 쿼리 결과(df)를 시간대(행) x 요일(열) 형태의 피벗 테이블로 변환
        # collect_order 순서(월~일)를 유지하기 위해 정렬 보장
        pivot_df = df.pivot(index="collect_hour", columns="gender_age", values="cnt").fillna(0)

        # 요일 순서 고정 (월, 화, 수, 목, 금, 토, 일)
        days_order = ['월', '화', '수', '목', '금', '토', '일']
        existing_days = [day for day in days_order if day in pivot_df.columns]

        # 2. X축(시간대 00~23) 및 시리즈 데이터 구성
        x_data = [f"{int(h):02d}시" for h in pivot_df.index]

        series_list = []
        for day in existing_days:
            series_list.append({
                "name": day,
                "type": "line",
                "data": pivot_df[day].round(1).tolist(),
            })

        # 3. ECharts 옵션 작성
        option = {
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "cross"},
            },
            "legend": {
                "top": "0%",
                "data": existing_days,
            },
            "grid": {
                "top": "15%",
                "left": "3%",
                "right": "4%",
                "bottom": "3%",
                "containLabel": True,
            },
            "xAxis": {
                "type": "category",
                "boundaryGap": False,
                "data": x_data,
            },
            "yAxis": {
                "type": "value",
                "name": "통행량",
            },
            "series": series_list,
        }

        st_echarts(options=option, height="400px", key=f"echarts_day_hour_{chart_id}")

def render_chart_grid(
    charts: List[Dict[str, Any]],
    cols_per_row: int = 3,
    ratios: List[float] = None,
):
    """차트 리스트를 받아 지정한 열 개수(cols_per_row)나 비율(ratios)에 맞춰 자동으로 행을 나누어 배치합니다."""
    for i in range(0, len(charts), cols_per_row):
        row_charts = charts[i : i + cols_per_row]

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

# # Realtargeting 로고
st.logo("images/logo_wide.png", size="large", link="https://realtargeting.streamlit.app")

conn = st.connection("mysql", type='sql')

st.subheader("일일 모니터링", divider="blue")
st.write(" ")

# session_state에 키가 없거나 값이 None/빈값인 경우를 안전하게 체크
user_id = st.session_state.get("id") or st.session_state.get("user_id")
user_re = st.session_state.get("re") or st.session_state.get("user_re")

if not user_id or not user_re:
    st.write("⚠️아이디 및 비밀번호를 확인하세요.")
    # st.toast("⚠️아이디 및 비밀번호를 확인하세요.")
else:
    cond_date = st.date_input("📆조회일자를 선택하세요.", "today", datetime.date(2024, 7, 1))
    st.write(" ")

    # ------------------------------- 쿼리 1
    st.write("시간대별 통행량")
    st.write(" ")
    qr1 = """
        select tt1.collect_hour, sum(tt1.cnt) as cnt
            from (
            select t1.collect_hour, round(avg(t1.cnt))	as cnt
            from (
            select rca.collect_hour as collect_hour, rca.collect_date as collect_date, sum(rca.collect_cnt) as cnt   
              from rt_collect_all rca 
             where rca.user_id = '{id}'
               and rca.work_no = {re}
               and rca.collect_date = '{today}'
              group by rca.collect_hour, rca.collect_date ) t1
            group by t1.collect_hour
            UNION ALL 
            select d.collect_hour, d.cnt 
              from rt_dummy_hour d  ) tt1
             group by tt1.collect_hour
             order by tt1.collect_hour
    """
    variables1 = {"id": st.session_state['id'], "re": st.session_state['re'], "today":cond_date.strftime('%Y%m%d')}
    chart_hour = {
        "chart_id": "hour_weekday",
        "title": "시간대별 통행량",
        "type": "echarts_line",
        "df": conn.query(qr1.format(**variables1), ttl=600),
        "x_col": "collect_hour",
        "y_col": "cnt",
    }

    # ------------------------------- 쿼리 2

    # ------------------------------- 쿼리 2-1
    # 4. 성별 통행량
    qr21 = """
            SELECT 
                (CASE WHEN substring(rca.class,1,1) = 'm' THEN '남성' 
                      WHEN substring(rca.class,1,1) = 'w' THEN '여성' END) as gender, 
                sum(rca.collect_cnt) as cnt
            FROM rt_collect_all rca 
            WHERE rca.user_id = '{id}' 
              AND rca.work_no = {re} 
              and rca.collect_date = '{today}'
              AND (rca.class like 'm%' OR rca.class like 'w%')
              AND rca.del_yn = 0
            GROUP BY (CASE WHEN substring(rca.class,1,1) = 'm' THEN '남성' 
                      WHEN substring(rca.class,1,1) = 'w' THEN '여성' END)
        """

    chart_gender = {
        "chart_id": "gender_pie",
        "title": "성별 통행량",
        "type": "echarts_pie_gender",
        "df": conn.query(qr21.format(**variables1), ttl=600),
        "name_col": "gender",
        "value_col": "cnt",
    }

    # 5. 성별(시간대) 평균 통행량
    qr22 = """
            SELECT t1.collect_hour as collect_hour, substring(t1.gender,1,1) as gender_age, round(avg(t1.cnt)) as cnt FROM (
                SELECT rca.collect_hour as collect_hour, rca.class as gender, rca.collect_date as collect_date, sum(rca.collect_cnt) as cnt
                FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND (rca.class like 'm%' OR rca.class like 'w%')
                and rca.del_yn = 0 and rca.collect_date = '{today}'
                GROUP BY rca.collect_hour, rca.class, rca.collect_date
            ) t1 GROUP BY t1.collect_hour, substring(t1.gender,1,1)
        """
    chart_gender_hour = {
        "chart_id": "gender_hour2",
        "title": "성별(시간대) 평균 통행량",
        "type": "echarts_multi_line_day_hour_gender_age",
        "df": conn.query(qr22.format(**variables1), ttl=600)
    }

    # 6. 연령별 통행량 (ECharts)
    qr23 = """
            SELECT (CASE WHEN t1.age = '01' THEN '10대 이하' WHEN t1.age = '23' THEN '20~30대' WHEN t1.age = '45' THEN '40~50대' WHEN t1.age = '67' THEN '60대 이상' END) as age,
                   (CASE WHEN t1.age = '01' THEN 1 WHEN t1.age = '23' THEN 2 WHEN t1.age = '45' THEN 3 WHEN t1.age = '67' THEN 4 END) as age_order, sum(t1.cnt) as cnt
            FROM (
                SELECT substring(rca.class, 2, 2) as age, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 and rca.collect_date = '{today}' GROUP BY substring(rca.class, 2, 2)
                UNION ALL SELECT age, cnt FROM rt_dummy_age
            ) t1 GROUP BY t1.age ORDER BY age_order
        """
    chart_age = {
        "chart_id": "age_pie",
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
                SELECT rca.collect_hour as collect_hour, substring(rca.class, 2, 2) as age, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND (rca.class like 'm%' OR rca.class like 'w%') and rca.del_yn = 0 and rca.collect_date = '{today}' GROUP BY rca.collect_hour, substring(rca.class, 2, 2)
            ) t1 GROUP BY t1.collect_hour, t1.age
        """
    chart_age_hour = {
        "chart_id": "age_hour",
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
    qr31 = "SELECT rca.direction as direction, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 and rca.collect_date = '{today}' GROUP BY rca.direction"
    chart_dir = {
        "chart_id": "dir_bar",
        "title": "방향별 통행량",
        "type": "bar",
        "df": conn.query(qr31.format(**variables1), ttl=600),
        "x": "direction",
        "y": "cnt",
        "x_label": "방향별",
        "y_label": "통행량",
    }

    # 9. 방향별(시간대) 평균 통행량
    qr32 = "SELECT rca.collect_hour as collect_hour, rca.direction as direction, sum(rca.collect_cnt) as cnt FROM rt_collect_all rca WHERE rca.user_id = '{id}' AND rca.work_no = {re} AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 and rca.collect_date = '{today}' GROUP BY rca.collect_hour, rca.direction"
    chart_dir_hour = {
        "chart_id": "dir_hour",
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
    # C. 대시보드 레이아웃 구성
    # --------------------------------------------------------------------------

    # Row 1
    render_chart_grid([chart_hour], cols_per_row=1)

    # Row 2
    render_chart_grid([chart_gender, chart_gender_hour], cols_per_row=2)

    # Row 3
    render_chart_grid([chart_age, chart_age_hour], cols_per_row=2)

    # Row 4
    render_chart_grid(
        [chart_dir, chart_dir_hour], cols_per_row=2, ratios=[0.2, 0.8]
    )