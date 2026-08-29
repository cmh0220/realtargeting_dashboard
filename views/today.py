import streamlit as st
import datetime

# # Realtargeting 로고
st.logo("images/logo_wide.png", size="large", link="https://realtargeting.streamlit.app")

conn = st.connection("mysql", type='sql')

st.subheader("일일 모니터링", divider="blue")
st.write(" ")

# session_state에 키가 없거나 값이 None/빈값인 경우를 안전하게 체크
user_id = st.session_state.get("id") or st.session_state.get("user_id")
user_re = st.session_state.get("re") or st.session_state.get("user_re")

if not user_id or not user_re:
    st.write("⚠️아이디 및 등록번호를 확인하세요.")
    # st.toast("⚠️아이디 및 등록번호를 확인하세요.")
else:
    d = st.date_input("📆조회일자를 선택하세요.", "today", datetime.date(2024, 7, 1))
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
    variables1 = {"id": st.session_state['id'], "re": st.session_state['re'], "today":d.strftime('%Y%m%d')}
    df1 = conn.query(qr1.format(**variables1), ttl=600)
    st.bar_chart(df1, x="collect_hour", y='cnt', x_label='시간', y_label='통행량')

    # ------------------------------- 쿼리 2
    left, right = st.columns([0.3, 0.7], gap="small", vertical_alignment="bottom")

    # ------------------------------- 쿼리 2-1
    left.write("성별 통행량")
    left.write(" ")
    qr21 = """
            select (CASE WHEN substring(rca.class,1,1) = 'm' THEN '남성'
            WHEN substring(rca.class,1,1) = 'w' THEN '여성' END) as gender, sum(rca.collect_cnt) as cnt
              from rt_collect_all rca 
             where rca.user_id = '{id}'
               and rca.work_no = {re}  
               and rca.collect_date = '{today}'       
               and (rca.class like 'm%' OR rca.class like 'w%')
              group by (CASE WHEN substring(rca.class,1,1) = 'm' THEN '남성'
            WHEN substring(rca.class,1,1) = 'w' THEN '여성' END)
        """
    df21 = conn.query(qr21.format(**variables1), ttl=600)
    left.bar_chart(df21, x="gender", y='cnt', x_label='성별', y_label='통행량')

    # ------------------------------- 쿼리 2-2

    right.write("시간대별 통행량")
    right.write(" ")

    qr22 = """
        select
        t1.collect_hour as hour, substring(t1.gender, 1, 1) as gender, round(sum(t1.cnt)) as cnt
        from
        (
            select rca.collect_hour as collect_hour, rca.class as gender, rca.collect_date as collect_date, sum(rca.collect_cnt) as cnt
            from rt_collect_all rca
            where rca.user_id = '{id}'
            and rca.work_no = {re} and rca.collect_date = '{today}' and (rca.class like 'm%' OR rca.class like 'w%')
            group by rca.collect_hour, rca.class , rca.collect_date
            UNION ALL 
            select d.collect_hour, 'm01' as gender, '{today}' as collect_date, d.cnt 
              from rt_dummy_hour d
              ) t1
        group by t1.collect_hour, substring(t1.gender, 1, 1)"""

    df22 = conn.query(qr22.format(**variables1), ttl=600)
    right.area_chart(df22, x="hour", y='cnt', color='gender', x_label='시간', y_label='통행량', use_container_width=True)


    # ------------------------------- 쿼리 3
    left2, right2 = st.columns([0.3, 0.7], gap="small", vertical_alignment="bottom")

    # ------------------------------- 쿼리 3-1
    left2.write("‍연령별 통행량")
    left2.write(" ")
    qr31 = """
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
                   and rca.collect_date = '{today}'
                   and (rca.class like 'm%' OR rca.class like 'w%')
                  group by substring(rca.class, 2, 2)
                union all
                select age, cnt
                from rt_dummy_age) t1
            group by t1.age
            """
    df31 = conn.query(qr31.format(**variables1), ttl=600)
    left2.bar_chart(df31, x="age", y='cnt', x_label='연령대', y_label='통행량')

    # ------------------------------- 쿼리 3-2
    right2.write("시간대별 통행량")
    right2.write(" ")

    qr32 = """
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
                   and rca.collect_date = '{today}'
                   and (rca.class like 'm%' OR rca.class like 'w%')
                  group by rca.collect_hour, substring(rca.class, 2, 2)) t1
            group by t1.collect_hour, t1.age
"""

    df32 = conn.query(qr32.format(**variables1), ttl=600)
    right2.area_chart(df32, x="hour", y='cnt', color='age', x_label='시간', y_label='통행량', use_container_width=True)