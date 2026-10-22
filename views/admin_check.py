import streamlit as st
from sqlalchemy import text

# ===================================================================
# 권한 체크 (notreal 계정만 접근 가능)
# ===================================================================
if st.session_state.get("user_id") != "notreal":
    st.error("⚠️ 접근 권한이 없습니다. 관리자(notreal) 계정으로 로그인해 주세요.")
    st.stop()

st.title("📋 일일점검 현황")
st.markdown("오늘 날짜 기준 수집 데이터 상태를 실시간으로 점검합니다.")

# DB 연결
conn = st.connection("mysql", type="sql")

# ===================================================================
# 상단 제어 영역 (새로고침 버튼)
# ===================================================================
col_left, col_right = st.columns([3, 1])
with col_right:
    # 새로고침 버튼 클릭 시 페이지를 재실행하여 실시간 데이터 조회
    if st.button("🔄 새로고침", width="stretch", type="secondary"):
        st.rerun()

# ===================================================================
# 일일점검 쿼리 실행
# ===================================================================
check_sql = """
    SELECT 
        -- 1. 최종 상태 (사유가 하나라도 있으면 '점검', 없으면 '정상')
        CASE 
            WHEN a.work_no IS NULL
              OR (i.user_id <> a.user_id)
              OR (a.device_no <> i.device_no)
              OR (i.start_date > a.collect_date)
              OR (i.end_date < a.collect_date)
              OR (i.start_time <> MIN(a.collect_hour))
              OR (HOUR(NOW()) - CAST(MAX(a.collect_hour) AS UNSIGNED) > 1)
            THEN '점검'
            ELSE '정상'
        END AS '상태',

        -- 2. 상세 점검 사유 (상태 바로 다음 위치)
        CASE 
            WHEN a.work_no IS NULL THEN '실적 데이터 미수집'
            ELSE NULLIF(CONCAT_WS(', ',
                CASE WHEN i.user_id <> a.user_id THEN '사용자 불일치' END,
                CASE WHEN a.device_no <> i.device_no THEN '장비번호 불일치' END,
                CASE WHEN i.start_date > a.collect_date THEN '시작일 이전 수집' END,
                CASE WHEN i.end_date < a.collect_date THEN '종료일 이후 수집' END,
                CASE WHEN i.start_time <> MIN(a.collect_hour) THEN '시작시간 불일치' END,
                CASE WHEN HOUR(NOW()) - CAST(MAX(a.collect_hour) AS UNSIGNED) > 1 THEN '1시간 이상 수집지연' END
            ), '')
        END AS '내용',

        i.work_no AS i_work_no,
        i.user_id AS i_user_id,
        a.user_id AS c_user_id,
        i.device_no AS i_dev_no,
        a.device_no AS c_dev_no,
        i.start_date as 'i_시작일자',
        a.collect_date as '●수집일자',
        i.end_date as 'i_종료일자',
        i.start_time as 'i_시작시간',
        MIN(a.collect_hour) AS '●시작시간',
        i.end_time as 'i_종료시간',
        MAX(a.collect_hour) AS '●마지막시간'
    FROM rt_collect_info i
    LEFT JOIN rt_collect_all a 
           ON i.work_no = a.work_no 
          AND a.collect_date = DATE_FORMAT(CURDATE(), '%Y%m%d')
          AND a.del_yn = 0
    WHERE i.start_date <= DATE_FORMAT(CURDATE(), '%Y%m%d')
      AND i.end_date >= DATE_FORMAT(CURDATE(), '%Y%m%d')
    GROUP BY 
        i.work_no,
        i.user_id,
        a.user_id,
        i.device_no,
        a.device_no,
        i.start_date,
        i.end_date,
        a.collect_date,
        i.start_time,
        i.end_time
    ORDER BY 
        i.work_no,
        a.collect_date DESC
"""

try:
    # ttl=0을 주어 쿼리 결과가 캐시되지 않고 매번 새로 조회되도록 설정
    df_check = conn.query(check_sql, ttl=0)

    if df_check.empty:
        st.info("오늘 날짜 기준으로 대상 데이터가 없습니다.")
    else:
        # 요약 지표 표시
        total_cnt = len(df_check)
        abnormal_cnt = len(df_check[df_check["상태"] == "점검"])
        normal_cnt = total_cnt - abnormal_cnt

        m1, m2, m3 = st.columns(3)
        m1.metric("총 점검 대상", f"{total_cnt}건")
        m2.metric("정상", f"{normal_cnt}건", delta=None)
        m3.metric("점검 필요", f"{abnormal_cnt}건", delta=f"-{abnormal_cnt}" if abnormal_cnt > 0 else "0", delta_color="inverse")

        st.markdown("---")

        # 데이터프레임 시각화 (전체 화면 활용)
        st.dataframe(
            df_check,
            use_container_width=True,
            hide_index=True,
        )

except Exception as e:
    st.error(f"데이터 조회 중 오류가 발생했습니다: {e}")