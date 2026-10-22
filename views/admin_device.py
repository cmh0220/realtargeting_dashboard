import streamlit as st
from sqlalchemy import text

# ===================================================================
# 권한 체크 (notreal 계정만 접근 가능)
# ===================================================================
if st.session_state.get("user_id") != "notreal":
    st.error("⚠️ 접근 권한이 없습니다. 관리자(notreal) 계정으로 로그인해 주세요.")
    st.stop()

st.title("⚙️ 기기설정 관리")


# DB 연결
conn = st.connection("mysql", type="sql")

# ===================================================================
# 데이터 조회 및 기기(device_no) 선택
# ===================================================================
# 기존 등록된 모든 device_no 목록 조회
device_list_sql = """
    SELECT device_no, device_comment 
    FROM rt_collect_setup 
    ORDER BY device_no ASC
"""
df_devices = conn.query(device_list_sql, ttl=0)

if df_devices.empty:
    st.warning("등록된 기기 설정 데이터가 없습니다.")
    st.stop()

# 세그먼트 버튼용 옵션 목록 생성 (예: ["1번 기기", "2번 기기", ...])
device_options = [f"{row['device_no']}번 기기" for _, row in df_devices.iterrows()]
device_map = {f"{row['device_no']}번 기기": row['device_no'] for _, row in df_devices.iterrows()}

st.caption("📱 수정할 기기 번호를 선택하세요.")
selected_option = st.segmented_control(
    "기기 선택",
    options=device_options,
    default=device_options[0],
    selection_mode="single",
    label_visibility="collapsed",
)

if not selected_option:
    selected_option = device_options[0]

selected_device_no = device_map[selected_option]

# 선택한 기기의 상세 정보 조회
detail_sql = """
    SELECT * FROM rt_collect_setup 
    WHERE device_no = :device_no
"""
df_detail = conn.query(detail_sql, params={"device_no": selected_device_no}, ttl=0)

if df_detail.empty:
    st.error("선택한 기기의 정보를 불러올 수 없습니다.")
    st.stop()

selected_data = df_detail.iloc[0].to_dict()


# Helper: safe int conversion
def safe_int(val, default=0):
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


# Helper: safe float conversion
def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


