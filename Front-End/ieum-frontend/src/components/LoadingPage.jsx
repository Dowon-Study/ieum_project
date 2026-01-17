// src/components/LoadingPage.jsx
import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import AnimatedText from "./AnimatedText";
import AnimatedMap from "./AnimatedMap";
import "./LoadingPage.css";
import logo from "../assets/ieum_logo.svg";
import StatusIcon from "./StatusIcon";

function LoadingPage({ searchPrompt = null, loadingStatus = {} }) {
  const [progress, setProgress] = useState(0);
  const [completedCount, setCompletedCount] = useState(0);

  useEffect(() => {
    // 순서대로 단계 확인
    const steps = ["policies", "jobs", "realestate", "summary"];
    const completed = steps.filter((key) => loadingStatus[key]?.completed).length;
    
    setCompletedCount(completed);
    setProgress(completed * 25); // 4단계이므로 각 25%
  }, [loadingStatus]);

  const getStatusClass = (statusObj) => {
    if (statusObj?.completed) return "completed";
    if (statusObj?.loading) return "loading";
    return "waiting";
  };

  const getOverallMessage = () => {
    if (progress === 100) return "분석이 완료되었습니다! 결과를 불러옵니다.";
    if (progress === 0) return "데이터 수집 엔진을 가동합니다...";
    return `총 4단계 중 ${completedCount}단계 분석 완료`;
  };

  return (
    <div className="loading-container">
      <header className="header">
        <img src={logo} alt="ieum logo" className="logo" />
        <nav className="nav-links">
          <a href="#">서비스 소개</a>
          <a>|</a>
          <a href="#">도움말</a>
        </nav>
      </header>

      <main className="loading-content">
        <div className="text-area">
          <AnimatedText />

          {/* 검색어 표시 영역 */}
          {searchPrompt && (
            <div className="search-prompt-display">
              <p className="search-label">분석 대상 키워드:</p>
              <p className="search-prompt">"{searchPrompt}"</p>
            </div>
          )}

          {/* 진행률 게이지 영역 */}
          <div className="progress-section">
            <div className="progress-bar-container">
              <div className="progress-bar">
                <motion.div
                  className="progress-fill"
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.5, ease: "easeInOut" }}
                />
              </div>
              <div className="progress-text">{progress}%</div>
            </div>
            <p className="overall-status">{getOverallMessage()}</p>
          </div>

          {/* 데이터 수집 상황 패널 (CSS 연동) */}
          <div className="loading-status-panel">
            <h4>실시간 분석 현황</h4>
            <div className="status-list">
              {[
                { id: "policies", label: "맞춤형 청년 정책 매칭" },
                { id: "jobs", label: "희망 직무 일자리 분석" },
                { id: "realestate", label: "예산 내 주거 매물 필터링" },
                { id: "summary", label: "최적 거주 지역 종합 랭킹" },
              ].map((step) => {
                const currentStatus = getStatusClass(loadingStatus[step.id]);
                return (
                  <div key={step.id} className={`status-item ${currentStatus}`}>
                    <StatusIcon status={currentStatus} />
                    <div className="status-content">
                      <span className="status-label" style={{ fontSize: "1rem" }}>
                        {step.label}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="map-area">
          <AnimatedMap />
        </div>
      </main>
    </div>
  );
}

export default LoadingPage;