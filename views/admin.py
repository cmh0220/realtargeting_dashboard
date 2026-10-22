import streamlit as st
from sqlalchemy import text

# ===================================================================
# 권한 체크 (notreal 계정만 접근 가능)
# ===================================================================
if st.session_state.get("user_id") != "notreal":
    st.error("⚠️ 접근 권한이 없습니다. 관리자(notreal) 계정으로 로그인해 주세요.")
    st.stop()

st.title("🛠️ 기본정보 관리")

# DB 연결
conn = st.connection("mysql", type="sql")

# ===================================================================
# 기기 목록 조회 (device_no 선택용 세그먼트 버튼 구성)
# ===================================================================
device_list_sql = """
    SELECT device_no, device_comment 
    FROM rt_collect_setup 
    ORDER BY device_no ASC
"""
df_setup_devices = conn.query(device_list_sql, ttl=0)

if not df_setup_devices.empty:
    device_options = [f"{row['device_no']}번" for _, row in df_setup_devices.iterrows()]
    device_map = {f"{row['device_no']}번": int(row['device_no']) for _, row in df_setup_devices.iterrows()}
else:
    device_options = ["0번"]
    device_map = {"0번": 0}

# ===================================================================
# 데이터 조회 및 선택 (수정 모드 vs 신규 모드)
# ===================================================================
mode = st.segmented_control(
    "작업 선택",
    options=["데이터 수정", "신규 입력"],
    default="데이터 수정",
    selection_mode="single",
)

if not mode:
    mode = "데이터 수정"

selected_data = {}

if mode == "데이터 수정":
    list_sql = """
        SELECT user_id, work_no, location, memo, user_name, device_no
        FROM rt_collect_info 
        ORDER BY work_no DESC
    """
    df_list = conn.query(list_sql, ttl=0)

    if df_list.empty:
        st.info("수정할 데이터가 없습니다. 먼저 신규 입력을 진행해 주세요.")
        st.stop()

    df_list["display_label"] = (
            df_list["work_no"].astype(str)
            + " / Work "
            + df_list["user_id"]
            + " ( "
            + df_list["location"].fillna("위치없음")
            + " / "
            + df_list["memo"].fillna(" ")
            + " ) 장비번호 : "
            + df_list["device_no"].fillna(0).astype(int).astype(str)
    )

    selected_label = st.selectbox("수정할 대상 선택", df_list["display_label"])

    if selected_label:
        selected_row = df_list[df_list["display_label"] == selected_label].iloc[0]
        target_user_id = selected_row["user_id"]
        target_work_no = selected_row["work_no"]

        detail_sql = """
            SELECT * FROM rt_collect_info 
            WHERE user_id = :user_id AND work_no = :work_no
        """
        df_detail = conn.query(
            detail_sql,
            params={"user_id": target_user_id, "work_no": target_work_no},
            ttl=0,
        )
        if not df_detail.empty:
            selected_data = df_detail.iloc[0].to_dict()

# ===================================================================
# [핵심] 폼 바깥에 배치하여 클릭 즉시 DB를 조회하도록 함
# ===================================================================
st.markdown("### 0.디바이스 번호 (device_no) 선택")

raw_device_no = selected_data.get("device_no")
current_dev_key = f"{int(raw_device_no)}번" if raw_device_no is not None and str(raw_device_no).isdigit() else \
device_options[0]
if current_dev_key not in device_options:
    current_dev_key = device_options[0]

selected_device_key = st.segmented_control(
    "디바이스 번호 선택",
    options=device_options,
    default=current_dev_key,
    selection_mode="single",
    label_visibility="collapsed",
)

if not selected_device_key:
    selected_device_key = current_dev_key

device_no = device_map.get(selected_device_key, 0)

# 🔄 버튼을 누를 때마다(즉시 새로고침되며) 실행되어 DB에서 속성 값을 가져옴
device_info_sql = """
    SELECT device_comment, user_id, work_no 
    FROM rt_collect_setup 
    WHERE device_no = :arg_device_no
"""
df_device_info = conn.query(
    device_info_sql,
    params={"arg_device_no": device_no},
    ttl=0,
)