# ===================================================================
# 입력 폼 (모바일 세로 배치 및 그룹화 최적화)
# ===================================================================
with st.form("admin_device_form"):
    st.subheader(f"📲 {selected_device_no}번 기기 기본 정보")

    device_comment = st.text_input(
        "기기 설명 (device_comment)",
        value=selected_data.get("device_comment", "") or "",
    )

    user_id = st.text_input(
        "사용자 ID (user_id)*",
        value=selected_data.get("user_id", "") or "",
    )

    work_no = st.number_input(
        "작업 번호 (work_no)",
        min_value=0,
        value=safe_int(selected_data.get("work_no"), 0),
        step=1,
    )

    device_group_no = st.number_input(
        "기기 그룹 번호 (device_group_no)",
        min_value=0,
        value=safe_int(selected_data.get("device_group_no"), 0),
        step=1,
    )

    class_type = st.text_input(
        "클래스 타입 (class_type)",
        value=selected_data.get("class_type", "") or "",
    )

    st.subheader("⏱️ 동작 시간 및 간격")

    col_h1, col_h2 = st.columns(2)
    with col_h1:
        start_hour = st.number_input(
            "시작 시간 (start_hour, 0~23)",
            min_value=0,
            max_value=23,
            value=safe_int(selected_data.get("start_hour"), 7),
            step=1,
        )
    with col_h2:
        end_hour = st.number_input(
            "종료 시간 [ ★59분제 적용, 예시) 21까지일 경우 20으로 기입! ] (end_hour, 0~23)",
            min_value=0,
            max_value=23,
            value=safe_int(selected_data.get("end_hour"), 21),
            step=1,
        )

    show_delay = st.number_input(
        "표시 지연 시간 (show_delay)",
        min_value=0,
        value=safe_int(selected_data.get("show_delay"), 0),
        step=1,
    )

    save_interval = st.number_input(
        "저장 간격 (save_interval)",
        min_value=0,
        value=safe_int(selected_data.get("save_interval"), 1),
        step=1,
        
    )

    st.subheader("🎯 감지 및 분석 설정")

    base_line_type = st.text_input(
        "기준선 타입 (base_line_type)",
        value=selected_data.get("base_line_type", "") or "",
    )

    base_line = st.number_input(
        "기준선 위치 (base_line)",
        value=safe_int(selected_data.get("base_line"), 0),
        step=1,
    )

    line_gap = st.number_input(
        "라인 간격 (line_gap)",
        min_value=0,
        value=safe_int(selected_data.get("line_gap"), 0),
        step=1,
    )

    col_i1, col_i2 = st.columns(2)
    with col_i1:
        iou_val = safe_float(selected_data.get("iou"), 0.0)
        iou = st.number_input(
            "IOU (0.0 ~ 1.0)",
            min_value=0.0,
            max_value=1.0,
            value=iou_val,
            step=0.01,
            format="%.4f",
        )
    with col_i2:
        conf_val = safe_float(selected_data.get("confidence_threshold"), 0.5)
        confidence_threshold = st.number_input(
            "신뢰도 임계값 (0.0 ~ 1.0)",
            min_value=0.0,
            max_value=1.0,
            value=conf_val,
            step=0.01,
            format="%.4f",
        )

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        direction_a = st.text_input(
            "방향 A (direction_a)",
            value=selected_data.get("direction_a", "") or "",
        )
        direction_ae = st.text_input(
            "방향 AE (direction_ae)",
            value=selected_data.get("direction_ae", "") or "",
        )
    with col_d2:
        direction_b = st.text_input(
            "방향 B (direction_b)",
            value=selected_data.get("direction_b", "") or "",
        )
        direction_be = st.text_input(
            "방향 BE (direction_be)",
            value=selected_data.get("direction_be", "") or "",
        )

    st.subheader("🔘 스위치 및 기능 활성화")

    default_model_yn = st.toggle("기본 모델 여부 (default_model_yn)",
                                 value=bool(safe_int(selected_data.get("default_model_yn"), 1)))
    is_rotate_camera = st.toggle("카메라 회전 여부 (is_rotate_camera)",
                                 value=bool(safe_int(selected_data.get("is_rotate_camera"), 0)))
    is_show = st.toggle("화면 표시 여부 (is_show)", value=bool(safe_int(selected_data.get("is_show"), 1)))
    is_backup = st.toggle("백업 여부 (is_backup)", value=bool(safe_int(selected_data.get("is_backup"), 1)))
    is_google_save = st.toggle("구글 저장 여부 (is_google_save)",
                               value=bool(safe_int(selected_data.get("is_google_save"), 0)))
    is_stay = st.toggle("체류 여부 (is_stay)", value=bool(safe_int(selected_data.get("is_stay"), 0)))
    is_heatmap = st.toggle("히트맵 여부 (is_heatmap)", value=bool(safe_int(selected_data.get("is_heatmap"), 0)))
    save_db = st.toggle("DB 저장 여부 (save_db)", value=bool(safe_int(selected_data.get("save_db"), 1)))
    is_snapshot_local = st.toggle("로컬 스냅샷 저장 (is_snapshot_local)",
                                  value=bool(safe_int(selected_data.get("is_snapshot_local"), 1)))
    is_snapshot_google = st.toggle("구글 스냅샷 저장 (is_snapshot_google)",
                                   value=bool(safe_int(selected_data.get("is_snapshot_google"), 1)))

    limit_cnt_snapshot = st.number_input(
        "스냅샷 제한 수 (limit_cnt_snapshot)",
        min_value=0,
        value=safe_int(selected_data.get("limit_cnt_snapshot"), 0),
        step=1,
    )

    submit_btn = st.form_submit_button(
        "기기설정 저장하기", type="primary", width="stretch"
    )

    if submit_btn:
        try:
            update_sql = text("""
                UPDATE rt_collect_setup SET
                    device_comment = :device_comment,
                    default_model_yn = :default_model_yn,
                    class_type = :class_type,
                    user_id = :user_id,
                    work_no = :work_no,
                    device_group_no = :device_group_no,
                    is_rotate_camera = :is_rotate_camera,
                    is_show = :is_show,
                    is_backup = :is_backup,
                    is_google_save = :is_google_save,
                    is_stay = :is_stay,
                    is_heatmap = :is_heatmap,
                    save_db = :save_db,
                    is_snapshot_local = :is_snapshot_local,
                    is_snapshot_google = :is_snapshot_google,
                    limit_cnt_snapshot = :limit_cnt_snapshot,
                    start_hour = :start_hour,
                    end_hour = :end_hour,
                    show_delay = :show_delay,
                    save_interval = :save_interval,
                    base_line_type = :base_line_type,
                    base_line = :base_line,
                    line_gap = :line_gap,
                    iou = :iou,
                    confidence_threshold = :confidence_threshold,
                    direction_a = :direction_a,
                    direction_ae = :direction_ae,
                    direction_b = :direction_b,
                    direction_be = :direction_be
                WHERE device_no = :device_no
            """)

            with conn.session as session:
                session.execute(
                    update_sql,
                    {
                        "device_no": selected_device_no,
                        "device_comment": device_comment or None,
                        "default_model_yn": 1 if default_model_yn else 0,
                        "class_type": class_type,
                        "user_id": user_id,
                        "work_no": work_no,
                        "device_group_no": device_group_no,
                        "is_rotate_camera": 1 if is_rotate_camera else 0,
                        "is_show": 1 if is_show else 0,
                        "is_backup": 1 if is_backup else 0,
                        "is_google_save": 1 if is_google_save else 0,
                        "is_stay": 1 if is_stay else 0,
                        "is_heatmap": 1 if is_heatmap else 0,
                        "save_db": 1 if save_db else 0,
                        "is_snapshot_local": 1 if is_snapshot_local else 0,
                        "is_snapshot_google": 1 if is_snapshot_google else 0,
                        "limit_cnt_snapshot": limit_cnt_snapshot,
                        "start_hour": start_hour,
                        "end_hour": end_hour,
                        "show_delay": show_delay,
                        "save_interval": save_interval,
                        "base_line_type": base_line_type or None,
                        "base_line": base_line,
                        "line_gap": line_gap,
                        "iou": iou,
                        "confidence_threshold": confidence_threshold,
                        "direction_a": direction_a,
                        "direction_ae": direction_ae,
                        "direction_b": direction_b,
                        "direction_be": direction_be,
                    },
                )
                session.commit()
            st.success(f"✔️ {selected_device_no}번 기기 설정 데이터가 성공적으로 수정되었습니다.")
            st.rerun()

        except Exception as e:
            st.error(f"저장 중 오류가 발생했습니다: {e}")