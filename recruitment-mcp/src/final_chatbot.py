# perfect_chatbot.py — 완벽한 통합 챗봇 (정책 조회 + 날짜 필터링 + 5개 지역 한정)
import asyncio
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

# 확장된 오케스트레이터 import
from .enhanced_orchestrator import EnhancedOrchestrator

class PerfectChatbot:
    def __init__(self):
        self.orchestrator = EnhancedOrchestrator()

        # ✅ 이 챗봇은 아래 5개 지역만 지원합니다.
        # 정선군(51770), 영월군(51750), 청양군(44790), 강릉시(51150), 김제시(52210)
        self.allowed_regions_code_to_name = {
            "51770": "정선군",
            "51750": "영월군",
            "44790": "청양군",
            "51150": "강릉시",
            "52210": "김제시",
        }
        self.allowed_regions_name_to_code = {
            "정선": "51770", "정선군": "51770",
            "영월": "51750", "영월군": "51750",
            "청양": "44790", "청양군": "44790",
            "강릉": "51150", "강릉시": "51150",
            "김제": "52210", "김제시": "52210",
        }

        self.state = {
            "raw": False,
            "max_results": 10,
            "region_code": "44790",  # ✅ 기본: 청양군
            "deal_ymd": "202506",    # 기본: 2025년 6월
            "job_field": None        # 직무 분야 필터
        }

        # API 명세서의 정확한 직무 분야 매핑 (기존 코드 그대로)
        self.job_fields = {
            "사업관리": "R600001",
            "경영.회계.사무": "R600002",
            "금융.보험": "R600003",
            "교육.자연.사회과학": "R600004",
            "법률.경찰.소방.교도.국방": "R600005",
            "보건.의료": "R600006",
            "사회복지.종교": "R600007",
            "문화.예술.디자인.방송": "R600008",
            "운전.운송": "R600009",
            "영업판매": "R600010",
            "경비.청소": "R600011",
            "이용.숙박.여행.오락.스포츠": "R600012",
            "음식서비스": "R600013",
            "건설": "R600014",
            "기계": "R600015",
            "재료": "R600016",
            "화학": "R600017",
            "섬유.의복": "R600018",
            "전기.전자": "R600019",
            "정보통신": "R600020",
            "식품가공": "R600021",
            "인쇄.목재.가구.공예": "R600022",
            "환경.에너지.안전": "R600023",
            "농림어업": "R600024",
            "연구": "R600025"
        }

        # 직무 분야 키워드 매핑 (자연어 인식용)
        self.job_keywords = {
            "통신": "정보통신", "it": "정보통신", "개발": "정보통신", "프로그래밍": "정보통신",
            "의료": "보건.의료", "병원": "보건.의료", "간호": "보건.의료",
            "교육": "교육.자연.사회과학", "선생님": "교육.자연.사회과학", "강사": "교육.자연.사회과학",
            "경영": "경영.회계.사무", "회계": "경영.회계.사무", "사무": "경영.회계.사무",
            "건설": "건설", "건축": "건설",
            "연구": "연구"
        }
    
       # 🆕 가격 파싱 헬퍼 함수를 클래스 내에 추가
    def _parse_price_from_text(self, text: str) -> Optional[int]:
        # "이하", "까지" 등의 키워드가 있어야만 필터링
        if not any(keyword in text for keyword in ["이하", "까지", "안으로", "아래"]):
            return None
        
        # 2억, 3억 5천만 등을 처리
        if "억" in text:
            # "2억 5천만" 또는 "2억" 패턴
            match = re.search(r"(\d+)억(?:\s*(\d+)(?:천만|만))?", text)
            if match:
                eok = int(match.group(1))
                man = int(match.group(2)) if match.group(2) else 0
                if "천만" in text:
                    return eok * 10000 + man * 1000
                else:
                    return eok * 10000 + man
        
        # "5000만원" 패턴
        elif "만" in text:
            match = re.search(r"(\d+)만", text)
            if match:
                return int(match.group(1))
        
        return None

    def format_policy_category_clean(self, policy: Dict) -> str:
        """
        정책 카테고리 중복 제거 함수
        """
        large_category = policy.get("lclsfNm", "")
        medium_category = policy.get("mclsfNm", "")
        
        if large_category and medium_category:
            # 완전히 같은 경우
            if large_category.strip() == medium_category.strip():
                return large_category.strip()
            
            # 콤마로 구분된 경우 중복 제거
            large_parts = [part.strip() for part in large_category.split(',') if part.strip()]
            medium_parts = [part.strip() for part in medium_category.split(',') if part.strip()]
            
            unique_parts = []
            # 대분류 먼저 추가
            for part in large_parts:
                if part and part not in unique_parts:
                    unique_parts.append(part)
            
            # 중분류에서 중복되지 않는 것만 추가
            for part in medium_parts:
                if part and part not in unique_parts:
                    unique_parts.append(part)
            
            if len(unique_parts) == 1:
                return unique_parts[0]
            else:
                return " > ".join(unique_parts)
        
        elif large_category:
            parts = list(dict.fromkeys([part.strip() for part in large_category.split(',') if part.strip()]))
            return parts[0] if len(parts) == 1 else ", ".join(parts)
        
        elif medium_category:
            parts = list(dict.fromkeys([part.strip() for part in medium_category.split(',') if part.strip()]))
            return parts[0] if len(parts) == 1 else ", ".join(parts)
        
        else:
            return "기타"

    def print_help(self):
        print("""
🤖 통합 챗봇 명령어 가이드  (지원 지역: 정선·영월·청양·강릉·김제)

[자연어 검색]
  "강릉시 IT 일자리와 아파트 매물, 정책 알려줘"
  "영월군 의료 분야 채용공고와 실거래가 보여줘"
  "청양군 정책만 알려줘"
  "김제시 아파트 실거래가만 보여줘"

[설정 명령어]
  /region <코드|이름>              → 지역 설정 (예: /region 42150 또는 /region 강릉시)
  /date <YYYYMM>                   → 부동산 거래 년월 설정
  /jobs <숫자>                     → 채용정보 결과 개수 설정
  /field <분야명>                  → 직무 분야 설정
  /show                            → 현재 설정 보기
  /help                            → 도움말
  /exit                            → 종료

[지역 코드 참고]
  51770: 정선군    51750: 영월군    44790: 청양군
  51150: 강릉시    52210: 김제시
""".strip())

    def analyze_user_intent(self, user_input: str) -> Dict[str, Any]:
        """사용자 입력을 분석해서 의도 파악 (정책 검색 추가 + 지역 5개 한정)"""
        text = user_input.lower().replace(" ", "")

        intent = {
            "type": "unknown",
            "search_jobs": False,
            "search_realestate": False,
            "search_policies": False,
            "filters": {},
            "region_mentioned": None,
            "max_price": None
        }

        intent["max_price"] = self._parse_price_from_text(user_input)

        # ✅ 지역 감지: 5개 지역만
        region_mapping = {
            "정선": "51770", "정선군": "51770",
            "영월": "51750", "영월군": "51750",
            "청양": "44790", "청양군": "44790",
            "강릉": "51150", "강릉시": "51150",
            "김제": "52210", "김제시": "52210",
        }
        for region_name, code in region_mapping.items():
            if region_name in text:
                intent["region_mentioned"] = code
                break

        # 검색 유형 감지
        job_keywords = ["채용", "구인", "일자리", "취업", "인턴", "공채", "모집", "구직", "직장"]
        realestate_keywords = ["아파트", "부동산", "실거래가", "매매", "집", "주택", "오피스텔", "매물"]
        policy_keywords = ["정책", "지원", "혜택", "복지", "청년정책"]
        living_keywords = ["살곳", "살", "거주", "이사", "정착", "생활"]

        has_job = any(keyword in text for keyword in job_keywords)
        has_realestate = any(keyword in text for keyword in realestate_keywords + living_keywords)
        has_policy = any(keyword in text for keyword in policy_keywords)

        # 검색 유형 결정
        search_count = sum([has_job, has_realestate, has_policy])
        if search_count >= 2:
            intent["type"] = "comprehensive"
            intent["search_jobs"] = has_job
            intent["search_realestate"] = has_realestate
            intent["search_policies"] = has_policy
        elif has_job:
            intent["type"] = "jobs_only"
            intent["search_jobs"] = True
        elif has_realestate:
            intent["type"] = "realestate_only"
            intent["search_realestate"] = True
        elif has_policy:
            intent["type"] = "policies_only"
            intent["search_policies"] = True
        elif any(keyword in text for keyword in ["통합", "전체", "모든", "다"]):
            intent["type"] = "comprehensive"
            intent["search_jobs"] = True
            intent["search_realestate"] = True
            intent["search_policies"] = True

        # 채용 필터 감지 (기존과 동일)
        if "청년" in text and "인턴" in text:
            intent["filters"]["hireTypeLst"] = "R1050,R1060,R1070"
        elif "정규직" in text:
            intent["filters"]["hireTypeLst"] = "R1010"
        elif "계약직" in text or "비정규" in text:
            intent["filters"]["hireTypeLst"] = "R1040"

        if "학력무관" in text:
            intent["filters"]["acbgCondLst"] = "R7010"
        elif "대졸" in text or "4년제" in text:
            intent["filters"]["acbgCondLst"] = "R7050"

        # 직무 분야 필터 감지 (키워드 매핑 추가)
        detected_field = None
        for field_name, code in self.job_fields.items():
            if field_name in text:
                detected_field = code
                break
        if not detected_field:
            for keyword, field_name in self.job_keywords.items():
                if keyword in text and field_name in self.job_fields:
                    detected_field = self.job_fields[field_name]
                    break
        if detected_field:
            intent["filters"]["ncsCdLst"] = detected_field

                    # 🆕 채용구분 감지 추가
        if "신입" in text:
            intent["filters"]["recrutSeNm"] = "R2010"
        elif "경력" in text:
            intent["filters"]["recrutSeNm"] = "R2020"  
        elif "신입" in text and "경력" in text:
            intent["filters"]["recrutSeNm"] = "R2030"
        elif "외국인" in text:
            intent["filters"]["recrutSeNm"] = "R2040"

        return intent
    
    def get_region_name(self, region_code: str) -> str:
        """지역 코드를 지역명으로 변환(5개 한정)"""
        return self.allowed_regions_code_to_name.get(region_code, f"지원하지 않는 지역({region_code})")

    def filter_active_policies(self, policies: List[Dict]) -> List[Dict]:
        """현재 날짜 기준으로 유효한 정책만 필터링"""
        today = datetime.now().strftime("%Y%m%d")
        active_policies = []

        for policy in policies:
            is_active = True

            # 1. 사업 종료일 체크
            biz_end_date = policy.get("bizPrdEndYmd", "")
            if biz_end_date and len(biz_end_date) == 8 and biz_end_date.isdigit():
                if biz_end_date < today:
                    is_active = False
                    continue

            # 2. 신청 마감일 체크 (aplyYmd에서 종료일 추출)
            apply_period = policy.get("aplyYmd", "")
            if apply_period and " ~ " in apply_period:
                dates = apply_period.split(" ~ ")
                if len(dates) == 2:
                    end_date = dates[1].strip()
                    if len(end_date) == 8 and end_date.isdigit():
                        if end_date < today:
                            is_active = False
                            continue
            elif apply_period and len(apply_period) == 8 and apply_period.isdigit():
                if apply_period < today:
                    is_active = False
                    continue

            # 3. 상시 신청이거나 날짜 정보가 없으면 활성으로 간주
            if is_active:
                active_policies.append(policy)

        return active_policies

    def format_job_results(self, results: List[Dict], limit: int = 5, region_name: str = "") -> str:
        """채용정보 결과를 보기 좋게 포맷"""
        if not results:
            if region_name:
                return (f"📋 **{region_name} 지역의 채용정보를 찾을 수 없습니다.**\n\n"
                        f"💡 **제안:**\n- 인근 시·군으로 확장해보세요\n- 원격근무 가능한 직종을 찾아보세요")
            return "📋 채용정보를 찾을 수 없습니다."

        output = [f"📋 **채용정보** (총 {len(results)}건, 지역 관련성 순)\n"]

        for i, job in enumerate(results[:limit], 1):
            title = job.get("recrutPbancTtl", "제목 없음")
            company = job.get("instNm", "기관명 없음")
            hire_type = job.get("hireTypeNmLst", "")
            region = job.get("workRgnNmLst", "")
            deadline = job.get("pbancEndYmd", "")
            ncs_field = job.get("ncsCdNmLst", "")

            if deadline and len(deadline) == 8:
                deadline = f"{deadline[:4]}.{deadline[4:6]}.{deadline[6:]}"

            region_display = region
            if region:
                region_count = region.count(',') + 1
                if region_count >= 10:
                    region_display = f"전국 ({region_count}개 지역)"
                elif region_count > 3:
                    region_display = f"{region.split(',')[0]} 외 {region_count-1}개 지역"
                else:
                    region_display = region

            output.append(f"{'='*50}")
            output.append(f"📍 **{i}. {company}** ({hire_type})")
            output.append(f"📌 **{title}**")
            if region_display:
                output.append(f"🌍 **근무지역**: {region_display}")
            if deadline:
                output.append(f"⏰ **마감일**: {deadline}")
            if ncs_field:
                output.append(f"🔧 **직무분야**: {ncs_field}")
            output.append("")

        return "\n".join(output)

    def format_realestate_results(self, apt_data: List[Dict], limit: int = 5) -> str:
        """부동산 결과 포맷"""
        if not apt_data:
            return "🏠 부동산 거래 정보를 찾을 수 없습니다."

        output = [f"🏠 **아파트 실거래가** (총 {len(apt_data)}건 중 상위 {min(limit, len(apt_data))}건)\n"]

        for i, apt in enumerate(apt_data[:limit], 1):
            name = apt.get("aptNm", "아파트명 없음")
            price = apt.get("dealAmount", "가격정보없음")
            area = apt.get("excluUseAr", "면적정보없음")
            floor = apt.get("floor", "층수정보없음")
            year = apt.get("buildYear", "건축년도없음")
            dong = apt.get("umdNm", "동정보없음")

            if price and price.replace(",", "").isdigit():
                price_int = int(price.replace(",", ""))
                if price_int >= 10000:
                    eok = price_int // 10000
                    man = price_int % 10000
                    if man > 0:
                        price_formatted = f"{eok}억 {man:,}만원"
                    else:
                        price_formatted = f"{eok}억원"
                else:
                    price_formatted = f"{price_int:,}만원"
            else:
                price_formatted = price

            output.append(f"{i}. **{name}** ({dong})")
            output.append(f"   💰 {price_formatted} | {area}㎡ | {floor}층 | {year}년")
            output.append("")

        return "\n".join(output)

    def format_policy_results(self, policies: List[Dict], limit: int = 5, region_name: str = "") -> str:
        """청년정책 결과 포맷"""
        if not policies:
            if region_name:
                return f"📋 **{region_name} 지역의 청년정책을 찾을 수 없습니다.**"
            return "📋 청년정책을 찾을 수 없습니다."

        output = [f"📋 **청년정책** (총 {len(policies)}건, 지역 관련성 순)\n"]

        for i, policy in enumerate(policies[:limit], 1):
            name = policy.get("plcyNm", "정책명 없음")
            large_category = policy.get("lclsfNm", "")
            medium_category = policy.get("mclsfNm", "")

            category = self.format_policy_category_clean(policy)
                
            keywords = policy.get("plcyKywdNm", "")
            region = policy.get("sprvsnInstCdNm", "")
            explanation = policy.get("plcyExplnCn", "")

            policy_no = policy.get("plcyNo", "")
            detail_url = ""
            if policy_no:
                detail_url = f"https://www.youthcenter.go.kr/youthPolicy/ythPlcyTotalSearch/ythPlcyDetail/{policy_no}"

            zip_codes = policy.get('zipCd', '')
            if zip_codes:
                region_count = len(zip_codes.split(',')) if ',' in zip_codes else 1
                if region_count >= 50:
                    scope_display = f"전국 ({region_count}개 지역)"
                elif region_count > 10:
                    scope_display = f"광역 ({region_count}개 지역)"
                elif region_count > 1:
                    scope_display = f"다지역 ({region_count}개 지역)"
                else:
                    scope_display = "지역특화"
            else:
                scope_display = "범위미상"

            support_content = policy.get("plcySprtCn", "")
            business_start = policy.get("bizPrdBgngYmd", "")
            business_end = policy.get("bizPrdEndYmd", "")
            apply_period = policy.get("aplyYmd", "")
            support_scale = policy.get("sprtSclCnt", "")
            additional_conditions = policy.get("addAplyQlfcCndCn", "")
            participation_target = policy.get("ptcpPrpTrgtCn", "")
            apply_method = policy.get("plcyAplyMthdCn", "")

            def format_date(date_str):
                if date_str and len(date_str) == 8 and date_str.isdigit():
                    return f"{date_str[:4]}년 {date_str[4:6]}월 {date_str[6:]}일"
                return date_str

            def format_apply_period(apply_str):
                if not apply_str:
                    return ""
                if " ~ " in apply_str:
                    dates = apply_str.split(" ~ ")
                    if len(dates) == 2:
                        start_formatted = format_date(dates[0].strip())
                        end_formatted = format_date(dates[1].strip())
                        return f"{start_formatted} ~ {end_formatted}"
                return format_date(apply_str)

            business_period = ""
            if business_start and business_end:
                if business_start.strip() and business_end.strip() and business_start != "00000000" and business_end != "00000000":
                    business_period = f"{format_date(business_start)} ~ {format_date(business_end)}"
            elif business_start and business_start.strip() and business_start != "00000000":
                business_period = f"{format_date(business_start)} ~"
            elif business_end and business_end.strip() and business_end != "00000000":
                business_period = f"~ {format_date(business_end)}"

            output.append(f"{'='*60}")
            output.append(f"📍 **{i}. {name}**")

            if explanation:
                if len(explanation) > 200:
                    output.append(f"📝 **설명**: {explanation[:200]}...")
                else:
                    output.append(f"📝 **설명**: {explanation}")
                output.append("")

            output.append(f"📂 **분류**: {category}")
            output.append(f"🎯 **적용범위**: {scope_display}")
            if keywords:
                output.append(f"🏷️ **키워드**: {keywords}")
            if region:
                output.append(f"🌍 **담당기관**: {region}")
            if support_content:
                output.append(f"💰 **지원내용**: {support_content}")
            if business_period:
                output.append(f"📅 **사업 운영 기간**: {business_period}")

            if apply_period:
                formatted_apply_period = format_apply_period(apply_period)
                if formatted_apply_period:
                    output.append(f"📋 **사업 신청기간**: {formatted_apply_period}")

            if support_scale and support_scale != "0":
                output.append(f"👥 **지원 규모**: {support_scale}명")
            if apply_method:
                output.append(f"📝 **신청방법**: {apply_method}")
            if additional_conditions:
                output.append(f"📌 **추가 사항**: {additional_conditions}")
            if participation_target:
                output.append(f"🚫 **참여제한 대상**: {participation_target}")
            if detail_url:
                output.append(f"🔗 **상세링크**: {detail_url}")
            output.append("")

        return "\n".join(output)

    def filter_and_sort_jobs_by_region(self, jobs: List[Dict], target_region_code: str) -> List[Dict]:
        """채용정보를 지역 기준으로 '필터링' (도시 우선 → 없으면 광역)"""
        # 이름(강릉/청양/...)으로 들어왔을 때 코드로 변환
        if target_region_code and target_region_code in self.allowed_regions_name_to_code:
            target_region_code = self.allowed_regions_name_to_code[target_region_code]

        region_mapping = {
            "51770": {"city": "정선", "province": "강원"},
            "51750": {"city": "영월", "province": "강원"},
            "44790": {"city": "청양", "province": "충남"},  # 🔑 '충청' 제거
            "51150": {"city": "강릉", "province": "강원"},
            "52210": {"city": "김제", "province": "전북"},  # 🔑 '전라' 제거
        }

        if target_region_code not in region_mapping:
            return []

        city = region_mapping[target_region_code]["city"]
        province = region_mapping[target_region_code]["province"]

        def normalize(s: str) -> str:
            return (s or "").replace(" ", "")

        def match(job: Dict, keyword: str) -> bool:
            return keyword in normalize(job.get("workRgnNmLst", ""))

        # 1) 도시 필터
        city_jobs = [j for j in jobs if match(j, city)]
        if city_jobs:
            return city_jobs

        # 2) 도시 0건이면 광역 필터
        province_jobs = [j for j in jobs if match(j, province)]
        if province_jobs:
            return province_jobs

        # 3) 둘 다 없으면 빈 리스트
        return []


    def filter_and_sort_policies_by_region(self, policies: List[Dict], target_region_code: str) -> List[Dict]:
        """청년정책 지역 관련성 정렬 (5개 지역 전용)"""
        region_mapping = {
            "51770": ["정선", "강원"],
            "51750": ["영월", "강원"],
            "44790": ["청양", "충남", "충청"],
            "51150": ["강릉", "강원"],
            "52210": ["김제", "전북", "전라"],
        }

        if target_region_code not in region_mapping:
            return policies[:10]

        target_keywords = region_mapping[target_region_code]

        def calculate_policy_score(policy):
            institution = policy.get("sprvsnInstCdNm", "").replace(" ", "")
            zip_codes = policy.get('zipCd', '')
            region_count = len(zip_codes.split(',')) if zip_codes and ',' in zip_codes else 1
            relevance_score = 999
            for i, keyword in enumerate(target_keywords):
                if keyword in institution:
                    relevance_score = i
                    break
            if relevance_score == 999 and zip_codes:
                if target_region_code in zip_codes:
                    relevance_score = len(target_keywords)
            return (relevance_score, region_count)

        scored_policies = [(policy, calculate_policy_score(policy)) for policy in policies]
        sorted_policies = sorted(scored_policies, key=lambda x: x[1])
        result_policies = [policy for policy, score in sorted_policies]
        return result_policies

    async def handle_search(self, intent: Dict[str, Any]) -> str:
        """검색 의도에 따라 적절한 검색 수행 (정책 검색 + 날짜 필터링)"""
        region_code = intent.get("region_mentioned") or self.state["region_code"]

        # ✅ 지역 제한 검증
        if region_code not in self.allowed_regions_code_to_name:
            allowed_list = ", ".join([f"{name}({code})" for code, name in self.allowed_regions_code_to_name.items()])
            return f"❌ 지원하지 않는 지역입니다. 사용 가능 지역: {allowed_list}"

        region_name = self.get_region_name(region_code)
        results = []

        try:
            # 1) 채용정보
            if intent["search_jobs"]:
                print("📋 채용정보 검색 중...")
                job_result = self.orchestrator.call_recruitment_tool(
                    'listRecruitments',
                    {
                        'pageNo': 1,
                        'numOfRows': 100,
                        'filters': {**intent.get("filters", {}),
                                    **({} if self.state["job_field"] is None else {"ncsCdLst": self.state["job_field"]})}
                    }
                )
                if job_result["status"] == "success":
                    job_data = job_result["result"].get("data", {}).get("result", [])
                    job_data = self.filter_and_sort_jobs_by_region(job_data, region_code)
                    results.append(self.format_job_results(job_data, limit=5, region_name=region_name))
                else:
                    results.append(f"📋 채용정보 검색 실패: {job_result.get('message', '알 수 없는 오류')}")

            # 2) 부동산
            if intent["search_realestate"]:
                print("🏠 부동산 검색 중...")
                # ... (기존 call_realestate_tool 호출 코드) ...

                apt_result = self.orchestrator.call_realestate_tool(
                    'getApartmentTrades',
                    {
                        'lawdcd': region_code,
                        'deal_ymd': self.state["deal_ymd"],
                        'pageNo': 1,
                        'numOfRows': 30 # 필터링을 위해 충분한 데이터를 가져옵니다.
                    }
                )
                
                if apt_result["status"] == "success":
                    apt_text = apt_result["result"].get("text", "")
                    apt_data = self.parse_apartment_xml(apt_text)

                    # 🆕 최대 가격 필터링 로직 추가
                    max_price = intent.get("max_price")
                    if max_price:
                        original_count = len(apt_data)
                        apt_data = [
                            apt for apt in apt_data
                            if int(apt.get("dealAmount", "0").replace(",", "")) <= max_price
                        ]
                        print(f"💰 {max_price:,}만원 이하 매물 필터링: {original_count}건 -> {len(apt_data)}건")
                    
                    results.append(self.format_realestate_results(apt_data, limit=5))
                else:
                    results.append(f"🏠 부동산 검색 실패: {apt_result.get('message', '알 수 없는 오류')}")

            # 3) 청년정책
            if intent["search_policies"]:
                print("📋 청년정책 검색 중...")
                policy_result = self.orchestrator.call_youth_policy_tool(
                    'searchPoliciesByRegion',
                    {
                        'regionCode': region_code,
                        'pageNum': 1,
                        'pageSize': 30
                    }
                )
                if policy_result["status"] == "success":
                    policies = policy_result["result"].get("policies", [])
                    active_policies = self.filter_active_policies(policies)
                    active_policies = self.filter_and_sort_policies_by_region(active_policies, region_code)
                    active_policies = active_policies[:5]
                    results.append(self.format_policy_results(active_policies, limit=5, region_name=region_name))
                    if len(policies) > len(active_policies):
                        results.append(f"ℹ️ 총 {len(policies)}개 중 현재 신청 가능한 {len(active_policies)}개 정책을 표시했습니다.")
                else:
                    results.append(f"📋 청년정책 검색 실패: {policy_result.get('message', '알 수 없는 오류')}")

        except Exception as e:
            return f"❌ 검색 중 오류가 발생했습니다: {str(e)}"

        if results:
            return f"\n🔍 **{region_name} 검색 결과**\n\n" + "\n\n".join(results)
        else:
            return "❌ 검색 결과를 찾을 수 없습니다."

    def parse_apartment_xml(self, xml_text: str) -> List[Dict]:
        """XML 형태의 아파트 데이터를 파싱"""
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(xml_text)
            items = root.findall('.//item')
            apt_list = []
            for item in items:
                apt_data = {}
                for child in item:
                    apt_data[child.tag] = child.text.strip() if child.text else ""
                apt_list.append(apt_data)
            return apt_list
        except Exception as e:
            print(f"XML 파싱 오류: {e}")
            return []

    async def run(self):
        """챗봇 메인 실행 루프"""
        print("🤖 통합 정보 조회 플랫폼이 시작되었습니다!")
        print("💼 채용정보 + 🏠 부동산 + 📋 청년정책을 통합 검색할 수 있습니다.")
        print("⏰ 현재 신청 가능한 정책만 표시됩니다.\n")
        print("📍 지원 지역: 정선군(51770), 영월군(51750), 청양군(44790), 강릉시(51150), 김제시(52210)\n")

        # 직무 분야 안내
        print("📋 **검색 가능한 직무 분야:**")
        print("=" * 60)
        fields_list = list(self.job_fields.keys())
        for i in range(0, len(fields_list), 4):
            row = fields_list[i:i+4]
            print("  ".join(f"{field:<15}" for field in row))
        print("=" * 60)
        print("💡 예: '강릉시 통신 일자리', '영월군 의료 분야 채용' 등\n")

        self.print_help()

        while True:
            try:
                user_input = input("\n💬 > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 플랫폼을 종료합니다. 좋은 하루 되세요!")
                break

            if not user_input:
                continue

            # 명령어 처리
            if user_input.lower() in ["/exit", "exit", "quit", "종료"]:
                print("👋 플랫폼을 종료합니다. 좋은 하루 되세요!")
                break

            elif user_input.lower() in ["/help", "help", "도움말"]:
                self.print_help()
                continue

            elif user_input.lower() == "/show":
                print("📊 현재 설정:")
                print(f"  📍 지역: {self.get_region_name(self.state['region_code'])} ({self.state['region_code']})")
                print(f"  📅 거래년월: {self.state['deal_ymd']}")
                if self.state["job_field"]:
                    field_name = [k for k, v in self.job_fields.items() if v == self.state["job_field"]][0]
                    print(f"  🔧 직무분야: {field_name}")
                else:
                    print(f"  🔧 직무분야: 전체")
                continue

            elif user_input.startswith("/region "):
                raw = user_input.split(" ", 1)[1].strip()
                new_code = None
                # 코드로 입력
                if raw in self.allowed_regions_code_to_name:
                    new_code = raw
                # 이름으로 입력
                elif raw in self.allowed_regions_name_to_code:
                    new_code = self.allowed_regions_name_to_code[raw]

                if new_code:
                    self.state["region_code"] = new_code
                    region_name = self.get_region_name(new_code)
                    print(f"📍 지역이 {region_name}({new_code})로 설정되었습니다.")
                else:
                    allowed = ", ".join([f"{name}({code})" for code, name in self.allowed_regions_code_to_name.items()])
                    print(f"❌ 지원하지 않는 지역입니다. 사용 가능 지역: {allowed}")
                continue

            elif user_input.startswith("/date "):
                date = user_input.split(" ", 1)[1].strip()
                if len(date) == 6 and date.isdigit():
                    self.state["deal_ymd"] = date
                    print(f"📅 거래 년월이 {date}로 설정되었습니다.")
                else:
                    print("❌ 날짜 형식: YYYYMM (예: 202506)")
                continue

            elif user_input.startswith("/jobs "):
                try:
                    count = int(user_input.split(" ", 1)[1].strip())
                    self.state["max_results"] = min(count, 50)
                    print(f"📊 채용정보 결과 개수가 {self.state['max_results']}개로 설정되었습니다.")
                except:
                    print("❌ 사용법: /jobs <숫자> (예: /jobs 10)")
                continue

            elif user_input.startswith("/field "):
                field_name = user_input.split(" ", 1)[1].strip()
                if field_name in self.job_fields:
                    self.state["job_field"] = self.job_fields[field_name]
                    print(f"🔧 직무 분야가 '{field_name}'로 설정되었습니다.")
                elif field_name == "전체":
                    self.state["job_field"] = None
                    print("🔧 직무 분야 필터가 해제되었습니다.")
                else:
                    print("❌ 사용 가능한 분야 일부:")
                    fields = list(self.job_fields.keys())[:12]
                    for i in range(0, len(fields), 3):
                        row = fields[i:i+3]
                        print("  ".join(f"{field:<20}" for field in row))
                    print("💡 사용법: /field <분야명> 또는 /field 전체")
                continue

            # 자연어 검색 처리
            intent = self.analyze_user_intent(user_input)
            print(f"🔍 분석된 의도: {intent['type']}")

            if intent["type"] == "unknown":
                print("🤔 무엇을 도와드릴까요? 예: '강릉시에서 통신 일자리와 아파트 매물, 정책 알려줘'")
                continue

            # 검색 실행
            result = await self.handle_search(intent)
            print(result)


async def main():
    chatbot = PerfectChatbot()
    await chatbot.run()


if __name__ == "__main__":
    asyncio.run(main())
