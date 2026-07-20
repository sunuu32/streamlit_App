import re
from googleapiclient.discovery import build


# ---------------------------------------
# URL -> Video ID
# ---------------------------------------
def get_video_id(url: str):

    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?]+)",
        r"shorts/([^?]+)",
        r"embed/([^?]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None


# ---------------------------------------
# API 객체
# ---------------------------------------
def get_service(api_key):

    return build(
        "youtube",
        "v3",
        developerKey=api_key
    )


# ---------------------------------------
# 영상 정보
# ---------------------------------------
def get_video_info(video_id, api_key):

    youtube = get_service(api_key)

    request = youtube.videos().list(
        part="snippet,statistics",
        id=video_id
    )

    response = request.execute()

    if len(response["items"]) == 0:
        raise Exception("영상을 찾을 수 없습니다.")

    item = response["items"][0]

    snippet = item["snippet"]
    statistics = item["statistics"]

    return {
        "title": snippet["title"],
        "channel": snippet["channelTitle"],
        "publishedAt": snippet["publishedAt"],
        "viewCount": statistics.get("viewCount", 0),
        "likeCount": statistics.get("likeCount", 0),
        "commentCount": statistics.get("commentCount", 0),
    }


# ---------------------------------------
# 댓글 가져오기
# ---------------------------------------
def get_comments(
    video_id,
    api_key,
    max_comments=200
):

    youtube = get_service(api_key)

    comments = []

    next_page = None

    while True:

        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(100, max_comments),
            order="time",
            pageToken=next_page,
            textFormat="plainText"
        )

        response = request.execute()

        for item in response["items"]:

            snippet = item["snippet"]["topLevelComment"]["snippet"]

            comments.append(
                {
                    "author": snippet.get(
                        "authorDisplayName",
                        ""
                    ),

                    "text": snippet.get(
                        "textDisplay",
                        ""
                    ),

                    "likeCount": snippet.get(
                        "likeCount",
                        0
                    ),

                    "publishedAt": snippet.get(
                        "publishedAt",
                        ""
                    )
                }
            )

            if len(comments) >= max_comments:
                return comments

        next_page = response.get("nextPageToken")

        if next_page is None:
            break

    return comments


# ---------------------------------------
# 댓글 개수만 조회
# ---------------------------------------
def get_comment_count(
    video_id,
    api_key
):

    info = get_video_info(
        video_id,
        api_key
    )

    return int(info["commentCount"])


# ---------------------------------------
# 채널명 조회
# ---------------------------------------
def get_channel_name(
    video_id,
    api_key
):

    info = get_video_info(
        video_id,
        api_key
    )

    return info["channel"]


# ---------------------------------------
# 제목 조회
# ---------------------------------------
def get_video_title(
    video_id,
    api_key
):

    info = get_video_info(
        video_id,
        api_key
    )

    return info["title"]
