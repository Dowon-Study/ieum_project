// src/components/RecommendationPage.jsx
import React from "react";
import { motion } from "framer-motion"; // 애니메이션 효과 추가
import "./RecommendationPage.css";
import BackgroundPattern from "../assets/background.svg?react";

function RecommendationPage({
  userName,
  recommendations,
  onSelectRegion,
  onBackToMain,
}) {
  return (
    <div className="recommendation-container">
      {/* 뒤로가기 플로팅 버튼 */}
      <button
        className="back-fab fixed-top-left"
        onClick={onBackToMain}
        title="처음 화면으로 돌아가기"
      >
        ← 조건 다시 입력
      </button>

      <div className="recommendation-header">
        <motion.h1 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          🎉 {userName}님에게 딱 맞는 지역 TOP {recommendations.length}
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          빅데이터 분석 결과, 거주 가능성과 일자리 매칭률이 가장 높은 곳입니다.
        </motion.p>
      </div>

      <div className="cards-grid">
        {recommendations.map((item, index) => (
          <motion.div
            key={item.regionCode}
            className="region-card"
            onClick={() => onSelectRegion(item.regionCode)}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1, duration: 0.4 }}
            whileHover={{ y: -8, transition: { duration: 0.2 } }}
          >
            {/* 순위 배지 */}
            <div className="rank-badge">{index + 1}위</div>
            
            <div className="region-name">
              <h2>{item.regionName}</h2>
              <span className="region-code">적합 점수: {item.score}점</span>
            </div>

            {/* 통계 미리보기 섹션 (백엔드 데이터 바인딩) */}
            <div className="stats-preview">
              <div className="stat-item">
                <span className="label">🏠 예산 내 매물</span>
                <span className="value highlight">{item.houseCount}건</span>
              </div>
              
              <div className="stat-divider-vertical" />
              
              <div className="stat-item">
                <span className="label">💼 관련 일자리</span>
                <span className="value">{item.jobCount}개</span>
              </div>
              
              <div className="stat-divider-vertical" />
              
              <div className="stat-item">
                <span className="label">📜 관련 정책</span>
                <span className="value">{item.policyCount}개</span>
              </div>
            </div>

            <div className="card-footer">
              <span>상세 분석 보고서 보기</span>
              <span className="arrow">→</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* 배경 패턴 */}
      <div className="background-container">
        <BackgroundPattern />
      </div>

      {/* 인라인 스타일 유지 및 보강 */}
      <style jsx>{`
        .recommendation-container {
          padding: 60px 20px;
          text-align: center;
          max-width: 1200px;
          margin: 0 auto;
          min-height: 100vh;
          position: relative;
          z-index: 1;
        }
        .recommendation-header {
          margin-bottom: 50px;
        }
        .recommendation-header h1 {
          font-size: 2.5rem;
          color: #1a1a1a;
          margin-bottom: 15px;
          font-weight: 800;
        }
        .recommendation-header p {
          font-size: 1.1rem;
          color: #666;
        }
        .cards-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
          gap: 25px;
          padding: 10px;
        }
        .region-card {
          background: rgba(255, 255, 255, 0.9);
          backdrop-filter: blur(10px);
          border-radius: 24px;
          padding: 30px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
          cursor: pointer;
          position: relative;
          border: 1px solid rgba(100, 108, 255, 0.1);
          text-align: left;
        }
        .rank-badge {
          position: absolute;
          top: 0;
          left: 0;
          background: linear-gradient(135deg, #646cff 0%, #7c4dff 100%);
          color: white;
          padding: 10px 20px;
          font-weight: bold;
          border-bottom-right-radius: 24px;
          font-size: 0.9rem;
        }
        .region-name {
          margin-top: 20px;
          margin-bottom: 25px;
        }
        .region-name h2 {
          margin: 0;
          font-size: 1.6rem;
          color: #2c3e50;
          letter-spacing: -0.5px;
        }
        .region-code {
          font-size: 0.9rem;
          color: #646cff;
          font-weight: 600;
          margin-top: 5px;
          display: block;
        }
        .stats-preview {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: #fdfdff;
          padding: 20px;
          border-radius: 18px;
          margin-bottom: 25px;
          border: 1px solid #f0f0f5;
        }
        .stat-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          flex: 1;
        }
        .stat-divider-vertical {
          width: 1px;
          height: 30px;
          background: #eee;
        }
        .stat-item .label {
          font-size: 0.75rem;
          color: #888;
          margin-bottom: 6px;
        }
        .stat-item .value {
          font-size: 1.25rem;
          font-weight: 700;
          color: #333;
        }
        .card-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 0.95rem;
          color: #555;
          font-weight: 600;
          padding-top: 15px;
          border-top: 1px dashed #eee;
        }
        .card-footer .arrow {
          transition: transform 0.2s;
        }
        .region-card:hover .arrow {
          transform: translateX(5px);
        }
        .back-fab {
          position: fixed;
          top: 30px;
          left: 30px;
          z-index: 100;
          padding: 12px 20px;
          background: white;
          border: none;
          border-radius: 50px;
          box-shadow: 0 4px 15px rgba(0,0,0,0.1);
          cursor: pointer;
          font-weight: 600;
          transition: all 0.2s;
        }
        .back-fab:hover {
          background: #f0f0ff;
          transform: scale(1.05);
        }
      `}</style>
    </div>
  );
}

export default RecommendationPage;