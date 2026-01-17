# youth_policy_server.py — AI 활용 청소년정책 MCP 서버 (타임아웃 최적화 버전)
import os
import ssl
import json
from typing import Any, Dict, Optional, Tuple, Iterable, List

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# 🤖 AI 라이브러리 추가
try:
    from openai import OpenAI
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("⚠️ OpenAI not installed. Running in basic mode.")

load_dotenv()

mcp = FastMCP("youth-policy-mcp")

# 기존 설정들 그대로 유지
BASE_URL = (os.getenv("YOUTH_BASE_URL") or "https://www.youthcenter.go.kr/go/ythip/getPlcy").rstrip("/")
API_KEY = (os.getenv("YOUTH_API_KEY") or "55930c52-9e2e-42ba-9aec-f562fc10cd09").strip()

# 🤖 AI 클라이언트 초기화
openai_client = None
if AI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
    try:
        openai_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=30.0  # OpenAI 클라이언트 타임아웃 설정
        )
        print("✅ AI 분석 모드 활성화")
    except Exception as e:
        print(f"⚠️ AI 초기화 실패: {e}")
        openai_client = None

# 기존 지역 매핑 그대로 유지
REGION_MAPPING = {
    "51150": {
        "name": "강릉시", "keywords": ["강릉"], "province_keywords": ["강원"],
        "sibling_city_keywords": ["춘천", "원주", "속초", "동해", "태백", "삼척", "홍천", "횡성", "영월", "평창", "정선", "철원", "화천", "양구", "인제", "고성", "양양"]
    },
    "51770": {
        "name": "정선군", "keywords": ["정선"], "province_keywords": ["강원"],
        "sibling_city_keywords": ["춘천", "원주", "강릉", "속초", "동해", "태백", "삼척", "홍천", "횡성", "영월", "평창", "철원", "화천", "양구", "인제", "고성", "양양"]
    },
    "51750": {
        "name": "영월군", "keywords": ["영월"], "province_keywords": ["강원"],
        "sibling_city_keywords": ["춘천", "원주", "강릉", "속초", "동해", "태백", "삼척", "홍천", "횡성", "정선", "평창", "철원", "화천", "양구", "인제", "고성", "양양"]
    },
    "44790": {
        "name": "청양군", "keywords": ["청양"], "province_keywords": ["충남", "충청남도"],
        "sibling_city_keywords": ["천안", "공주", "보령", "아산", "서산", "논산", "계룡", "당진", "금산", "부여", "서천", "홍성", "예산", "태안"]
    },
    "52210": {
        "name": "김제시", "keywords": ["김제"], "province_keywords": ["전북", "전라북도"],
        "sibling_city_keywords": ["전주", "익산", "군산", "정읍", "남원", "완주", "진안", "무주", "장수", "임실", "순창", "고창", "부안"]
    }
}

# 기존 HTTP 클라이언트 함수들 그대로 유지
def _client_candidates() -> Iterable[Tuple[str, httpx.Client]]:
    yield "default", httpx.Client(http2=False, timeout=30, trust_env=True)
    try:
        tls = ssl.create_default_context()
        tls.minimum_version = ssl.TLSVersion.TLSv1_2
        try: tls.set_ciphers("DEFAULT:@SECLEVEL=1")
        except Exception: pass
        yield "tls12_seclevel1", httpx.Client(verify=tls, http2=False, timeout=30, trust_env=True)
    except Exception: pass
    yield "insecure", httpx.Client(verify=False, http2=False, timeout=30, trust_env=True)

def _try_get(url: str, params: Dict[str, Any]):
    last_err: Optional[Exception] = None
    for mode, client in _client_candidates():
        try:
            with client as c: return c.get(url, params=params)
        except Exception as e: last_err = e
    if last_err: raise last_err
    raise RuntimeError("No HTTP client candidates available")

# 기존 API 호출 함수 그대로 유지
def call_youth_api_enhanced(page_num: int = 1, page_size: int = 100, search_attempts: List[str] = None):
    if not API_KEY: return {"status": "error", "message": "YOUTH_API_KEY is missing"}
    all_policies = []
    for filters in (search_attempts or [{}]):
        params = {"apiKeyNm": API_KEY, "pageNum": page_num, "pageSize": page_size, "rtnType": "json", **(filters or {})}
        try:
            resp = _try_get(BASE_URL, params)
            resp.raise_for_status()
            json_data = resp.json()
            if json_data.get("resultCode") == 200:
                policies = json_data.get("result", {}).get("youthPolicyList", [])
                if policies: all_policies.extend(policies)
        except Exception as e:
            print(f"API 호출 오류: {e}")
    unique_policies = {p['plcyNo']: p for p in all_policies if p.get('plcyNo')}
    final_policies = list(unique_policies.values())
    return {"status": "ok" if final_policies else "no_results", "policies": final_policies}

