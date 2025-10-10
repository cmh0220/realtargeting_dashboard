# apt4sale 최종버전 백업  2024.11.13

import re
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
    st.header("검색창!")
    # 여기에 조회 조건 입력 필드 추가
    condition = st.text_input("아파트명을 입력하세요!!", key="condition")
    # 조회 버튼
    submit_button = st.button("조회!!")

    # 히스토리 섹션
    show_history()


# 컬럼 정렬 함수
def sort_dataframe(df, column):
    if column:
        return df.sort_values(by=[column], ascending=st.session_state['ascending'])
    return df


def get_token_for_authorization():
    # ': 'Bearer
    headers = {
        'Host': 'new.land.naver.com',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Referer': 'https://land.naver.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    try:
        url = f"https://new.land.naver.com/complexes?ms=37.3375315,127.1065792,15&a=APT&e=RETAIL"

        r = requests.get(url, headers=headers)
        if (r is None) or (r.status_code != 200):
            print(f"Failed to get token for authorization!\nurl: {url}")
            return None

        retval = r.content.decode('utf-8')

        with open("./token.html", "w", encoding="utf-8") as f:
            f.write(retval)

        findval = re.findall('"token":"(.+?)"', retval)
        if type(findval) != list:
            print(f"Pattern not found to get token for authorization!\nurl: {url}")
            return None

        if len(findval[0]) < 100:
            print(f"Pattern not found to get token for authorization!\nurl: {url}")
            return None

        print(f"Token for authorization: {findval[0]}")
        return 'Bearer ' + findval[0]
    except Exception as e:
        print(f"An error occurred while getting token for authorization: {e}")
        return None


def SaveAptInfo(p_page, p_comp, p_list_sum):
    down_url = 'https://new.land.naver.com/api/articles/complex/' + p_comp + '?realEstateType=APT&tradeType=A1%3AB1&tag=%3A%3A%3A%3A%3A%3A%3A%3A&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=900000000&areaMin=0&areaMax=900000000&oldBuildYears&recentlyBuildYears&minHouseHoldCount&maxHouseHoldCount&showArticle=false&sameAddressGroup=true&minMaintenanceCost&maxMaintenanceCost&priceType=RETAIL&directions=&page=' + p_page + '&complexNo=' + p_comp + '&buildingNos=&areaNos=&type=list&order=rank'

    r = requests.get(down_url, data={"sameAddressGroup": "true"}, headers={
        "Accept-Encoding": "gzip",
        "Host": "m.land.naver.com",
        "Referer": "https://new.land.naver.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        # "User-Agent": "Mozilla/5.0 (Phone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "authorization": get_token_for_authorization()
    })

    st.info("@@디버그1@@r.text : " + r.text)
    r.encoding = "utf-8"

    st.info("@@디버그2@@r.text : " + r.text)
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
                # [data['articleNo'],
                [data['articleName'], data['tradeTypeName'],
                 data['area1'], data['area2'],  #제곱미터
                 round(float(data['area1']) / 3.3), round(float(data['area2']) / 3.3),  # 평
                 data['buildingName'], data['floorInfo'], data['direction'], dowp_int,
                 round(dowp_int / round(float(data['area1']) / 3.3)),
                 '', data['realtorName']])
        else:

            # 금액 숫자로 변환
            dowp = str(data['dealOrWarrantPrc'])
            dowp_int = int(dowp.replace(',', '')) if dowp.find('억') == -1 else (int(dowp[:dowp.find('억')]) * 10000) + (
                0 if dowp.endswith('억') else int(dowp[dowp.find('억') + 1:].replace(',', '')))

            p_list_sum.append(
                # [data['articleNo'],
                [data['articleName'], data['tradeTypeName'],
                 data['area1'], data['area2'],  # 제곱미터
                 round(float(data['area1']) / 3.3), round(float(data['area2']) / 3.3),  # 평
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
    # list_sum.sort(key=lambda x: (x[2], x[3], str(x[10])))
    # list_sum.sort(key=lambda x: (x[2], x[3]))
    return list_sum


# 그리드에 출력
st.header("아파트 매물현황")
st.write("v1.0")

def search_data(con_search):
    # 입력한 조회 조건을 세션 상태의 히스토리에 추가
    if con_search and con_search not in st.session_state['history']:
        st.session_state['history'].append(con_search)

    list_sum_result = find_info(con_search)

    # columns = ["아파트명","매매/전세", "공급", "공급평", "전용", "전용평", "동", "층", "향", "금액", "평당가", "상세내용", "공인중개사"]
    columns = ["아파트명", "매/전", "공급", "전용", "공급평", "전용평", "동", "층", "향", "가격", "평당가", "상세내용", "중개사"]

    # 조회된 데이터를 그리드로 표시
    if list_sum_result:
        df = pd.DataFrame(list_sum_result, columns=columns)

        # 데이터 정렬
        sorted_df = sort_dataframe(df, st.session_state['sort_column'])

        # 정렬된 데이터 표시
        st.write(sorted_df)

        # 데이터 출처 표기
        st.write('출처 : 네이버 부동산 (https://land.naver.com')


    else:
        st.write("조회 결과가 없습니다.")


if submit_button:
    search_data(condition)