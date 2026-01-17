// src/components/MainPage.jsx
import React, { useState } from "react";
import "./MainPage.css";
import Modal from "./Modal";
import logo from "../assets/ieum_logo.svg";
import slogan from "../assets/slogan.svg";
import BackgroundPattern from "../assets/background.svg?react";

function MainPage({ onSubmit }) {
  // 사용자 프로필 상태
  const [profile, setProfile] = useState({
    name: "",
    age: "",
    gender: "",
    job: "",
    budget: "", // 총 예산
    rent_budget: "", // 월세 상한
    policy: "",
    car: "",
  });

  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false);
  const [isAboutModalOpen, setIsAboutModalOpen] = useState(false);

  // 입력값 변경 핸들러
  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfile((prev) => ({ ...prev, [name]: value }));
  };

  // 제출 핸들러 (이제 채팅창 없이 바로 분석 요청)
  const handleProfileSubmit = (e) => {
    e.preventDefault();

    // 유효성 검사
    if (!profile.name || !profile.age || !profile.budget) {
      alert("정확한 분석을 위해 이름, 나이, 예산은 꼭 입력해주세요!");
      return;
    }

    // 상위 컴포넌트(App.jsx)로 프로필 전달 -> 로딩/분석 시작
    onSubmit(profile);
  };

  return (
    <div className="main-container">
      {/* 헤더 */}
      <header className="header">
        <img src={logo} alt="ieum logo" className="logo" />
        <img src={slogan} alt="slogan" className="slogan" />
        <nav className="nav-links">
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              setIsAboutModalOpen(true);
            }}
          >
            서비스 소개
          </a>
          <a>|</a>
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              setIsHelpModalOpen(true);
            }}
          >
            도움말
          </a>
        </nav>
      </header>

      <main className="content">
        <h1>
          나의 새로운 시작은
          <br />
          어디서?
        </h1>
        <p>프로필을 입력하면 AI가 당신에게 딱 맞는 지역을 찾아드립니다.</p>

        <div className="center-interaction-area">
          <div className="profile-card fade-in">
            <div className="profile-header">
              <h3>👋 맞춤 추천을 위한 기본 정보</h3>
              <p>
                입력하신 정보 바탕으로 소멸 위험 지역 중 최적의 장소를
                분석합니다.
              </p>
            </div>

            <form
              onSubmit={handleProfileSubmit}
              className="profile-form-vertical"
            >
              <div className="input-group">
                <label>
                  이름 / 닉네임 <span className="required">*</span>
                </label>
                <input
                  name="name"
                  placeholder="홍길동"
                  value={profile.name}
                  onChange={handleProfileChange}
                  autoFocus
                />
              </div>

              <div className="input-group-row">
                <div className="input-half">
                  <label>
                    나이 <span className="required">*</span>
                  </label>
                  <input
                    name="age"
                    type="number"
                    placeholder="26"
                    value={profile.age}
                    onChange={handleProfileChange}
                  />
                </div>
                <div className="input-half">
                  <label>성별</label>
                  <select
                    name="gender"
                    value={profile.gender}
                    onChange={handleProfileChange}
                  >
                    <option value="">선택</option>
                    <option value="male">남성</option>
                    <option value="female">여성</option>
                  </select>
                </div>
              </div>

              <div className="input-group">
                <label>희망 직무 (일자리 검색용)</label>
                <input
                  name="job"
                  placeholder="예: IT 개발자, 간호사, 생산직"
                  value={profile.job}
                  onChange={handleProfileChange}
                />
              </div>

              <div className="input-group-row">
                <div className="input-half">
                  <label>
                    총 주거 예산 (전세/보증금){" "}
                    <span className="required">*</span>
                  </label>
                  <input
                    name="budget"
                    placeholder="예: 2억"
                    value={profile.budget}
                    onChange={handleProfileChange}
                  />
                </div>
                <div className="input-half">
                  <label>월세 희망 상한액</label>
                  <input
                    name="rent_budget"
                    placeholder="예: 50만원"
                    value={profile.rent_budget}
                    onChange={handleProfileChange}
                  />
                </div>
              </div>

              <div className="input-group">
                <label>관심 정책 키워드</label>
                <input
                  name="policy"
                  placeholder="예: 청년월세, 창업지원, 귀농"
                  value={profile.policy}
                  onChange={handleProfileChange}
                />
              </div>

              <button type="submit" className="profile-submit-btn-large">
                내 조건으로 지역 찾기 🔍
              </button>
            </form>
          </div>
        </div>

        <div className="background-container">
          <BackgroundPattern />
        </div>
      </main>

      {/* 모달 컴포넌트들 */}
      <Modal
        isOpen={isAboutModalOpen}
        onClose={() => setIsAboutModalOpen(false)}
        title="서비스 소개"
      >
        <p>
          <strong>'이음'은 지역 소멸 위기 지역과 당신을 연결합니다.</strong>
        </p>
        <p>
          단순히 유명한 도시가 아니라, 당신의 예산과 직무에 맞는 숨겨진 보석
          같은 지역을 데이터 기반으로 추천해 드립니다.
        </p>
      </Modal>

      <Modal
        isOpen={isHelpModalOpen}
        onClose={() => setIsHelpModalOpen(false)}
        title="도움말"
      >
        <p>
          <strong>어떻게 사용하나요?</strong>
        </p>
        <p>1. 본인의 예산과 희망 직무를 입력하세요.</p>
        <p>
          2. '지역 찾기' 버튼을 누르면 AI가 전국의 소멸 위험 지역을 분석합니다.
        </p>
        <p>
          3. 추천된 Top 5 지역 중 마음에 드는 곳을 선택하여 상세 정보를
          확인하세요.
        </p>
      </Modal>
    </div>
  );
}

export default MainPage;
// src/services/api.js