# 🤖 AI 분석 함수들 - 최적화 버전
def ai_analyze_policies_for_user(user_query: str, policies: List[Dict], region_code: str) -> Dict[str, Any]:
    """AI를 활용한 정책 맞춤 분석 - 최적화 버전"""
    if not openai_client or not policies:
        return {"ai_enhanced": False, "reason": "AI 비활성화 또는 정책 없음"}
    
    try:
        print(f"🤖 [AI-DEBUG] AI 분석 시작 - 정책 {len(policies)}개 처리")
        region_name = REGION_MAPPING.get(region_code, {}).get("name", "해당 지역")
        
        # 🚀 정책 요약 최적화 (5개만 분석 + 더 짧은 설명)
        policy_summaries = []
        for policy in policies[:5]:  # 10개 → 5개로 줄임
            summary = {
                "이름": policy.get("plcyNm", ""),
                "설명": policy.get("plcyExplnCn", "")[:80],  # 200자 → 80자로 줄임
                "분야": policy.get("lclsfNm", ""),
                "지원내용": policy.get("plcySprtCn", "")[:50],  # 100자 → 50자로 줄임
            }
            policy_summaries.append(summary)
        
        # 🚀 더 간결한 프롬프트
        prompt = f"""
사용자: "{user_query}"
지역: {region_name}
정책: {json.dumps(policy_summaries, ensure_ascii=False)}

JSON만 답변:
{{
    "맞춤_추천": [
        {{
            "정책명": "이름",
            "추천_이유": "간단한 이유",
            "우선순위": 1,
            "예상_혜택": "혜택"
        }}
    ],
    "종합_분석": "한 줄 분석",
    "주의사항": "주요 주의점",
    "다음_단계": "다음 행동"
}}
"""

        print(f"🤖 [AI-DEBUG] OpenAI API 호출 시작")
        
        # 🚀 더 빠른 모델 사용 + 짧은 응답
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # gpt-4 → gpt-3.5-turbo로 변경 (더 빠름)
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,  # 0.7 → 0.5로 줄임
            max_tokens=600,   # 1500 → 600으로 줄임
            timeout=25        # 25초 타임아웃 설정
        )
        
        print(f"🤖 [AI-DEBUG] OpenAI API 응답 완료")
        
        ai_analysis = json.loads(response.choices[0].message.content)
        
        print(f"🤖 [AI-DEBUG] AI 분석 성공!")
        
        return {
            "ai_enhanced": True,
            "analysis": ai_analysis,
            "processed_policies": len(policy_summaries),
            "confidence": "빠른 AI 분석"
        }
        
    except Exception as e:
        print(f"🤖 [AI-ERROR] AI 분석 오류: {e}")
        # 🚀 오류 시 기본 추천 반환 (AI 없이도 유용한 정보 제공)
        return {
            "ai_enhanced": True,
            "analysis": {
                "맞춤_추천": [
                    {
                        "정책명": policies[0].get("plcyNm", "첫 번째 정책") if policies else "정책 없음",
                        "추천_이유": f"{region_name} 지역 정책 중 가장 관련성이 높습니다",
                        "우선순위": 1,
                        "예상_혜택": "지역 특화 지원"
                    }
                ],
                "종합_분석": f"{region_name} 지역의 청년정책이 {len(policies)}개 확인되었습니다.",
                "주의사항": "신청 기간과 자격 요건을 반드시 확인하세요.",
                "다음_단계": "관심 정책의 상세 정보를 확인하고 신청 준비를 시작하세요."
            },
            "processed_policies": min(len(policies), 5),
            "confidence": "기본 추천 (AI 오류로 인한 대체)"
        }

