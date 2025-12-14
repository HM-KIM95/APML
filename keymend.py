import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv
from pytrends.request import TrendReq

# =========================================================
# 1. ENV 로드
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "naver.env"))

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
    raise EnvironmentError("NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 설정되지 않았습니다.")

# =========================================================
# 2. 네이버 데이터랩
# =========================================================
def fetch_naver_trend(keywords, start_date, end_date):
    url = "https://openapi.naver.com/v1/datalab/search"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        "Content-Type": "application/json"
    }

    rows = []

    for kw in keywords:
        payload = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": "month",
            "keywordGroups": [
                {
                    "groupName": kw,
                    "keywords": [kw]
                }
            ]
        }

        res = requests.post(url, headers=headers, data=json.dumps(payload))
        res.raise_for_status()

        data = res.json()["results"][0]["data"]

        for d in data:
            rows.append({
                "keyword": kw,
                "date": d["period"],
                "ratio": d["ratio"]
            })

    return pd.DataFrame(rows)

# =========================================================
# 3. 상승률 기반 키워드 추천
# =========================================================
def recommend_keywords(df, top_n=5):
    recommendations = []

    for kw, g in df.groupby("keyword"):
        g = g.sort_values("date")

        if len(g) < 3:
            continue

        recent = g.iloc[-1]["ratio"]
        prev_avg = g.iloc[-3:-1]["ratio"].mean()

        growth = ((recent - prev_avg) / prev_avg) * 100 if prev_avg > 0 else 0

        recommendations.append({
            "keyword": kw,
            "latest_ratio": round(recent, 2),
            "growth_rate(%)": round(growth, 2)
        })

    rec_df = pd.DataFrame(recommendations)
    return rec_df.sort_values("growth_rate(%)", ascending=False).head(top_n)

# =========================================================
# 4. 실행부
# =========================================================
if __name__ == "__main__":
    # 🔹 키워드 후보 풀 (여기만 계속 늘리면 됩니다)
    keyword_pool = [
        "인공지능", "ChatGPT", "생성형 AI", "AI 투자", "AI 관련주",
        "프롬프트 엔지니어링", "AI 윤리", "AI 규제", "오픈AI", "LLM"
    ]

    df = fetch_naver_trend(
        keywords=keyword_pool,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )

    추천 = recommend_keywords(df, top_n=5)

    print("\n🔥 이번 주 블로그 추천 키워드 TOP 5")
    print(추천)

    추천.to_csv("weekly_keyword_recommendation.csv", index=False)