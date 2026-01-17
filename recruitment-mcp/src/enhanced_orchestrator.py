# enhanced_orchestrator.py — 청소년정책 포함 확장 오케스트레이터
import asyncio
import json
from typing import Dict, Any, Optional

# 상대 import로 변경
from . import server
from . import realestate_server
from . import youth_policy_server

class EnhancedOrchestrator:
    """채용정보 + 부동산 + 청소년정책을 통합하는 확장된 오케스트레이터"""
    
    def __init__(self):
        self.recruitment_server = server
        self.realestate_server = realestate_server
        self.youth_policy_server = youth_policy_server
    
    def get_available_tools(self) -> Dict[str, list]:
        """사용 가능한 모든 도구 목록"""
        return {
            'recruitment': [
                {'name': 'listRecruitments', 'description': '공공기관 채용정보 목록 조회'},
                {'name': 'getRecruitmentDetail', 'description': '채용정보 상세 조회'},
                {'name': 'ping', 'description': '헬스체크'}
            ],
            'realestate': [
                {'name': 'getApartmentTrades', 'description': '아파트 실거래가 조회'},
                {'name': 'getOfficeTrades', 'description': '오피스텔 실거래가 조회'},
                {'name': 'getHouseTrades', 'description': '단독/다가구 실거래가 조회'},
                {'name': 'ping', 'description': '헬스체크'}
            ],
            'youth_policy': [
                {'name': 'searchYouthPolicies', 'description': '청소년정책 검색'},
                {'name': 'getYouthPolicyDetail', 'description': '청소년정책 상세 조회'},
                {'name': 'searchPoliciesByRegion', 'description': '지역별 청소년정책 검색'},
                {'name': 'searchPoliciesByKeywords', 'description': '키워드 기반 청소년정책 검색'},
                {'name': 'ping', 'description': '헬스체크'}
            ]
        }
    
    def call_recruitment_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """채용정보 서버 도구 호출"""
        try:
            if tool_name == 'listRecruitments':
                return {
                    "status": "success",
                    "server": "recruitment",
                    "tool": tool_name,
                    "result": self.recruitment_server.listRecruitments(**arguments)
                }
            elif tool_name == 'getRecruitmentDetail':
                return {
                    "status": "success", 
                    "server": "recruitment",
                    "tool": tool_name,
                    "result": self.recruitment_server.getRecruitmentDetail(**arguments)
                }
            elif tool_name == 'ping':
                return {
                    "status": "success",
                    "server": "recruitment", 
                    "tool": tool_name,
                    "result": self.recruitment_server.ping()
                }
            else:
                return {
                    "status": "error",
                    "server": "recruitment",
                    "tool": tool_name,
                    "message": f"알 수 없는 도구: {tool_name}"
                }
        except Exception as e:
            return {
                "status": "error",
                "server": "recruitment",
                "tool": tool_name,
                "message": str(e)
            }
    
    def call_realestate_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """부동산 서버 도구 호출"""
        try:
            if tool_name == 'getApartmentTrades':
                return {
                    "status": "success",
                    "server": "realestate",
                    "tool": tool_name,
                    "result": self.realestate_server.getApartmentTrades(**arguments)
                }
            elif tool_name == 'getOfficeTrades':
                return {
                    "status": "success",
                    "server": "realestate", 
                    "tool": tool_name,
                    "result": self.realestate_server.getOfficeTrades(**arguments)
                }
            elif tool_name == 'getHouseTrades':
                return {
                    "status": "success",
                    "server": "realestate",
                    "tool": tool_name, 
                    "result": self.realestate_server.getHouseTrades(**arguments)
                }
            elif tool_name == 'ping':
                return {
                    "status": "success",
                    "server": "realestate",
                    "tool": tool_name,
                    "result": self.realestate_server.ping()
                }
            else:
                return {
                    "status": "error",
                    "server": "realestate",
                    "tool": tool_name,
                    "message": f"알 수 없는 도구: {tool_name}"
                }
        except Exception as e:
            return {
                "status": "error",
                "server": "realestate",
                "tool": tool_name,
                "message": str(e)
            }
    
    def call_youth_policy_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """청소년정책 서버 도구 호출"""
        try:
            if tool_name == 'searchYouthPolicies':
                return {
                    "status": "success",
                    "server": "youth_policy",
                    "tool": tool_name,
                    "result": self.youth_policy_server.searchYouthPolicies(**arguments)
                }
            elif tool_name == 'getYouthPolicyDetail':
                return {
                    "status": "success",
                    "server": "youth_policy",
                    "tool": tool_name,
                    "result": self.youth_policy_server.getYouthPolicyDetail(**arguments)
                }
            elif tool_name == 'searchPoliciesByRegion':
                user_query = arguments.get('user_query')
                print(f"🔧 [ORCHESTRATOR-DEBUG] tool_name: {tool_name}")
                print(f"🔧 [ORCHESTRATOR-DEBUG] arguments: {arguments}")
                print(f"🔧 [ORCHESTRATOR-DEBUG] user_query 추출: '{user_query}'")

                return {
                    "status": "success",
                    "server": "youth_policy",
                    "tool": tool_name,
                    "result": self.youth_policy_server.searchPoliciesByRegion(
                        regionCode=arguments.get('regionCode'),
                        pageNum=arguments.get('pageNum', 1),
                        pageSize=arguments.get('pageSize', 50),
                        categories=arguments.get('categories'),
                        user_query=arguments.get('user_query')  # ⭐ 추가
                    )
                }

            # 2번째 수정  
            elif tool_name == 'searchPoliciesByKeywords':
                return {
                    "status": "success",
                    "server": "youth_policy",
                    "tool": tool_name,
                    "result": self.youth_policy_server.searchPoliciesByKeywords(
                        **arguments,
                        user_query=arguments.get('user_query')  # ⭐ 추가
                    )
                }

            elif tool_name == 'ping':
                return {
                    "status": "success",
                    "server": "youth_policy",
                    "tool": tool_name,
                    "result": self.youth_policy_server.ping()
                }
            else:
                return {
                    "status": "error",
                    "server": "youth_policy",
                    "tool": tool_name,
                    "message": f"알 수 없는 도구: {tool_name}"
                }
        except Exception as e:
            return {
                "status": "error",
                "server": "youth_policy",
                "tool": tool_name,
                "message": str(e)
            }
    
    def comprehensive_region_analysis(self, region_code: str, deal_ymd: str = "202506"):
        """지역 종합 분석 - 채용정보 + 부동산 + 청소년정책"""
        print(f"🔍 지역 종합 분석 시작: {region_code}")
        
        results = {}
        
        # 1. 채용정보 조회
        print("  📋 채용정보 조회 중...")
        recruitment_result = self.call_recruitment_tool(
            'listRecruitments',
            {'pageNo': 1, 'numOfRows': 10}
        )
        results['recruitment'] = recruitment_result
        
        # 2. 부동산 아파트 실거래가 조회
        print("  🏠 아파트 실거래가 조회 중...")
        apt_result = self.call_realestate_tool(
            'getApartmentTrades',
            {
                'lawdcd': region_code,
                'deal_ymd': deal_ymd,
                'pageNo': 1,
                'numOfRows': 5
            }
        )
        results['apartment_trades'] = apt_result
        
        # 3. 지역별 청소년정책 조회 (새로 추가!)
        print("  🎯 지역별 청소년정책 조회 중...")
        policy_result = self.call_youth_policy_tool(
            'searchPoliciesByRegion',
            {
                'regionCode': region_code,
                'pageNum': 1,
                'pageSize': 10,
                'categories': "일자리,주거,교육,복지"  # 주요 관심 분야
            }
        )
        results['youth_policies'] = policy_result
        
        # 4. 청년 특화 정책 검색
        print("  🚀 청년 특화 정책 검색 중...")
        youth_specific_result = self.call_youth_policy_tool(
            'searchPoliciesByKeywords',
            {
                'keywords': "청년,취업,창업,주거지원,생활비지원",
                'regionCode': region_code,
                'pageNum': 1,
                'pageSize': 8
            }
        )
        results['youth_specific_policies'] = youth_specific_result
        
        print("✅ 지역 종합 분석 완료")
        return results

    def analyze_living_feasibility(self, region_code: str, age_group: str = "청년"):
        """거주 타당성 분석 - 일자리, 주거비, 정책 지원 종합"""
        print(f"📊 {age_group} 거주 타당성 분석: {region_code}")
        
        results = {}
        
        # 1. 일자리 현황
        recruitment_result = self.call_recruitment_tool(
            'listRecruitments',
            {'pageNo': 1, 'numOfRows': 20}
        )
        results['job_market'] = recruitment_result
        
        # 2. 주거비 현황 (최근 6개월)
        months = ["202501", "202502", "202503", "202504", "202505", "202506"]
        housing_costs = []
        
        for month in months[-3:]:  # 최근 3개월만
            apt_result = self.call_realestate_tool(
                'getApartmentTrades',
                {
                    'lawdcd': region_code,
                    'deal_ymd': month,
                    'pageNum': 1,
                    'numOfRows': 10
                }
            )
            housing_costs.append({month: apt_result})
        
        results['housing_trends'] = housing_costs
        
        # 3. 정책 지원 현황
        if age_group == "청년":
            policy_keywords = "청년,취업지원,주거지원,창업지원,생활비지원"
        else:
            policy_keywords = "일자리,주거,복지,교육"
        
        policy_result = self.call_youth_policy_tool(
            'searchPoliciesByKeywords',
            {
                'keywords': policy_keywords,
                'regionCode': region_code,
                'pageNum': 1,
                'pageSize': 15
            }
        )
        results['policy_support'] = policy_result
        
        return results


