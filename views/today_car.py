import streamlit as st

#Realtargeting 로고
st.logo("images/logo_wide.png", size="large", link="https://realtargeting.streamlit.app", icon_image="images/logo_wide.png")

st.header("🚗 일일 모니터링(차량)")

# 화면 우측 하단 팝업 알림
st.toast("🚧 해당 기능은 현재 준비 중입니다.", icon="ℹ️")

# 본문 안내 문구 (선택사항)
st.info("현재 시스템 점검 및 기능 개발 중입니다. 빠른 시일 내에 서비스하겠습니다.")