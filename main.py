"""
SERP Analyzer MCP — P0 골격 (연결 검증용)
- 도구: analyze_serp(keyword, top_n)  ← 지금은 임시(stub) 응답
- 키는 환경변수에서 읽음 (코드/깃허브엔 절대 안 들어감 = 안전)
  Render Environment에 등록:
    NAVER_CLIENT_ID, NAVER_CLIENT_SECRET   (P1부터 실제 사용)
    MCP_SECRET_PATH   ← 이 도구의 비밀 주소
- P0 단계 목표: 배포 → Claude 연결 → analyze_serp 가 인식되는지만 확인
  (실제 SERP 분석 로직은 P1부터 단계적으로 채운다)
"""
import os
from fastmcp import FastMCP

# P1부터 사용. P0에서는 없어도 서버가 떠야 하므로 get()으로 안전하게 읽는다.
NAVER_CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
# 비밀 주소: 환경변수에서 읽음. 안 넣으면 기본값 "/mcp"(잠금 안 됨)
SECRET_PATH         = os.environ.get("MCP_SECRET_PATH", "/mcp")

mcp = FastMCP("serp-analyzer")


@mcp.tool
def analyze_serp(keyword: str, top_n: int = 5) -> dict:
    """키워드의 상위 노출 블로그를 분석해 경쟁/구조/누락주제와 기본 추천을 반환한다.
    (P0: 연결 검증용 임시 응답. 실제 분석은 다음 단계에서 구현된다.)
    keyword: 분석할 키워드 (필수)
    top_n: 분석할 상위 글 개수 (기본 5)
    """
    return {
        "keyword": keyword,
        "status": "stub",
        "message": "SERP Analyzer 연결 성공 — 분석 로직은 다음 단계(P1~)에서 구현됩니다.",
        "top_n": top_n,
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))   # Render가 PORT를 넣어줌
    # 비밀 주소(SECRET_PATH)에서만 도구가 열림 = 주소를 모르면 접근 불가
    mcp.run(transport="http", host="0.0.0.0", port=port, path=SECRET_PATH)
