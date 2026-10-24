from datetime import datetime, date, timedelta
import datetime, base64, os
from typing import Any, Dict, List
import streamlit as st
from streamlit_echarts import st_echarts
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import pandas as pd
import requests

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

def render_section_header(icon: str, ko_title: str, en_title: str):
    """보고서 스타일의 일체형 섹션 헤더를 렌더링합니다."""
    st.markdown(
        f"""
        <div style="display: flex; align-items: baseline; gap: 12px; margin-top: 20px; margin-bottom: 16px;">
            <span style="font-size: 32px; line-height: 1;">{icon}</span>
            <div style="display: flex; align-items: baseline; gap: 12px;">
                <span style="font-size: 30px; font-weight: bold; color: #0f172a; letter-spacing: -0.5px;">{ko_title}</span>
                <span style="font-size: 24px; font-weight: 500; color: #94a3b8; font-family: sans-serif;">{en_title}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
# ------------------------------------------------------------------------------
# Page CSS Customization
# ------------------------------------------------------------------------------
st.markdown(
    """
    <style>
        /* st.logo 이미지 컨테이너 크기 확대 */
        [data-testid="stSidebarHeader"] img {
            height: 100px !important;   /* 원하는 높이로 조절 */
            width: auto !important;
            max-width: 100% !important;
        }
        /* 로고 영역 컨테이너 여백 조정 */
        [data-testid="stSidebarHeader"] {
            padding-top: 40px !important;
            padding-bottom: 40px !important;
            padding-left: 0px !important;
        }

        /* 💡 셀렉트박스 입력창 커서 숨김, 입력 차단 및 선택 불가 처리 */
        div[data-baseweb="select"] input {
            caret-color: transparent !important; /* 깜빡이는 커서 숨김 */
            user-select: none !important;        /* 텍스트 드래그 및 선택 방지 */
        }

        /* 셀렉트박스 전체에 클릭만 허용하고 텍스트 커서 모양(I-beam) 방지 */
        div[data-baseweb="select"] {
            cursor: pointer !important;
        }

        div[data-baseweb="select"] * {
            cursor: pointer !important;
        }
        
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        header { display: none !important; }
        footer { display: none !important; }
        .main .block-container {
            max-width: 100% !important;
            padding: 1rem !important;
        }
        @font-face {
            font-family: 'NanumGothic';
            src: url('fonts/NanumGothicExtraBold.ttf') format('truetype');
        }
        * {
            font-family: 'NanumGothicExtraBold', sans-serif !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

def get_image_base64(image_path: str) -> str:
    """이미지 파일을 HTML에 직접 매립하기 위한 Base64 인코딩 함수"""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
    return ""

def render_pdf_cover(selected_work_info: dict = None):
    """
    업로드된 완성형 A4 표지 레이아웃 렌더링 (Markdown 코드 블록 오류 방지 처리)
    """
    selected_work_no = selected_work_info.get("작업번호") or selected_work_info.get("work_no")

    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month
    current_day = datetime.datetime.now().day

    doc_no = f"발행일자 : {current_year}년 {current_month}월 {current_day}일"

    # 이미지 파일 경로 지정
    logo_b64 = get_image_base64("images/logo_wide.png")
    qr_b64 = get_image_base64("images/qr_chat.png")
    kakao_logo_b64 = get_image_base64("images/kakao_icon.png")

    # 태그 내부에 들어갈 이미지 HTML을 미리 완성 (f-string 중첩 에러 방지)
    qr_html = f"<img src='{qr_b64}' class='cover-qr-img'>" if qr_b64 else "<div style='width:110px; height:110px; background:#eee; display:flex; align-items:center; justify-content:center; font-size:11px;'>QR Image</div>"
    kakao_logo_html = f"<img src='{kakao_logo_b64}' class='cover-logo-img'>" if kakao_logo_b64 else ""
    logo_html = f"<img src='{logo_b64}' class='cover-logo-img'>" if logo_b64 else ""

    # 들여쓰기 공백 없이 좌측에 바짝 붙인 HTML 문자열
    cover_html = f"""<style>
@media print {{
    .pdf-cover-container {{
        page-break-after: always !important;
        break-after: page !important;
    }}
}}
.pdf-cover-container {{
    width: 100%;
    height: 1120px;
    background-color: #ffffff;
    position: relative;
    box-sizing: border-box;
    padding: 20px 40px;
    page-break-after: always;
    break-after: page;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}}
.cover-doc-no {{
    text-align: right;
    font-size: 16px;
    font-weight: 700;
    color: #333333;
    margin-bottom: 20px;
}}
.cover-main-wrapper {{
    width: 100%;
    height: 780px; /* A4 1페이지에 맞도록 높이 보정 */
    background-color: #f0f0f0;
    position: relative;
}}
.cover-blue-box {{
    width: 53%;
    height: 580px;
    background-color: #1565c0;
    padding: 48px 40px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}
.cover-title-kr {{
    color: #ffffff;
    font-size: 64px;
    font-weight: 800;
    line-height: 1.25;
    letter-spacing: -1px;
}}
.cover-title-en {{
    color: #90caf9;
    font-size: 44px;
    font-weight: 600;
    font-style: italic;
    line-height: 1.3;
    margin-top: 24px;
}}
.cover-footer-desc {{
    color: rgba(255, 255, 255, 0.9);
    font-size: 18px;
    line-height: 1.6;
}}
/* 담당자 인적사항 및 QR 우측 배치 */
.cover-bottom-wrapper {{
    margin-top: 200px; /* 오버플로우 방지를 위한 여백 보정 */
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding: 0 10px;
}}
.cover-info-list {{
    font-size: 18px;
    line-height: 1.9;
    color: #222222;
}}
.cover-info-list div {{
    display: flex;
}}
.cover-info-label {{
    font-weight: 800;
    width: 110px; /* 라벨 너비 확보 */
}}
.cover-info-val {{
    font-weight: 700;
}}
/* 우측 카카오톡 + QR 수직 정렬 컨테이너 */
.cover-qr-box {{
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}}
.cover-kakao-title {{
    font-size: 18px;
    font-weight: 800;
    color: #3c1e1e;
    margin: 4px 0 8px 0;
}}
.cover-qr-img {{
    width: 110px;
    height: 110px;
    object-fit: contain;
}}
/* 하단 로고 및 카피라이트 */
.cover-footer-logo-zone {{
    margin-top: 50px;
    text-align: center;
}}
.cover-logo-img {{
    height: 75px;
    object-fit: contain;
    margin-bottom: 12px;
}}
.cover-copyright {{
    font-size: 16px;
    font-weight: 600;
    color: #333333;
}}
.cover-qr-box {{
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}}

/* 🎯 로고와 텍스트를 좌우(가로)로 배치하는 헤더 박스 */
.cover-kakao-header {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px; /* 로고와 텍스트 사이 간격 */
    margin-bottom: 8px; /* QR 코드와의 간격 */
}}

/* 카카오 로고 이미지 크기 (텍스트 2줄 높이에 맞춤) */
.cover-kakao-header img {{
    height: 36px; /* 텍스트 2줄 높이에 맞춘 36px */
    width: auto;
    object-fit: contain;
}}

/* 카카오톡 상담하기 2줄 텍스트 */
.cover-kakao-title {{
    font-size: 18px;
    font-weight: 800;
    color: #3c1e1e;
    line-height: 1.25; /* 2줄 텍스트 행간 고정 */
    text-align: left; /* 좌측 정렬 */
}}

.cover-qr-img {{
    width: 110px;
    height: 110px;
    object-fit: contain;
}}
</style>
<div class="pdf-cover-container">
    <div class="cover-doc-no">{doc_no}</div>
    <div class="cover-main-wrapper">
        <div class="cover-blue-box">
            <div>
                <div class="cover-title-kr">
                    AI 통행량<br>분석 보고서
                </div>
                <div class="cover-title-en">
                    AI Foot Traffic<br>Intelligence Report
                </div>
            </div>
            <div class="cover-footer-desc">
                본 보고서는 AI 통행량 분석 시스템을 기반으로 한<br>실제 데이터를 통해 작성 되었습니다.
            </div>
        </div>
    </div>
    <div class="cover-bottom-wrapper">
        <div class="cover-info-list">
            <div><span class="cover-info-label">담 당 자</span><span class="cover-info-val">채명훈</span></div>
            <div><span class="cover-info-label">연 락 처</span><span class="cover-info-val">010-4424-3291</span></div>
            <div><span class="cover-info-label">E-mail</span><span class="cover-info-val">realtargeting@gmail.com</span></div>
            <div><span class="cover-info-label">홈페이지</span><span class="cover-info-val">https://www.realtargeting.co.kr</span></div>
            <div style="margin-top: 4px;"><span class="cover-info-val">아이하우스(주)</span></div>
        </div>
        <div class="cover-qr-box">
            <div class="cover-kakao-header">
                {kakao_logo_html}
                <div class="cover-kakao-title">카카오톡<br>상담하기</div>
            </div>
            {qr_html}
        </div>       
    </div>
    <div class="cover-footer-logo-zone">
        {logo_html}
        <div class="cover-copyright">Copyright ® RealTargeting Allright Resolved.</div>
    </div>
</div>"""

    st.markdown(cover_html, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# 1. 공통 차트 렌더러 (Chart Component Functions)
# ------------------------------------------------------------------------------
def render_location_map(selected_work_info: Dict[str, Any]):
    """왼쪽에는 측정 기본 정보 카드, 오른쪽(너비 50%)에는 지도를 배치합니다."""

    # 1. 컬럼 분할 (3:2 비율)
    col_info, col_map = st.columns([3, 2], gap="medium")

    # 2. [왼쪽 컬럼] 기본 정보 카드 렌더링
    with col_info:
        start_date = format_date_str(selected_work_info.get("시작일자") or selected_work_info.get("start_date"))
        end_date = format_date_str(selected_work_info.get("종료일자") or selected_work_info.get("end_date"))
        start_time = format_time_str(selected_work_info.get("시작시간") or selected_work_info.get("start_time"))
        end_time = format_time_str(selected_work_info.get("종료시간") or selected_work_info.get("end_time"))
        address = selected_work_info.get("주소") or selected_work_info.get("location", "-")
        memo = selected_work_info.get("측정지점") or selected_work_info.get("memo") or f"지점 {selected_work_info.get('작업번호') or selected_work_info.get('work_no')}"

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

    # 3. [오른쪽 컬럼] 지도 렌더링
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


def render_info_footer(logo_path_or_url: str = None):
    """
    대시보드 하단 안내문 및 로고 레이아웃 렌더링 함수
    :param logo_path_or_url: 가운데 들어갈 로고 이미지 경로 또는 URL
    """

    # Custom CSS 적용
    st.markdown("""
    <style>
        .info-title {
            font-size: 20px;
            font-weight: 800;
            color: #1E293B;
            margin-bottom: 8px;
        }
        .info-divider {
            border-bottom: 3px solid #3B82F6;
            margin-bottom: 24px;
        }
        .info-list {
            font-size: 14.5px;
            line-height: 1.7;
            color: #334155;
            margin-bottom: 30px;
        }
        .info-list p {
            margin-bottom: 12px;
            word-break: keep-all;
        }

        /* 주의사항 박스 */
        .warning-box {
            background-color: #FEF9C3;
            border: 1px solid #FDE047;
            border-radius: 8px;
            padding: 30px 24px;
            margin-top: 35px;
            margin-bottom: 25px;
            color: #1E293B;
            font-size: 13.5px;
            line-height: 1.6;
        }
        .warning-header {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            font-weight: 700;
            font-size: 14px;
            margin-bottom: 12px;
            color: #854D0E;
        }
        .warning-list {
            margin-left: 28px;
            color: #334155;
        }
        .warning-list li {
            margin-bottom: 4px;
        }

        /* 저작권 표시 */
        .copyright {
            text-align: right;
            font-size: 13px;
            color: #64748B;
            font-weight: 600;
            margin-top: 15px;
        }
    </style>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # 1. 상단 타이틀 및 안내문
    # ----------------------------------------------------
    st.markdown('<div class="info-title">AI 통행량 분석 안내</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-divider"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-list">
        <p><b>1.</b> 통행량 데이터 수집 프로세스는 인공지능 기술을 이용하여 모든 과정이 자동으로 처리됩니다.</p>
        <p><b>2.</b> 수집된 정보는 모두 개인을 식별할 수 없는 메타데이터로 구성되어 있으며 파일 암호화 및 접근통제가 적용되어 있습니다.</p>
        <p><b>3.</b> 영상정보처리기기 운영 및 관리지침에 의해 관리되고 있으며, 통행량 데이터 수집시 영상을 녹화하거나 저장하지 않으며 개인정보보호법을 엄격히 준수합니다.</p>
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # 3. 하단 경고 및 안내 박스
    # ----------------------------------------------------
    st.markdown("""
    <div class="warning-box" style="margin-top: 35px;">
        <div class="warning-header">
            <span style="font-size: 20px;">⚠️</span>
            <div>
                본 보고서는 인공지능 AI 영상인식 기술을 활용하여 통행량을 분석하여 작성되었습니다.<br>
                상황에 따라 아래와 같이 일부 오탐지 되는 경우도 있는 점 미리 안내드립니다. 따라서 이 점 충분히 감안하여 상권분석에 활용하시기 바랍니다.
            </div>
        </div>
        <ol class="warning-list" type="1">
            <li>측정 순간 객체의 일부 혹은 전체가 가려진 경우(차량, 타 보행자) 누락 가능</li>
            <li>뛰어가거나 차량, 자전거, 오토바이에 탑승하여 빠르게 통과 하는 경우 누락 가능</li>
            <li>조명이 부족한 경우(새벽, 야간) 탐지 누락 가능</li>
            <li>사람이 봐도 성별 구분이 어려운 경우 성별 오탐지</li>
            <li>그 외 AI가 인식하지 못하는 경우 발생</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # 2. 중앙 로고 영역
    # ----------------------------------------------------
    if logo_path_or_url:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.image(logo_path_or_url, width='stretch')
    else:
        # 파일이 없을 때 보여주는 샘플 대용 박스 (실제 적용 시 삭제 가능)
        st.info("💡 여기에 로고 이미지(logo_path_or_url)를 지정해 주세요.")

    # ----------------------------------------------------
    # 4. 카피라이트 (Copyright)
    # ----------------------------------------------------
    st.markdown('<div style="text-align: right;" class="copyright">Copyright © 2026. All Rights Reserved.</div>', unsafe_allow_html=True)


# 1. 해당 작업(work_no)의 모든 코멘트를 한 번에 가져오는 함수
@st.cache_data(ttl=0)
def fetch_all_comments(user_id: str, work_no: str):
    query = """
        SELECT com1, com2, com3, com4, com5, com6, com7, com8, com9 
        FROM rt_collect_comment 
        WHERE user_id = :user_id AND work_no = :work_no
    """
    try:
        df = conn.query(query, params={"user_id": user_id, "work_no": work_no}, ttl=0)
        if df is not None and not df.empty:
            # 첫 번째 행을 딕셔너리 형태로 변환하여 반환 (예: {'com1': '내용...', 'com2': '내용...', ...})
            return df.iloc[0].to_dict()
    except Exception as e:
        pass
    return {}

def render_comment_box(comments_dict: dict, comment_key: str = "com1"):
    comment_text = ""
    if comments_dict:
        val = comments_dict.get(comment_key)
        if val and str(val).strip() != "None" and str(val).strip() != "nan":
            comment_text = str(val)

    st.markdown(
        f"""
            <div style="            
                box-sizing: border-box;
                background-color: #f1f3f5;
                border-radius: 6px;
                padding: 20px;                      /* 🌟 상하좌우 모든 방향에 동일하게 4px 적용 */
                margein-left: 2px;
                font-size: 15px;
                color: #212529;
                line-height: 1.6;
                white-space: pre-line;
                word-break: keep-all;
                height: 200px;
            "><B>Comment</B><BR>
                {comment_text}
            </div>
            """,
        unsafe_allow_html=True
    )

# ------------------------------------------------------------------------------
# 1. 공통 차트 렌더러 (Chart Component Functions)
# ------------------------------------------------------------------------------
def render_location_map(selected_work_info: Dict[str, Any]):
    """왼쪽에는 측정 기본 정보 카드, 오른쪽(너비 50%)에는 지도를 배치합니다."""

    # 1. 컬럼 분할 (3:2 비율)
    col_info, col_map = st.columns([3, 2], gap="medium")

    # 2. [왼쪽 컬럼] 기본 정보 카드 렌더링
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
                    위치 : {memo}                    
                </h4>
                <h4 style="margin-top: 0; margin-bottom: 12px; color: #1e293b; font-size: 17px; font-weight: bold;">
                    주소 : {address}
                </h4>
                <hr style="margin: 8px 0 16px 0; border: none; border-top: 1px solid #e2e8f0;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div>
                        <span style="font-size: 17px; color: #64748b; display: block;">📅 측정 시작일자</span>
                        <span style="font-size: 17px; font-weight: 600; color: #0f172a; margin-left: 24px;">{start_date}</span>
                    </div>
                    <div>
                        <span style="font-size: 17px; color: #64748b; display: block;">📅 측정 종료일자</span>
                        <span style="font-size: 17px; font-weight: 600; color: #0f172a; margin-left: 24px;">{end_date}</span>
                    </div>
                    <div>
                        <span style="font-size: 17px; color: #64748b; display: block;">⏰ 측정 시작시간</span>
                        <span style="font-size: 17px; font-weight: 600; color: #2563eb; margin-left: 24px;">{start_time}</span>
                    </div>
                    <div>
                        <span style="font-size: 17px; color: #64748b; display: block;">⏰ 측정 종료시간</span>
                        <span style="font-size: 17px; font-weight: 600; color: #2563eb; margin-left: 24px;">{end_time}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. [오른쪽 컬럼] 지도 렌더링
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


def render_metric_cards(df_h1, df_h2, df_h3, df_h4, df_h5, df_h6, df_h7, df_h8):
    """상단 주요 지표 카드를 출력합니다."""
    st.write(" ")
    col1, col2, col3, col4 = st.columns(4)
    st.write(" ")
    col5, col6, col7, col8 = st.columns(4)

    def get_val_cnt(df, surfix):
        if df is not None and not df.empty and df.iloc[0, 0] is not None:
            return f"{int(round(float(df.iloc[0, 0]))):,}{surfix}"
        return f"0{surfix}"

    def get_val_sec(df, surfix):
        if df is not None and not df.empty and df.iloc[0, 0] is not None:
            return f"{float(df.iloc[0, 0]):,.1f}{surfix}"
        return f"0.0{surfix}"

    col1.metric("전체 누적 통행량", get_val_cnt(df_h1, "명"))
    col2.metric("일평균 통행량", get_val_cnt(df_h2, "명"))
    col3.metric("시간당 통행량", get_val_cnt(df_h3, "명"))
    col4.metric("분당 통행량", get_val_cnt(df_h4, "명"))
    col5.metric("주중 평균 통행량", get_val_cnt(df_h5, "명"))
    col6.metric("주말 평균 통행량", get_val_cnt(df_h6, "명"))
    col7.metric("전체 평균 체류시간", get_val_sec(df_h7, "초"))
    col8.metric("시간당 평균 체류시간", get_val_sec(df_h8, "초"))


def render_chart_item(chart_info: Dict[str, Any]):
    """개별 차트 데이터를 받아 유형에 맞는 Streamlit 차트를 출력합니다."""
    title = chart_info.get("title", "")
    chart_type = chart_info.get("type", "bar")
    df = chart_info.get("df")
    chart_id = chart_info.get("chart_id", "default_chart")
    chart_height = chart_info.get("chart_height", 300)
    comp_key = f"{chart_type}_{chart_id}"

    st.markdown(
        f"<h4 style='font-size: 20px; font-weight: bold; margin-bottom: 10px;'>{title}</h4>",
        unsafe_allow_html=True,
    )
    st.write(" ")

    if chart_type == "bar":
        x_col = chart_info.get("x")
        y_col = chart_info.get("y")
        x_label = chart_info.get("x_label", "")
        y_label = chart_info.get("y_label", "")

        x_data = df[x_col].astype(str).tolist() if x_col and x_col in df.columns else []

        if isinstance(y_col, list):
            series_data = [
                {"name": col, "type": "bar", "data": df[col].tolist()}
                for col in y_col if col in df.columns
            ]
        else:
            series_data = [
                {
                    "name": y_col or "",
                    "type": "bar",
                    "data": df[y_col].tolist() if y_col and y_col in df.columns else []
                }
            ]

        options = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"show": True if isinstance(y_col, list) and len(y_col) > 1 else False},
            "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": {"type": "category", "data": x_data, "name": x_label, "nameLocation": "middle", "nameGap": 30},
            "yAxis": {"type": "value", "name": y_label},
            "series": series_data
        }
        st_echarts(options=options, height=f"{chart_height}px", key=comp_key)

    elif chart_type == "echarts_multi_bar_gender":
        # index_col: x축 기준 (예: 일자 또는 시간), columns_col: 그룹화할 기준 (예: 성별), values_col: 값
        index_col = chart_info.get("index_col", "collect_date")
        columns_col = chart_info.get("columns_col", "gender")
        values_col = chart_info.get("values_col", "cnt")
        y_name = chart_info.get("y_name", "통행량")
        is_stacked = chart_info.get("stacked", True)  # 기본값: 누적 바 차트 (False면 그룹 바 차트)

        # 데이터 피벗 (없는 데이터는 0으로 채움)
        pivot_df = df.pivot(index=index_col, columns=columns_col, values=values_col).fillna(0)

        x_data = [str(idx) for idx in pivot_df.index]
        legend_keys = list(pivot_df.columns)

        # 🎨 성별/항목별 맞춤 색상 맵 정의 (원하시는 HEX 코드로 자유롭게 변경 가능합니다)
        color_map = {
            "남성": "#60A5FA",  # 파란 계열
            "여성": "#F472B6",  # 핑크 계열
            "m": "#60A5FA",  # 영문 키값이 'm'인 경우 대비
            "w": "#F472B6",  # 영문 키값이 'w'인 경우 대비
            "왼쪽": "#A865B5",  # 연한 보라색 계열 (예: Lavender)
            "오른쪽": "#9fcc4b"  # 연한 연두색 계열 (예: Light Mint/Green)
        }

        # 각 그룹별 시리즈 생성 (color 속성 추가)
        series_list = []
        for key in legend_keys:
            series_item = {
                "name": str(key),
                "type": "bar",
                "stack": "total" if is_stacked else None,
                "data": pivot_df[key].round(1).tolist(),
            }
            # 정의된 색상이 있다면 적용
            if str(key) in color_map:
                series_item["itemStyle"] = {"color": color_map[str(key)]}

            series_list.append(series_item)

        options = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"top": "0%", "data": [str(k) for k in legend_keys]},
            "grid": {"top": "15%", "left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value", "name": y_name},
            "series": series_list,
        }
        st_echarts(options=options, height=f"{chart_height}px", key=comp_key)

    elif chart_type == "echarts_multi_bar_age":
        # index_col: x축 기준 (예: 일자 또는 시간), columns_col: 그룹화할 기준 (예: 성별), values_col: 값
        index_col = chart_info.get("index_col", "collect_date")
        columns_col = chart_info.get("columns_col", "age")
        values_col = chart_info.get("values_col", "cnt")
        y_name = chart_info.get("y_name", "통행량")
        is_stacked = chart_info.get("stacked", True)  # 기본값: 누적 바 차트 (False면 그룹 바 차트)

        # 데이터 피벗 (없는 데이터는 0으로 채움)
        pivot_df = df.pivot(index=index_col, columns=columns_col, values=values_col).fillna(0)

        x_data = [str(idx) for idx in pivot_df.index]
        legend_keys = list(pivot_df.columns)

        # 🎨 성별/항목별 맞춤 색상 맵 정의 (원하시는 HEX 코드로 자유롭게 변경 가능합니다)
        color_map = {
            "남성": "#60A5FA",  # 파란 계열
            "여성": "#F472B6",  # 핑크 계열
            "m": "#60A5FA",  # 영문 키값이 'm'인 경우 대비
            "w": "#F472B6",  # 영문 키값이 'w'인 경우 대비
            "왼쪽": "#A865B5",  # 연한 보라색 계열 (예: Lavender)
            "오른쪽": "#9fcc4b"  # 연한 연두색 계열 (예: Light Mint/Green)
        }

        # 각 그룹별 시리즈 생성 (color 속성 추가)
        series_list = []
        for key in legend_keys:
            series_item = {
                "name": str(key),
                "type": "bar",
                "stack": "total" if is_stacked else None,
                "data": pivot_df[key].round(1).tolist(),
            }
            # 정의된 색상이 있다면 적용
            if str(key) in color_map:
                series_item["itemStyle"] = {"color": color_map[str(key)]}

            series_list.append(series_item)

        options = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"top": "0%", "data": [str(k) for k in legend_keys]},
            "grid": {"top": "15%", "left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value", "name": y_name},
            "series": series_list,
        }
        st_echarts(options=options, height=f"{chart_height}px", key=comp_key)

    elif chart_type == "echarts_multi_bar_direction":
        # index_col: x축 기준 (예: 일자 또는 시간), columns_col: 그룹화할 기준 (예: 성별), values_col: 값
        index_col = chart_info.get("index_col", "collect_date")
        columns_col = chart_info.get("columns_col", "direction")
        values_col = chart_info.get("values_col", "cnt")
        y_name = chart_info.get("y_name", "통행량")
        is_stacked = chart_info.get("stacked", True)  # 기본값: 누적 바 차트 (False면 그룹 바 차트)

        # 데이터 피벗 (없는 데이터는 0으로 채움)
        pivot_df = df.pivot(index=index_col, columns=columns_col, values=values_col).fillna(0)

        x_data = [str(idx) for idx in pivot_df.index]
        legend_keys = list(pivot_df.columns)

        # 🎨 성별/항목별 맞춤 색상 맵 정의 (원하시는 HEX 코드로 자유롭게 변경 가능합니다)
        color_map = {
            "남성": "#60A5FA",  # 파란 계열
            "여성": "#F472B6",  # 핑크 계열
            "m": "#60A5FA",  # 영문 키값이 'm'인 경우 대비
            "w": "#F472B6",  # 영문 키값이 'w'인 경우 대비
            "왼쪽": "#A865B5",  # 연한 보라색 계열 (예: Lavender)
            "오른쪽": "#9fcc4b"  # 연한 연두색 계열 (예: Light Mint/Green)
        }

        # 각 그룹별 시리즈 생성 (color 속성 추가)
        series_list = []
        for key in legend_keys:
            series_item = {
                "name": str(key),
                "type": "bar",
                "stack": "total" if is_stacked else None,
                "data": pivot_df[key].round(1).tolist(),
            }
            # 정의된 색상이 있다면 적용
            if str(key) in color_map:
                series_item["itemStyle"] = {"color": color_map[str(key)]}

            series_list.append(series_item)

        options = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"top": "0%", "data": [str(k) for k in legend_keys]},
            "grid": {"top": "15%", "left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value", "name": y_name},
            "series": series_list,
        }
        st_echarts(options=options, height=f"{chart_height}px", key=comp_key)

    elif chart_type == "echarts_pie":
        name_col = chart_info.get("name_col", "name")
        val_col = chart_info.get("value_col", "cnt")
        semi_pie = chart_info.get("semi_pie", None)

        # 🛡️ 방어 로직: 데이터 유무 및 컬럼 체크
        if df is None or df.empty:
            st.warning(f"⚠️ '{title}' 차트에 표시할 데이터가 없습니다.")
            return

        if name_col not in df.columns or val_col not in df.columns:
            st.error(f"⚠️ 차트 생성 오류: 데이터프레임에 [{name_col}, {val_col}] 컬럼이 존재하지 않습니다.")
            return

        start_angle = 90
        end_angle = 450

        if semi_pie == "up":
            start_angle = 180
            end_angle = 0

        # 🎨 성별 맞춤 색상 맵 정의
        color_map = {
            "남성": "#60A5FA",  # 파란 계열
            "여성": "#F472B6",  # 핑크 계열
            "남": "#60A5FA",
            "여": "#F472B6",
            "m": "#60A5FA",  # 영문 키값 대비
            "w": "#F472B6",
            "왼쪽": "#A865B5",  # 연한 보라색 계열 (예: Lavender)
            "오른쪽": "#9fcc4b"  # 연한 연두색 계열 (예: Light Mint/Green)
        }

        # 데이터 세팅 (성별일 경우 지정 색상 적용, 그 외는 ECharts 기본 색상)
        chart_data = []
        for _, row in df.iterrows():
            item_name = str(row[name_col])
            item_val = int(row[val_col]) if pd.notnull(row[val_col]) else 0
            item_dict = {
                "name": item_name,
                "value": item_val
            }

            # 키값이 color_map에 들어있으면 해당 색상 적용
            if item_name in color_map:
                item_dict["itemStyle"] = {"color": color_map[item_name]}

            chart_data.append(item_dict)

        options = {
            "tooltip": {"trigger": "item", "formatter": "{b}: {c:,}명 ({d}%)"},
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

        st_echarts(options=options, height=f"{chart_height}px", key=comp_key)

    elif chart_type == "echarts_line":
        x_col = chart_info.get("x_col", "collect_hour")
        y_col = chart_info.get("y_col", "cnt")
        x_data = df[x_col].astype(str).tolist()
        y_data = df[y_col].tolist()

        option = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value"},
            "series": [{"data": y_data, "type": "line", "areaStyle": {}}],
        }
        st_echarts(options=option, height=f"{chart_height}px", key=comp_key)


    elif chart_type == "echarts_multi_line":
        index_col = chart_info.get("index_col", "collect_hour")
        columns_col = chart_info.get("columns_col", "collect_day")
        values_col = chart_info.get("values_col", "cnt")
        y_name = chart_info.get("y_name", "통행량")

        # 🛡️ 방어 로직: 데이터 유무 및 컬럼 체크

        if df is None or df.empty:
            st.warning(f"⚠️ '{title}' 차트에 표시할 데이터가 없습니다.")
            return

        missing_cols = [col for col in [index_col, columns_col, values_col] if col not in df.columns]

        if missing_cols:
            st.error(f"⚠️ 차트 생성 오류: 데이터프레임에 다음 컬럼이 존재하지 않습니다: {missing_cols}")

            return

        try:
            pivot_df = df.pivot(index=index_col, columns=columns_col, values=values_col).fillna(0)
            days_order = ['월', '화', '수', '목', '금', '토', '일']
            if any(col in days_order for col in pivot_df.columns):
                legend_keys = [d for d in days_order if d in pivot_df.columns]
            else:
                legend_keys = list(pivot_df.columns)

            x_data = [f"{int(h):02d}시" if str(h).isdigit() else str(h) for h in pivot_df.index]

            # 🎨 성별 맞춤 색상 맵 정의

            color_map = {
                "남성": "#60A5FA",  # 파란 계열
                "여성": "#F472B6",  # 핑크 계열
                "남": "#60A5FA",
                "여": "#F472B6",
                "m": "#60A5FA",
                "w": "#F472B6",
                "왼쪽": "#A865B5",  # 연한 보라색 계열 (예: Lavender)
                "오른쪽": "#9fcc4b"  # 연한 연두색 계열 (예: Light Mint/Green)
            }

            # 각 그룹별 시리즈 생성 (성별 색상 매핑 포함)
            series_list = []
            for key in legend_keys:
                series_item = {
                    "name": str(key),
                    "type": "line",
                    "data": pivot_df[key].round(1).tolist()
                }

                # 키가 성별 관련 단어일 경우 itemStyle 적용
                if str(key) in color_map:
                    series_item["itemStyle"] = {"color": color_map[str(key)]}
                    series_item["lineStyle"] = {"color": color_map[str(key)]}
                series_list.append(series_item)

            option = {
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
                "legend": {"top": "0%", "data": [str(k) for k in legend_keys]},
                "grid": {"top": "15%", "left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
                "xAxis": {"type": "category", "boundaryGap": False, "data": x_data},
                "yAxis": {"type": "value", "name": y_name},
                "series": series_list,
            }

            st_echarts(options=option, height=f"{chart_height}px", key=comp_key)

        except Exception as e:
            st.error(f"⚠️ '{title}' 차트 렌더링 중 오류가 발생했습니다: {str(e)}")

    elif chart_type == "echarts_icon_bar":

        # 🛡️ 방어 로직: 데이터 유무 확인
        if df is None or df.empty:
            st.warning(f"⚠️ '{title}' 차트에 표시할 데이터가 없습니다.")
            return
        name_col = chart_info.get("name_col", "class")
        val_col = chart_info.get("value_col", "cnt")

        if name_col not in df.columns or val_col not in df.columns:
            st.error(f"⚠️ 차트 생성 오류: 데이터프레임에 [{name_col}, {val_col}] 컬럼이 존재하지 않습니다.")
            return
        y_categories = []
        chart_values = []
        # 이모지와 매핑된 디스플레이 이름
        display_map = {
            "bycicle": "🚲 자전거",
            "bicycle": "🚲 자전거",
            "stroller": "👶 유모차",
            "dog": "🐕 애완견"
        }

        for _, row in df.iterrows():
            cls_name = str(row[name_col]).lower()
            try:
                val = int(row[val_col]) if row[val_col] is not None else 0
            except (ValueError, TypeError):
                val = 0
            display_name = display_map.get(cls_name, str(row[name_col]))
            y_categories.append(display_name)
            chart_values.append(val)

        options = {
            "title": {"text": title, "textStyle": {"fontSize": 16}},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "grid": {"containLabel": True, "left": 10, "right": 30, "top": "15%", "bottom": "10%"},
            "xAxis": {
                "type": "value",
                "splitLine": {"show": False},
                "axisLabel": {"show": True},
            },
            "yAxis": {
                "type": "category",
                "data": y_categories,
                "inverse": True,
                "axisLine": {"show": True},
                "axisTick": {"show": False},
                "axisLabel": {"margin": 15, "fontSize": 14, "fontWeight": "bold"},
            },
            "series": [
                {
                    "type": "bar",
                    "data": chart_values,
                    "barWidth": "40%",
                    "label": {
                        "show": True,
                        "position": "right",
                        "formatter": "{c}",
                        "fontWeight": "bold",
                        "fontSize": 20
                    },
                    "itemStyle": {
                        "color": "#3B82F6",
                        "borderRadius": [0, 4, 4, 0]  # 막대 끝을 둥글게 처리
                    }
                }
            ],
        }

        st_echarts(options=options, height=f"{chart_height}px", key=comp_key)


def render_chart_grid(
        charts: List[Dict[str, Any]],
        cols_per_row: int = 3,
        ratios: List[float] = None,
):
    """차트 리스트를 받아 지정한 열 개수나 비율에 맞춰 자동으로 행을 나누어 배치합니다."""
    for i in range(0, len(charts), cols_per_row):
        row_charts = charts[i: i + cols_per_row]
        cols = st.columns(
            ratios if ratios and len(ratios) == len(row_charts) else len(row_charts),
            vertical_alignment="bottom"
        )
        for idx, chart in enumerate(row_charts):
            with cols[idx]:
                render_chart_item(chart)


# ------------------------------------------------------------------------------
# 2. 메인 페이지 로직
# ------------------------------------------------------------------------------

conn = st.connection("mysql", type="sql")

# 1. URL Query Parameter 확인 (Playwright 백엔드 접속 체크)
# 2. URL Query Parameter 파싱
query_params = st.query_params.to_dict() if hasattr(st.query_params, "to_dict") else dict(st.query_params)

param_user_id = query_params.get("user_id")
if isinstance(param_user_id, list): param_user_id = param_user_id[0]

param_work_no = query_params.get("work_no")
if isinstance(param_work_no, list): param_work_no = param_work_no[0]

selected_work_info = None

# DB에서 해당 work_no의 시작/종료 일자 및 정보 조회
work_query = f"""
        SELECT * 
        FROM rt_collect_info 
        WHERE user_id = '{param_user_id}' AND work_no = {param_work_no}
        LIMIT 1
    """
try:
    df_work = conn.query(work_query, ttl=0)
    if not df_work.empty:
        selected_work_info = df_work.to_dict(orient="records")[0]
    else:
        # rt_work 테이블 정보가 없을 경우 기본값 세팅 (필요 시 테이블명 수정)
        selected_work_info = {
            "work_no": param_work_no,
            "작업번호": param_work_no,
            "start_date": "20200101",
            "end_date": "20991231",
            "start_time": "00",
            "end_time": "24"
        }
except Exception as e:
    st.error(f"지점 정보 조회 실패: {e}")


# 선택된 work_no 세션 반영
st.session_state["selected_work_no"] = param_work_no
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

# 2. PDF 출력 모드 시 전용 스타일 적용 (사이드바, 헤더, 로고 완벽 제거)
st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        header { display: none !important; }
        footer { display: none !important; }
        .main .block-container {
            max-width: 100% !important;
            padding: 1rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# 3. user_id 및 work_list(작업 정보) 결정 분기
# 🎯 Playwright 접속 시: URL 파라미터 기반으로 user_id 및 단일 work_info 구성
if not param_user_id:
    st.error("⚠️ 로그인 정보가 없거나 열람 가능한 지점이 없습니다. 사이드바에서 먼저 로그인해 주세요.")
else:

    # 1. 표지 렌더링
    render_pdf_cover(selected_work_info)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.subheader("통행량 분석 보고서", divider="blue")

    st.write(" ")

    # 지도 및 기본 정보 표시
    render_location_map(selected_work_info)
    st.write(" ")
    st.write(" ")

    # ------------------------------------------------------------------------------
    # 🌟 [추가 기능] 측정 기간 일자별 날씨 정보 연동 영역
    # ------------------------------------------------------------------------------
    st.subheader("🌦️ 측정 기간 일자별 날씨 정보", divider="gray")
    st.write(" ")
    # 1. 지점 위도/경도 좌표 추출
    lat_val = selected_work_info.get("위도") or selected_work_info.get("latitude")
    lng_val = selected_work_info.get("경도") or selected_work_info.get("longitude")

    if lat_val is not None and lng_val is not None:
        try:
            lat_float = float(lat_val)
            lng_float = float(lng_val)

            # 2. 시작일자/종료일자 문자열(YYYYMMDD)을 API 포맷(YYYY-MM-DD)으로 변환
            if len(start_date_str) == 8 and len(end_date_str) == 8:
                api_start_date = f"{start_date_str[:4]}-{start_date_str[4:6]}-{start_date_str[6:]}"
                api_end_date = f"{end_date_str[:4]}-{end_date_str[4:6]}-{end_date_str[6:]}"

                # 💡 [추가] 종료일이 오늘(또는 어제)보다 미래일 경우, 조회 가능한 최대 과거 날짜(어제)로 자동 조정
                max_available_date = date.today() - timedelta(days=1)
                try:
                    parsed_end_date = datetime.strptime(api_end_date, "%Y-%m-%d").date()
                    if parsed_end_date > max_available_date:
                        api_end_date = max_available_date.strftime("%Y-%m-%d")
                        # 시작일이 조정된 종료일보다 이후가 되는 경우 방지
                        if api_start_date > api_end_date:
                            api_start_date = api_end_date
                except Exception:
                    pass

                # 3. Open-Meteo API 호출 함수
                @st.cache_data
                def fetch_weather_range(lat, lon, start, end):
                    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start}&end_date={end}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&timezone=Asia%2FSeoul"
                    try:
                        res = requests.get(url, timeout=10)
                        if res.status_code == 200:
                            return res.json()
                    except Exception:
                        pass
                    return None


                # WMO 날씨 코드를 아이콘 및 한글 상태로 매핑
                def get_weather_icon(code):
                    if code == 0:
                        return "☀️ 맑음"
                    elif code in [1, 2, 3]:
                        return "⛅ 구름/흐림"
                    elif code in [45, 48]:
                        return "🌫️ 안개"
                    elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67]:
                        return "🌧️ 비"
                    elif code in [71, 73, 75, 77, 85, 86]:
                        return "❄️ 눈"
                    elif code >= 95:
                        return "⛈️ 천둥번개"
                    else:
                        return "🌡️ 기타"


                weather_data = fetch_weather_range(lat_float, lng_float, api_start_date, api_end_date)

                if weather_data and "daily" in weather_data:
                    daily = weather_data["daily"]
                    weather_df = pd.DataFrame({
                        "날짜": daily["time"],
                        "최고기온": daily["temperature_2m_max"],
                        "최저기온": daily["temperature_2m_min"],
                        "강수량": daily["precipitation_sum"],
                        "날씨코드": daily["weathercode"]
                    })
                    weather_df["상태"] = weather_df["날씨코드"].apply(get_weather_icon)

                    # 💡 [추가] 날씨 카드 섹션을 최대 7일(1줄)까지만 표기하도록 제한 (추후 전체 보려면 아래 줄을 주석 처리 하세요)
                    weather_df = weather_df.head(7)

                    # 일자별 카드 형태로 그리드 표시 (최대 7일씩 행 분할 등 처리)
                    num_days = len(weather_df)
                    if num_days > 0:
                        # 화면 너비에 맞게 최대 7열씩 나누어 출력
                        cols = st.columns(min(num_days, 7))
                        for idx, row in weather_df.iterrows():
                            col_idx = idx % 7
                            if col_idx == 0 and idx > 0:
                                cols = st.columns(min(num_days - idx, 7))

                            with cols[col_idx]:
                                icon_part = row["상태"].split()[0]
                                text_part = row["상태"].split()[1] if len(row["상태"].split()) > 1 else ""
                                st.markdown(
                                    f"""
                                                <div style="
                                                    background-color: #f8f9fa;
                                                    border: 1px solid #e2e8f0;
                                                    border-radius: 6px;
                                                    padding: 10px;
                                                    text-align: center;
                                                    margin-bottom: 10px;
                                                ">
                                                    <div style="font-size: 13px; font-weight: bold; color: #475569;">{row['날짜']}</div>
                                                    <div style="font-size: 24px; margin: 4px 0;">{icon_part}</div>
                                                    <div style="font-size: 12px; color: #64748b; margin-bottom: 6px;">{text_part}</div>
                                                    <div style="font-size: 13px; color: #ef4444;">최고: {row['최고기온']}°C</div>
                                                    <div style="font-size: 13px; color: #3b82f6;">최저: {row['최저기온']}°C</div>
                                                    <div style="font-size: 12px; color: #0f172a; margin-top: 4px;">💧 {row['강수량']}mm</div>
                                                </div>
                                                """,
                                    unsafe_allow_html=True
                                )

                        # 기온 변화 추이 시각화 차트 추가
                        st.write(" ")
                        # ------------------------------------------------------------------------------
                        # 📈 기온(선) 및 강수량(막대) 멀티 차트 렌더링 (ECharts 듀얼축 활용)
                        # ------------------------------------------------------------------------------
                        st.write(" ")
                        st.write(" ")
                        st.write(" ")

                        x_data = weather_df["날짜"].tolist()
                        max_temp = weather_df["최고기온"].tolist()
                        min_temp = weather_df["최저기온"].tolist()
                        precipitation = weather_df["강수량"].tolist()

                        weather_chart_options = {
                            "tooltip": {
                                "trigger": "axis",
                                "axisPointer": {"type": "cross"}
                            },
                            "legend": {
                                "data": ["최고기온", "최저기온", "강수량"],
                                "top": "0%"
                            },
                            "grid": {
                                "top": "18%",
                                "left": "5%",
                                "right": "5%",
                                "bottom": "10%",
                                "containLabel": True
                            },
                            "xAxis": [
                                {
                                    "type": "category",
                                    "data": x_data,
                                    "axisPointer": {"type": "shadow"}
                                }
                            ],
                            "yAxis": [
                                {
                                    "type": "value",
                                    "name": "기온 (°C)",
                                    "position": "left",
                                    "axisLabel": {"formatter": "{value} °C"}
                                },
                                {
                                    "type": "value",
                                    "name": "강수량 (mm)",
                                    "position": "right",
                                    "splitLine": {"show": False},  # 배경 격자선 중복 방지
                                    "axisLabel": {"formatter": "{value} mm"}
                                }
                            ],
                            "series": [
                                {
                                    "name": "최고기온",
                                    "type": "line",
                                    "data": max_temp,
                                    "itemStyle": {"color": "#ef4444"},  # 빨간 계열 (최고기온)
                                    "lineStyle": {"width": 2}
                                },
                                {
                                    "name": "최저기온",
                                    "type": "line",
                                    "data": min_temp,
                                    "itemStyle": {"color": "#3b82f6"},  # 파란 계열 (최저기온)
                                    "lineStyle": {"width": 2}
                                },
                                {
                                    "name": "강수량",
                                    "type": "bar",
                                    "yAxisIndex": 1,  # 우측 Y축 사용
                                    "data": precipitation,
                                    "itemStyle": {
                                        "color": "#93c5fd",  # 연한 하늘색 막대
                                        "borderRadius": [4, 4, 0, 0]
                                    },
                                    "barWidth": "35%"
                                }
                            ]
                        }

                        st_echarts(options=weather_chart_options, height="600px", key="weather_multi_chart")
                        # 📌 출처 및 면책 안내 문구 추가
                        st.markdown(
                            """
                            <div style="
                                font-size: 12px; 
                                color: #64748b; 
                                text-align: right; 
                                margin-top: 4px; 
                                margin-bottom: 16px;
                            ">
                                📊 <b>기상 데이터 출처:</b> Open-Meteo API (기상 재분석 모델)<br>
                                ⚠️ 본 기상 정보는 글로벌 기상 모델을 기반으로 산출된 값으로, 실제 기상청 공식 실측값과는 다소 차이가 있을 수 있습니다.
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.info("ℹ️ 해당 측정 기간 내 조회된 날씨 데이터가 없습니다.")
                else:
                    st.warning("⚠️ 지정된 날짜 및 위치의 기상 데이터를 불러오지 못했습니다.")
            else:
                st.info("ℹ️ 측정 시작일자 또는 종료일자 형식(YYYYMMDD)이 올바르지 않습니다.")
        except Exception as e:
            st.warning(f"⚠️ 날씨 정보를 불러오는 중 오류가 발생했습니다: {e}")
    else:
        st.info("ℹ️ 해당 지점의 위도/경도 정보가 없어 날씨 정보를 불러올 수 없습니다.")

    all_comments = fetch_all_comments(param_user_id, param_work_no)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_section_header("📅", "분석 요약", "Summary")
    st.write(" ")

    variables1 = {
        "id": param_user_id,
        "work_no": param_work_no,
        "start_date_str": start_date_str,
        "end_date_str": end_date_str,
        "start_time_str": start_time_str,
        "end_time_str": end_time_str,
    }

    # --------------------------------------------------------------------------
    # A. Metric 상단 지표 조회 및 렌더링
    # --------------------------------------------------------------------------
    qr_h1 = """SELECT sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 """
    qr_h2 = """SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND rca.class IN ('m01', 'm23', 'm45', 'm67', 'w01', 'w23', 'w45', 'w67', 'unknown') AND rca.del_yn = 0 GROUP BY rca.collect_date) t1"""
    qr_h3 = """SELECT round(avg(t1.cnt)) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} AND rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' and (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date, rca.collect_hour) t1"""
    qr_h4 = """SELECT round(avg(t1.cnt)/60) as avg FROM (SELECT rca.collect_date, rca.collect_hour as collect_hour, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_date, rca.collect_hour) t1"""
    qr_h5 = """SELECT IFNULL(ROUND(AVG(t1.cnt)), 0) AS weekday_avg FROM (SELECT rca.collect_date AS collect_date, IFNULL(SUM(rca.collect_cnt), 0) AS cnt FROM rt_collect_summary rca JOIN rt_calendar c ON rca.collect_date = c.dt WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND rca.class IN ('m01', 'm23', 'm45', 'm67', 'w01', 'w23', 'w45', 'w67', 'unknown') AND rca.del_yn = 0 AND c.anal_gubun = 'Weekday' GROUP BY rca.collect_date) t1"""
    qr_h6 = """SELECT IFNULL(ROUND(AVG(t1.cnt)), 0) AS weekend_avg FROM (SELECT rca.collect_date AS collect_date, IFNULL(SUM(rca.collect_cnt), 0) AS cnt FROM rt_collect_summary rca JOIN rt_calendar c ON rca.collect_date = c.dt WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND rca.class IN ('m01', 'm23', 'm45', 'm67', 'w01', 'w23', 'w45', 'w67', 'unknown') AND rca.del_yn = 0 AND c.anal_gubun = 'Weekend' GROUP BY rca.collect_date) t1"""
    qr_h7 = """SELECT avg(rca.stay_time) as stay_time FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.stay_time <> 99999 AND rca.del_yn = 0 """
    qr_h8 = """SELECT AVG(t1.hourly_avg_stay) as stay_time FROM (SELECT rca.collect_hour, AVG(rca.stay_time) AS hourly_avg_stay FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') AND rca.stay_time <> 99999 AND rca.del_yn = 0 GROUP BY rca.collect_hour) t1;"""

    # 1. 하루 평균 통행량 데이터 조회 (등급 판정용)
    df_h2_res = conn.query(qr_h2.format(**variables1), ttl=600)
    avg_daily_cnt = 0
    if not df_h2_res.empty and df_h2_res.iloc[0, 0] is not None:
        avg_daily_cnt = float(df_h2_res.iloc[0, 0])

    # 2. 등급 판정 및 색상 설정 로직
    if avg_daily_cnt >= 10000:
        grade = "S"
        grade_color = "#FF4B4B"  # 빨강
    elif avg_daily_cnt >= 5000:
        grade = "A"
        grade_color = "#FF8C00"  # 주황
    elif avg_daily_cnt >= 1000:
        grade = "B"
        grade_color = "#FFD000"  # 황갈/골드
    elif avg_daily_cnt >= 500:
        grade = "C"
        grade_color = "#1E88E5"  # 파랑
    else:
        grade = "D"
        grade_color = "#8E44AD"  # 보라

    # 3. 등급 시각화 영역 (HTML/CSS로 색상 반영)
    col_g1, col_g2 = st.columns([1, 2.5])

    with col_g1:
        st.markdown(
            f"""
            <div style="
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 10px;
                padding: 12px;
                text-align: center;
                height: 150px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="text-align: left; font-size: 20px; color: #6c757d; font-weight: bold; margin-bottom: 2px; margin-left: 10px;">
                    트래픽 등급
                </div>      
                <div style="font-size: 50px; font-weight: 900; color: {grade_color}; line-height: 1.1;">
                    {grade}
                </div>         
            </div>            
            """,
            unsafe_allow_html=True,
        )

    with col_g2:
        st.markdown(
            """
            <div style="
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 10px;
                padding: 14px 18px;
                height: 150px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="text-align: right; font-size: 14px; font-weight: bold; color: #495057; margin-bottom: 8px;">
                    (기준 : 하루 평균)
                </div>                
                <div style="font-size: 20px; font-weight: 600; line-height: 1.6; text-align: center;">
                    <span style="color: #FF4B4B;">S</span> : 1만명 이상 &nbsp;&nbsp;|&nbsp;&nbsp;
                    <span style="color: #FF8C00;">A</span> : 5천명 이상 &nbsp;&nbsp;|&nbsp;&nbsp;
                    <span style="color: #FFD000;">B</span> : 1천명 이상 &nbsp;&nbsp;&nbsp;&nbsp;<BR>
                    <span style="color: #1E88E5;">C</span> : 500명 이상 &nbsp;&nbsp;|&nbsp;&nbsp;
                    <span style="color: #8E44AD;">D</span> : 100명 이하
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write(" ")
    st.write(" ")
    st.write(" ")

    render_metric_cards(
        conn.query(qr_h1.format(**variables1), ttl=600),
        conn.query(qr_h2.format(**variables1), ttl=600),
        conn.query(qr_h3.format(**variables1), ttl=600),
        conn.query(qr_h4.format(**variables1), ttl=600),
        conn.query(qr_h5.format(**variables1), ttl=600),
        conn.query(qr_h6.format(**variables1), ttl=600),
        conn.query(qr_h7.format(**variables1), ttl=600),
        conn.query(qr_h8.format(**variables1), ttl=600),
    )
    st.write(" ")

    # --------------------------------------------------------------------------
    # B. 차트 설정 메타데이터 정의
    # --------------------------------------------------------------------------

    # 1. 날짜별 통행량
    qr1 = "SELECT DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, SUM(rca.collect_cnt) AS cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') ORDER BY MIN(STR_TO_DATE(rca.collect_date, '%Y%m%d'));"
    chart_date = {
        "chart_id": "date_traffic",
        "title": "일자별 통행량",
        "type": "bar",
        "df": conn.query(qr1.format(**variables1), ttl=600),
        "x": "collect_date",
        "y": "cnt",
        "x_label": "일자",
        "y_label": "통행량",
        "chart_height": 530
    }

    # 2. 시간대별 통행량 (주중/주말)
    qr3_combined = """
        SELECT '주중' AS gubun, tt1.collect_hour, SUM(tt1.cnt) AS cnt 
        FROM (
            SELECT t1.collect_hour, ROUND(AVG(t1.cnt)) AS cnt 
            FROM (
                SELECT rca.collect_hour, rca.collect_date, SUM(rca.collect_cnt) AS cnt 
                FROM rt_collect_summary rca 
                JOIN rt_calendar c ON rca.collect_date = c.dt 
                WHERE rca.user_id = '{id}' AND rca.work_no = {work_no}
                  and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' 
                  AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
                  AND rca.del_yn = 0 AND c.anal_gubun = 'Weekday' 
                GROUP BY rca.collect_hour, rca.collect_date
            ) t1 GROUP BY t1.collect_hour
        ) tt1 GROUP BY tt1.collect_hour

        UNION ALL

        SELECT '주말' AS gubun, tt1.collect_hour, SUM(tt1.cnt) AS cnt 
        FROM (
            SELECT t1.collect_hour, ROUND(AVG(t1.cnt)) AS cnt 
            FROM (
                SELECT rca.collect_hour, rca.collect_date, SUM(rca.collect_cnt) AS cnt 
                FROM rt_collect_summary rca 
                JOIN rt_calendar c ON rca.collect_date = c.dt 
                WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} 
                  and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
                  AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
                  AND rca.del_yn = 0 AND c.anal_gubun = 'Weekend' 
                GROUP BY rca.collect_hour, rca.collect_date
            ) t1 GROUP BY t1.collect_hour
        ) tt1 GROUP BY tt1.collect_hour
        ORDER BY collect_hour
        """

    chart_hour_weekday_weekend = {
        "chart_id": "hour_weekday_weekend",
        "title": "주중/주말 시간대별 평균 통행량",
        "type": "echarts_multi_line",
        "df": conn.query(qr3_combined.format(**variables1), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "gubun",
        "values_col": "cnt",
        "y_name": "통행량",
        "chart_height": 400
    }

    # 1. 날짜별 평균 체류시간
    qr1_stay_perday = "SELECT DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, AVG(rca.stay_time) AS cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') ORDER BY MIN(STR_TO_DATE(rca.collect_date, '%Y%m%d'));"
    chart_date_stay = {
        "chart_id": "date_stay",
        "title": "일자별 평균 체류시간",
        "type": "bar",
        "df": conn.query(qr1_stay_perday.format(**variables1), ttl=600),
        "x": "collect_date",
        "y": "cnt",
        "x_label": "일자",
        "y_label": "평균 체류시간",
        "chart_height": 450
    }

    # 3. 요일/시간대별 통행량 및 체류시간
    qr2 = "SELECT t1.collect_hour, t1.collect_day, t1.collect_order, avg(t1.cnt) as cnt FROM (SELECT (CASE WHEN rca.collect_day = 'Sun' THEN '일' WHEN rca.collect_day = 'Mon' THEN '월' WHEN rca.collect_day = 'Tue' THEN '화' WHEN rca.collect_day = 'Wed' THEN '수' WHEN rca.collect_day = 'Thu' THEN '목' WHEN rca.collect_day = 'Fri' THEN '금' WHEN rca.collect_day = 'Sat' THEN '토' END) as collect_day, (CASE WHEN rca.collect_day = 'Sun' THEN 1 WHEN rca.collect_day = 'Mon' THEN 2 WHEN rca.collect_day = 'Tue' THEN 3 WHEN rca.collect_day = 'Wed' THEN 4 WHEN rca.collect_day = 'Thu' THEN 5 WHEN rca.collect_day = 'Fri' THEN 6 WHEN rca.collect_day = 'Sat' THEN 7 END) as collect_order, rca.collect_hour, rca.collect_date, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY collect_day, collect_order, rca.collect_hour, rca.collect_date) t1 GROUP BY t1.collect_hour, t1.collect_day, t1.collect_order ORDER BY t1.collect_hour, t1.collect_day, t1.collect_order"
    chart_day_hour = {
        "chart_id": "day_hour_traffic",
        "title": "요일별/시간대별 평균 통행량",
        "type": "echarts_multi_line",
        "df": conn.query(qr2.format(**variables1), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "collect_day",
        "values_col": "cnt",
        "y_name": "통행량",
        "chart_height": 400
    }

    qr20 = "SELECT t1.collect_hour, t1.collect_day, t1.collect_order, round(avg(t1.stay_time), 1) as stay_time FROM (SELECT (CASE WHEN rca.collect_day = 'Sun' THEN '일' WHEN rca.collect_day = 'Mon' THEN '월' WHEN rca.collect_day = 'Tue' THEN '화' WHEN rca.collect_day = 'Wed' THEN '수' WHEN rca.collect_day = 'Thu' THEN '목' WHEN rca.collect_day = 'Fri' THEN '금' WHEN rca.collect_day = 'Sat' THEN '토' END) as collect_day, (CASE WHEN rca.collect_day = 'Sun' THEN 1 WHEN rca.collect_day = 'Mon' THEN 2 WHEN rca.collect_day = 'Tue' THEN 3 WHEN rca.collect_day = 'Wed' THEN 4 WHEN rca.collect_day = 'Thu' THEN 5 WHEN rca.collect_day = 'Fri' THEN 6 WHEN rca.collect_day = 'Sat' THEN 7 END) as collect_order, rca.collect_hour, rca.collect_date, avg(rca.stay_time) as stay_time FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 AND rca.stay_time <> 99999 GROUP BY collect_day, collect_order, rca.collect_hour, rca.collect_date) t1 GROUP BY t1.collect_hour, t1.collect_day, t1.collect_order ORDER BY t1.collect_hour, t1.collect_day, t1.collect_order"
    chart_day_hour_stay_time = {
        "chart_id": "day_hour_stay",
        "title": "요일별/시간대별 평균 체류시간",
        "type": "echarts_multi_line",
        "df": conn.query(qr20.format(**variables1), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "collect_day",
        "values_col": "stay_time",
        "y_name": "체류시간(초)",
        "chart_height": 450
    }

    # 4. 성별 일자별 차트
    qr20_1 = """select (CASE WHEN rca.gender = 'male' THEN '남성' WHEN rca.gender = 'female' THEN '여성' END) as gender, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, sum(rca.collect_cnt) as cnt
                      from rt_collect_summary rca 
                        WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' 
                            and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' 
                            AND (rca.class like 'm%' OR rca.class like 'w%') 
                            AND rca.del_yn = 0 
                            AND rca.stay_time <> 99999        
                      group by (CASE WHEN rca.gender = 'male' THEN '남성' WHEN rca.gender = 'female' THEN '여성' END), DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d')"""

    chart_gender_day = {
        "title": "일자별 성별 통행량 분석",
        "type": "echarts_multi_bar_gender",
        "df": conn.query(qr20_1.format(**variables1), ttl=600),
        "index_col": "collect_date",  # X축이 될 열 이름 (예: 일자)
        "columns_col": "gender",  # 범례(남/여)로 분리할 열 이름
        "values_col": "cnt",  # 수치 값이 들어있는 열 이름
        "y_name": "통행량(명)",
        "stacked": True,  # True면 누적 바 차트, False면 나란히 배치되는 그룹 바 차트
        "chart_height": 280
    }

    qr21 = "SELECT (CASE WHEN rca.gender = 'male' THEN '남성' WHEN rca.gender = 'female' THEN '여성' END) as gender, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY (CASE WHEN rca.gender = 'male' THEN '남성' WHEN rca.gender = 'female' THEN '여성' END)"
    chart_gender = {
        "chart_id": "gender_pie",
        "title": "성별 통행량",
        "type": "echarts_pie",
        "df": conn.query(qr21.format(**variables1), ttl=600),
        "name_col": "gender",
        "value_col": "cnt",
        "semi_pie": None,
        "chart_height": 280
    }

    qr22 = """
            SELECT 
                t1.collect_hour AS collect_hour, 
                (CASE WHEN t1.gender_code = 'male' THEN '남성' 
                      WHEN t1.gender_code = 'female' THEN '여성' END) AS gender, 
                ROUND(AVG(t1.cnt)) AS cnt 
            FROM (
                SELECT 
                    rca.collect_hour AS collect_hour, 
                    rca.gender AS gender_code, 
                    rca.collect_date AS collect_date, 
                    SUM(rca.collect_cnt) AS cnt
                FROM rt_collect_summary rca 
                WHERE rca.user_id = '{id}' 
                  AND rca.work_no = {work_no} 
                  and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
                  AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
                  AND rca.del_yn = 0 
                GROUP BY rca.collect_hour, rca.gender, rca.collect_date
            ) t1 
            GROUP BY t1.collect_hour, t1.gender_code
            ORDER BY t1.collect_hour
        """

    chart_gender_hour = {
        "chart_id": "gender_hour",
        "title": "성별/시간대별 평균 통행량",
        "type": "echarts_multi_line",
        "df": conn.query(qr22.format(**variables1), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "gender",
        "values_col": "cnt",
        "y_name": "통행량",
        "chart_height": 280
    }

    qr25 = """
                SELECT 
                    t1.collect_hour AS collect_hour, 
                    (CASE WHEN t1.gender_code = 'male' THEN '남성' 
                          WHEN t1.gender_code = 'female' THEN '여성' END) AS gender, 
                    ROUND(AVG(t1.stay_time),1) AS stay_time 
                FROM (
                    SELECT 
                        rca.collect_hour AS collect_hour, 
                        rca.gender AS gender_code, 
                        rca.collect_date AS collect_date, 
                        AVG(rca.stay_time) AS stay_time
                    FROM rt_collect_summary rca 
                    WHERE rca.user_id = '{id}' 
                      AND rca.work_no = {work_no} 
                      and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}'
                      AND (rca.class LIKE 'm%' OR rca.class LIKE 'w%') 
                      AND rca.del_yn = 0 
                    GROUP BY rca.collect_hour, rca.gender, rca.collect_date
                ) t1 
                GROUP BY t1.collect_hour, t1.gender_code
                ORDER BY t1.collect_hour
            """

    chart_gender_hour_stay = {
        "chart_id": "gender_hour_stay",
        "title": "성별/시간대별 평균 체류시간",
        "type": "echarts_multi_line",
        "df": conn.query(qr25.format(**variables1), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "gender",
        "values_col": "stay_time",
        "y_name": "체류시간",
        "chart_height": 280
    }

    # 5. 연령별 일자별 차트
    qr23_1 = """select rca.age as age, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, sum(rca.collect_cnt) as cnt
                          from rt_collect_summary rca 
                            WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' 
                                and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' 
                                AND (rca.class like 'm%' OR rca.class like 'w%') 
                                AND rca.del_yn = 0 
                                AND rca.stay_time <> 99999        
                          group by rca.age, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d')"""

    chart_age_day = {
        "title": "일자별 연령별 통행량 분석",
        "type": "echarts_multi_bar_age",
        "df": conn.query(qr23_1.format(**variables1), ttl=600),
        "index_col": "collect_date",  # X축이 될 열 이름 (예: 일자)
        "columns_col": "age",  # 연령대
        "values_col": "cnt",  # 수치 값이 들어있는 열 이름
        "y_name": "통행량(명)",
        "stacked": True,  # True면 누적 바 차트, False면 나란히 배치되는 그룹 바 차트
        "chart_height": 280
    }

    # 5. 연령별 차트
    qr23 = "SELECT t1.age as age, (CASE WHEN t1.age = '10대 이하' THEN 1 WHEN t1.age = '20~30대' THEN 2 WHEN t1.age = '40~50대' THEN 3 WHEN t1.age = '60~70대' THEN 4 END) as age_order, sum(t1.cnt) as cnt FROM (SELECT rca.age as age, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.age UNION ALL SELECT age, cnt FROM rt_dummy_age2) t1 GROUP BY t1.age ORDER BY age_order"
    chart_age = {
        "chart_id": "age_pie",
        "title": "연령별 통행량",
        "type": "echarts_pie",
        "df": conn.query(qr23.format(**variables1), ttl=600),
        "name_col": "age",
        "value_col": "cnt",
        "semi_pie": None,
        "chart_height": 280
    }

    qr24 = "SELECT t1.collect_hour as hour, t1.age as age, sum(t1.cnt) as cnt FROM (SELECT rca.collect_hour as collect_hour, rca.age as age, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') and rca.del_yn = 0 GROUP BY rca.collect_hour, rca.age) t1 GROUP BY t1.collect_hour, t1.age"
    chart_age_hour = {
        "chart_id": "age_hour",
        "title": "연령별(시간대) 평균 통행량",
        "type": "echarts_multi_line",
        "df": conn.query(qr24.format(**variables1), ttl=600),
        "index_col": "hour",
        "columns_col": "age",
        "values_col": "cnt",
        "y_name": "통행량",
        "chart_height": 280
    }

    # 연령별 체류시간
    qr24_s = "SELECT t1.collect_hour as hour, t1.age as age, ROUND(AVG(t1.stay_time),1) as stay_time FROM (SELECT rca.collect_hour as collect_hour, rca.age as age, avg(rca.stay_time) as stay_time FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') and rca.del_yn = 0 GROUP BY rca.collect_hour, rca.age) t1 GROUP BY t1.collect_hour, t1.age"
    chart_age_hour_stay = {
        "chart_id": "age_hour_stay",
        "title": "연령별(시간대) 평균 체류시간",
        "type": "echarts_multi_line",
        "df": conn.query(qr24_s.format(**variables1), ttl=600),
        "index_col": "hour",
        "columns_col": "age",
        "values_col": "stay_time",
        "y_name": "체류시간",
        "chart_height": 260
    }

    # 5. 연령별 일자별 차트
    qr30 = """select rca.direction as direction, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d') AS collect_date, sum(rca.collect_cnt) as cnt
                              from rt_collect_summary rca 
                                WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' 
                                    and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' 
                                    AND (rca.class like 'm%' OR rca.class like 'w%') 
                                    AND rca.del_yn = 0 
                                    AND rca.stay_time <> 99999        
                              group by rca.direction, DATE_FORMAT(STR_TO_DATE(rca.collect_date, '%Y%m%d'), '%m/%d')"""

    chart_direction_day = {
        "title": "일자별 방향별 통행량 분석",
        "type": "echarts_multi_bar_direction",
        "df": conn.query(qr30.format(**variables1), ttl=600),
        "index_col": "collect_date",  # X축이 될 열 이름 (예: 일자)
        "columns_col": "direction",  # 방향
        "values_col": "cnt",  # 수치 값이 들어있는 열 이름
        "y_name": "통행량(명)",
        "stacked": True,  # True면 누적 바 차트, False면 나란히 배치되는 그룹 바 차트
        "chart_height": 500
    }

    # 6. 방향별 차트
    qr31 = "SELECT rca.direction as direction, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.direction"
    chart_direction = {
        "chart_id": "direction_pie",
        "title": "방향별 통행량",
        "type": "echarts_pie",
        "df": conn.query(qr31.format(**variables1), ttl=600),
        "name_col": "direction",
        "value_col": "cnt",
        "semi_pie": None,
        "chart_height": 550
    }

    qr32 = "SELECT rca.collect_hour as collect_hour, rca.direction as direction, sum(rca.collect_cnt) as cnt FROM rt_collect_summary rca WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} and rca.collect_date >= '{start_date_str}' and rca.collect_date <= '{end_date_str}' and rca.collect_hour >= '{start_time_str}' and rca.collect_hour < '{end_time_str}' AND (rca.class like 'm%' OR rca.class like 'w%') AND rca.del_yn = 0 GROUP BY rca.collect_hour, rca.direction"
    chart_dir_hour = {
        "chart_id": "dir_hour",
        "title": "방향별(시간대) 평균 통행량",
        "type": "echarts_multi_line",
        "df": conn.query(qr32.format(**variables1), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "direction",
        "values_col": "cnt",
        "y_name": "통행량",
        "chart_height": 500
    }

    # 자전거, 유모차, 애완견 통행량 쿼리
    qr_pictorial = """
                SELECT (CASE WHEN rca.class = 'bycicle' THEN 'bycicle'
                             WHEN rca.class = 'stroller' THEN 'stroller'
                             WHEN rca.class = 'dog' THEN 'dog' END) AS class,
                       SUM(rca.collect_cnt) AS cnt
                  FROM rt_collect_summary rca 
                 WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} 
                   AND rca.collect_date >= '{start_date_str}' AND rca.collect_date <= '{end_date_str}' 
                   AND rca.collect_hour >= '{start_time_str}' AND rca.collect_hour < '{end_time_str}' 
                   AND rca.class IN ('bycicle', 'stroller', 'dog') 
                   AND rca.del_yn = 0 
                   AND rca.stay_time <> 99999        
                 GROUP BY class
            """

    chart_pictorial = {
        "chart_id": "pictorial_features",
        "title": "기타 객체 통행량 분석",
        "type": "echarts_icon_bar",  # 👈 타입 변경
        "df": conn.query(qr_pictorial.format(**variables1), ttl=600),
        "name_col": "class",
        "value_col": "cnt",
        "chart_height": 450
    }

    qr99 = """
                    select t1.collect_hour as collect_hour
                    , (CASE WHEN t1.class = 'bycicle' THEN 'Bycicle'
                            WHEN t1.class = 'stroller' THEN 'Stroller'
                            WHEN t1.class = 'dog' THEN 'Dog' END) as class
                    , (CASE WHEN t1.class = 'bycicle' THEN 1
                            WHEN t1.class = 'stroller' THEN 2
                            WHEN t1.class = 'dog' THEN 3 END) as class_order
                        , sum(t1.cnt) as cnt
                from (
                    select rca.collect_hour as collect_hour, rca.class as class, sum(rca.collect_cnt) as cnt
                      from rt_collect_summary rca 
                     WHERE rca.user_id = '{id}' AND rca.work_no = {work_no} 
                       AND rca.collect_date >= '{start_date_str}' AND rca.collect_date <= '{end_date_str}' 
                       AND rca.collect_hour >= '{start_time_str}' AND rca.collect_hour < '{end_time_str}' 
                       AND rca.class IN ('bycicle', 'stroller', 'dog') 
                       AND rca.del_yn = 0 
                       AND rca.stay_time <> 99999
                      group by rca.collect_hour, rca.class) t1
                group by t1.collect_hour, t1.class
                """
    chart_etc_hour = {
        "chart_id": "etc_hour",
        "title": "기타 객체(시간대) 평균 통행량",
        "type": "echarts_multi_line",
        "df": conn.query(qr99.format(**variables1), ttl=600),
        "index_col": "collect_hour",
        "columns_col": "class",
        "values_col": "cnt",
        "y_name": "통행량",
        "chart_height": 450
    }

    # --------------------------------------------------------------------------
    # C. 대시보드 레이아웃 구성
    # --------------------------------------------------------------------------
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_date], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    render_comment_box(all_comments, comment_key="com1")
    st.markdown('<div style="text-align: right;" class="copyright">Copyright © 2026. All Rights Reserved.</div>',
                unsafe_allow_html=True)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_section_header("🕒", "시간대 분석", "Timeline Analysis")
    st.write(" ")
    render_chart_grid([chart_hour_weekday_weekend], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    render_section_header("🗓️", "요일 분석", "Week Analysis")
    st.write(" ")
    render_chart_grid([chart_day_hour], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    render_comment_box(all_comments, comment_key="com2")
    st.markdown('<div style="text-align: right;" class="copyright">Copyright © 2026. All Rights Reserved.</div>',
                unsafe_allow_html=True)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_section_header("⏱️", "체류시간 분석", "Stay Time Analysis")
    st.write(" ")
    render_chart_grid([chart_date_stay], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_day_hour_stay_time], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    render_comment_box(all_comments, comment_key="com3")
    st.markdown('<div style="text-align: right;" class="copyright">Copyright © 2026. All Rights Reserved.</div>',
                unsafe_allow_html=True)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_section_header("🚻", "성별 분석", "Gender Analysis")
    st.write(" ")
    render_chart_grid([chart_gender_day], cols_per_row=1)
    st.write(" ")
    render_chart_grid([chart_gender, chart_gender_hour], cols_per_row=2)
    st.write(" ")
    render_chart_grid([chart_gender_hour_stay], cols_per_row=1)
    st.write(" ")
    render_comment_box(all_comments, comment_key="com4")
    st.markdown('<div style="text-align: right;" class="copyright">Copyright © 2026. All Rights Reserved.</div>',
                unsafe_allow_html=True)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_section_header("👥", "연령대 분석", "Age Analysis")
    st.write(" ")
    render_chart_grid([chart_age_day], cols_per_row=1)
    st.write(" ")
    render_chart_grid([chart_age, chart_age_hour], cols_per_row=2)
    st.write(" ")
    render_chart_grid([chart_age_hour_stay], cols_per_row=1)
    st.write(" ")
    render_comment_box(all_comments, comment_key="com5")
    st.markdown('<div style="text-align: right;" class="copyright">Copyright © 2026. All Rights Reserved.</div>',
                unsafe_allow_html=True)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_section_header("🚲", "기타 분석", "Additional Analysis")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_direction_day], cols_per_row=1)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_direction, chart_dir_hour], cols_per_row=2)
    st.markdown('<div style="text-align: right;" class="copyright">Copyright © 2026. All Rights Reserved.</div>', unsafe_allow_html=True)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_chart_grid([chart_pictorial, chart_etc_hour], cols_per_row=2)
    st.write(" ")
    st.write(" ")
    st.write(" ")
    st.write(" ")
    render_info_footer(logo_path_or_url="images/logo_wide.png")

