"""
SERP Analyzer MCP — P1 (네이버 검색 API로 상위 글 수집) + 키 진단
- 키 앞뒤 공백/줄바꿈을 자동 제거(.strip())해서 흔한 401 원인을 막는다.
- 그래도 실패하면, 키 값을 노출하지 않으면서 길이/공백 여부를 알려줘 원인 파악을 돕는다.
- 키는 환경변수에서 읽음 (코드/깃허브엔 절대 안 들어감)
  Render Environment: NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, MCP_SECRET_PATH
"""
import os
import re
import html
import requests
from fastmcp import FastMCP

# 원본(raw)과 정리본(strip)을 모두 보관 — 공백이 있었는지 진단용
_RAW_ID     = os.environ.get("NAVER_CLIENT_ID", "")
_RAW_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
NAVER_CLIENT_ID     = _RAW_ID.strip()
NAVER_CLIENT_SECRET = _RAW_SECRET.strip()
SECRET_PATH         = os.environ.get("MCP_SECRET_PATH", "/mcp").strip()

NAVER_BLOG_SEARCH = "https://openapi.naver.com/v1/search/blog.json"

mcp = FastMCP("serp-analyzer")


def _clean(text):
    text = re.sub(r"<[^>]+>", "", text or "")
    return html.unescape(text).strip()


def search_naver_blog(keyword, display):
    resp = requests.get(
        NAVER_BLOG_SEARCH,
        params={"query": keyword, "display": display, "sort": "sim"},
        headers={
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        },
        timeout=10,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    posts = []
    for i, it in enumerate(items, start=1):
        posts.append({
            "rank": i,
            "title": _clean(it.get("title", "")),
            "url": it.get("link", ""),
            "snippet": _clean(it.get("description", "")),
            "blogger": it.get("bloggername", ""),
        })
    return posts


@mcp.tool
def analyze_serp(keyword: str, top_n: int = 5) -> dict:
    """키워드의 상위 노출 블로그를 분석한다.
    (P1: 네이버 검색 API로 상위 top_n개 글의 제목/주소/요약 수집. 본문 분석은 다음 단계.)
    keyword: 분석할 키워드 (필수)
    top_n: 가져올 상위 글 개수 (기본 5, 1~100)
    """
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        return {
            "keyword": keyword,
            "status": "error",
            "message": "네이버 키(NAVER_CLIENT_ID / NAVER_CLIENT_SECRET)가 환경변수에 없습니다.",
        }

    top_n = max(1, min(int(top_n), 100))
    try:
        posts = search_naver_blog(keyword, top_n)
    except Exception as e:
        # 키 값은 노출하지 않고, 길이와 공백 여부만 알려줌 (원인 파악용)
        return {
            "keyword": keyword,
            "status": "error",
            "message": f"네이버 검색 API 호출 실패: {e}",
            "debug": {
                "id_len": len(NAVER_CLIENT_ID),
                "secret_len": len(NAVER_CLIENT_SECRET),
                "id_had_whitespace": _RAW_ID != NAVER_CLIENT_ID,
                "secret_had_whitespace": _RAW_SECRET != NAVER_CLIENT_SECRET,
            },
        }

    return {
        "keyword": keyword,
        "status": "p1",
        "top_posts_analyzed": len(posts),
        "posts": posts,
        "meta": {
            "source": "naver-search-api",
            "note": "순위는 네이버 검색 API 관련도순이며 실제 검색결과 페이지와 다를 수 있음",
        },
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="http", host="0.0.0.0", port=port, path=SECRET_PATH)
