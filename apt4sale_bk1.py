# Streamlit 윤보가 세션처리부분 수정하기 전 버전
import json
import requests
import streamlit as st
import pandas as pd


list_sum_result = []

# Streamlit 페이지 레이아웃 설정
st.set_page_config(layout="wide")

# 세션 상태를 초기화하는 함수
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'sort_column' not in st.session_state:
    st.session_state['sort_column'] = None
if 'ascending' not in st.session_state:
    st.session_state['ascending'] = True

# 조회 조건 히스토리를 표시하고 선택 가능하게 하는 함수
def show_history():
    if st.session_state['history']:
        st.subheader("조회 히스토리")
        for i, hist in enumerate(st.session_state['history']):
            if st.button(hist, key=f"hist_{i}"):
                # 히스토리에서 선택된 항목을 입력 필드에 설정하고 자동 조회
                st.session_state.condition = hist
                search_data(hist)

# 사이드바에 입력 조건을 위한 폼 생성
with st.sidebar:
    st.header("조회 조건")
    # 여기에 조회 조건 입력 필드 추가
    condition = st.text_input("조건을 입력하세요", key = "condition")
    # 조회 버튼
    submit_button = st.button("조회")

    # 히스토리 섹션
    show_history()



# 컬럼 정렬 함수
def sort_dataframe(df, column):
    if column:
        return df.sort_values(by=[column], ascending=st.session_state['ascending'])
    return df

def SaveAptInfo(p_page, p_comp, p_list_sum):
    down_url = 'https://new.land.naver.com/api/articles/complex/' + p_comp + '?realEstateType=APT&tradeType=A1%3AB1&tag=%3A%3A%3A%3A%3A%3A%3A%3A&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=900000000&areaMin=0&areaMax=900000000&oldBuildYears&recentlyBuildYears&minHouseHoldCount&maxHouseHoldCount&showArticle=false&sameAddressGroup=true&minMaintenanceCost&maxMaintenanceCost&priceType=RETAIL&directions=&page=' + p_page + '&complexNo=' + p_comp + '&buildingNos=&areaNos=&type=list&order=rank'

    r = requests.get(down_url, data={"sameAddressGroup": "true"}, headers={
        "Accept-Encoding": "gzip",
        "Host": "m.land.naver.com",
        "Referer": "https://new.land.naver.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        #"User-Agent": "Mozilla/5.0 (Phone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE2NDk4MzA1OTgsImV4cCI6MTY0OTg0MTM5OH0.lNapCTDOQAQZwIGafsVQeUqBmSzUTKm8dUJHaJJgrK0"
    })


    #st.info('파싱 체크1' + r.text)
    r.encoding = "utf-8"

    #st.info('파싱 체크2' + r.text)

    temp = json.loads(r.text)

    p_apt_list = temp['articleList']

    # 추출한 정보를 리스트에 적재
    for data in temp['articleList']:

        # 추출한 정보 로그
        # print(data)

        if data.get("articleFeatureDesc") == None:

            # 금액 숫자로 변환
            dowp = str(data['dealOrWarrantPrc'])
            dowp_int = int(dowp.replace(',', '')) if dowp.find('억') == -1 else (int(dowp[:dowp.find('억')]) * 10000) + (
                0 if dowp.endswith('억') else int(dowp[dowp.find('억') + 1:].replace(',', '')))

            p_list_sum.append(
                #[data['articleNo'],
                 [data['articleName'], data['tradeTypeName'], data['area1'],
                 round(float(data['area1']) / 3.3), data['area2'], round(float(data['area2']) / 3.3),
                 data['buildingName'], data['floorInfo'], data['direction'], dowp_int,
                 round(dowp_int / round(float(data['area1']) / 3.3)),
                 '', data['realtorName']])
        else:

            # 금액 숫자로 변환
            dowp = str(data['dealOrWarrantPrc'])
            dowp_int = int(dowp.replace(',', '')) if dowp.find('억') == -1 else (int(dowp[:dowp.find('억')]) * 10000) + (
                0 if dowp.endswith('억') else int(dowp[dowp.find('억') + 1:].replace(',', '')))

            p_list_sum.append(
                #[data['articleNo'],
                 [data['articleName'], data['tradeTypeName'], data['area1'],
                 round(float(data['area1']) / 3.3), data['area2'], round(float(data['area2']) / 3.3),
                 data['buildingName'], data['floorInfo'], data['direction'], dowp_int,
                 round(dowp_int / round(float(data['area1']) / 3.3)),
                 data['articleFeatureDesc'], data['realtorName']])
    return p_list_sum, p_apt_list

def find_info(a_comp):
    comp = condition
    list_sum = []

    # 1회차 조회
    list_sum, apt_list = SaveAptInfo('1', a_comp, list_sum)

    # 2회차 조회
    if (len(apt_list) == 20):
        list_sum, apt_list = SaveAptInfo('2', a_comp, list_sum)

    # 3회차 조회
    if (len(apt_list) == 20):
        list_sum, apt_list = SaveAptInfo('3', a_comp, list_sum)

    # 4회차 조회
    if (len(apt_list) == 20):
        list_sum, apt_list = SaveAptInfo('4', a_comp, list_sum)

    # 5회차 조회
    if (len(apt_list) == 20):
        list_sum, apt_list = SaveAptInfo('5', a_comp, list_sum)

    # 6회차 조회
    if (len(apt_list) == 20):
        list_sum, apt_list = SaveAptInfo('6', a_comp, list_sum)

    # 7회차 조회
    if (len(apt_list) == 20):
        list_sum, apt_list = SaveAptInfo('7', a_comp, list_sum)

    # 정렬
    #list_sum.sort(key=lambda x: (x[2], x[3], str(x[10])))
     #list_sum.sort(key=lambda x: (x[2], x[3]))
    return list_sum


# 그리드에 출력

st.header("조회 결과")

def search_data(con_search):
    # 입력한 조회 조건을 세션 상태의 히스토리에 추가
    if con_search and con_search not in st.session_state['history']:
        st.session_state['history'].append(con_search)

    list_sum_result = find_info(con_search)

    #columns =  ["아파트명","매매/전세", "공급", "공급평", "전용", "전용평", "동", "층", "향", "금액", "평당가", "상세내용", "공인중개사"]
    columns = ["wefe", "fewf", "fwf", "dfe", "ccd", "edq", "sdfg", "grgh", "vrrf", "sdfwww", "zzcv", "vdv", "aaaaa"]

    # 조회된 데이터를 그리드로 표시
    if list_sum_result:
        df = pd.DataFrame(list_sum_result, columns=columns)

        # 데이터 정렬
        sorted_df = sort_dataframe(df, st.session_state['sort_column'])

        # 정렬된 데이터 표시
        st.write(sorted_df)

        # HTML로 변환 및 스타일 적용
        #html = df.to_html(index=False, justify='center', border=0)
        # HTML 테이블을 Streamlit에 표시
        #st.markdown(html, unsafe_allow_html=True)


    else:
        st.write("조회 결과가 없습니다.")


if submit_button:
    search_data(condition)