def test_all_servers():
    """모든 서버 연결 테스트"""
    print("🏓 전체 서버 Ping 테스트...")
    orchestrator = EnhancedOrchestrator()
    
    servers = [
        ('recruitment', 'call_recruitment_tool'),
        ('realestate', 'call_realestate_tool'),
        ('youth_policy', 'call_youth_policy_tool')
    ]
    
    all_ok = True
    for server_name, method_name in servers:
        try:
            method = getattr(orchestrator, method_name)
            result = method('ping', {})
            if result['status'] == 'success':
                print(f"  ✅ {server_name} 서버: 연결됨")
            else:
                print(f"  ❌ {server_name} 서버: {result['message']}")
                all_ok = False
        except Exception as e:
            print(f"  ❌ {server_name} 서버: 연결 오류 - {str(e)}")
            all_ok = False
    
    return all_ok


def main():
    print("=" * 60)
    print("🚀 확장된 MCP 오케스트레이터 테스트")
    print("📍 채용정보 + 부동산 + 청소년정책 통합 플랫폼")
    print("=" * 60)
    
    # 1. 전체 서버 연결 테스트
    if not test_all_servers():
        print("❌ 일부 서버 연결 실패. 계속 진행...")
    
    # 2. 사용 가능한 도구 목록
    orchestrator = EnhancedOrchestrator()
    tools = orchestrator.get_available_tools()
    
    print("\n📋 사용 가능한 도구들:")
    for server_name, server_tools in tools.items():
        print(f"\n🔧 {server_name} 서버:")
        for tool in server_tools:
            print(f"  - {tool['name']}: {tool['description']}")
    
    # 3. 종합 분석 테스트
    print("\n" + "=" * 50)
    print("🚀 종로구 종합 분석 테스트")
    print("=" * 50)
    
    # 지역 종합 분석
    comprehensive_results = orchestrator.comprehensive_region_analysis(
        region_code="11110",  # 종로구
        deal_ymd="202506"
    )
    
    # 거주 타당성 분석
    print("\n" + "=" * 50)
    print("📊 청년 거주 타당성 분석")
    print("=" * 50)
    
    feasibility_results = orchestrator.analyze_living_feasibility(
        region_code="11110",
        age_group="청년"
    )
    
    # 4. 결과 저장
    all_results = {
        "comprehensive_analysis": comprehensive_results,
        "living_feasibility": feasibility_results
    }
    
    print(f"\n💾 전체 결과를 enhanced_results.json에 저장합니다...")
    with open('enhanced_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 확장된 플랫폼 테스트 완료! 🎉")
    print("📄 상세 결과는 enhanced_results.json 파일을 확인하세요.")


if __name__ == "__main__":
    main()