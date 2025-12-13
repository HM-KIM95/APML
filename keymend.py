import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv
from pytrends.request import TrendReq


# =========================================================
# 1. 환경변수 로드 (naver.env)
# =========================================================
load_dotenv("naver.env")

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
    raise EnvironmentError("NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 설정되지 않았습니다.")


# =========================================================
# 2. 네이버 데이터랩 검색 추이
# =========================================================
def fetch_naver_trend(
    keywords,
    start_date="2024-01-01",
    end_date="2024-12-31",
    time_unit="month"
):
    url = "https://openapi.naver.com/v1/datalab/search"

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        "Content-Type": "application/json"
    }

    payload = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": [
            {
                "groupName": "KEYWORDS",
                "keywords": keywords
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()

    data = response.json()["results"][0]["data"]
    df = pd.DataFrame(data)
    df.rename(columns={"period": "date", "ratio": "naver_ratio"}, inplace=True)

    return df


# =========================================================
# 3. Google Trends 검색 추이
# =========================================================
def fetch_google_trend(
    keywords,
    start_date="2024-01-01",
    end_date="2024-12-31",
    geo="KR"
):
    pytrends = TrendReq(hl="ko-KR", tz=540)

    timeframe = f"{start_date} {end_date}"
    pytrends.build_payload(
        kw_list=keywords,
        timeframe=timeframe,
        geo=geo
    )

    df = pytrends.interest_over_time()

    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])

    df.reset_index(inplace=True)
    df.rename(columns={"date": "date"}, inplace=True)

    return df


# =========================================================
# 4. 실행부 (하나의 파이프라인)
# =========================================================
if __name__ == "__main__":
    # 키워드 설정
    naver_keywords = ["인공지능", "AI", "ChatGPT"]
    google_keywords = ["Artificial Intelligence", "ChatGPT"]

    start_date = "2024-01-01"
    end_date = "2024-12-31"

    # 네이버 트렌드
    naver_df = fetch_naver_trend(
        keywords=naver_keywords,
        start_date=start_date,
        end_date=end_date
    )

    # 구글 트렌드
    google_df = fetch_google_trend(
        keywords=google_keywords,
        start_date=start_date,
        end_date=end_date
    )

    # 결과 출력
    print("\n===== NAVER DATA LAB =====")
    print(naver_df.head())

    print("\n===== GOOGLE TRENDS =====")
    print(google_df.head())

    # CSV 저장
    naver_df.to_csv("naver_trend.csv", index=False)
    google_df.to_csv("google_trend.csv", index=False)

    print("\nCSV 파일 저장 완료")