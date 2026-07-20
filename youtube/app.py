import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from youtube import (
    get_video_id,
    get_video_info,
    get_comments,
)
from analysis import (
    analyze_sentiment,
    make_wordcloud,
)

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="YouTube 댓글 분석기",
    page_icon="📺",
    layout="wide"
)

st.title("📺 YouTube 댓글 분석기")
st.caption("댓글 감성분석 · 워드클라우드 · 시간대별 분석")

# -----------------------------
# 사이드바
# -----------------------------
st.sidebar.header("설정")

api_key = st.sidebar.text_input(
    "YouTube API Key",
    type="password"
)

max_comments = st.sidebar.slider(
    "댓글 개수",
    50,
    1000,
    200,
    step=50
)

video_url = st.text_input(
    "유튜브 영상 주소",
    placeholder="https://www.youtube.com/watch?v=..."
)

# -----------------------------
# URL 확인
# -----------------------------
if video_url:

    video_id = get_video_id(video_url)

    if video_id:

        st.video(video_url)

        if api_key:

            try:

                info = get_video_info(video_id, api_key)

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "조회수",
                    f"{int(info['viewCount']):,}"
                )

                col2.metric(
                    "좋아요",
                    f"{int(info['likeCount']):,}"
                )

                col3.metric(
                    "댓글수",
                    f"{int(info['commentCount']):,}"
                )

                st.subheader(info["title"])

            except Exception as e:
                st.error(e)

        else:
            st.warning("왼쪽에서 API Key를 입력하세요.")

# -----------------------------
# 분석 시작
# -----------------------------
if st.button("댓글 분석 시작"):

    if api_key == "":
        st.error("API Key를 입력하세요.")
        st.stop()

    if video_url == "":
        st.error("영상 주소를 입력하세요.")
        st.stop()

    video_id = get_video_id(video_url)

    progress = st.progress(0)

    with st.spinner("댓글 가져오는 중..."):

        comments = get_comments(
            video_id,
            api_key,
            max_comments
        )

    progress.progress(30)

    if len(comments) == 0:
        st.error("댓글을 가져오지 못했습니다.")
        st.stop()

    df = pd.DataFrame(comments)

    progress.progress(50)

    # -------------------------
    # 감성분석
    # -------------------------
    df = analyze_sentiment(df)

    progress.progress(70)

    # -------------------------
    # 통계
    # -------------------------
    st.header("📊 댓글 통계")

    c1, c2, c3 = st.columns(3)

    c1.metric("댓글", len(df))

    c2.metric(
        "평균 좋아요",
        round(df["likeCount"].mean(), 1)
    )

    c3.metric(
        "작성자 수",
        df["author"].nunique()
    )

    # -------------------------
    # 댓글 데이터
    # -------------------------
    st.header("댓글")

    st.dataframe(
        df,
        use_container_width=True,
        height=350
    )

    # -------------------------
    # 시간대별
    # -------------------------
    st.header("📈 시간대별 댓글")

    df["publishedAt"] = pd.to_datetime(df["publishedAt"])

    hourly = (
        df
        .groupby(df["publishedAt"].dt.hour)
        .size()
        .reset_index(name="count")
    )

    fig = px.bar(
        hourly,
        x="publishedAt",
        y="count",
        labels={
            "publishedAt":"시간",
            "count":"댓글수"
        }
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # -------------------------
    # 감성
    # -------------------------
    st.header("😊 감성분석")

    sentiment = (
        df["sentiment"]
        .value_counts()
        .reset_index()
    )

    sentiment.columns = [
        "감성",
        "개수"
    ]

    fig2 = px.pie(
        sentiment,
        values="개수",
        names="감성"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    # -------------------------
    # 워드클라우드
    # -------------------------
    st.header("☁️ 워드클라우드")

    wc = make_wordcloud(df["text"])

    fig3, ax = plt.subplots(figsize=(12,6))

    ax.imshow(wc)

    ax.axis("off")

    st.pyplot(fig3)

    # -------------------------
    # 단어 빈도
    # -------------------------
    st.header("TOP20 단어")

    freq = pd.DataFrame(
        wc.words_.items(),
        columns=["단어","빈도"]
    )

    freq = freq.head(20)

    fig4 = px.bar(
        freq,
        x="단어",
        y="빈도"
    )

    st.plotly_chart(
        fig4,
        use_container_width=True
    )

    # -------------------------
    # 다운로드
    # -------------------------
    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "CSV 다운로드",
        csv,
        "youtube_comments.csv",
        "text/csv"
    )

    progress.progress(100)

    st.success("분석 완료!")
