import re
from collections import Counter

import pandas as pd
from konlpy.tag import Okt
from wordcloud import WordCloud

okt = Okt()

# ------------------------------------------
# 불용어
# ------------------------------------------

STOPWORDS = {
    "하다","되다","이다","있다","없다",
    "그리고","그러나","하지만","입니다",
    "정말","진짜","너무","영상","이번",
    "오늘","그냥","이거","저거","그것",
    "에서","으로","까지","에게","대한",
    "합니다","합니다","있는","없는",
    "같은","이런","저런","그런",
    "ㅋㅋ","ㅎㅎ","ㅠㅠ","ㅜㅜ",
    "진심","완전","와","오","아",
    "입니다","네요","네요","어요",
    "좋아요","구독","댓글"
}

# ------------------------------------------
# 긍정 단어
# ------------------------------------------

POSITIVE = {
    "좋다","최고","재밌다","감동",
    "행복","추천","멋지다","사랑",
    "웃기다","감사","훌륭","대박",
    "예쁘다","잘한다","최강","굿",
    "최고다","재미","최애","응원",
    "완벽","신기","존경"
}

# ------------------------------------------
# 부정 단어
# ------------------------------------------

NEGATIVE = {
    "싫다","최악","별로","짜증",
    "화난","실망","못한다","노잼",
    "쓰레기","별로다","구리다",
    "끔찍","나쁘다","불편",
    "답답","욕","비추","망했다",
    "억지","실수","지루"
}


# ------------------------------------------
# 한글만 추출
# ------------------------------------------

def clean_text(text):

    text = str(text)

    text = re.sub(r"http\S+", "", text)

    text = re.sub(r"[^가-힣 ]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ------------------------------------------
# 명사 추출
# ------------------------------------------

def extract_words(text):

    text = clean_text(text)

    nouns = okt.nouns(text)

    result = []

    for word in nouns:

        if len(word) < 2:
            continue

        if word in STOPWORDS:
            continue

        result.append(word)

    return result


# ------------------------------------------
# 감성 분석
# ------------------------------------------

def sentiment_score(text):

    text = clean_text(text)

    morphs = okt.morphs(text)

    score = 0

    for word in morphs:

        if word in POSITIVE:
            score += 1

        if word in NEGATIVE:
            score -= 1

    return score


def analyze_sentiment(df):

    sentiments = []

    scores = []

    for text in df["text"]:

        score = sentiment_score(text)

        scores.append(score)

        if score > 0:
            sentiments.append("긍정")

        elif score < 0:
            sentiments.append("부정")

        else:
            sentiments.append("중립")

    df["score"] = scores

    df["sentiment"] = sentiments

    return df


# ------------------------------------------
# 단어 빈도
# ------------------------------------------

def get_word_frequency(texts):

    words = []

    for text in texts:

        words.extend(
            extract_words(text)
        )

    return Counter(words)


# ------------------------------------------
# 워드클라우드
# ------------------------------------------

def make_wordcloud(texts):

    counter = get_word_frequency(texts)

    try:

        wc = WordCloud(
            width=1200,
            height=700,
            background_color="white",
            font_path="NanumGothic.ttf"
        )

    except:

        wc = WordCloud(
            width=1200,
            height=700,
            background_color="white"
        )

    wc.generate_from_frequencies(counter)

    return wc


# ------------------------------------------
# TOP20
# ------------------------------------------

def top_words(texts, top_n=20):

    counter = get_word_frequency(texts)

    df = pd.DataFrame(
        counter.most_common(top_n),
        columns=["단어","빈도"]
    )

    return df
