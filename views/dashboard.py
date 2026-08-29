import streamlit as st
from streamlit_echarts import st_echarts

# # Realtargeting 로고
st.logo("images/logo_wide.png", size="large", link="https://realtargeting.streamlit.app", icon_image="images/단순창발효관광재단 로고.png")

conn = st.connection("mysql", type='sql')

# st.write(st.session_state)
# 그래프
if st.session_state['id'] == None or st.session_state['re'] == None:
    st.write("⚠️아이디 및 등록번호를 확인하세요.")
    st.toast("⚠️아이디 및 등록번호를 확인하세요.")
else:

    variables1 = {"id": st.session_state['id'], "re": st.session_state['re']}

    qr_h1 = """
        select
        sum(rca.collect_cnt) as cnt
        from rt_collect_all rca
        where
        rca.user_id = '{id}'
        and rca.work_no = {re}
        and rca.del_yn = 0
        """
    df_h1 = conn.query(qr_h1.format(**variables1), ttl=600)

    qr_h2 = """
        select round(avg(t1.cnt)) as avg
        from (
            select rca.collect_date, sum(rca.collect_cnt) as cnt
              from rt_collect_all rca 
             where rca.user_id = '{id}'
               and rca.work_no = {re}   
               and rca.collect_hour >= '07'
             group by rca.collect_date) t1
        """
    df_h2 = conn.query(qr_h2.format(**variables1), ttl=600)

    qr_h3 = """
        select round(avg(t1.cnt)) as avg
        from (
            select rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt
              from rt_collect_all rca 
             where rca.user_id = '{id}'
               and rca.work_no = {re}   
               and rca.collect_hour >= '07'
             group by rca.collect_date, rca.collect_hour) t1
        """
    df_h3 = conn.query(qr_h3.format(**variables1), ttl=600)

    qr_h4 = """
        select round(avg(t1.cnt)/60) as avg
        from (
            select rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt
              from rt_collect_all rca 
             where rca.user_id = '{id}'
               and rca.work_no = {re}   
               and rca.collect_hour >= '07'
             group by rca.collect_date, rca.collect_hour) t1
        """
    df_h4 = conn.query(qr_h4.format(**variables1), ttl=600)


    col1, col2, col3, col4 = st.columns(4)
    col1.metric("전체 누적 통행량", str(format(round(int(df_h1.iloc[0,0]),0), ',')) + "명", "1,200 명")
    col2.metric("일평균 통행량", str(format(round(int(df_h2.iloc[0,0]),0), ',')) + "명", "1,200 명")
    col3.metric("시간당 통행량", str(format(round(int(df_h3.iloc[0,0]),0), ',')) + "명", "1,200 명")
    col4.metric("분당 통행량", str(format(round(int(df_h4.iloc[0,0]),0), ',')) + "명", "-1,200 명")

    st.write(" ")

    left, center, right = st.columns(3, vertical_alignment="bottom")

    left.write("😊날짜별 통행량")
    left.write(" ")
    qr1 = """
        SELECT 
            DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date,
            SUM(rca.collect_cnt) AS cnt, 
            SUM(rca.collect_cnt * 1000) AS amt 
        FROM rt_collect_all rca
        WHERE rca.user_id = '{id}' 
          AND rca.work_no = {re}
          AND rca.del_yn = 0 
        GROUP BY DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') 
        ORDER BY MIN(STR_TO_DATE(rca.collect_date, '%Y%m%d'));
    """
    df1 = conn.query(qr1.format(**variables1), ttl=600)
    left.bar_chart(df1, x="collect_date", y='cnt', x_label='일자', y_label='통행량', height=300)

    center.write("😊시간대별 통행량")
    center.write(" ")
    qr3 = """
            select tt1.collect_hour, sum(tt1.cnt) as cnt
                from (
                select t1.collect_hour, round(avg(t1.cnt))	as cnt
                from (
                select rca.collect_hour as collect_hour, rca.collect_date as collect_date, sum(rca.collect_cnt) as cnt   
                  from rt_collect_all rca 
                 where rca.user_id = '{id}'
                   and rca.work_no = {re}
                   group by rca.collect_hour, rca.collect_date ) t1
                group by t1.collect_hour
                UNION ALL 
                select d.collect_hour, d.cnt 
                  from rt_dummy_hour d  ) tt1
                 group by tt1.collect_hour
                 order by tt1.collect_hour
        """
    df3 = conn.query(qr3.format(**variables1), ttl=600)
    center.area_chart(df3, x="collect_hour", y='cnt', x_label='시간', y_label='통행량', height=300)

    right.write("😊요일별(시간대) 평균 통행량")
    right.write(" ")
    qr2 = """
        select t1.collect_hour, t1.collect_day, t1.collect_order, avg(t1.cnt)	as cnt 
        from (
        select (CASE WHEN rca.collect_day = 'Sun' THEN '일'
                WHEN rca.collect_day = 'Mon' THEN '월'
                WHEN rca.collect_day = 'Tue' THEN '화'
                WHEN rca.collect_day = 'Wed' THEN '수'
                WHEN rca.collect_day = 'Thu' THEN '목'
                WHEN rca.collect_day = 'Fri' THEN '금'
                WHEN rca.collect_day = 'Sat' THEN '토'
                END) as collect_day
          ,(CASE WHEN rca.collect_day = 'Sun' THEN 1
                WHEN rca.collect_day = 'Mon' THEN 2
                WHEN rca.collect_day = 'Tue' THEN 3
                WHEN rca.collect_day = 'Wed' THEN 4
                WHEN rca.collect_day = 'Thu' THEN 5
                WHEN rca.collect_day = 'Fri' THEN 6
                WHEN rca.collect_day = 'Sat' THEN 7
                END) as collect_order, rca.collect_hour as collect_hour, rca.collect_date as collect_date, sum(rca.collect_cnt) as cnt
          from rt_collect_all rca
         where rca.user_id = '{id}'
           and rca.work_no = {re}
          group by (CASE WHEN rca.collect_day = 'Sun' THEN '일'
                WHEN rca.collect_day = 'Mon' THEN '월'
                WHEN rca.collect_day = 'Tue' THEN '화'
                WHEN rca.collect_day = 'Wed' THEN '수'
                WHEN rca.collect_day = 'Thu' THEN '목'
                WHEN rca.collect_day = 'Fri' THEN '금'
                WHEN rca.collect_day = 'Sat' THEN '토'
                END)
          , (CASE WHEN rca.collect_day = 'Sun' THEN 1
                WHEN rca.collect_day = 'Mon' THEN 2
                WHEN rca.collect_day = 'Tue' THEN 3
                WHEN rca.collect_day = 'Wed' THEN 4
                WHEN rca.collect_day = 'Thu' THEN 5
                WHEN rca.collect_day = 'Fri' THEN 6
                WHEN rca.collect_day = 'Sat' THEN 7
                END), rca.collect_hour, rca.collect_date ) t1
    group by t1.collect_hour, t1.collect_day, t1.collect_order
    order by t1.collect_hour, t1.collect_day, t1.collect_order
    """
    df2 = conn.query(qr2.format(**variables1), ttl=600)
    right.area_chart(df2, x="collect_hour", y='cnt', color='collect_day', x_label='요일', y_label='통행량', height=300)

    # 2번째 행

    c1, c2, c3, c4 = st.columns([0.1, 0.3, 0.3, 0.3], vertical_alignment="bottom")

    c1.write("😊성별 통행량")
    c1.write(" ")
    qr21 = """
        select (CASE WHEN substring(rca.class,1,1) = 'm' THEN '남성'
        WHEN substring(rca.class,1,1) = 'w' THEN '여성' END) as gender, sum(rca.collect_cnt) as cnt
          from rt_collect_all rca 
         where rca.user_id = '{id}'
           and rca.work_no = {re}         
           and (rca.class like 'm%' OR rca.class like 'w%')
          group by (CASE WHEN substring(rca.class,1,1) = 'm' THEN '남성'
        WHEN substring(rca.class,1,1) = 'w' THEN '여성' END)
    """
    df21 = conn.query(qr21.format(**variables1), ttl=600)
    c1.bar_chart(df21, x="gender", y='cnt', x_label='성별', y_label='통행량', height=300)


    c2.write("😊성별(시간대) 평균 통행량")
    c2.write(" ")
    qr22 = """
          select t1.collect_hour as hour, substring(t1.gender,1,1) as gender, round(avg(t1.cnt)) as cnt
          from (
        select rca.collect_hour as collect_hour, rca.class as gender, rca.collect_date as collect_date, sum(rca.collect_cnt) as cnt
          from rt_collect_all rca 
         where rca.user_id = '{id}'
           and rca.work_no = {re}
           and (rca.class like 'm%' OR rca.class like 'w%')        
          group by rca.collect_hour, rca.class, rca.collect_date ) t1
          group by t1.collect_hour, substring(t1.gender,1,1)
    """
    df22 = conn.query(qr22.format(**variables1), ttl=600)
    c2.area_chart(df22, x="hour", y='cnt', color='gender', x_label='시간대', y_label='통행량', height=300)


    c3.write("😊연령별 통행량")
    c3.write(" ")
    qr23 = """
            select (CASE WHEN t1.age = '01' THEN '10대 이하'
                        WHEN t1.age = '23' THEN '20~30대'
                        WHEN t1.age = '45' THEN '40~50대'
                        WHEN t1.age = '67' THEN '60대 이상' END) as age
                , (CASE WHEN t1.age = '01' THEN 1
                        WHEN t1.age = '23' THEN 2
                        WHEN t1.age = '45' THEN 3
                        WHEN t1.age = '67' THEN 4 END) as age_order
                    , sum(t1.cnt) as cnt
            from (
                select substring(rca.class, 2, 2) as age, sum(rca.collect_cnt) as cnt
                  from rt_collect_all rca 
                 where rca.user_id = '{id}'
                   and rca.work_no = {re}
                   and (rca.class like 'm%' OR rca.class like 'w%')
                   and rca.del_yn = 0
                  group by substring(rca.class, 2, 2)
                union all
                select age, cnt
                from rt_dummy_age) t1
            group by t1.age
            order by age_order
    """
    df23 = conn.query(qr23.format(**variables1), ttl=600)

    # 1. 데이터프레임을 ECharts가 요구하는 [{"name": ..., "value": ...}] 형태의 리스트로 변환
    chart_data = [
        {"name": row["age"], "value": int(row["cnt"])}
        for _, row in df23.iterrows()
    ]

    # 2. ECharts 옵션 작성 (제공해주신 옵션 구조 활용)
    options = {
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}: {c} ({d}%)"  # 마우스 올렸을 때 [이름: 값 (비율%)] 표시
        },
        "legend": {
            "bottom": "5%",
            "left": "center"
        },
        "series": [
            {
                "name": "연령별 통행량",
                "type": "pie",
                "radius": ["40%", "70%"],
                "center": ["50%", "70%"],
                "startAngle": 0,
                "endAngle": 180,
                "data": chart_data,  # 변환한 데이터 주입
            }
        ],
    }

    # 3. Streamlit에 ECharts 출력 (반원 형태이므로 높이를 300px~350px로 조정하면 여백이 적당합니다)
    with c3:
        st_echarts(options=options, height="300px")


    c4.write("😊연령별(시간대) 평균 통행량")
    c4.write(" ")
    qr24 = """
            select t1.collect_hour as hour
                , (CASE WHEN t1.age = '01' THEN '10대 이하'
                        WHEN t1.age = '23' THEN '20~30대'
                        WHEN t1.age = '45' THEN '40~50대'
                        WHEN t1.age = '67' THEN '60대 이상' END) as age
                , (CASE WHEN t1.age = '01' THEN 1
                        WHEN t1.age = '23' THEN 2
                        WHEN t1.age = '45' THEN 3
                        WHEN t1.age = '67' THEN 4 END) as age_order
                    , sum(t1.cnt) as cnt
            from (
                select rca.collect_hour as collect_hour, substring(rca.class, 2, 2) as age, sum(rca.collect_cnt) as cnt
                  from rt_collect_all rca 
                 where rca.user_id = '{id}'
                   and rca.work_no = {re}   
                   and (rca.class like 'm%' OR rca.class like 'w%')
                  group by rca.collect_hour, substring(rca.class, 2, 2)) t1
            group by t1.collect_hour, t1.age
    """
    df24 = conn.query(qr24.format(**variables1), ttl=600)
    c4.area_chart(df24, x="hour", y='cnt', color='age', x_label='시간대', y_label='통행량', height=300)

    # 3번째 행
    d1, d2 = st.columns([0.2, 0.8], vertical_alignment="bottom")


    d1.write("😊방향별 통행량")
    d1.write(" ")

    qr31 = """
            select rca.direction as direction, sum(rca.collect_cnt) as cnt
              from rt_collect_all rca 
                 where rca.user_id = '{id}'
                   and rca.work_no = {re}     
              group by rca.direction
        """

    df31 = conn.query(qr31.format(**variables1), ttl=600)
    d1.bar_chart(df31, x="direction", y='cnt', x_label='방향별', y_label='통행량', height=300)

    ##########################################
    # d2
    ##########################################
    d2.write("😊방향별(시간대) 평균 통행량")
    d2.write(" ")

    qr32 = """
            select rca.collect_hour as collect_hour, rca.direction as direction, sum(rca.collect_cnt) as cnt
              from rt_collect_all rca 
                 where rca.user_id = '{id}'
                   and rca.work_no = {re}    
              group by rca.collect_hour, rca.direction 
        """

    df32 = conn.query(qr32.format(**variables1), ttl=600)
    d2.area_chart(df32, x="collect_hour", y='cnt', color='direction', x_label='시간대', y_label='통행량', height=300)