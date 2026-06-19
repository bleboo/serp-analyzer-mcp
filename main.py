"""
SERP Analyzer MCP — P1 (네이버 검색 API로 상위 글 수집)
- 도구: analyze_serp(keyword, top_n)
  → P1: 키워드의 상위 top_n개 블로그 글의 제목/주소/요약을 네이버 검색 API로 수집
  → (본문 길이·H태그·공통키워드·누락주제 분석은 다음 단계 P2~에서 추가)
- 키는 환경변수에서 읽음 (코드/깃허브엔 절대 안 들어감 = 안전)
  Render Environment에 등록:
    NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
    MCP_SECRET_PATH   ← 이 도구의 비밀 주소
"""
import os
import re
import html
import requests
from fastmcp import FastMCP

NAVER_CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
SECRET_PATH         = os.environ.get("MCP_SECRET_PATH", "/mcp")

NAVER_BLOG_SEARCH = "https://openapi.naver.com/v1/search/blog.json"

mcp = FastMCP("serp-analyzer")


# === 공통 유틸 ===
def _clean(text):
    """네이버 응답의 <b> 태그·HTML 엔티티(&quot; 등)를 제거해 깔끔한 텍스트로."""
    text = re.sub(r"<[^>]+>", "", text or "")
    return html.unescape(text).strip()


# === [수집 구역] SerpProvider: 네이버 검색 API로 상위 결과 가져오기 ===
def search_naver_blog(keyword, display):
    """키워드로 네이버 블로그 상위 결과 수집.
    반환: [{rank, title, url, snippet, blogger}, ...]
    """
    resp = requests.get(
        NAVER_BLOG_SEARCH,
        params={"query": keyword, "display": display, "sort": "sim"},  # sim = 관련도순
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


# === [도구 구역] MCP Tool ===
@mcp.tool
def analyze_serp(keyword: str, top_n: int = 5) -> dict:
    """키워드의 상위 노출 블로그를 분석한다.
    (P1: 네이버 검색 API로 상위 top_n개 글의 제목/주소/요약을 수집. 본문 분석은 다음 단계.)
    keyword: 분석할 키워드 (필수)
    top_n: 가져올 상위 글 개수 (기본 5, 1~100)
    """
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        return {
            "keyword": keyword,
            "status": "error",
            "message": "네이버 키(NAVER_CLIENT_ID / NAVER_CLIENT_SECRET)가 환경변수에 없습니다. Render Environment를 확인하세요.",
        }

    top_n = max(1, min(int(top_n), 100))
    try:
        posts = search_naver_blog(keyword, top_n)
    except Exception as e:
        return {
            "keyword": keyword,
            "status": "error",
            "message": f"네이버 검색 API 호출 실패: {e}",
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
    port = int(os.environ.get("PORT", 8000))   # Render가 PORT를 넣어줌
    mcp.run(transport="http", host="0.0.0.0", port=port, path=SECRET_PATH)