if not df_device_info.empty:
    d_row = df_device_info.iloc[0]
    comment_val = d_row["device_comment"] if d_row["device_comment"] else "-"
    uid_val = d_row["user_id"] if d_row["user_id"] else "-"
    work_val = d_row["work_no"] if d_row["work_no"] is not None else "-"
    info_str = f"💡 속성 정보: **{comment_val}** / **{uid_val}** / **{work_val}**"
else:
    info_str = "💡 등록된 기기 정보가 없습니다."

st.info(info_str)

# ===================================================================
# 입력 폼 (나머지 컬럼 입력/수정)
# ===================================================================
with st.form("admin_info_form"):
    st.subheader("1. 기본 식별 정보")

    user_id = st.text_input(
        "사용자 ID (user_id)*",
        value=selected_data.get("user_id", ""),
        disabled=(mode == "데이터 수정"),
    )

    work_no = st.number_input(
        "작업 번호 (work_no)*",
        min_value=1,
        value=int(selected_data.get("work_no", 1)) if selected_data.get("work_no") else 1,
        step=1,
        disabled=(mode == "데이터 수정"),
    )

    user_company = st.text_input(
        "기업명 (user_company)", value=selected_data.get("user_company", "") or ""
    )
    user_name = st.text_input(
        "사용자 이름 (user_name)", value=selected_data.get("user_name", "") or ""
    )

    st.subheader("2. 일정 및 시간 정보")
    start_date = st.text_input(
        "시작일자 (start_date, YYYYMMDD)",
        value=selected_data.get("start_date", ""),
        max_chars=8,
    )
    end_date = st.text_input(
        "종료일자 (end_date, YYYYMMDD)",
        value=selected_data.get("end_date", ""),
        max_chars=8,
    )
    start_time = st.text_input(
        "시작시간 (start_time, HH)",
        value=selected_data.get("start_time", ""),
        max_chars=2,
    )
    end_time = st.text_input(
        "종료시간 (end_time, HH)",
        value=selected_data.get("end_time", ""),
        max_chars=2,
    )

    st.subheader("3. 위치 및 메모 정보")
    location = st.text_input(
        "위치 (location)", value=selected_data.get("location", "")
    )
    memo = st.text_area("메모 (memo)", value=selected_data.get("memo", ""))

    col1, col2 = st.columns(2)
    with col1:
        latitude = st.text_input(
            "위도 (latitude)", str(selected_data.get("latitude", ""))
        )
    with col2:
        longitude = st.text_input(
            "경도 (longitude)", str(selected_data.get("longitude", ""))
        )

    left_memo = st.text_input(
        "좌측 메모 (left_memo)", value=selected_data.get("left_memo", "")
    )
    right_memo = st.text_input(
        "우측 메모 (right_memo)", value=selected_data.get("right_memo", "")
    )

    st.subheader("4. 금액 및 상태 정보")
    supply_amount = st.number_input(
        "공급가액 (supply_amount)",
        value=int(selected_data.get("supply_amount", 0) or 0),
    )
    vat_amount = st.number_input(
        "부가세액 (vat_amount)", value=int(selected_data.get("vat_amount", 0) or 0)
    )
    sales_amount = st.number_input(
        "판매금액 (sales_amount)",
        value=int(selected_data.get("sales_amount", 0) or 0),
    )

    status = st.text_input(
        "상태 (status)", value=selected_data.get("status", "")
    )
    view_start_date = st.text_input(
        "열람 시작일 (view_start_date, YYYYMMDD)",
        value=selected_data.get("view_start_date", ""),
        max_chars=8,
    )
    view_end_date = st.text_input(
        "열람 종료일 (view_end_date, YYYYMMDD)",
        value=selected_data.get("view_end_date", ""),
        max_chars=8,
    )

    view_yn_val = (
        int(selected_data.get("view_yn", 1))
        if selected_data.get("view_yn") is not None
        else 1
    )
    view_yn = st.checkbox("웹 열람 여부 (view_yn)", value=bool(view_yn_val))

    submit_btn = st.form_submit_button(
        "저장하기", type="primary", width="stretch"
    )

    if submit_btn:
        if not user_id:
            st.error("user_id는 필수 입력 항목입니다.")
        else:
            try:
                with conn.session as session:
                    if mode == "신규 입력":
                        insert_sql = text("""
                            INSERT INTO rt_collect_info (
                                user_id, work_no, device_no, user_company, user_name,
                                start_date, end_date, start_time, end_time, location, memo,
                                latitude, longitude, left_memo, right_memo,
                                supply_amount, vat_amount, sales_amount, status,
                                view_start_date, view_end_date, view_yn
                            ) VALUES (
                                :user_id, :work_no, :device_no, :user_company, :user_name,
                                :start_date, :end_date, :start_time, :end_time, :location, :memo,
                                :latitude, :longitude, :left_memo, :right_memo,
                                :supply_amount, :vat_amount, :sales_amount, :status,
                                :view_start_date, :view_end_date, :view_yn
                            )
                        """)
                        session.execute(
                            insert_sql,
                            {
                                "user_id": user_id,
                                "work_no": work_no,
                                "device_no": device_no,
                                "user_company": user_company or None,
                                "user_name": user_name or None,
                                "start_date": start_date or None,
                                "end_date": end_date or None,
                                "start_time": start_time or None,
                                "end_time": end_time or None,
                                "location": location or None,
                                "memo": memo or None,
                                "latitude": float(latitude)
                                if latitude
                                else None,
                                "longitude": float(longitude)
                                if longitude
                                else None,
                                "left_memo": left_memo or None,
                                "right_memo": right_memo or None,
                                "supply_amount": supply_amount,
                                "vat_amount": vat_amount,
                                "sales_amount": sales_amount,
                                "status": status or None,
                                "view_start_date": view_start_date or None,
                                "view_end_date": view_end_date or None,
                                "view_yn": 1 if view_yn else 0,
                            },
                        )
                        session.commit()
                        st.success("✔️ 신규 데이터가 성공적으로 등록되었습니다.")
                    else:
                        update_sql = text("""
                            UPDATE rt_collect_info SET
                                device_no = :device_no,
                                user_company = :user_company,
                                user_name = :user_name,
                                start_date = :start_date,
                                end_date = :end_date,
                                start_time = :start_time,
                                end_time = :end_time,
                                location = :location,
                                memo = :memo,
                                latitude = :latitude,
                                longitude = :longitude,
                                left_memo = :left_memo,
                                right_memo = :right_memo,
                                supply_amount = :supply_amount,
                                vat_amount = :vat_amount,
                                sales_amount = :sales_amount,
                                status = :status,
                                view_start_date = :view_start_date,
                                view_end_date = :view_end_date,
                                view_yn = :view_yn
                            WHERE user_id = :user_id AND work_no = :work_no
                        """)
                        session.execute(
                            update_sql,
                            {
                                "user_id": user_id,
                                "work_no": work_no,
                                "device_no": device_no,
                                "user_company": user_company or None,
                                "user_name": user_name or None,
                                "start_date": start_date or None,
                                "end_date": end_date or None,
                                "start_time": start_time or None,
                                "end_time": end_time or None,
                                "location": location or None,
                                "memo": memo or None,
                                "latitude": float(latitude)
                                if latitude
                                else None,
                                "longitude": float(longitude)
                                if longitude
                                else None,
                                "left_memo": left_memo or None,
                                "right_memo": right_memo or None,
                                "supply_amount": supply_amount,
                                "vat_amount": vat_amount,
                                "sales_amount": sales_amount,
                                "status": status or None,
                                "view_start_date": view_start_date or None,
                                "view_end_date": view_end_date or None,
                                "view_yn": 1 if view_yn else 0,
                            },
                        )
                        session.commit()
                        st.success("✔️ 데이터가 성공적으로 수정되었습니다.")
            except Exception as e:
                st.error(f"저장 중 오류가 발생했습니다: {e}")