import streamlit as st
import pandas as pd
from datetime import datetime
import random

from tourism_api import get_festivals
from festival_utils import (
    filter_festivals,
    get_festival_status,
    get_region_list,
)


# =========================================================
# 페이지 설정
# =========================================================

st.set_page_config(
    page_title="전국 축제 탐험대",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>
    .main {
        background-color: #f8f9fa;
    }

    .festival-card {
        padding: 20px;
        border-radius: 15px;
        background-color: white;
        box-shadow: 0 3px 12px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        border: 1px solid #eeeeee;
    }

    .festival-title {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .festival-info {
        color: #555555;
        font-size: 15px;
        line-height: 1.7;
    }

    .status-ing {
        color: #e53935;
        font-weight: bold;
    }

    .status-before {
        color: #1976d2;
        font-weight: bold;
    }

    .status-after {
        color: #777777;
        font-weight: bold;
    }

    .big-number {
        font-size: 32px;
        font-weight: 700;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 제목
# =========================================================

st.title("🎉 전국 축제 탐험대")
st.markdown(
    """
    **한국관광공사 관광정보 API**를 활용해  
    전국에서 열리는 다양한 축제를 찾아보세요! 🇰🇷
    
    오늘 갈 수 있는 축제를 찾거나, 지역별 축제를 탐색하고,
    랜덤 축제 추천도 받아볼 수 있습니다. 🎲
    """
)


# =========================================================
# 세션 상태
# =========================================================

if "random_festival" not in st.session_state:
    st.session_state.random_festival = None


# =========================================================
# 사이드바
# =========================================================

with st.sidebar:

    st.header("🔍 축제 검색")

    st.markdown("### API 설정")

    # Streamlit Cloud Secrets에 API_KEY가 있으면 자동 사용
    secret_api_key = ""

    try:
        secret_api_key = st.secrets.get("TOUR_API_KEY", "")
    except Exception:
        secret_api_key = ""

    if secret_api_key:
        api_key = secret_api_key

        st.success("✅ Streamlit Secrets의 API 키를 사용합니다.")

    else:
        api_key = st.text_input(
            "한국관광공사 API 키",
            type="password",
            help="API 키를 입력하세요.",
        )

        st.caption(
            "Streamlit Cloud에서는 Secrets에 "
            "TOUR_API_KEY를 등록하면 자동으로 사용할 수 있습니다."
        )

    st.divider()

    # 지역 선택
    region = st.selectbox(
        "📍 지역",
        [
            "전체",
            "서울",
            "인천",
            "대전",
            "대구",
            "광주",
            "부산",
            "울산",
            "세종",
            "경기",
            "강원",
            "충북",
            "충남",
            "전북",
            "전남",
            "경북",
            "경남",
            "제주",
        ],
    )

    # 검색어
    search_keyword = st.text_input(
        "🔎 축제명 검색",
        placeholder="예: 벚꽃, 불꽃, 음악",
    )

    # 상태
    status_filter = st.selectbox(
        "📅 축제 상태",
        [
            "전체",
            "진행 중",
            "개최 예정",
            "종료",
        ],
    )

    # 정렬
    sort_option = st.selectbox(
        "↕️ 정렬",
        [
            "최신 축제부터",
            "가까운 축제부터",
            "축제명 가나다순",
        ],
    )

    # 축제 개수
    num_items = st.slider(
        "📊 불러올 축제 개수",
        min_value=10,
        max_value=100,
        value=30,
        step=10,
    )

    st.divider()

    load_button = st.button(
        "🎊 축제 불러오기",
        use_container_width=True,
        type="primary",
    )


# =========================================================
# API 키 확인
# =========================================================

if not api_key:

    st.info(
        "👈 먼저 왼쪽 사이드바에 한국관광공사 API 키를 입력해주세요."
    )

    st.markdown(
        """
        ### 💡 사용 방법

        1. 한국관광공사 관광정보 API 키를 준비합니다.
        2. 왼쪽 사이드바에 API 키를 입력합니다.
        3. 지역과 검색 조건을 선택합니다.
        4. **🎊 축제 불러오기** 버튼을 클릭합니다.
        5. 마음에 드는 축제를 찾아보세요!

        ### 🎲 재미있는 기능

        - 오늘 갈 수 있는 축제 찾기
        - 랜덤 축제 추천
        - 지역별 축제 탐색
        - 축제 지도 보기
        - 축제 데이터 CSV 다운로드
        """
    )

    st.stop()


# =========================================================
# 축제 데이터 불러오기
# =========================================================

if load_button:

    with st.spinner("🎉 전국의 축제 정보를 불러오는 중입니다..."):

        try:

            df = get_festivals(
                api_key=api_key,
                num_rows=num_items,
            )

            if df is None or df.empty:

                st.warning(
                    "축제 데이터를 찾지 못했습니다. "
                    "API 키 또는 API 설정을 확인해주세요."
                )

                st.stop()

            st.session_state.festivals = df

            st.success(
                f"🎊 총 {len(df)}개의 축제 정보를 불러왔습니다!"
            )

        except Exception as e:

            st.error(
                "축제 정보를 불러오는 중 오류가 발생했습니다."
            )

            st.exception(e)

            st.stop()


# =========================================================
# 데이터 존재 여부 확인
# =========================================================

if "festivals" not in st.session_state:

    st.info(
        "👈 검색 조건을 선택한 후 "
        "**🎊 축제 불러오기** 버튼을 눌러주세요."
    )

    st.stop()


df = st.session_state.festivals.copy()


# =========================================================
# 데이터 필터링
# =========================================================

filtered_df = filter_festivals(
    df=df,
    region=region,
    keyword=search_keyword,
    status=status_filter,
)


# =========================================================
# 정렬
# =========================================================

if sort_option == "축제명 가나다순":

    if "title" in filtered_df.columns:
        filtered_df = filtered_df.sort_values(
            by="title",
            ascending=True,
        )

elif sort_option == "가까운 축제부터":

    if "start_date" in filtered_df.columns:
        filtered_df = filtered_df.sort_values(
            by="start_date",
            ascending=True,
        )

else:

    if "start_date" in filtered_df.columns:
        filtered_df = filtered_df.sort_values(
            by="start_date",
            ascending=False,
        )


# =========================================================
# 통계
# =========================================================

st.subheader("📊 축제 현황")

col1, col2, col3, col4 = st.columns(4)

today = pd.Timestamp.today().normalize()


def calculate_status(row):

    try:

        start = pd.to_datetime(
            row.get("start_date"),
            errors="coerce",
        )

        end = pd.to_datetime(
            row.get("end_date"),
            errors="coerce",
        )

        if pd.isna(start) or pd.isna(end):
            return "정보 없음"

        if start <= today <= end:
            return "진행 중"

        elif today < start:
            return "개최 예정"

        else:
            return "종료"

    except Exception:

        return "정보 없음"


status_series = filtered_df.apply(
    calculate_status,
    axis=1,
)

ongoing_count = (status_series == "진행 중").sum()

upcoming_count = (status_series == "개최 예정").sum()

ended_count = (status_series == "종료").sum()


with col1:
    st.metric(
        "🎉 검색된 축제",
        f"{len(filtered_df):,}개",
    )

with col2:
    st.metric(
        "🔥 진행 중",
        f"{ongoing_count:,}개",
    )

with col3:
    st.metric(
        "📅 개최 예정",
        f"{upcoming_count:,}개",
    )

with col4:
    st.metric(
        "🏁 종료",
        f"{ended_count:,}개",
    )


# =========================================================
# 재미있는 기능 탭
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🎉 축제 목록",
        "🎲 랜덤 축제 추천",
        "🗺️ 축제 지도",
        "📥 데이터 다운로드",
    ]
)


# =========================================================
# TAB 1 : 축제 목록
# =========================================================

with tab1:

    st.subheader(
        f"🎊 축제 목록 ({len(filtered_df)}개)"
    )

    if filtered_df.empty:

        st.warning(
            "검색 조건에 맞는 축제가 없습니다."
        )

    else:

        for _, festival in filtered_df.iterrows():

            title = festival.get(
                "title",
                "축제명 없음",
            )

            image_url = festival.get(
                "image",
                "",
            )

            address = festival.get(
                "address",
                "주소 정보 없음",
            )

            start_date = festival.get(
                "start_date",
                "",
            )

            end_date = festival.get(
                "end_date",
                "",
            )

            homepage = festival.get(
                "homepage",
                "",
            )

            latitude = festival.get(
                "latitude",
                None,
            )

            longitude = festival.get(
                "longitude",
                None,
            )

            status = calculate_status(
                festival
            )

            if status == "진행 중":
                status_html = (
                    '<span class="status-ing">'
                    "🔥 진행 중"
                    "</span>"
                )

            elif status == "개최 예정":
                status_html = (
                    '<span class="status-before">'
                    "📅 개최 예정"
                    "</span>"
                )

            elif status == "종료":
                status_html = (
                    '<span class="status-after">'
                    "🏁 종료"
                    "</span>"
                )

            else:
                status_html = "ℹ️ 정보 없음"

            col_image, col_info = st.columns(
                [1, 2]
            )

            with col_image:

                if (
                    image_url
                    and str(image_url) != "nan"
                ):

                    try:
                        st.image(
                            image_url,
                            use_container_width=True,
                        )

                    except Exception:

                        st.info(
                            "이미지를 불러올 수 없습니다."
                        )

                else:

                    st.info(
                        "🖼️ 이미지 없음"
                    )

            with col_info:

                st.markdown(
                    f"""
                    <div class="festival-card">

                    <div class="festival-title">
                    {title}
                    </div>

                    <div class="festival-info">

                    {status_html}

                    <br>

                    📅 {start_date} ~ {end_date}

                    <br>

                    📍 {address}

                    </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if homepage:

                    st.link_button(
                        "🔗 축제 상세 페이지",
                        homepage,
                    )

            st.divider()


# =========================================================
# TAB 2 : 랜덤 축제 추천
# =========================================================

with tab2:

    st.subheader(
        "🎲 오늘의 랜덤 축제 뽑기"
    )

    st.markdown(
        """
        어디로 갈지 모르겠다면  
        **랜덤 축제 뽑기**로 새로운 여행지를 발견해보세요!
        """
    )

    if filtered_df.empty:

        st.warning(
            "랜덤 추천할 축제가 없습니다."
        )

    else:

        if st.button(
            "🎲 랜덤 축제 뽑기!",
            type="primary",
        ):

            random_index = random.randint(
                0,
                len(filtered_df) - 1,
            )

            st.session_state.random_festival = (
                filtered_df.iloc[random_index]
            )

        if (
            st.session_state.random_festival
            is not None
        ):

            festival = (
                st.session_state.random_festival
            )

            title = festival.get(
                "title",
                "축제명 없음",
            )

            image = festival.get(
                "image",
                "",
            )

            address = festival.get(
                "address",
                "",
            )

            start_date = festival.get(
                "start_date",
                "",
            )

            end_date = festival.get(
                "end_date",
                "",
            )

            homepage = festival.get(
                "homepage",
                "",
            )

            st.success(
                "🎉 오늘의 축제가 결정되었습니다!"
            )

            if image:

                st.image(
                    image,
                    width=600,
                )

            st.markdown(
                f"# 🎊 {title}"
            )

            st.write(
                f"📅 **기간:** "
                f"{start_date} ~ {end_date}"
            )

            st.write(
                f"📍 **장소:** "
                f"{address}"
            )

            if homepage:

                st.link_button(
                    "🔗 축제 상세정보 보기",
                    homepage,
                )


# =========================================================
# TAB 3 : 지도
# =========================================================

with tab3:

    st.subheader(
        "🗺️ 전국 축제 지도"
    )

    map_df = filtered_df.copy()

    if (
        "latitude" in map_df.columns
        and "longitude" in map_df.columns
    ):

        map_df["latitude"] = pd.to_numeric(
            map_df["latitude"],
            errors="coerce",
        )

        map_df["longitude"] = pd.to_numeric(
            map_df["longitude"],
            errors="coerce",
        )

        map_df = map_df.dropna(
            subset=[
                "latitude",
                "longitude",
            ]
        )

        if not map_df.empty:

            st.map(
                map_df[
                    [
                        "latitude",
                        "longitude",
                    ]
                ]
            )

            st.caption(
                f"📍 총 {len(map_df)}개의 "
                "축제가 지도에 표시되었습니다."
            )

        else:

            st.warning(
                "지도에 표시할 위치 정보가 없습니다."
            )

    else:

        st.warning(
            "축제 위치 정보가 제공되지 않았습니다."
        )


# =========================================================
# TAB 4 : CSV 다운로드
# =========================================================

with tab4:

    st.subheader(
        "📥 축제 데이터 다운로드"
    )

    st.write(
        "현재 검색 결과를 CSV 파일로 다운로드할 수 있습니다."
    )

    csv_data = filtered_df.to_csv(
        index=False,
        encoding="utf-8-sig",
    )

    st.download_button(
        label="📥 CSV 다운로드",
        data=csv_data,
        file_name=(
            "korea_festival_data.csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )


# =========================================================
# 푸터
# =========================================================

st.divider()

st.caption(
    "본 서비스는 한국관광공사 관광정보 API를 활용하여 "
    "축제 정보를 제공합니다."
)

st.caption(
    "※ 실제 축제 일정 및 운영 여부는 "
    "축제 공식 홈페이지에서 최종 확인해주세요."
)

# tourism_api.py

import requests
import pandas as pd
import streamlit as st
from datetime import datetime
from urllib.parse import urlencode


# =========================================================
# 한국관광공사 관광정보 API 설정
# =========================================================

API_BASE_URL = (
    "https://apis.data.go.kr/B551011/KorService2"
)

FESTIVAL_ENDPOINT = (
    f"{API_BASE_URL}/searchFestival2"
)


# =========================================================
# API 호출 함수
# =========================================================

@st.cache_data(ttl=3600, show_spinner=False)
def get_festivals(
    api_key: str,
    num_rows: int = 30,
):
    """
    한국관광공사 관광정보 API에서
    축제/행사 정보를 가져옵니다.

    app.py에서 다음과 같이 호출합니다.

        df = get_festivals(
            api_key=api_key,
            num_rows=num_items,
        )

    반환값:
        pandas.DataFrame
    """

    if not api_key:
        raise ValueError(
            "한국관광공사 API 인증키가 없습니다."
        )

    # -----------------------------------------------------
    # 오늘 날짜
    # -----------------------------------------------------

    today = datetime.now().strftime("%Y%m%d")

    # -----------------------------------------------------
    # API 요청 파라미터
    # -----------------------------------------------------

    params = {
        "serviceKey": api_key,
        "numOfRows": num_rows,
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "FestivalExplorer",
        "_type": "json",

        # 행사/축제 카테고리
        "eventStartDate": today,

        # 최신순 정렬
        "arrange": "A",
    }

    # -----------------------------------------------------
    # API 호출
    # -----------------------------------------------------

    try:

        response = requests.get(
            FESTIVAL_ENDPOINT,
            params=params,
            timeout=30,
        )

    except requests.exceptions.Timeout:

        raise RuntimeError(
            "한국관광공사 API 요청 시간이 초과되었습니다. "
            "잠시 후 다시 시도해주세요."
        )

    except requests.exceptions.RequestException as e:

        raise RuntimeError(
            f"한국관광공사 API 연결에 실패했습니다: {e}"
        )

    # -----------------------------------------------------
    # HTTP 상태 코드 확인
    # -----------------------------------------------------

    if response.status_code != 200:

        raise RuntimeError(
            f"한국관광공사 API 오류 "
            f"(HTTP {response.status_code})"
        )

    # -----------------------------------------------------
    # JSON 변환
    # -----------------------------------------------------

    try:

        data = response.json()

    except ValueError:

        raise RuntimeError(
            "API 응답을 JSON 형식으로 변환할 수 없습니다."
        )

    # -----------------------------------------------------
    # 응답 구조 확인
    # -----------------------------------------------------

    try:

        response_body = data[
            "response"
        ]

        header = response_body.get(
            "header",
            {},
        )

        result_code = str(
            header.get(
                "resultCode",
                "",
            )
        )

        result_msg = header.get(
            "resultMsg",
            "",
        )

        # API 오류 코드 확인
        if result_code not in [
            "0000",
            "0",
            "",
        ]:

            raise RuntimeError(
                "한국관광공사 API 오류: "
                f"{result_code} - "
                f"{result_msg}"
            )

        body = response_body.get(
            "body",
            {},
        )

        items = body.get(
            "items",
            {},
        )

        item_list = items.get(
            "item",
            [],
        )

    except KeyError:

        raise RuntimeError(
            "한국관광공사 API 응답 형식이 "
            "예상과 다릅니다."
        )

    # -----------------------------------------------------
    # 데이터가 없는 경우
    # -----------------------------------------------------

    if not item_list:

        return pd.DataFrame(
            columns=[
                "title",
                "image",
                "address",
                "start_date",
                "end_date",
                "homepage",
                "latitude",
                "longitude",
            ]
        )

    # -----------------------------------------------------
    # DataFrame 생성
    # -----------------------------------------------------

    df = pd.DataFrame(
        item_list
    )

    # =====================================================
    # API 원본 컬럼을 앱에서 사용하는 컬럼으로 변환
    # =====================================================

    column_mapping = {

        # 축제명
        "title": "title",

        # 대표 이미지
        "firstimage": "image",

        # 이미지가 없는 경우 대체 이미지
        "firstimage2": "image2",

        # 주소
        "addr1": "address",

        # 상세 주소
        "addr2": "address_detail",

        # 행사 시작일
        "eventstartdate": "start_date",

        # 행사 종료일
        "eventenddate": "end_date",

        # 홈페이지
        "homepage": "homepage",

        # 위도
        "mapy": "latitude",

        # 경도
        "mapx": "longitude",

        # 지역 코드
        "areacode": "area_code",

        # 시군구 코드
        "sigungucode": "sigungu_code",

        # 행사 내용
        "overview": "overview",

        # 수정일
        "modifiedtime": "modified_time",

        # 콘텐츠 ID
        "contentid": "content_id",

        # 콘텐츠 타입
        "contenttypeid": "content_type_id",
    }

    # 실제 존재하는 컬럼만 변환
    rename_dict = {
        old: new
        for old, new in column_mapping.items()
        if old in df.columns
    }

    df = df.rename(
        columns=rename_dict
    )

    # =====================================================
    # 필수 컬럼이 없을 경우 생성
    # app.py가 오류 없이 작동하도록 보장
    # =====================================================

    required_columns = [

        "title",
        "image",
        "address",
        "start_date",
        "end_date",
        "homepage",
        "latitude",
        "longitude",

    ]

    for column in required_columns:

        if column not in df.columns:

            df[column] = ""


    # =====================================================
    # 이미지 처리
    # =====================================================

    # 대표 이미지가 없는 경우 두 번째 이미지 사용
    if "image2" in df.columns:

        df["image"] = (
            df["image"]
            .fillna("")
            .astype(str)
        )

        df["image2"] = (
            df["image2"]
            .fillna("")
            .astype(str)
        )

        df["image"] = df.apply(
            lambda row:
                row["image"]
                if row["image"]
                and row["image"] != "nan"
                else row["image2"],
            axis=1,
        )


    # =====================================================
    # 홈페이지 URL 처리
    # =====================================================

    df["homepage"] = (
        df["homepage"]
        .fillna("")
        .astype(str)
    )

    # HTML 태그가 포함된 홈페이지 데이터 처리
    df["homepage"] = (
        df["homepage"]
        .str.replace(
            "<br>",
            "",
            regex=False,
        )
        .str.replace(
            "<br/>",
            "",
            regex=False,
        )
        .str.replace(
            "&amp;",
            "&",
            regex=False,
        )
    )


    # =====================================================
    # 날짜 처리
    # =====================================================

    df["start_date"] = (
        pd.to_datetime(
            df["start_date"],
            format="%Y%m%d",
            errors="coerce",
        )
        .dt.strftime("%Y-%m-%d")
    )

    df["end_date"] = (
        pd.to_datetime(
            df["end_date"],
            format="%Y%m%d",
            errors="coerce",
        )
        .dt.strftime("%Y-%m-%d")
    )


    # =====================================================
    # 위도 / 경도 숫자 변환
    # =====================================================

    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce",
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce",
    )


    # =====================================================
    # 문자열 데이터 정리
    # =====================================================

    string_columns = [

        "title",
        "image",
        "address",
        "homepage",

    ]

    for column in string_columns:

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )


    # =====================================================
    # 축제명 없는 데이터 제거
    # =====================================================

    df = df[
        df["title"].str.strip() != ""
    ].copy()


    # =====================================================
    # 중복 축제 제거
    # =====================================================

    if "content_id" in df.columns:

        df = df.drop_duplicates(
            subset=["content_id"],
            keep="first",
        )

    else:

        df = df.drop_duplicates(
            subset=[
                "title",
                "start_date",
            ],
            keep="first",
        )


    # =====================================================
    # 날짜 기준 정렬
    # =====================================================

    df["_sort_date"] = pd.to_datetime(
        df["start_date"],
        errors="coerce",
    )

    df = df.sort_values(
        by="_sort_date",
        ascending=True,
        na_position="last",
    )

    df = df.drop(
        columns=["_sort_date"],
        errors="ignore",
    )


    # =====================================================
    # 인덱스 초기화
    # =====================================================

    df = df.reset_index(
        drop=True
    )


    # =====================================================
    # 최종 반환
    # =====================================================

    return df

# festival_utils.py

import pandas as pd
from datetime import datetime


# =========================================================
# 지역 코드 매핑
# 한국관광공사 관광정보 API 지역 코드 기준
# =========================================================

REGION_CODE_MAP = {
    "서울": "1",
    "인천": "2",
    "대전": "3",
    "대구": "4",
    "광주": "5",
    "부산": "6",
    "울산": "7",
    "세종": "8",
    "경기": "31",
    "강원": "32",
    "충북": "33",
    "충남": "34",
    "전북": "37",
    "전남": "38",
    "경북": "35",
    "경남": "36",
    "제주": "39",
}


# =========================================================
# 지역 목록 반환
# app.py에서 사용
# =========================================================

def get_region_list():
    """
    지역 선택 목록을 반환합니다.
    """

    return [
        "전체",
        "서울",
        "인천",
        "대전",
        "대구",
        "광주",
        "부산",
        "울산",
        "세종",
        "경기",
        "강원",
        "충북",
        "충남",
        "전북",
        "전남",
        "경북",
        "경남",
        "제주",
    ]


# =========================================================
# 날짜 변환 함수
# =========================================================

def convert_to_datetime(value):
    """
    다양한 날짜 형식을 pandas Timestamp로 변환합니다.
    """

    if value is None:
        return pd.NaT

    if pd.isna(value):
        return pd.NaT

    value = str(value).strip()

    if not value:
        return pd.NaT

    # YYYYMMDD
    if len(value) == 8 and value.isdigit():

        try:
            return pd.to_datetime(
                value,
                format="%Y%m%d",
                errors="coerce",
            )

        except Exception:
            pass

    # YYYY-MM-DD
    try:

        return pd.to_datetime(
            value,
            errors="coerce",
        )

    except Exception:

        return pd.NaT


# =========================================================
# 축제 상태 판별
# =========================================================

def get_festival_status(
    start_date,
    end_date,
):
    """
    축제 시작일과 종료일을 기준으로
    현재 상태를 반환합니다.

    반환값:
        진행 중
        개최 예정
        종료
        정보 없음
    """

    start = convert_to_datetime(
        start_date
    )

    end = convert_to_datetime(
        end_date
    )

    today = pd.Timestamp.today().normalize()

    # 날짜 정보가 없는 경우
    if pd.isna(start) or pd.isna(end):

        return "정보 없음"

    # 현재 진행 중
    if start <= today <= end:

        return "진행 중"

    # 아직 시작하지 않음
    elif today < start:

        return "개최 예정"

    # 이미 종료
    else:

        return "종료"


# =========================================================
# 축제 필터링
# =========================================================

def filter_festivals(
    df,
    region="전체",
    keyword="",
    status="전체",
):
    """
    축제 데이터를 지역, 검색어, 상태 기준으로 필터링합니다.

    app.py에서 다음과 같이 사용합니다.

        filtered_df = filter_festivals(
            df=df,
            region=region,
            keyword=search_keyword,
            status=status_filter,
        )
    """

    # 원본 데이터 보호
    filtered_df = df.copy()

    # -----------------------------------------------------
    # 데이터가 없는 경우
    # -----------------------------------------------------

    if filtered_df.empty:

        return filtered_df

    # -----------------------------------------------------
    # 필수 컬럼 보장
    # -----------------------------------------------------

    required_columns = [
        "title",
        "address",
        "start_date",
        "end_date",
    ]

    for column in required_columns:

        if column not in filtered_df.columns:

            filtered_df[column] = ""


    # =====================================================
    # 지역 필터
    # =====================================================

    if (
        region
        and region != "전체"
    ):

        # 지역명을 주소에서 검색
        #
        # 예:
        # 서울특별시 → 서울
        # 부산광역시 → 부산
        # 경기도 → 경기
        #
        # API의 areacode가 존재한다면
        # 코드 기준 필터도 함께 적용합니다.

        region_code = REGION_CODE_MAP.get(
            region
        )

        address_series = (
            filtered_df["address"]
            .fillna("")
            .astype(str)
        )

        # 지역명 패턴
        region_patterns = {
            "서울": [
                "서울",
            ],
            "인천": [
                "인천",
            ],
            "대전": [
                "대전",
            ],
            "대구": [
                "대구",
            ],
            "광주": [
                "광주",
            ],
            "부산": [
                "부산",
            ],
            "울산": [
                "울산",
            ],
            "세종": [
                "세종",
            ],
            "경기": [
                "경기",
            ],
            "강원": [
                "강원",
            ],
            "충북": [
                "충북",
                "충청북도",
            ],
            "충남": [
                "충남",
                "충청남도",
            ],
            "전북": [
                "전북",
                "전라북도",
            ],
            "전남": [
                "전남",
                "전라남도",
            ],
            "경북": [
                "경북",
                "경상북도",
            ],
            "경남": [
                "경남",
                "경상남도",
            ],
            "제주": [
                "제주",
            ],
        }

        patterns = region_patterns.get(
            region,
            [region],
        )

        # 주소에 지역명이 포함되어 있는지 확인
        address_mask = pd.Series(
            False,
            index=filtered_df.index,
        )

        for pattern in patterns:

            address_mask = (
                address_mask
                | address_series.str.contains(
                    pattern,
                    case=False,
                    na=False,
                )
            )

        # 지역 코드도 확인
        code_mask = pd.Series(
            False,
            index=filtered_df.index,
        )

        if (
            region_code
            and "area_code"
            in filtered_df.columns
        ):

            code_mask = (
                filtered_df[
                    "area_code"
                ]
                .fillna("")
                .astype(str)
                .str.strip()
                == str(region_code)
            )

        # 주소 또는 지역 코드가 일치하면 포함
        filtered_df = filtered_df[
            address_mask | code_mask
        ].copy()


    # =====================================================
    # 축제명 검색
    # =====================================================

    if keyword:

        keyword = str(
            keyword
        ).strip()

        if keyword:

            title_series = (
                filtered_df["title"]
                .fillna("")
                .astype(str)
            )

            address_series = (
                filtered_df["address"]
                .fillna("")
                .astype(str)
            )

            overview_series = pd.Series(
                "",
                index=filtered_df.index,
            )

            if "overview" in filtered_df.columns:

                overview_series = (
                    filtered_df[
                        "overview"
                    ]
                    .fillna("")
                    .astype(str)
                )

            # 축제명 + 주소 + 설명 검색
            search_mask = (

                title_series.str.contains(
                    keyword,
                    case=False,
                    na=False,
                )

                |

                address_series.str.contains(
                    keyword,
                    case=False,
                    na=False,
                )

                |

                overview_series.str.contains(
                    keyword,
                    case=False,
                    na=False,
                )

            )

            filtered_df = filtered_df[
                search_mask
            ].copy()


    # =====================================================
    # 축제 상태 필터
    # =====================================================

    if (
        status
        and status != "전체"
    ):

        status_mask = filtered_df.apply(

            lambda row:
                get_festival_status(
                    row.get(
                        "start_date"
                    ),
                    row.get(
                        "end_date"
                    ),
                )
                == status,

            axis=1,
        )

        filtered_df = filtered_df[
            status_mask
        ].copy()


    # =====================================================
    # 인덱스 초기화
    # =====================================================

    filtered_df = filtered_df.reset_index(
        drop=True
    )


    return filtered_df


# =========================================================
# 축제 상태 컬럼 추가
# =========================================================

def add_status_column(
    df,
):
    """
    DataFrame에 축제 상태 컬럼을 추가합니다.
    """

    result = df.copy()

    if result.empty:

        return result

    result["status"] = result.apply(

        lambda row:
            get_festival_status(
                row.get(
                    "start_date"
                ),
                row.get(
                    "end_date"
                ),
            ),

        axis=1,
    )

    return result


# =========================================================
# 진행 중인 축제만 반환
# =========================================================

def get_ongoing_festivals(
    df,
):
    """
    현재 진행 중인 축제만 반환합니다.
    """

    if df is None or df.empty:

        return pd.DataFrame(
            columns=df.columns
            if df is not None
            else []
        )

    result = filter_festivals(
        df=df,
        status="진행 중",
    )

    return result


# =========================================================
# 개최 예정 축제만 반환
# =========================================================

def get_upcoming_festivals(
    df,
):
    """
    앞으로 개최될 축제만 반환합니다.
    """

    if df is None or df.empty:

        return pd.DataFrame(
            columns=df.columns
            if df is not None
            else []
        )

    result = filter_festivals(
        df=df,
        status="개최 예정",
    )

    return result


# =========================================================
# 축제 종료 여부 확인
# =========================================================

def is_festival_finished(
    start_date,
    end_date,
):
    """
    축제가 종료되었는지 확인합니다.

    반환값:
        True
        False
    """

    status = get_festival_status(
        start_date,
        end_date,
    )

    return status == "종료"


# =========================================================
# 축제 진행 여부 확인
# =========================================================

def is_festival_ongoing(
    start_date,
    end_date,
):
    """
    축제가 현재 진행 중인지 확인합니다.

    반환값:
        True
        False
    """

    status = get_festival_status(
        start_date,
        end_date,
    )

    return status == "진행 중"


# =========================================================
# 축제 개최 예정 여부 확인
# =========================================================

def is_festival_upcoming(
    start_date,
    end_date,
):
    """
    축제가 개최 예정인지 확인합니다.

    반환값:
        True
        False
    """

    status = get_festival_status(
        start_date,
        end_date,
    )

    return status == "개최 예정"


# =========================================================
# 축제까지 남은 날짜 계산
# =========================================================

def get_days_until_festival(
    start_date,
):
    """
    축제 시작일까지 남은 날짜를 계산합니다.

    반환값:
        정수
        None
    """

    start = convert_to_datetime(
        start_date
    )

    if pd.isna(start):

        return None

    today = pd.Timestamp.today().normalize()

    difference = (
        start - today
    ).days

    return difference


# =========================================================
# 축제 기간 계산
# =========================================================

def get_festival_duration(
    start_date,
    end_date,
):
    """
    축제 기간을 일수로 계산합니다.
    """

    start = convert_to_datetime(
        start_date
    )

    end = convert_to_datetime(
        end_date
    )

    if (
        pd.isna(start)
        or pd.isna(end)
    ):

        return None

    duration = (
        end - start
    ).days + 1

    return max(
        duration,
        1,
    )


# =========================================================
# 축제 데이터 요약
# =========================================================

def get_festival_statistics(
    df,
):
    """
    축제 데이터의 통계 정보를 반환합니다.

    반환값:
        dict
    """

    if df is None or df.empty:

        return {
            "total": 0,
            "ongoing": 0,
            "upcoming": 0,
            "finished": 0,
            "unknown": 0,
        }

    status_list = []

    for _, row in df.iterrows():

        status = get_festival_status(
            row.get(
                "start_date"
            ),
            row.get(
                "end_date"
            ),
        )

        status_list.append(
            status
        )

    status_series = pd.Series(
        status_list
    )

    return {
        "total": len(df),

        "ongoing": int(
            (
                status_series
                == "진행 중"
            ).sum()
        ),

        "upcoming": int(
            (
                status_series
                == "개최 예정"
            ).sum()
        ),

        "finished": int(
            (
                status_series
                == "종료"
            ).sum()
        ),

        "unknown": int(
            (
                status_series
                == "정보 없음"
            ).sum()
        ),
    }
