import streamlit as st
from openai import OpenAI
from datetime import date
import urllib.parse

# -------------------------
# 페이지 설정
# -------------------------

st.set_page_config(
    page_title="오늘의 운세",
    page_icon="🔮",
    layout="centered"
)

# -------------------------
# 스타일
# -------------------------

st.markdown("""
<style>

.stApp{
background: linear-gradient(135deg,#0f172a,#1e3a8a,#4f46e5);
}

.main-title{
font-size:42px;
font-weight:bold;
text-align:center;
color:white;
margin-bottom:10px;
}

.sub{
text-align:center;
color:#dddddd;
margin-bottom:30px;
}

.card{
background:white;
padding:20px;
border-radius:15px;
box-shadow:0 0 20px rgba(0,0,0,.2);
margin-bottom:20px;
}

</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🔮 오늘의 운세</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">AI가 운세와 음악을 추천해드립니다.</div>', unsafe_allow_html=True)

# -------------------------
# OpenAI
# -------------------------

client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)

# -------------------------
# 별자리 계산
# -------------------------

def zodiac(month, day):

    signs = [
        ((1,20),"물병자리"),
        ((2,19),"물고기자리"),
        ((3,21),"양자리"),
        ((4,20),"황소자리"),
        ((5,21),"쌍둥이자리"),
        ((6,22),"게자리"),
        ((7,23),"사자자리"),
        ((8,23),"처녀자리"),
        ((9,24),"천칭자리"),
        ((10,24),"전갈자리"),
        ((11,23),"사수자리"),
        ((12,22),"염소자리"),
        ((12,31),"염소자리")
    ]

    for (m,d),name in signs:
        if (month,day)<=(m,d):
            return name

# -------------------------
# 입력
# -------------------------

birthday = st.date_input(
    "🎂 생년월일",
    min_value=date(1950,1,1),
    max_value=date.today()
)

# -------------------------
# 버튼
# -------------------------

if st.button("✨ 오늘의 운세 보기", use_container_width=True):

    sign = zodiac(birthday.month,birthday.day)

    prompt = f"""
사용자의 정보

생년월일 : {birthday}

별자리 : {sign}

아래 형식으로 작성하세요.

오늘의 운세
400자

행운의 색

행운의 숫자

행운의 아이템

오늘 조심할 점

추천 노래 3곡

형식

1. 제목 - 가수
추천 이유
"""

    with st.spinner("AI가 운세를 보는 중입니다..."):

        response = client.chat.completions.create(

            model="gpt-4.1-mini",

            messages=[

                {
                    "role":"system",
                    "content":
                    """
                    당신은 유명한 운세 전문가입니다.
                    항상 긍정적이고 따뜻하게 말합니다.
                    음악 추천도 잘합니다.
                    """
                },

                {
                    "role":"user",
                    "content":prompt
                }

            ],

            temperature=0.9

        )

        result = response.choices[0].message.content

    st.markdown("### ✨ 결과")

    st.markdown(f"""
<div class="card">

{result.replace(chr(10),"<br>")}

</div>
""", unsafe_allow_html=True)

    st.divider()

    st.subheader("🎵 추천곡 바로 듣기")

    lines = result.split("\n")

    for line in lines:

        if line.startswith("1.") or line.startswith("2.") or line.startswith("3."):

            song = line.split(".",1)[1].strip()

            url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(song)

            st.link_button(song, url)
