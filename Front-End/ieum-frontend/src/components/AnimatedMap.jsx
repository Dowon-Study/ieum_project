// src/components/AnimatedMap.jsx
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import KoreaMap from '../assets/south_korea.svg?react';

const initialNodes = [
    { id: 1, x: 100, y: 650 }, 
    { id: 2, x: 500, y: 680 }, 
    { id: 3, x: 200, y: 400 }, 
    { id: 4, x: 400, y: 350 }, 
    { id: 5, x: 300, y: 200 }, 
    { id: 6, x: 150, y: 100 }, 
    { id: 7, x: 500, y: 150 }, 
];

const lines = [
    { from: 1, to: 3 }, { from: 1, to: 2 }, { from: 3, to: 5 },
    { from: 3, to: 4 }, { from: 2, to: 4 }, { from: 5, to: 6 },
    { from: 5, to: 7 }, { from: 6, to: 4 }, { from: 7, to: 4 },
];

function AnimatedMap() {
    const [nodes, setNodes] = useState(initialNodes);

    useEffect(() => {
        const interval = setInterval(() => {
            setNodes(prevNodes => {
                const viewBoxWidth = 600;
                const viewBoxHeight = 800;

                return prevNodes.map(node => {
                    // 기존 좌표가 없을 경우를 대비한 안전장치
                    const currentX = node.x ?? 0;
                    const currentY = node.y ?? 0;

                    let newX = currentX + (Math.random() - 0.5) * 40;
                    let newY = currentY + (Math.random() - 0.5) * 40;

                    const radius = 8;
                    newX = Math.max(radius, Math.min(newX, viewBoxWidth - radius));
                    newY = Math.max(radius, Math.min(newY, viewBoxHeight - radius));

                    return { ...node, x: newX, y: newY };
                });
            });
        }, 750);

        return () => clearInterval(interval);
    }, []);

    // 헬퍼 함수에서 절대 undefined를 반환하지 않도록 수정
    const findNode = (id) => nodes.find(n => n.id === id) || { x: 0, y: 0 };

    return (
        <div className="map-container">
            <KoreaMap className="map-background" />
            <svg className="map-overlay" viewBox="0 0 600 800">
                {/* 선(line) 렌더링 */}
                {lines.map((line, index) => {
                    const fromNode = findNode(line.from);
                    const toNode = findNode(line.to);

                    // 좌표값이 유효한지 최종 검사
                    const x1 = fromNode.x ?? 0;
                    const y1 = fromNode.y ?? 0;
                    const x2 = toNode.x ?? 0;
                    const y2 = toNode.y ?? 0;

                    return (
                        <motion.line
                            key={`line-${index}`}
                            x1={x1}
                            y1={y1}
                            x2={x2}
                            y2={y2}
                            stroke="#E8843C"
                            strokeWidth="2"
                            opacity={0.6}
                            // animate에 직접 값을 넣을 때도 0을 보장
                            animate={{ 
                                x1: x1, 
                                y1: y1, 
                                x2: x2, 
                                y2: y2 
                            }}
                            transition={{ duration: 0.75, ease: "linear" }}
                        />
                    );
                })}

                {/* 노드(circle) 렌더링 */}
                {nodes.map(node => {
                    const cx = node.x ?? 0;
                    const cy = node.y ?? 0;

                    return (
                        <motion.circle
                            key={`node-${node.id}`}
                            cx={cx}
                            cy={cy}
                            r="8"
                            fill="#ffffff"
                            stroke="#E8843C"
                            strokeWidth="1.5"
                            animate={{ 
                                cx: cx, 
                                cy: cy 
                            }}
                            transition={{ duration: 0.75, ease: "linear" }}
                        />
                    );
                })}
            </svg>
        </div>
    );
}

export default AnimatedMap;