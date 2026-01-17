# realestate_server.py — 아파트 전월세 전용 MCP 서버
import os
import ssl
from typing import Any, Dict, Optional, Tuple, Iterable

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("realestate-mcp")

# 공공데이터포털 국토교통부 아파트 전월세 자료 API
BASE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent"
API_KEY = (os.getenv("MOLIT_API_KEY") or "").strip()

def _client_candidates() -> Iterable[Tuple[str, httpx.Client]]:
    """TLS/SSL 호환성을 위한 클라이언트 후보 생성"""
    # 1) 기본값
    yield "default", httpx.Client(http2=False, timeout=20, trust_env=True)

    # 2) TLS 1.2 + 낮은 보안 레벨 (공공기관 구형 서버 호환용)
    try:
        tls = ssl.create_default_context()
        tls.minimum_version = ssl.TLSVersion.TLSv1_2
        try:
            tls.set_ciphers("DEFAULT:@SECLEVEL=1")
        except Exception:
            pass
        yield "tls12_seclevel1", httpx.Client(verify=tls, http2=False, timeout=20, trust_env=True)
    except Exception:
        pass

    # 3) 최후 수단 (인증서 검증 무시)
    yield "insecure", httpx.Client(verify=False, http2=False, timeout=20, trust_env=True)


def _try_get(url: str, params: Dict[str, Any]):
    """가능한 클라이언트로 순차적 요청 시도"""
    last_err: Optional[Exception] = None
    for mode, client in _client_candidates():
        try:
            with client as c:
                resp = c.get(url, params=params)
                return mode, resp
        except Exception as e:
            last_err = e
            continue
    if last_err:
        raise last_err
    raise RuntimeError("No HTTP client candidates available")


def call_apt_rent_api(
    lawdcd: str,
    deal_ymd: str,
    page_no: int = 1,
    num_rows: int = 10,
    filters: Optional[Dict[str, Any]] = None,
):
    if not API_KEY:
        return {
            "status": "error",
            "message": "MOLIT_API_KEY is missing in .env",
        }

    # 아파트 전월세 조회 오퍼레이션
    url = f"{BASE_URL}/getRTMSDataSvcAptRent"
    
    params: Dict[str, Any] = {
        "serviceKey": API_KEY,
        "pageNo": page_no,
        "numOfRows": num_rows,
        "LAWD_CD": lawdcd,
        "DEAL_YMD": deal_ymd,
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
                "data": resp.json(),
                "note": "Apartment Rent Data"
            }
        except Exception:
            return {
                "status": "ok",
                "text": resp.text,
                "note": "Apartment Rent Data (Text Format)"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "request_url": url,
        }


@mcp.tool()
def getApartmentTrades(
    lawdcd: str,
    deal_ymd: str,
    pageNo: int = 1,
    numOfRows: int = 10,
    filters: Optional[Dict[str, Any]] = None,
):
    """
    [아파트 전월세 조회]
    오케스트레이터와의 호환성을 위해 함수 이름은 getApartmentTrades로 유지하지만,
    실제로는 '아파트 전월세' 데이터를 조회합니다.
    
    - lawdcd: 법정동코드 5자리 (예: 11110)
    - deal_ymd: 계약년월 YYYYMM (예: 202506)
    """
    return call_apt_rent_api(
        lawdcd=lawdcd,
        deal_ymd=deal_ymd,
        page_no=pageNo,
        num_rows=numOfRows,
        filters=filters
    )


@mcp.tool()
def ping():
    """헬스체크"""
    return {"status": "ok", "message": "Realestate (APT RENT ONLY) Server Pong"}


def main():
    try:
        names = [t.name for t in mcp._tools]
        print("[REALESTATE SERVER - APT RENT] tools:", names, flush=True)
    except Exception:
        pass
    mcp.run()


if __name__ == "__main__":
    main()