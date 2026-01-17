// src/components/ResultsPage.jsx - 최종 수정 버전

import React, { useState, useMemo, useRef, useEffect } from "react";
import "./ResultsPage.css";

import briefcaseIcon from "../assets/briefcase.svg";
import homeIcon from "../assets/home.svg";
import docIcon from "../assets/document-text.svg";
import arrowDownIcon from "../assets/arrow-down.svg";
import koreaMap from "../assets/south_korea.svg";
import bgImg from "../assets/background.svg";

import hospitalIcon from "../assets/hospital.svg"; // 병원
import pillIcon from "../assets/pill.svg"; // 약국
import convIcon from "../assets/conv.svg"; // 편의점

function ResultsPage({
  searchData,
  resultData,
  onBackToMain,
  onBackToRecommendations,
}) {
  const [activeTab, setActiveTab] = useState("summary");
  const containerRef = useRef(null); // 스냅 컨테이너
  const analysisRef = useRef(null); // 분석결과 섹션
  const [page, setPage] = useState(0); // 0: 히어로, 1: 분석
  const animatingRef = useRef(false); // 전환 진행 중 여부
  const tabContentRef = useRef(null);

  const scrollToAnalysis = () => goTo(1, 1100);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !analysisRef.current) return;

    // 내부 스크롤은 그대로 두고, 섹션 전환 때만 개입
    const onWheel = (e) => {
      if (isInsideMap(e.target) || isScrollableArea(e.target, e.deltaY)) return;
      e.preventDefault();
      if (animatingRef.current) return;

      if (e.deltaY > 0 && page === 0) goTo(1, 1100);
      else if (e.deltaY < 0 && page === 1) goTo(0, 1100);
    };

    const onKey = (e) => {
      if (isScrollableArea(document.activeElement || e.target)) return;
      if (["ArrowDown", "PageDown", " "].includes(e.key)) {
        e.preventDefault();
        if (page === 0) goTo(1, 1100);
      }
      if (["ArrowUp", "PageUp"].includes(e.key)) {
        e.preventDefault();
        if (page === 1) goTo(0, 1100);
      }
    };

    container.addEventListener("wheel", onWheel, { passive: false });
    container.addEventListener("keydown", onKey);
    return () => {
      container.removeEventListener("wheel", onWheel);
      container.removeEventListener("keydown", onKey);
    };
  }, [page]);

  useEffect(() => {
    const el = tabContentRef.current;
    if (!el) return;
    // 탭 전환 시 항상 최상단
    el.scrollTop = 0;
    el.querySelectorAll("[data-reset-on-tab]").forEach((node) => {
      node.scrollTop = 0;
    });
  }, [activeTab]);

  const mapRef = useRef(null);

  // 지도와 마커 저장용 ref
  const mapInstanceRef = useRef(null);
  const markersRef = useRef({});

  const highlightMarker = (aptNm, on = true) => {
    const entry = markersRef.current[aptNm];
    if (!entry) return;
    entry.marker.setZIndex(on ? 999 : 0);
  };

  // 주변시설 검색 함수 ref
  const searchNearbyRef = useRef(null);

  // 부드러운 컨테이너 스크롤
  const smoothScrollTo = (targetY, duration = 1100, onDone) => {
    const el = containerRef.current;
    if (!el) return;
    const startY = el.scrollTop;
    const diff = targetY - startY;
    let start;
    const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);
    const step = (ts) => {
      if (!start) start = ts;
      const p = Math.min((ts - start) / duration, 1);
      el.scrollTop = startY + diff * easeOutCubic(p);
      if (p < 1) requestAnimationFrame(step);
      else onDone && onDone();
    };
    requestAnimationFrame(step);
  };

  // 컨테이너 기준 Y 좌표
  const getTop = (el, container) => {
    const cTop = container.getBoundingClientRect().top;
    const eTop = el.getBoundingClientRect().top;
    return container.scrollTop + (eTop - cTop);
  };

  // 섹션 인덱스로 전환
  const goTo = (index, duration = 1100) => {
    if (!containerRef.current || animatingRef.current) return;
    const y =
      index === 0 ? 0 : getTop(analysisRef.current, containerRef.current);
    animatingRef.current = true;
    smoothScrollTo(y, duration, () => {
      animatingRef.current = false;
      setPage(index);
    });
  };

  // 맵 컨테이너 내부 검사
  const isInsideMap = (node) => {
    const el = mapRef.current;
    return !!(el && (node === el || el.contains(node)));
  };

  // 내부 스크롤 영역 판별
  const isScrollableArea = (node, dy = 0) => {
    const container = containerRef.current;
    while (node && node !== container) {
      const style = window.getComputedStyle(node);
      const canScroll = /(auto|scroll)/.test(style.overflowY);
      if (canScroll && node.scrollHeight > node.clientHeight) {
        const atTop = node.scrollTop <= 0;
        const atBottom =
          Math.ceil(node.scrollTop + node.clientHeight) >= node.scrollHeight;
        if (!atTop && !atBottom) return true;
        if (atTop && dy < 0) return false;
        if (atBottom && dy > 0) return false;
        return true;
      }
      node = node.parentElement;
    }
    return false;
  };

  const handlePropertyClick = (aptNm) => {
    const map = mapInstanceRef.current;
    const target = markersRef.current[aptNm];
    if (!map || !target) return;
    map.setCenter(target.coords);
    target.infowindow.open(map, target.marker);
    if (searchNearbyRef.current) {
      searchNearbyRef.current(target.coords);
    }
  };

  const formatPrice = (priceStr) => {
    if (!priceStr) return "가격 정보 없음";
    const price = priceStr.replace(/,/g, "");
    if (isNaN(price)) return priceStr;
    const priceNum = parseInt(price, 10);
    if (priceNum >= 10000) {
      const eok = Math.floor(priceNum / 10000);
      const man = priceNum % 10000;
      return man > 0 ? `${eok}억 ${man.toLocaleString()}만원` : `${eok}억원`;
    }
    return `${priceNum.toLocaleString()}만원`;
  };

  useEffect(() => {
    if (activeTab !== "realestate") return;
    if (!mapRef.current || !window.kakao) return;

    const { kakao } = window;

    const map = new kakao.maps.Map(mapRef.current, {
      center: new kakao.maps.LatLng(37.5665, 126.978),
      level: 6,
    });
    mapInstanceRef.current = map;

    const geocoder = new kakao.maps.services.Geocoder();
    const places = new kakao.maps.services.Places();
    const items = resultData.realestate?.properties || [];
    if (items.length === 0) return;

    // 주변시설 마커 관리
    const facilityMarkers = [];
    const clearFacilityMarkers = () => {
      facilityMarkers.forEach((m) => m.setMap(null));
      facilityMarkers.length = 0;
    };

    // 커스텀 아이콘
    const ICON_SIZE = 24;
    const markerSize = new kakao.maps.Size(ICON_SIZE, ICON_SIZE);
    const markerOffset = new kakao.maps.Point(ICON_SIZE / 2, ICON_SIZE);

    const CATEGORY_ICON_URLS = {
      병원: hospitalIcon,
      약국: pillIcon,
      편의점: convIcon,
    };

    const getFacilityMarkerImage = (keyword) => {
      const url = CATEGORY_ICON_URLS[keyword] || convIcon;
      return new kakao.maps.MarkerImage(url, markerSize, {
        offset: markerOffset,
      });
    };

    // 주변시설 검색
    searchNearbyRef.current = (coords) => {
      clearFacilityMarkers();
      const categories = ["병원", "편의점", "약국"];
      categories.forEach((keyword) => {
        places.keywordSearch(
          keyword,
          (results, status) => {
            if (status === kakao.maps.services.Status.OK) {
              results.forEach((place) => {
                const facilityMarker = new kakao.maps.Marker({
                  position: new kakao.maps.LatLng(place.y, place.x),
                  map,
                  image: getFacilityMarkerImage(keyword),
                });
                facilityMarkers.push(facilityMarker);

                const info = new kakao.maps.InfoWindow({
                  content: `<div style="padding:5px;font-size:12px;">${place.place_name}</div>`,
                });

                kakao.maps.event.addListener(facilityMarker, "click", () => {
                  info.open(map, facilityMarker);
                  map.setCenter(coords);
                });
              });
            }
          },
          { location: coords, radius: 1000 }
        );
      });
    };

    // 첫 매물 중심
    const firstProperty = items[0];
    const firstQuery = `${firstProperty.estateAgentSggNm || ""} ${
      firstProperty.umdNm || ""
    }`.trim();
    if (firstQuery) {
      geocoder.addressSearch(firstQuery, (result, status) => {
        if (status === kakao.maps.services.Status.OK) {
          const coords = new kakao.maps.LatLng(result[0].y, result[0].x);
          map.setCenter(coords);
        }
      });
    }

    // 아파트 마커
    items.slice(0, 20).forEach((property) => {
      const query = `${property.estateAgentSggNm || ""} ${
        property.umdNm || ""
      } ${property.jibun || ""}`.trim();
      geocoder.addressSearch(query, (result, status) => {
        if (status === kakao.maps.services.Status.OK) {
          const coords = new kakao.maps.LatLng(result[0].y, result[0].x);
          const marker = new kakao.maps.Marker({ position: coords, map });
          const infowindow = new kakao.maps.InfoWindow({
            content: `<div style="padding:5px;font-size:12px;">
                        ${property.aptNm || "아파트"}<br/>
                        ${formatPrice(property.dealAmount)}
                      </div>`,
          });
          kakao.maps.event.addListener(marker, "click", () => {
            infowindow.open(map, marker);
            map.setCenter(coords);
          });
          markersRef.current[property.aptNm] = { marker, infowindow, coords };
        }
      });
    });
  }, [activeTab, resultData.realestate]);

  // 데이터 안전성 검증
  const hasValidData = (data) =>
    data && typeof data === "object" && data.success === true;
  const hasArrayData = (data, arrayKey) =>
    hasValidData(data) &&
    Array.isArray(data[arrayKey]) &&
    data[arrayKey].length > 0;

  // 탭별 상태
  const tabStatus = useMemo(() => {
    return {
      summary: {
        hasData: hasValidData(resultData?.summary),
        isEmpty:
          !hasValidData(resultData?.summary) ||
          (resultData?.summary?.summary?.total_jobs === 0 &&
            resultData?.summary?.summary?.total_properties === 0 &&
            resultData?.summary?.summary?.total_policies === 0),
        error:
          resultData?.summary?.success === false
            ? "종합 분석 데이터를 불러올 수 없습니다."
            : null,
      },
      jobs: {
        hasData: hasArrayData(resultData?.jobs, "jobs"),
        isEmpty:
          hasValidData(resultData?.jobs) &&
          (!resultData?.jobs?.jobs || resultData?.jobs?.jobs.length === 0),
        error:
          resultData?.jobs?.success === false
            ? "일자리 정보를 불러올 수 없습니다."
            : null,
      },
      realestate: {
        hasData: hasArrayData(resultData?.realestate, "properties"),
        isEmpty:
          hasValidData(resultData?.realestate) &&
          (!resultData?.realestate?.properties ||
            resultData?.realestate?.properties.length === 0),
        error:
          resultData?.realestate?.success === false
            ? "부동산 정보를 불러올 수 없습니다."
            : null,
      },
      policies: {
        hasData: hasArrayData(resultData?.policies, "policies"),
        isEmpty:
          hasValidData(resultData?.policies) &&
          (!resultData?.policies?.policies ||
            resultData?.policies?.policies.length === 0),
        error:
          resultData?.policies?.success === false
            ? "정책 정보를 불러올 수 없습니다."
            : null,
      },
    };
  }, [resultData]);

  const handleTabChange = (tabName) => setActiveTab(tabName);

  const getTabButtonClass = (tabName) => {
    let className = "tab-button";
    if (activeTab === tabName) className += " active";
    const status = tabStatus[tabName];
    if (status.error) className += " error";
    else if (status.isEmpty) className += " empty";
    else if (status.hasData) className += " success";
    return className;
  };

  const getTabIcon = (tabName) => {
    const status = tabStatus[tabName];
    if (status.error) return "";
    if (status.isEmpty) return "";
    if (status.hasData) return "";
    return "";
  };

  const formatDate = (dateStr) => {
    if (!dateStr || dateStr.length !== 8) return dateStr;
    return `${dateStr.slice(0, 4)}.${dateStr.slice(4, 6)}.${dateStr.slice(
      6,
      8
    )}`;
  };

  // 요약 탭
  // ResultsPage.jsx 내의 renderSummaryTab 함수 수정 버전

