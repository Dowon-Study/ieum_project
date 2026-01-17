import React from "react";
import "./Modal.css";

function Modal({ isOpen, onClose, title, children }) {
    // isOpen 상태가 false이면 아무것도 렌더링하지 않음
    if (!isOpen) {
        return null;
    }

    return (
        // 모달 오버레이: 뒷 배경을 어둡게 하고 클릭 시 모달을 닫음
        <div className="modal-overlay" onClick={onClose}>
            {/* 모달 컨텐츠: 실제 모달 내용. 이벤트 버블링을 막아 컨텐츠 클릭 시 닫히지 않게 함 */}
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>{title}</h2>
                    <button className="modal-close-button" onClick={onClose}>
                        &times;
                    </button>
                </div>
                <div className="modal-body">{children}</div>
            </div>
        </div>
    );
}

export default Modal;