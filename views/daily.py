import streamlit as st

# # Realtargeting 로고
st.logo("images/logo_wide.png", size="large", link="https://realtargeting.streamlit.app", icon_image="images/단순창발효관광재단 로고.png")



# if 'id' not in st.session_state:
#     st.session_state['id'] = None
#
# if 're' not in st.session_state:
#     st.session_state['re'] = None

# with st.sidebar:
#
#
#     # st.text_input("아이디", st.session_state['id2'], disabled=True)
#     # st.text_input("등록번호",  st.session_state['re2'], disabled=True)

conn = st.connection("mysql", type='sql')

st.title("날짜별 분석")
st.write(" ")


if st.session_state['id'] == None or st.session_state['re'] == None:
    st.write("⚠️아이디 및 등록번호를 확인하세요.")
    st.toast("⚠️아이디 및 등록번호를 확인하세요.")
else:
    st.write("😊날짜별 통행량")
    st.write(" ")

    df = conn.query(f"select DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') as collect_date"
                    f",  sum(rca.collect_cnt) as cnt, sum(rca.collect_cnt * 1000) as amt from rt_collect_all rca "
                    f"where rca.user_id = '{st.session_state['id']}' and rca.work_no = {st.session_state['re']} "
                    f"and rca.del_yn = 0 group by DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') order by rca.collect_date;"
        , ttl=600)
    st.bar_chart(df, x="collect_date", y='cnt', x_label='일자', y_label='통행량')

    st.write("😊요일별 평균 통행량")
    st.write(" ")

    df2 = conn.query(
		f"select t1.collect_hour, t1.collect_day, t1.collect_order, avg(t1.cnt)	as cnt \
		from (\
		select (CASE WHEN rca.collect_day = 'Sun' THEN '일'\
				WHEN rca.collect_day = 'Mon' THEN '월'\
				WHEN rca.collect_day = 'Tue' THEN '화'\
				WHEN rca.collect_day = 'Wed' THEN '수'\
				WHEN rca.collect_day = 'Thu' THEN '목'\
				WHEN rca.collect_day = 'Fri' THEN '금'\
				WHEN rca.collect_day = 'Sat' THEN '토'\
				END) as collect_day\
		  ,(CASE WHEN rca.collect_day = 'Sun' THEN 1\
				WHEN rca.collect_day = 'Mon' THEN 2\
				WHEN rca.collect_day = 'Tue' THEN 3\
				WHEN rca.collect_day = 'Wed' THEN 4\
				WHEN rca.collect_day = 'Thu' THEN 5\
				WHEN rca.collect_day = 'Fri' THEN 6\
				WHEN rca.collect_day = 'Sat' THEN 7\
				END) as collect_order, rca.collect_hour as collect_hour, rca.collect_date as collect_date, sum(rca.collect_cnt) as cnt\
		  from rt_collect_all rca\
		 where rca.user_id = '{st.session_state['id']}'\
		   and rca.work_no = {st.session_state['re']}\
		  group by (CASE WHEN rca.collect_day = 'Sun' THEN '일'\
				WHEN rca.collect_day = 'Mon' THEN '월'\
				WHEN rca.collect_day = 'Tue' THEN '화'\
				WHEN rca.collect_day = 'Wed' THEN '수'\
				WHEN rca.collect_day = 'Thu' THEN '목'\
				WHEN rca.collect_day = 'Fri' THEN '금'\
				WHEN rca.collect_day = 'Sat' THEN '토'\
				END)\
		  , (CASE WHEN rca.collect_day = 'Sun' THEN 1\
				WHEN rca.collect_day = 'Mon' THEN 2\
				WHEN rca.collect_day = 'Tue' THEN 3\
				WHEN rca.collect_day = 'Wed' THEN 4\
				WHEN rca.collect_day = 'Thu' THEN 5\
				WHEN rca.collect_day = 'Fri' THEN 6\
				WHEN rca.collect_day = 'Sat' THEN 7\
				END), rca.collect_hour, rca.collect_date ) t1\
	group by t1.collect_hour, t1.collect_day, t1.collect_order;", ttl=600)

    st.area_chart(df2, x="collect_hour", y='cnt', color='collect_day', x_label='요일', y_label='통행량')