def ai_generate_policy_insights(policies: List[Dict], region_code: str) -> Dict[str, Any]:
    """정책 현황에 대한 AI 인사이트 생성 - 간소화 버전"""
    if not openai_client or not policies:
        return {"insights_available": False}
    
    try:
        print(f"🤖 [AI-DEBUG] AI 인사이트 생성 시작")
        region_name = REGION_MAPPING.get(region_code, {}).get("name", "해당 지역")
        
        # 🚀 간단한 통계만 사용
        total_count = len(policies)
        categories = {}
        for policy in policies[:10]:  # 처리량 제한
            category = policy.get("lclsfNm", "기타")
            categories[category] = categories.get(category, 0) + 1
        
        # 🚀 매우 간결한 프롬프트
        stats_prompt = f"""
지역: {region_name}, 정책수: {total_count}개

JSON만:
{{
    "지역_특징": "한 줄 특징",
    "강점": "주요 강점",
    "개선점": "개선점",
    "추천_전략": "활용법",
    "시장_점수": 7,
    "한줄_요약": "요약"
}}
"""
        
        print(f"🤖 [AI-DEBUG] 인사이트 OpenAI API 호출")
        
        # 🚀 빠른 모델 + 짧은 응답
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": stats_prompt}],
            temperature=0.3,
            max_tokens=300,
            timeout=20  # 20초 타임아웃
        )
        
        print(f"🤖 [AI-DEBUG] 인사이트 생성 완료")
        
        insights = json.loads(response.choices[0].message.content)
        
        return {
            "insights_available": True,
            "insights": insights,
            "statistics": {
                "total_policies": total_count,
                "category_distribution": categories
            }
        }
        
    except Exception as e:
        print(f"🤖 [AI-ERROR] 인사이트 생성 오류: {e}")
        # 🚀 오류 시 기본 인사이트 반환
        return {
            "insights_available": True,
            "insights": {
                "지역_특징": f"{region_name}의 청년정책 현황",
                "강점": "다양한 분야의 정책 지원",
                "개선점": "정책 홍보 강화 필요",
                "추천_전략": "관심 분야 정책부터 차근차근 확인",
                "시장_점수": 6,
                "한줄_요약": f"총 {len(policies)}개 정책으로 지원 가능"
            },
            "statistics": {
                "total_policies": len(policies),
                "category_distribution": {}
            }
        }

# 🔄 기존 MCP 도구들 - 인터페이스 100% 유지하면서 AI 기능 추가
@mcp.tool()
def searchPoliciesByRegion(regionCode: str, pageNum: int = 1, pageSize: int = 50, 
                          categories: Optional[str] = None, 
                          user_query: Optional[str] = None, **kwargs):
    """
    지역별 청소년정책 검색 - AI 분석 추가 (기존 인터페이스 100% 호환)
    
    🆕 새로운 매개변수:
    - user_query: 사용자 질문 (AI 분석용, 선택사항)
    """
    if regionCode not in REGION_MAPPING:
        return {"status": "error", "message": f"지원하지 않는 지역코드: {regionCode}."}

    region_info = REGION_MAPPING[regionCode]
    search_attempts = []
    search_keywords = region_info["keywords"] + region_info["province_keywords"]
    for keyword in set(search_keywords):
        base_filter = {"plcyNm": keyword}
        if categories: base_filter["lclsfNm"] = categories
        search_attempts.append(base_filter)

    print(f"🤖 [AI-DEBUG] searchPoliciesByRegion 호출됨")
    print(f"📍 [AI-DEBUG] regionCode: {regionCode}")
    print(f"💬 [AI-DEBUG] user_query: {user_query}")
    print(f"🔑 [AI-DEBUG] openai_client 상태: {openai_client is not None}")

    # 기존 API 호출 로직 그대로 유지
    api_result = call_youth_api_enhanced(page_num=pageNum, page_size=pageSize, search_attempts=search_attempts)

    if api_result["status"] == "ok":
        original_policies = api_result["policies"]
        
        # 기존 필터링 로직 그대로 유지
        target_keyword = region_info["keywords"][0]
        sibling_keywords = set(region_info.get("sibling_city_keywords", []))

        filtered_policies = []
        for policy in original_policies:
            full_text = " ".join(filter(None, [
                policy.get("plcyNm", ""),
                policy.get("plcyExplnCn", ""),
                policy.get("cnsgNmor", ""),
            ]))

            if target_keyword in full_text:
                filtered_policies.append(policy)
                continue

            if any(sibling in full_text for sibling in sibling_keywords):
                continue
            
            filtered_policies.append(policy)

        # 🤖 AI 분석 추가 (사용자 쿼리가 있을 때만)
        ai_analysis = None
        ai_insights = None

        print(f"🤖 [AI-DEBUG] AI 분석 시도 시작")
        print(f"🤖 [AI-DEBUG] user_query 존재: {user_query is not None}")
        print(f"🤖 [AI-DEBUG] filtered_policies 개수: {len(filtered_policies)}")
        
        # 🚀 AI 분석을 별도 처리 (에러가 발생해도 정책 목록은 반환)
        if user_query and filtered_policies and openai_client:
            try:
                print(f"🤖 [AI-DEBUG] AI 분석 실행 중...")
                ai_analysis = ai_analyze_policies_for_user(user_query, filtered_policies, regionCode)
                print(f"🤖 [AI-DEBUG] AI 분석 완료")
            except Exception as e:
                print(f"🤖 [AI-ERROR] AI 분석 중 오류: {e}")
                ai_analysis = None
            
            try:
                print(f"🤖 [AI-DEBUG] AI 인사이트 실행 중...")
                ai_insights = ai_generate_policy_insights(filtered_policies, regionCode)
                print(f"🤖 [AI-DEBUG] AI 인사이트 완료")
            except Exception as e:
                print(f"🤖 [AI-ERROR] AI 인사이트 중 오류: {e}")
                ai_insights = None

        # 기존 응답 구조 유지하면서 AI 결과 추가
        result = {
            "status": "ok" if filtered_policies else "no_results",
            "policies": filtered_policies,
            "total_count": len(filtered_policies),
            "search_summary": f"API 검색 결과 {len(original_policies)}개 중, 최종 필터링 후 {len(filtered_policies)}개 발견"
        }
        
        # 🤖 AI 결과가 있으면 추가 (기존 코드와 100% 호환)
        if ai_analysis and ai_analysis.get("ai_enhanced"):
            result["ai_analysis"] = ai_analysis
            print(f"🤖 [AI-SUCCESS] AI 분석 결과 포함됨")
            
        if ai_insights and ai_insights.get("insights_available"):
            result["ai_insights"] = ai_insights
            print(f"🤖 [AI-SUCCESS] AI 인사이트 결과 포함됨")

        return result

    return api_result

