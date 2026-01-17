// src/components/AnimatedText.jsx
import React, { useState, useEffect } from 'react';
import './AnimatedText.css';

const TEXTS = [
    "데이터를 분석하는 중이에요",
    "일자리를 분석하는 중이에요",
    "주거지를 찾고 있는 중이에요",
    "지원 정책을 찾아보는 중이에요",
];

function AnimatedText() {
    const [textIndex, setTextIndex] = useState(0);
    const [dotCount, setDotCount] = useState(0);

    useEffect(() => {
        const dotInterval = setInterval(() => {
            setDotCount((prev) => (prev + 1) % 4);
        }, 500);

        const textInterval = setInterval(() => {
            setTextIndex((prev) => (prev + 1) % TEXTS.length);
        }, 4500);

        return () => {
            clearInterval(dotInterval);
            clearInterval(textInterval);
        };
    }, []);

    const currentText = TEXTS[textIndex];
    const dots = '.'.repeat(dotCount);

    return <p className="animated-loading-text">{currentText}{dots}</p>;
}

export default AnimatedText;