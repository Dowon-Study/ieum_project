# server.py — MCP 서버 (자동 TLS 폴백: default → TLS1.2+SECLEVEL1 → verify=False)
import os
import ssl
from typing import Any, Dict, Optional, Tuple, Iterable

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("recruitment-mcp")

BASE_URL = (os.getenv("BASE_URL") or "https://apis.data.go.kr/1051000/recruitment").rstrip("/")
API_KEY = (os.getenv("DATA_GO_KR_KEY") or "").strip()

def _client_candidates() -> Iterable[Tuple[str, httpx.Client]]:
    """
    TLS/SSL 환경에 따라 순차적으로 시도할 httpx.Client 후보들.
    각 후보는 (모드이름, Client) 형태로 yield됩니다.
    """
    # 1) 기본값: TLS 자동 협상 + 시스템 프록시/환경 변수 신뢰
    yield "default", httpx.Client(http2=False, timeout=20, trust_env=True)

    # 2) TLS 1.2 이상 + 낮은 보안 레벨(일부 구형 서버/프록시 대응)
    try:
        tls = ssl.create_default_context()
        tls.minimum_version = ssl.TLSVersion.TLSv1_2
        # 일부 공공/기관망 장비가 오래된 cipher만 허용 → OpenSSL3 기본 보안레벨과 충돌
        try:
            tls.set_ciphers("DEFAULT:@SECLEVEL=1")
        except Exception:
            pass
        yield "tls12_seclevel1", httpx.Client(verify=tls, http2=False, timeout=20, trust_env=True)
    except Exception:
        pass

    # 3) 최후 수단: 인증서 검증 비활성화 (가능하면 피하고, 네트워크 진단용으로만 사용)
    #    성공 시에도 ssl_mode로 'insecure'가 내려갑니다.
    yield "insecure", httpx.Client(verify=False, http2=False, timeout=20, trust_env=True)


def _try_get(url: str, params: Dict[str, Any]):
    """
    위의 후보 클라이언트들을 순서대로 시도. 성공하면 (mode, response) 반환.
    전부 실패하면 마지막 예외를 다시 던짐.
    """
    last_err: Optional[Exception] = None
    for mode, client in _client_candidates():
        try:
            with client as c:
                resp = c.get(url, params=params)
                return mode, resp
        except Exception as e:
            last_err = e
            continue
    # 전부 실패
    if last_err:
        raise last_err
    raise RuntimeError("No HTTP client candidates available")


def call_api(
    path: str,
    page_no: int = 1,
    num_rows: int = 10,
    filters: Optional[Dict[str, Any]] = None,
):
    if not API_KEY:
        return {
            "status": "error",
            "message": "DATA_GO_KR_KEY is missing in .env",
            "request_url": f"{BASE_URL}/{path.lstrip('/')}",
        }

    url = f"{BASE_URL}/{path.lstrip('/')}"
    params: Dict[str, Any] = {
        "serviceKey": API_KEY,  # 반드시 'Decoding(원문)' 키 사용 (% 없는 원문키)
        "type": "json",
        "pageNo": page_no,
        "numOfRows": num_rows,
    }
    if filters:
        params.update(filters)

    try:
        mode, resp = _try_get(url, params)
        req_url = str(resp.request.url)
        status_code = resp.status_code
        resp.raise_for_status()
        try:
            return {
                "status": "ok",
                "ssl_mode": mode,
                "request_url": req_url,
                "status_code": status_code,
                "data": resp.json(),
            }
        except Exception:
            return {
                "status": "ok",
                "ssl_mode": mode,
                "request_url": req_url,
                "status_code": status_code,
                "text": resp.text,
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "request_url": url,
        }


@mcp.tool()
def listRecruitments(
    path: str = "list",
    pageNo: int = 1,
    numOfRows: int = 10,
    filters: Optional[Dict[str, Any]] = None,
):
    """
    공공기관 채용정보 목록 조회
    - path: 기본 'list'
    - pageNo, numOfRows: 페이지/행 수
    - filters: {"hireTypeLst":"R1050,R1060,R1070", ...} 등 추가 파라미터
    """
    return call_api(path=path, page_no=pageNo, num_rows=numOfRows, filters=filters)


@mcp.tool()
def getRecruitmentDetail(path: str, **params):
    """
    상세 조회(엔드포인트/파라미터를 그대로 전달)
    예: path="detail", recruitSn="..." 등
    """
    page_no = int(params.pop("pageNo", 1)) if "pageNo" in params else 1
    num_rows = int(params.pop("numOfRows", 10)) if "numOfRows" in params else 10
    return call_api(path=path, page_no=page_no, num_rows=num_rows, filters=params)


@mcp.tool()
def ping():
    """헬스체크"""
    return {"status": "ok", "message": "pong"}


def main():
    # 시작 시 툴 목록 로그 (툴 등록 확인용)
    try:
        names = [t.name for t in mcp._tools]
        print("[SERVER] tools:", names, flush=True)
    except Exception:
        pass
    mcp.run()


if __name__ == "__main__":
    main()
