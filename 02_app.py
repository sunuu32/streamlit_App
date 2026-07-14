import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="📈 Global Top10 Stock Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 글로벌 시가총액 TOP10 주식 대시보드")
st.markdown("최근 **1년간 주가 변화**를 확인할 수 있습니다.")

# -----------------------------
# 글로벌 시가총액 TOP10 (미국 기준 Yahoo Finance 티커)
# -----------------------------
stocks = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Broadcom": "AVGO",
    "Tesla": "TSLA",
    "TSMC": "TSM",
    "Saudi Aramco": "2222.SR"
}

# -----------------------------
# 사이드바
# -----------------------------
st.sidebar.header("⚙️ 설정")

selected = st.sidebar.multiselect(
    "기업 선택",
    list(stocks.keys()),
    default=["Apple", "Microsoft", "NVIDIA"]
)

if len(selected) == 0:
    st.warning("하나 이상의 기업을 선택해주세요.")
    st.stop()

# -----------------------------
# 주가 데이터 다운로드
# -----------------------------
@st.cache_data(ttl=3600)
def load_stock(ticker):
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y", auto_adjust=True)
    return df
# -----------------------------
# 주가 그래프
# -----------------------------
fig = go.Figure()

summary = []

for company in selected:

    ticker = stocks[company]

    df = load_stock(ticker)

    if df.empty:
        continue

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            name=company
        )
    )

    start = float(df["Close"].iloc[0])
    end = float(df["Close"].iloc[-1])

    summary.append({
        "기업": company,
        "현재가": round(end, 2),
        "1년 수익률(%)": round((end-start)/start*100,2)
    })

fig.update_layout(
    title="최근 1년 주가",
    template="plotly_white",
    height=650,
    hovermode="x unified",
    legend_title="기업"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# 수익률 표
# -----------------------------
st.subheader("📊 1년 수익률")

result = pd.DataFrame(summary)

if not result.empty:
    result = result.sort_values("1년 수익률(%)", ascending=False)
    st.dataframe(result, use_container_width=True, hide_index=True)

# -----------------------------
# 개별 기업 분석
# -----------------------------
st.divider()

st.subheader("📉 이동평균선 분석")

company = st.selectbox(
    "기업 선택",
    list(stocks.keys())
)

ticker = stocks[company]

df = load_stock(ticker)

df["MA20"] = df["Close"].rolling(20).mean()
df["MA60"] = df["Close"].rolling(60).mean()

fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    x=df.index,
    y=df["Close"],
    name="Close",
    line=dict(width=3)
))

fig2.add_trace(go.Scatter(
    x=df.index,
    y=df["MA20"],
    name="20일 이동평균"
))

fig2.add_trace(go.Scatter(
    x=df.index,
    y=df["MA60"],
    name="60일 이동평균"
))

fig2.update_layout(
    template="plotly_white",
    height=600,
    title=f"{company} 이동평균선"
)

st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# 거래량
# -----------------------------
st.subheader("📦 거래량")

fig3 = go.Figure()

fig3.add_trace(go.Bar(
    x=df.index,
    y=df["Volume"],
    name="Volume"
))

fig3.update_layout(
    template="plotly_white",
    height=350
)

st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# 주요 지표
# -----------------------------
st.divider()

st.subheader("📌 주요 지표")

latest = df.iloc[-1]
previous = df.iloc[-2]

change = latest["Close"] - previous["Close"]
change_pct = change / previous["Close"] * 100

col1, col2, col3 = st.columns(3)

col1.metric(
    "현재가",
    f"${latest['Close']:.2f}",
    f"{change_pct:.2f}%"
)

col2.metric(
    "52주 최고",
    f"${df['Close'].max():.2f}"
)

col3.metric(
    "52주 최저",
    f"${df['Close'].min():.2f}"
)

# -----------------------------
# 원본 데이터
# -----------------------------
st.divider()

with st.expander("📄 원본 데이터 보기"):
    st.dataframe(df.tail(100), use_container_width=True)

st.caption("데이터 출처 : Yahoo Finance (yfinance)")