const renderSummaryTab = () => {
  const status = tabStatus.summary;
  if (status.error) return <div className="error-state">{status.error}</div>;
  if (!status.hasData)
    return <div className="no-data">종합 분석 데이터를 준비 중입니다...</div>;

  const summary = resultData.summary.summary || {};
  const regionInfo = resultData.summary.region_info || {};
  const preview = resultData.summary.preview_data || {};

  return (
    <div className="summary-tab-wrapper">
      {/* 1. 상단 지역 타이틀 및 AI 리포트 */}
      <div className="summary-header-card">
        <div className="region-badge">RECOMMENDED REGION</div>
        <h3 className="summary-region-title">
          <span>{regionInfo.name || summary.region_name}</span> 정착 분석 리포트
        </h3>
        <div className="ai-report-box">
          <p className="ai-report-text">
            {summary.text || "데이터 분석 중입니다..."}
          </p>
        </div>
      </div>

      {/* 2. 주요 지표 요약 (대시보드 형태) */}
      <div className="summary-stats-grid">
        <div className="stat-item job">
          <div className="stat-label">맞춤 일자리</div>
          <div className="stat-value">{summary.total_jobs}<span>건</span></div>
          <div className="stat-desc">의료/보건 분야 집중</div>
        </div>
        <div className="stat-item property">
          <div className="stat-label">평균 매매/전세</div>
          <div className="stat-value">52<span>건</span></div>
          <div className="stat-desc">가남읍/점봉동 중심</div>
        </div>
        <div className="stat-item policy">
          <div className="stat-label">청년 지원정책</div>
          <div className="stat-value">{summary.total_policies}<span>건</span></div>
          <div className="stat-desc">주거/금융 지원 혜택</div>
        </div>
      </div>

      {/* 3. 섹션별 퀵 프리뷰 (가로 배치) */}
      <div className="preview-sections">
        {/* 추천 일자리 프리뷰 */}
        <div className="preview-column">
          <h5><img src={briefcaseIcon} alt="" /> 추천 채용공고</h5>
          <div className="preview-list">
            {resultData.jobs?.jobs?.slice(0, 2).map((job, i) => (
              <div key={i} className="mini-card">
                <span className="mini-tag">{job.hireTypeNmLst}</span>
                <h6>{job.instNm}</h6>
                <p>{job.recrutPbancTtl}</p>
              </div>
            ))}
          </div>
        </div>

        {/* 추천 매물 프리뷰 */}
        <div className="preview-column">
          <h5><img src={homeIcon} alt="" /> 실거래 정보</h5>
          <div className="preview-list">
            {resultData.realestate?.properties?.slice(0, 2).map((prop, i) => (
              <div key={i} className="mini-card">
                <span className="mini-tag price">{prop.dealAmount}</span>
                <h6>{prop.aptNm}</h6>
                <p>{prop.umdNm} · {prop.excluUseAr}㎡</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

  // 일자리 탭
 // ResultsPage.jsx 내의 renderJobsTab 함수 수정

const renderJobsTab = () => {
  const status = tabStatus.jobs;
  if (status.error) return <div className="error-state">{status.error}</div>;
  if (status.isEmpty) return (
    <div className="no-data">
      <p><strong>해당 지역의 채용정보를 찾을 수 없습니다.</strong></p>
      <p>인근 시·군으로 탐색 범위를 넓혀보시는 것을 추천합니다.</p>
    </div>
  );
  if (!status.hasData) return <div className="loading-state">일자리 정보를 불러오는 중...</div>;

  const jobs = resultData.jobs.jobs || [];
  const stats = resultData.jobs.statistics || {};
  const regionName = resultData.jobs.region_info?.name || "";

  // 날짜 포맷팅 및 D-Day 계산 함수
  const getDDay = (dateStr) => {
    if (!dateStr) return null;
    const targetDate = new Date(`${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`);
    const today = new Date();
    const diff = Math.ceil((targetDate - today) / (1000 * 60 * 60 * 24));
    return diff === 0 ? "오늘마감" : diff > 0 ? `D-${diff}` : "마감";
  };

  return (
    <div className="jobs-tab-wrapper">
      {/* 1. 상단 채용 통계 보드 */}
      <div className="jobs-stats-board">
        <div className="stat-card">
          <span className="label">탐색된 공고</span>
          <span className="value">{stats.total || jobs.length}<span>건</span></span>
        </div>
        <div className="stat-card">
          <span className="label">신규 등록</span>
          <span className="value">3<span>건</span></span>
        </div>
        <div className="stat-card">
          <span className="label">주요 직무</span>
          <span className="value-text">보건/의료</span>
        </div>
      </div>

      <div className="jobs-header">
        <h4>{regionName} 채용 공고 리스트</h4>
        <div className="jobs-filter-info">추천순 | 마감임박순</div>
      </div>

      {/* 2. 현대적인 채용 카드 그리드 */}
      <div className="jobs-grid">
        {jobs.map((job, index) => {
          const dDay = getDDay(String(job.pbancEndYmd));
          const isUrgent = dDay === "오늘마감" || (typeof dDay === 'string' && dDay.includes('D-') && parseInt(dDay.split('-')[1]) <= 3);

          return (
            <div key={job.recrutPblntSn || index} className="job-post-card">
              <div className="card-header">
                <span className="inst-name">{job.instNm}</span>
                <span className={`d-day-badge ${isUrgent ? 'urgent' : ''}`}>{dDay}</span>
              </div>

              <h4 className="job-title">{job.recrutPbancTtl}</h4>

              <div className="job-tags">
                <span className="tag type">{job.hireTypeNmLst}</span>
                <span className="tag career">{job.recrutSeNm}</span>
                <span className="tag edu">{job.acbgCondNmLst}</span>
              </div>

              <div className="job-info-footer">
                <div className="info-item">
                  <span className="icon">📍</span>
                  <span className="text">{job.workRgnNmLst}</span>
                </div>
                <div className="info-item">
                  <span className="icon">📅</span>
                  <span className="text">~ {formatDate(String(job.pbancEndYmd))}</span>
                </div>
              </div>

              <a href={job.srcUrl} target="_blank" rel="noopener noreferrer" className="apply-link">
                공고 확인하기
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </a>
            </div>
          );
        })}
      </div>
    </div>
  );
};

  // 부동산 탭
  // ResultsPage.jsx 내의 renderRealestateTab 함수 수정

const renderRealestateTab = () => {
  const status = tabStatus.realestate;
  if (status.error) return <div className="error-state">{status.error}</div>;
  if (status.isEmpty) return <div className="no-data">해당 지역의 실거래 정보가 없습니다.</div>;
  if (!status.hasData) return <div className="loading-state">부동산 정보를 불러오는 중...</div>;

  const properties = resultData.realestate.properties || [];

  // 면적 평수 환산 함수
  const convertToPyeong = (m2) => Math.round(parseFloat(m2) * 0.3025);

  // 거래 타입 분류 함수 (보증금/임대료 기반)
  const getDealType = (amount) => {
    const parts = amount.split(" / ");
    if (parts.length > 1 && parts[1] !== "0") return { type: "월세", class: "monthly" };
    return { type: "전세/매매", class: "jeonse" };
  };

  return (
    <div className="realestate-wrapper">
      {/* 왼쪽: 고도화된 매물 리스트 */}
      <div className="properties-side-panel">
        <div className="panel-header">
          <h4>실거래 목록 <span className="count-badge">{properties.length}</span></h4>
          <p className="panel-sub">최근 거래된 실거래가 정보입니다.</p>
        </div>
        
        <div className="realestate-list" data-reset-on-tab>
          {properties.map((property, index) => {
            const { type, class: typeClass } = getDealType(property.dealAmount);
            const pyeong = convertToPyeong(property.excluUseAr);

            return (
              <div
                key={`${property.aptNm}-${index}`}
                className="property-item-card"
                onClick={() => handlePropertyClick(property.aptNm)}
                onMouseEnter={() => highlightMarker(property.aptNm, true)}
                onMouseLeave={() => highlightMarker(property.aptNm, false)}
              >
                <div className="item-top">
                  <span className={`deal-type-tag ${typeClass}`}>{type}</span>
                  <span className="location-tag">{property.umdNm}</span>
                </div>
                
                <h4 className="apt-name">{property.aptNm}</h4>
                
                <div className="price-info">
                  <span className="main-price">{property.dealAmount}</span>
                  <span className="price-unit">만원</span>
                </div>

                <div className="property-specs">
                  <div className="spec">
                    <span className="spec-label">면적</span>
                    <span className="spec-value">{property.excluUseAr}㎡ <span>({pyeong}평)</span></span>
                  </div>
                  <div className="spec">
                    <span className="spec-label">층수/건축</span>
                    <span className="spec-value">{property.floor}층 / {property.buildYear}년</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 오른쪽: 지도 섹션 */}
      <div className="map-side-panel">
        <div className="map-container-outer">
          <div ref={mapRef} className="kakao-map-canvas"></div>
          {/* 지도 위 플로팅 가이드 */}
          <div className="map-guide-overlay">
            <p>📍 아파트를 클릭하여 주변 1km 시설(병원, 약국, 편의점)을 확인하세요.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

  // 정책 탭 (AI 섹션 클래스 기반으로 교체)
  // ResultsPage.jsx 내의 renderPoliciesTab 함수 수정

const renderPoliciesTab = () => {
  const status = tabStatus.policies;
  if (status.error) return <div className="error-state">{status.error}</div>;
  if (status.isEmpty) return <div className="no-data">해당 지역의 청년정책이 없습니다.</div>;
  if (!status.hasData) return <div className="loading-state">정책 정보를 불러오는 중...</div>;

  const rawPolicies = resultData.policies.policies || [];
  
  // 1. 점수(sim) 기준 내림차순 정렬
  const sortedPolicies = [...rawPolicies].sort((a, b) => (b.sim || 0) - (a.sim || 0));
  const regionName = resultData.policies.region_info?.name || "";

  return (
    <div className="policies-tab-container">
      <div className="policy-header">
        <h3>{regionName} 청년 맞춤 정책 <span className="policy-count">{sortedPolicies.length}</span></h3>
        <p className="policy-subtitle">AI가 분석한 사용자 조건 대비 적합도 순으로 정렬되었습니다.</p>
      </div>

      <div className="policy-grid">
        {sortedPolicies.map((policy, index) => {
          const matchScore = Math.round((policy.sim || 0) * 100); // 0.77 -> 77%
          const isBestMatch = index === 0; // 최상단 정책

          return (
            <div key={policy.plcyNo} className={`policy-card ${isBestMatch ? 'best-match' : ''}`}>
              {isBestMatch && <div className="best-badge">✨ AI BEST MATCH</div>}
              
              <div className="card-top">
                <div className="match-rate">
                  <div className="rate-circle" style={{ '--p': matchScore }}>
                    <span className="rate-num">{matchScore}%</span>
                  </div>
                  <span className="rate-label">적합도</span>
                </div>
                <div className="title-area">
                  <span className="policy-category">{policy.mclsfNm || policy.lclsfNm}</span>
                  <h4 className="policy-title">{policy.plcyNm}</h4>
                </div>
              </div>

              <div className="card-mid">
                <p className="policy-desc">{policy.plcyExplnCn}</p>
                <div className="benefit-box">
                  <strong>🎁 핵심 혜택</strong>
                  <p>{policy.plcySprtCn || "상세 지원내용은 링크를 참조하세요."}</p>
                </div>
              </div>

              <div className="card-bottom">
                <div className="info-row">
                  <span className="info-label">대상</span>
                  <span className="info-value">
                    {policy.sprtTrgtAgeLmtYn === 'Y' ? '연령 제한 없음' : `만 ${policy.sprtTrgtMinAge}~${policy.sprtTrgtMaxAge}세`}
                  </span>
                </div>
                <div className="info-row">
                  <span className="info-label">기관</span>
                  <span className="info-value">{policy.sprvsnInstCdNm}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">기간</span>
                  <span className="info-value">{policy.aplyYmd || '상시접수'}</span>
                </div>
              </div>

              {policy.refUrlAddr1 && (
                <a href={policy.refUrlAddr1} target="_blank" rel="noopener noreferrer" className="policy-apply-btn">
                  상세보기 및 신청
                </a>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

  // 사용자 프롬프트 → 히어로 부제
  const rawPrompt =
    searchData?.prompt ??
    searchData?.userPrompt ??
    searchData?.query ??
    resultData?.input_prompt ??
    resultData?.query?.raw ??
    resultData?.summary?.user_prompt ??
    "";

  const userPromptDisplay =
    typeof rawPrompt === "string" && rawPrompt.trim()
      ? rawPrompt.trim()
      : resultData?.summary?.region_info?.name ||
        resultData?.summary?.summary?.region_name ||
        "사용자 입력";

  return (
    <div
      className="results-container snap-container"
      ref={containerRef}
      tabIndex={0}
      style={{ "--bg-img": `url(${bgImg})` }}
    >
      <button
        className="back-fab"
        onClick={onBackToRecommendations}
        aria-label="Back to recommendations"
        title="다른 지역 목록 보기"
      >
        ← 다른 지역 보기
      </button>
      <button
        className="newchat-fab"
        onClick={onBackToMain}
        aria-label="Start a new chat"
        title="New Chat"
      >
        조건 다시 입력 ↻
      </button>

      {/* ① 탐색결과 섹션 */}
      <section className="snap-section hero-section">
        <div className="hero-wrap">
          <h1 className="hero-title">ieum의 탐색 결과</h1>
          <p className="hero-sub">
            <span className="hero-prompt">"{userPromptDisplay}"</span>의 분석
            결과입니다.
          </p>

          {/* AI 브리핑 카드 (수정됨) */}
          <div className="briefing-card">
            {/* 상단: 핵심 지표 3가지 */}
            <div className="briefing-stats-row">
              <div className="stat-box">
                <div className="icon-wrapper job">
                  <img src={briefcaseIcon} alt="일자리" />
                </div>
                <div className="stat-text">
                  <span className="label">일자리</span>
                  <span className="count">
                    {resultData?.summary?.summary?.total_jobs ?? 0}건
                  </span>
                </div>
              </div>
              <div className="stat-divider"></div>
              <div className="stat-box">
                <div className="icon-wrapper house">
                  <img src={homeIcon} alt="부동산" />
                </div>
                <div className="stat-text">
                  <span className="label">부동산</span>
                  <span className="count">
                    {resultData?.summary?.summary?.total_properties ?? 0}건
                  </span>
                </div>
              </div>
              <div className="stat-divider"></div>
              <div className="stat-box">
                <div className="icon-wrapper policy">
                  <img src={docIcon} alt="정책" />
                </div>
                <div className="stat-text">
                  <span className="label">정책</span>
                  <span className="count">
                    {resultData?.summary?.summary?.total_policies ?? 0}건
                  </span>
                </div>
              </div>
            </div>

            {/* 하단: LLM 지역 분석 텍스트 */}
            <div className="briefing-content">
              <div className="ai-badge-row">
                <span className="ai-badge-pill">✨ AI 분석 리포트</span>
              </div>
              <p className="ai-description">
                {resultData?.summary?.summary?.text ||
                  `${searchData?.prompt} 지역은 사용자의 예산과 직무에 적합한 환경을 갖추고 있습니다. 
                  특히 일자리와 주거 지원 정책의 밸런스가 좋아 정착하기에 유리한 지역으로 분석됩니다.`}
              </p>
            </div>
          </div>

          {/* 아래로 안내 */}
          <button className="scroll-hint" onClick={scrollToAnalysis}>
            아래로 스크롤하여 상세 분석 결과를 확인하세요.
            <img src={arrowDownIcon} alt="" />
          </button>
        </div>
      </section>

      {/* ② 분석결과 섹션 */}
      <section className="snap-section analysis-section" ref={analysisRef}>
        <div className="analysis-inner">
          <h3 className="analysis-title">분석 결과</h3>

          <div className="tabs-container">
            <div className="tabs-header">
              <button
                className={getTabButtonClass("summary")}
                onClick={() => setActiveTab("summary")}
              >
                종합 요약
              </button>
              <button
                className={getTabButtonClass("jobs")}
                onClick={() => setActiveTab("jobs")}
              >
                일자리
              </button>
              <button
                className={getTabButtonClass("realestate")}
                onClick={() => setActiveTab("realestate")}
              >
                부동산
              </button>
              <button
                className={getTabButtonClass("policies")}
                onClick={() => setActiveTab("policies")}
              >
                정책
              </button>
            </div>

            <div className="tab-content" ref={tabContentRef}>
              {activeTab === "summary" && renderSummaryTab()}
              {activeTab === "jobs" && renderJobsTab()}
              {activeTab === "realestate" && renderRealestateTab()}
              {activeTab === "policies" && renderPoliciesTab()}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default ResultsPage;