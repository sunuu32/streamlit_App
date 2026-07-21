import streamlit as st
import pandas as pd
import requests
import random
import re
from datetime import datetime

st.set_page_config(
    page_title="전국 축제 탐험대",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main { background-color: #f8f9fa; }
.festival-card {
    padding: 18px; border-radius: 15px; background: white;
    box-shadow: 0 3px 12px rgba(0,0,0,0.08);
    margin-bottom: 15px; border: 1px solid #eeeeee;
}
.small-muted { color:#777; font-size:14px; }
</style>
""", unsafe_allow_html=True)

API_URL = "https://apis.data.go.kr/B551011/KorService2/searchFestival2"

REGIONS = [
    "전체","서울","인천","대전","대구","광주","부산","울산","세종",
    "경기","강원","충북","충남","전북","전남","경북","경남","제주"
]

REGION_PATTERNS = {
    "서울":["서울"], "인천":["인천"], "대전":["대전"], "대구":["대구"],
    "광주":["광주"], "부산":["부산"], "울산":["울산"], "세종":["세종"],
    "경기":["경기"], "강원":["강원"], "충북":["충북","충청북도"],
    "충남":["충남","충청남도"], "전북":["전북","전라북도"],
    "전남":["전남","전라남도"], "경북":["경북","경상북도"],
    "경남":["경남","경상남도"], "제주":["제주"]
}

def clean_html(text):
    if text is None or pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", text).strip()

def parse_date(value):
    if value is None or pd.isna(value):
        return pd.NaT
    value = str(value).strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return pd.to_datetime(value, format=fmt)
        except Exception:
            pass
    return pd.to_datetime(value, errors="coerce")

def status_of(start, end):
    s, e = parse_date(start), parse_date(end)
    today = pd.Timestamp.today().normalize()
    if pd.isna(s) or pd.isna(e):
        return "정보 없음"
    if s <= today <= e:
        return "진행 중"
    if today < s:
        return "개최 예정"
    return "종료"

@st.cache_data(ttl=3600, show_spinner=False)
def get_festivals(api_key, num_rows=30):
    today = datetime.now().strftime("%Y%m%d")
    params = {
        "serviceKey": api_key.strip(),
        "numOfRows": int(num_rows),
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "FestivalExplorer",
        "_type": "json",
        "eventStartDate": today,
        "arrange": "A",
    }

    try:
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("API 요청 시간이 초과되었습니다.")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"한국관광공사 API 연결 실패: {e}")

    try:
        data = response.json()
    except Exception:
        raise RuntimeError("API 응답을 JSON으로 변환할 수 없습니다.")

    try:
        body = data["response"]["body"]
        header = data["response"].get("header", {})
        result_code = str(header.get("resultCode", "0000"))
        result_msg = header.get("resultMsg", "")
        if result_code not in ("0000", "0"):
            raise RuntimeError(f"API 오류: {result_code} - {result_msg}")

        items = body.get("items", {}).get("item", [])
        if isinstance(items, dict):
            items = [items]
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        raise RuntimeError("한국관광공사 API 응답 구조를 확인할 수 없습니다.")

    if not items:
        return pd.DataFrame(columns=[
            "title","image","address","start_date","end_date",
            "homepage","latitude","longitude","overview",
            "area_code","content_id"
        ])

    df = pd.DataFrame(items)

    def col(name):
        return df[name] if name in df.columns else pd.Series("", index=df.index)

    result = pd.DataFrame({
        "title": col("title").map(clean_html),
        "image": col("firstimage").fillna("").astype(str),
        "image2": col("firstimage2").fillna("").astype(str),
        "address": col("addr1").map(clean_html),
        "address_detail": col("addr2").map(clean_html),
        "start_date": col("eventstartdate"),
        "end_date": col("eventenddate"),
        "homepage": col("homepage").map(clean_html),
        "latitude": pd.to_numeric(col("mapy"), errors="coerce"),
        "longitude": pd.to_numeric(col("mapx"), errors="coerce"),
        "overview": col("overview").map(clean_html),
        "area_code": col("areacode").fillna("").astype(str),
        "content_id": col("contentid").fillna("").astype(str),
    })

    result["image"] = result["image"].where(
        result["image"].str.startswith("http", na=False),
        result["image2"]
    )

    result["start_date"] = pd.to_datetime(
        result["start_date"], format="%Y%m%d", errors="coerce"
    )
    result["end_date"] = pd.to_datetime(
        result["end_date"], format="%Y%m%d", errors="coerce"
    )

    result = result[result["title"].str.strip() != ""].copy()
    result = result.drop_duplicates(
        subset=["content_id"] if result["content_id"].str.strip().ne("").any()
        else ["title","start_date"]
    )
    result = result.sort_values("start_date", na_position="last").reset_index(drop=True)
    return result

def filter_data(df, region, keyword, status):
    result = df.copy()

    if region != "전체":
        patterns = REGION_PATTERNS.get(region, [region])
        addr = result["address"].fillna("").astype(str)
        mask = pd.Series(False, index=result.index)
        for p in patterns:
            mask |= addr.str.contains(p, na=False)
        result = result[mask].copy()

    if keyword.strip():
        keyword = keyword.strip()
        title = result["title"].fillna("").astype(str)
        addr = result["address"].fillna("").astype(str)
        overview = result["overview"].fillna("").astype(str)
        mask = (
            title.str.contains(keyword, case=False, na=False)
            | addr.str.contains(keyword, case=False, na=False)
            | overview.str.contains(keyword, case=False, na=False)
        )
        result = result[mask].copy()

    if status != "전체":
        result = result[
            result.apply(
                lambda r: status_of(r["start_date"], r["end_date"]) == status,
                axis=1
            )
        ].copy()

    return result.reset_index(drop=True)

def format_date(value):
    if pd.isna(value):
        return "날짜 정보 없음"
    return pd.Timestamp(value).strftime("%Y-%m-%d")

def safe_url(value):
    value = str(value).strip()
    if value and value.startswith(("http://", "https://")):
        return value
    return ""

st.title("🎉 전국 축제 탐험대")
st.markdown(
    "한국관광공사 관광정보 API로 전국 축제를 찾아보고, "
    "오늘 갈 축제를 랜덤으로 추천받아 보세요! 🇰🇷"
)

if "festivals" not in st.session_state:
    st.session_state.festivals = None
if "random_festival" not in st.session_state:
    st.session_state.random_festival = None

with st.sidebar:
    st.header("🔍 축제 검색")

    try:
        secret_key = st.secrets.get("TOUR_API_KEY", "")
    except Exception:
        secret_key = ""

    if secret_key:
        api_key = secret_key
        st.success("✅ Streamlit Secrets API 키 사용 중")
    else:
        api_key = st.text_input(
            "한국관광공사 API 키",
            type="password",
            help="Streamlit Cloud Secrets에 TOUR_API_KEY를 등록하면 자동 입력됩니다."
        )

    st.divider()

    region = st.selectbox("📍 지역", REGIONS)
    keyword = st.text_input("🔎 축제명·장소 검색", placeholder="예: 벚꽃, 불꽃, 음악")
    status = st.selectbox("📅 상태", ["전체", "진행 중", "개최 예정", "종료"])
    sort_option = st.selectbox(
        "↕️ 정렬",
        ["가까운 축제부터", "최신 축제부터", "축제명 가나다순"]
    )
    num_items = st.slider("📊 불러올 축제 개수", 10, 100, 30, 10)

    load_button = st.button("🎊 축제 불러오기", type="primary", use_container_width=True)

if load_button:
    if not api_key:
        st.error("API 키를 입력해주세요.")
        st.stop()

    with st.spinner("🎉 축제 정보를 불러오는 중입니다..."):
        try:
            st.session_state.festivals = get_festivals(api_key, num_items)
            st.session_state.random_festival = None
        except Exception as e:
            st.error(str(e))
            st.stop()

if st.session_state.festivals is None:
    st.info("👈 왼쪽에서 API 키와 검색 조건을 설정한 뒤 '축제 불러오기'를 눌러주세요.")
    st.markdown("""
    ### ✨ 주요 기능
    - 전국 축제 검색
    - 지역별 필터
    - 축제명·장소·설명 검색
    - 진행 중 / 개최 예정 / 종료 필터
    - 🎲 랜덤 축제 추천
    - 🗺️ 축제 지도
    - 📥 CSV 다운로드
    """)
    st.stop()

df = st.session_state.festivals.copy()
filtered = filter_data(df, region, keyword, status)

if sort_option == "가까운 축제부터":
    filtered = filtered.sort_values("start_date", ascending=True, na_position="last")
elif sort_option == "최신 축제부터":
    filtered = filtered.sort_values("start_date", ascending=False, na_position="last")
else:
    filtered = filtered.sort_values("title", ascending=True)

filtered = filtered.reset_index(drop=True)

statuses = filtered.apply(
    lambda r: status_of(r["start_date"], r["end_date"]), axis=1
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("🎉 검색 결과", f"{len(filtered):,}개")
c2.metric("🔥 진행 중", f"{(statuses == '진행 중').sum():,}개")
c3.metric("📅 개최 예정", f"{(statuses == '개최 예정').sum():,}개")
c4.metric("🏁 종료", f"{(statuses == '종료').sum():,}개")

tab1, tab2, tab3, tab4 = st.tabs([
    "🎉 축제 목록", "🎲 랜덤 추천", "🗺️ 축제 지도", "📥 다운로드"
])

with tab1:
    st.subheader(f"🎊 축제 목록 ({len(filtered)}개)")

    if filtered.empty:
        st.warning("검색 조건에 맞는 축제가 없습니다.")
    else:
        for _, festival in filtered.iterrows():
            title = festival["title"]
            image = safe_url(festival["image"])
            start = format_date(festival["start_date"])
            end = format_date(festival["end_date"])
            address = festival["address"] or "주소 정보 없음"
            homepage = safe_url(festival["homepage"])
            overview = festival["overview"]
            current_status = status_of(festival["start_date"], festival["end_date"])

            left, right = st.columns([1, 2])

            with left:
                if image:
                    st.image(image, use_container_width=True)
                else:
                    st.info("🖼️ 이미지 없음")

            with right:
                st.markdown(f"### 🎉 {title}")

                if current_status == "진행 중":
                    st.success("🔥 현재 진행 중")
                elif current_status == "개최 예정":
                    days = (festival["start_date"] - pd.Timestamp.today().normalize()).days
                    st.info(f"📅 개최 예정 · {max(days, 0)}일 후 시작")
                elif current_status == "종료":
                    st.caption("🏁 종료된 축제")

                st.write(f"📅 **기간:** {start} ~ {end}")
                st.write(f"📍 **장소:** {address}")

                if overview:
                    st.write(overview[:300] + ("..." if len(overview) > 300 else ""))

                if homepage:
                    st.link_button("🔗 축제 상세정보", homepage)

            st.divider()

with tab2:
    st.subheader("🎲 오늘의 랜덤 축제")

    if filtered.empty:
        st.warning("추천할 축제가 없습니다.")
    else:
        if st.button("🎲 랜덤 축제 뽑기!", type="primary"):
            st.session_state.random_festival = filtered.sample(1).iloc[0]

        festival = st.session_state.random_festival

        if festival is not None:
            st.success("🎉 오늘의 여행지를 골랐습니다!")

            image = safe_url(festival["image"])
            if image:
                st.image(image, width=700)

            st.markdown(f"# 🎊 {festival['title']}")
            st.write(f"📅 **기간:** {format_date(festival['start_date'])} ~ {format_date(festival['end_date'])}")
            st.write(f"📍 **장소:** {festival['address'] or '정보 없음'}")

            if festival["overview"]:
                st.write(festival["overview"])

            homepage = safe_url(festival["homepage"])
            if homepage:
                st.link_button("🔗 공식 상세정보 보기", homepage)

with tab3:
    st.subheader("🗺️ 축제 지도")

    map_df = filtered.dropna(subset=["latitude", "longitude"]).copy()

    if map_df.empty:
        st.warning("지도에 표시할 위치 정보가 없습니다.")
    else:
        st.map(map_df[["latitude", "longitude"]])
        st.caption(f"📍 {len(map_df)}개의 축제를 지도에 표시했습니다.")

with tab4:
    st.subheader("📥 축제 데이터 다운로드")

    download_df = filtered.copy()
    download_df["start_date"] = download_df["start_date"].dt.strftime("%Y-%m-%d")
    download_df["end_date"] = download_df["end_date"].dt.strftime("%Y-%m-%d")

    csv_data = download_df.to_csv(index=False, encoding="utf-8-sig")

    st.download_button(
        "📥 CSV 다운로드",
        data=csv_data,
        file_name="korea_festival_data.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.divider()
st.caption(
    "본 서비스는 한국관광공사 관광정보 API를 활용합니다. "
    "축제 일정 및 운영 여부는 공식 홈페이지에서 최종 확인해주세요."
)
