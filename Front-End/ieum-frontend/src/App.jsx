import React, { useState } from "react";
import MainPage from "./components/MainPage";
import RecommendationPage from "./components/RecommendationPage";
import ResultsPage from "./components/ResultsPage";
import LoadingPage from "./components/LoadingPage";
import { fetchRecommendations, fetchRegionDetail } from "./services/api";

function App() {
  // --- [1] 상태 관리 ---
  const [currentPage, setCurrentPage] = useState("main"); // main, analyzing, recommendation, results
  const [userProfile, setUserProfile] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  
  // 상세 분석 페이지용 데이터 상태
  const [searchData, setSearchData] = useState(null);
  const [resultData, setResultData] = useState(null);

  // 로딩 게이지 상태 (최초 전국 분석 시에만 사용)
  const [loadingStatus, setLoadingStatus] = useState({
    policies: { loading: false, completed: false },
    jobs: { loading: false, completed: false },
    realestate: { loading: false, completed: false },
    summary: { loading: false, completed: false },
  });

  // --- [2] 유틸리티 함수 ---

  // 로딩 게이지 애니메이션 실행 (25%씩 상승)
  const runLoadingSequence = async () => {
    const setStep = (step, isLoading, isDone) => {
      setLoadingStatus(prev => ({
        ...prev,
        [step]: { loading: isLoading, completed: isDone }
      }));
    };

    const steps = ["policies", "jobs", "realestate", "summary"];
    for (const step of steps) {
      setStep(step, true, false);
      await new Promise(r => setTimeout(r, 600)); // 0.6초 지연으로 시각적 피드백 제공
      setStep(step, false, true);
    }
  };

  // --- [3] 이벤트 핸들러 ---

  // (1) 메인 페이지: 조건 입력 후 '지역 찾기' 클릭
  const handleProfileSubmit = async (profileData) => {
    setUserProfile(profileData);
    setCurrentPage("analyzing"); // 4단계 로딩 화면으로 전환

    try {
      // API 호출과 애니메이션을 동시에 시작
      const apiPromise = fetchRecommendations(profileData);
      await runLoadingSequence(); 
      const data = await apiPromise;

      setRecommendations(data);
      setCurrentPage("recommendation"); // 분석 완료 후 추천 리스트로 이동
    } catch (error) {
      console.error("Ranking fetch error:", error);
      alert("데이터 분석 중 오류가 발생했습니다. 서버 상태를 확인해주세요.");
      setCurrentPage("main");
    }
  };

  // (2) 추천 페이지: 특정 지역 카드 클릭 (상세 페이지로 즉시 이동)
  const handleSelectRegion = async (regionCode) => {
    const selected = recommendations.find(r => r.regionCode === regionCode);
    if (!selected) return;

    // 🚀 수정된 부분: setCurrentPage("analyzing")을 호출하지 않음
    // 버튼 클릭 시 로딩창 없이 백그라운드에서 데이터를 즉시 가져옵니다.
    try {
      // 백엔드에 상세 데이터(GPT 리포트 포함) 요청
      const detailData = await fetchRegionDetail(regionCode, userProfile);

      // 데이터가 도착하면 바로 결과 페이지 데이터 세팅 후 전환
      setSearchData({ prompt: selected.regionName, regionCode: regionCode });
      setResultData(detailData);
      setCurrentPage("results"); 
    } catch (error) {
      console.error("Detail fetch error:", error);
      alert("상세 보고서를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.");
    }
  };

  // (3) 내비게이션 핸들러
  const handleBackToMain = () => {
    setCurrentPage("main");
    setRecommendations([]);
    setResultData(null);
  };

  const handleBackToRecommendations = () => {
    setCurrentPage("recommendation");
    setResultData(null);
  };

  // --- [4] 화면 렌더링 분기 ---
  return (
    <div className="App">
      {/* 1. 조건 입력 메인 화면 */}
      {currentPage === "main" && (
        <MainPage onSubmit={handleProfileSubmit} />
      )}
      
      {/* 2. 최초 분석 로딩 화면 (게이지 상승 효과) */}
      {currentPage === "analyzing" && (
        <LoadingPage 
          searchPrompt={userProfile?.job || "맞춤 정보"} 
          loadingStatus={loadingStatus} 
        />
      )}

      {/* 3. 추천 지역 카드(TOP 6) 리스트 화면 */}
      {currentPage === "recommendation" && (
        <RecommendationPage 
          userName={userProfile?.name} 
          recommendations={recommendations} 
          onSelectRegion={handleSelectRegion} 
          onBackToMain={handleBackToMain} 
        />
      )}

      {/* 4. 상세 결과 보고서 화면 (즉시 전환됨) */}
      {currentPage === "results" && searchData && resultData && (
        <ResultsPage
          searchData={searchData}
          resultData={resultData}
          onBackToMain={handleBackToMain}
          onBackToRecommendations={handleBackToRecommendations}
        />
      )}
    </div>
  );
}

export default App;