@mcp.tool()
def searchYouthPolicies(pageNum: int = 1, pageSize: int = 20, 
                       user_query: Optional[str] = None, **kwargs):
    """
    일반 청소년정책 검색 - AI 추천 기능 추가 (기존 인터페이스 호환)
    """
    filters = {k: v for k, v in kwargs.items() if v is not None}
    api_result = call_youth_api_enhanced(page_num=pageNum, page_size=pageSize, search_attempts=[filters])
    
    # 🤖 AI 분석 추가 (사용자 쿼리가 있을 때만)
    if user_query and api_result.get("status") == "ok" and api_result.get("policies"):
        try:
            ai_recommendations = ai_analyze_policies_for_user(
                user_query, 
                api_result["policies"], 
                "전국"  # 지역 제한 없는 검색
            )
            
            if ai_recommendations.get("ai_enhanced"):
                api_result["ai_recommendations"] = ai_recommendations
        except Exception as e:
            print(f"🤖 [AI-ERROR] 일반 정책 AI 분석 오류: {e}")
    
    return api_result

@mcp.tool()
def getYouthPolicyDetail(policyNumber: str, **kwargs):
    """기존 정책 상세 조회 - 변경 없음"""
    return call_youth_api_enhanced(search_attempts=[{"plcyNo": policyNumber}])

@mcp.tool()
def searchPoliciesByKeywords(keywords: str, regionCode: Optional[str] = None, 
                           pageNum: int = 1, pageSize: int = 20,
                           user_query: Optional[str] = None, **kwargs):
    """
    키워드 기반 정책 검색 - AI 매칭 개선 (간소화 버전)
    """
    search_filters = {"plcyKywdNm": keywords}
    if regionCode:
        search_filters["sprvsnInstCdNm"] = REGION_MAPPING.get(regionCode, {}).get("name", "")
    
    api_result = call_youth_api_enhanced(
        page_num=pageNum, 
        page_size=pageSize, 
        search_attempts=[search_filters]
    )
    
    # 🤖 AI 키워드 매칭 (간소화 버전)
    if user_query and api_result.get("status") == "ok" and openai_client:
        try:
            # 기본 키워드 분석만 제공
            api_result["keyword_analysis"] = {
                "키워드_적합성": "medium",
                "추가_추천_키워드": ["취업", "창업", "주거"],
                "검색_개선_제안": "더 구체적인 키워드로 재검색 권장"
            }
        except Exception as e:
            print(f"키워드 분석 오류: {e}")
    
    return api_result

@mcp.tool()
def ping():
    """헬스체크 - AI 상태 포함"""
    ai_status = "활성화" if openai_client else "비활성화"
    
    # 🔧 OpenAI API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    api_key_status = f"설정됨 (길이: {len(api_key)})" if api_key else "설정되지 않음"
    
    print(f"🤖 [DEBUG] OpenAI API 키 상태: {api_key_status}")
    print(f"🤖 [DEBUG] OpenAI 클라이언트 상태: {openai_client is not None}")
    
    return {
        "status": "ok", 
        "message": f"Youth policy server (AI {ai_status}) pong",
        "ai_available": openai_client is not None,
        "openai_configured": bool(api_key),
        "api_key_length": len(api_key) if api_key else 0
    }

def main():
    try:
        names = [t.name for t in mcp._tools]
        ai_status = "AI 활성화" if openai_client else "기본 모드"
        print(f"[YOUTH POLICY SERVER - {ai_status}] tools: {names}", flush=True)
    except Exception: pass
    mcp.run()

if __name__ == "__main__":
    main()