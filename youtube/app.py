import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import re
from datetime import datetime
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# 1. 페이지 설정
st.set_page_config(page_title="유튜브 댓글 분석기", page_icon="📊", layout="wide")
st.title("📊 유튜브 댓글 타임라인 & 감정 분석기")
st.markdown("유튜브 영상의 댓글을 수집하여 시간대별 추이와 워드클라우드를 분석합니다.")

# 2. 사이드바 - API 키 및 설정
st.sidebar.header("⚙️ 설정 및 인증")

# Streamlit Secrets 사용 권장, 없을 경우 화면에서 입력
api_key = st.sidebar.text_input("YouTube API Key를 입력하세요", type="password", 
                                value=st.secrets.get("YOUTUBE_API_KEY", ""))

max_comments = st.sidebar.slider("수집할 댓글 개수 선택", min_value=20, max_value=500, value=100, step=20)

st.sidebar.markdown("""
---
### 💡 사용 방법
1. YouTube Data API v3 키를 발급받아 입력합니다.
2. 분석하고 싶은 유튜브 영상 링크를 넣습니다.
3. 분석하기 버튼을 누르고 결과를 확인합니다.
""")

# 3. 유튜브 영상 ID 추출 함수
def extract_video_id(url):
    pattern = r'(?:v=|\/shorts\/|\/embed\/|\/youtu\.be\/|\/v\/|\/e\/|watch\?v%3D|watch\?feature=player_embedded&v=)([^#\&\?]*Layout)'
    # 일반적인 url 매칭 패턴
    regex = re.compile(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=|embed/|v/|shorts/)?([^?&\s]+)')
    match = regex.match(url)
    if match:
        return match.group(5)
    return None

# 4. 유튜브 댓글 수집 함수
def get_youtube_comments(video_id, max_results, api_key):
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        comments = []
        next_page_token = None
        
        while len(comments) < max_results:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(100, max_results - len(comments)),
                pageToken=next_page_token,
                textFormat="plainText"
            )
            response = request.execute()
            
            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                text = snippet["textDisplay"]
                like_count = snippet["likeCount"]
                published_at = snippet["publishedAt"]
                
                comments.append({
                    "comment": text,
                    "likes": like_count,
                    "date": pd.to_datetime(published_at)
                })
                
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
                
        return pd.DataFrame(comments)
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None

# 5. 한글 텍스트 정제 함수
def clean_korean_text(text_list):
    full_text = " ".join(text_list)
    # 한글과 공백을 제외한 문자 제거
    cleaned = re.sub(r'[^가-힣\s]', '', full_text)
    return cleaned

# 6. 메인 화면 UI
video_url = st.text_input("유튜브 영상 링크를 입력하세요:", placeholder="https://www.youtube.com/watch?v=...")

if video_url:
    video_id = extract_video_id(video_url)
    
    if video_id:
        # 레이아웃 나누기 (영상 미리보기 및 기본 정보)
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("📺 영상 미리보기")
            st.video(video_url)
        with col2:
            st.subheader("📈 분석 실행")
            st.info(f"추출된 영상 ID: **{video_id}**")
            analyze_btn = st.button("🚀 댓글 분석 시작", use_container_width=True)
            
        if analyze_btn:
            if not api_key:
                st.warning("🔑 사이드바에 YouTube API Key를 입력해주세요.")
            else:
                with st.spinner("유튜브에서 댓글을 열심히 긁어오는 중... 🏃‍♂️"):
                    df = get_youtube_comments(video_id, max_comments, api_key)
                    
                if df is not None and not df.empty:
                    st.success(f"총 {len(df)}개의 댓글을 성공적으로 수집했습니다!")
                    
                    # --- 시각화 섹션 ---
                    st.markdown("---")
                    
                    # 1. 대시보드 지표
                    m1, m2 = st.columns(2)
                    m1.metric("총 수집 댓글 수", f"{len(df)}개")
                    m2.metric("가장 많은 좋아요를 받은 댓글", f"{df['likes'].max()}개")
                    
                    st.markdown("### 🕒 시간대별 댓글 작성 추이")
                    # 시간대별 카운트를 위해 날짜 포맷 변경 (일자별/시간별)
                    df['date_only'] = df['date'].dt.strftime('%Y-%m-%d %H:00')
                    trend_df = df.groupby('date_only').size().reset_index(name='count')
                    trend_df = trend_df.sort_values('date_only')
                    
                    fig_trend = px.line(trend_df, x='date_only', y='count', title="시간대별 댓글 등록 트렌드",
                                       labels={'date_only': '작성 시간', 'count': '댓글 수'}, template="plotly_white")
                    st.plotly_chart(fig_trend, use_container_width=True)
                    
                    
                    # 2. 댓글 반응도 (좋아요 순 TOP 5)
                    st.markdown("### 🔥 가장 반응이 뜨거운 댓글 TOP 5")
                    top_likes = df.sort_values(by='likes', ascending=False).head(5)[['comment', 'likes']]
                    st.table(top_likes)
                    
                    
                    # 3. 한글 워드클라우드
                    st.markdown("### 🔠 댓글 키워드 분석 (한글 워드클라우드)")
                    kor_text = clean_korean_text(df['comment'].tolist())
                    
                    if len(kor_text.strip()) > 5:
                        # Streamlit Cloud 리눅스 환경의 기본 나눔 폰트 경로 지정 (혹은 폰트 미지정시 기본 폰트 사용)
                        # 필요 시 나눔고딕 등 ttf 파일을 앱 루트에 두고 경로를 지정하면 완벽하게 나옵니다.
                        try:
                            wordcloud = WordCloud(
                                width=800, height=400, 
                                background_color='white',
                                font_path='/usr/share/fonts/truetype/nanum/NanumGothic.ttf', # 리눅스 기본 나눔폰트 경로 예시
                                max_words=100
                            ).generate(kor_text)
                        except:
                            # 폰트 경로 오류 시 기본 폰트로 우회 (한글이 깨질 수 있으므로 대비책)
                            wordcloud = WordCloud(width=800, height=400, background_color='white', max_words=100).generate(kor_text)
                            
                        fig, ax = plt.subplots(figsize=(10, 5))
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis('off')
                        st.pyplot(fig)
                    else:
                        st.info("워드클라우드를 생성할 만큼의 한글 데이터가 부족합니다.")
                        
                    # 데이터 프레임 확인
                    with st.expander("📥 수집된 전체 데이터 보기"):
                        st.dataframe(df[['date', 'likes', 'comment']])
                else:
                    st.error("댓글을 가져오지 못했습니다. 영상에 댓글이 없거나 API 제한을 확인하세요.")
    else:
        st.error("올바른 유튜브 URL 형식이 아닙니다. 다시 확인해 주세요.")
