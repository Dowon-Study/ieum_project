// src/services/api.js
const BASE_URL = "http://127.0.0.1:8003";

/**
 * 예산 문자열("2억", "50만원")을 정수(만원 단위)로 안전하게 변환하는 함수
 */
const parseBudgetValue = (val) => {
  if (val === undefined || val === null || val === "") return 0;
  
  let total = 0;
  // 숫자와 '억', '만'만 남기고 나머지 제거
  const cleaned = String(val).replace(/[^0-9억만]/g, "");

  try {
    if (cleaned.includes("억")) {
      const parts = cleaned.split("억");
      total += (parseInt(parts[0]) || 0) * 10000; // 1억 = 10,000만원
      if (parts[1]) {
        total += parseInt(parts[1].replace("만", "")) || 0;
      }
    } else {
      total = parseInt(cleaned.replace("만", "")) || 0;
    }
    
    return isNaN(total) ? 0 : total;
  } catch (e) {
    console.warn("Budget parsing error:", e);
    return 0;
  }
};

/**
 * [API 1] 통합 랭킹 가져오기 (6개 추천 지역 리스트)
 * 메인 페이지에서 '지역 찾기' 클릭 시 호출됩니다.
 */
export const fetchRecommendations = async (profile) => {
  if (!profile) throw new Error("사용자 프로필 정보가 누락되었습니다.");

  const payload = {
    user_interest: profile.job || "전체",
    policy_query: profile.policy || "청년 지원",
    budget: parseBudgetValue(profile.budget),
    rent_budget: parseBudgetValue(profile.rent_budget),
  };

  console.log("📤 [Ranking Request]:", payload);

  try {
    const response = await fetch(`${BASE_URL}/api/recommendation/integrated-ranking`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "추천 리스트 요청 실패");
    }

    const data = await response.json();

    // 백엔드 응답 구조에 맞춘 유연한 데이터 매핑
    const list = Array.isArray(data) ? data : (data.top_recommendations || []);
    
    return list.map(item => ({
      regionName: item.regionName || item.region_name,
      regionCode: item.regionCode || item.region_code,
      score: item.score || item.total_relevance_score,
      houseCount: item.houseCount ?? item.matched_data_counts?.available_house_count ?? 0,
      jobCount: item.jobCount ?? item.matched_data_counts?.job_posting_count ?? 0,
      policyCount: item.policyCount ?? item.matched_data_counts?.policy_count ?? 0
    }));
  } catch (error) {
    console.error("❌ fetchRecommendations Error:", error);
    throw error;
  }
};

/**
 * [API 2] 특정 지역 상세 데이터 가져오기 (GPT 분석 포함)
 * 추천 카드 클릭 시 호출되며, AI 분석 리포트(text)를 포함한 전체 데이터를 받아옵니다.
 */
export const fetchRegionDetail = async (regionCode, profile) => {
  if (!regionCode || !profile) throw new Error("지역 코드 또는 프로필 정보가 없습니다.");

  const payload = {
    regionCode: String(regionCode),
    user_interest: profile.job || "전체",
    policy_query: profile.policy || "청년 지원",
    budget: parseBudgetValue(profile.budget),
    rent_budget: parseBudgetValue(profile.rent_budget),
  };

  console.log("📤 [Detail Request for GPT]:", payload);

  try {
    const response = await fetch(`${BASE_URL}/api/recommendation/region-detail`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "상세 정보 요청 실패");
    }

    // 백엔드에서 조립된 { summary, jobs, realestate, policies } 구조를 반환
    const detailData = await response.json();
    console.log("📥 [Detail Response with AI Report]:", detailData);
    
    return detailData;
  } catch (error) {
    console.error("❌ fetchRegionDetail Error:", error);
    throw error;
  }
};