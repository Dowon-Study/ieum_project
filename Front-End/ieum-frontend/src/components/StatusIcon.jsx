// src/components/StatusIcon.jsx
import React from 'react';
import './StatusIcon.css'; // 아이콘 스타일을 위한 CSS 파일

// 아이콘 상태: 'loading', 'completed', 'waiting', 'error'
function StatusIcon({ status = 'waiting' }) {
    if (status === 'completed') {
        return (
            <div className="status-icon-wrapper completed">
                <svg className="checkmark-icon" viewBox="0 0 52 52">
                    <circle className="checkmark-circle" cx="26" cy="26" r="25" fill="none" />
                    <path className="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8" />
                </svg>
            </div>
        );
    }

    if (status === 'loading') {
        return (
            <div className="status-icon-wrapper loading">
                <div className="spinner-arc"></div>
            </div>
        );
    }

    // waiting 또는 error 상태
    return (
        <div className="status-icon-wrapper waiting">
            <div className="waiting-circle"></div>
        </div>
    );
}

export default StatusIcon;