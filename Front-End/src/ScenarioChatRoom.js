import React, { useEffect, useRef, useState } from 'react';
import { API_BASE } from './api';
import './css/ChatRoom.css';

export default function ScenarioChatRoom({ scenario, roles, news, onReset }) {
  const [msgs, setMsgs] = useState([]);
  const [streaming, setStreaming] = useState(true);
  const esRef = useRef(null);          // 用來關閉流

  useEffect(() => {
    const params = new URLSearchParams();
    params.append('scenario', scenario);
    roles.forEach(r => params.append('role', r));
    params.append('news', news);

    const es = new EventSource(`${API_BASE.replace(/^http/, 'http')}/stream?${params.toString()}`);
    esRef.current = es;

    es.onmessage = e => {
      const m = JSON.parse(e.data);
      setMsgs(prev => [...prev, m]);
    };

    es.addEventListener('done', () => {
      setStreaming(false);
      es.close();
    });

    es.onerror = () => {
      setStreaming(false);
      es.close();
    };

    return () => es.close();         // 離開元件時關掉
  }, [scenario, roles, news]);

  /* 自動配色 --------------------------------------------- */
  const bg = role => {
    if (role === 'SYSTEM') return '#d3d3d3';
    const h = [...role].reduce((s, c) => s + c.charCodeAt(0), 0) % 360;
    return `hsl(${h},60%,90%)`;
  };

  /* Render ----------------------------------------------- */
  return (
    <div className="chat-container">
      <div className="scenario-header">
        <h3>情境：「{scenario}」</h3>
        <button onClick={onReset}>重新設定</button>
      </div>

      <div className="messages">
        {msgs
          .filter(Boolean)
          .filter(m => m.role !== 'SYSTEM' && m.role !== '主持人')
          .map((m, idx) => (
            <div
              key={idx}
              className="message role-message"
              style={{
                background: bg(m.role),
                alignSelf: 'flex-start'
              }}
            >
              <strong>{m.role}：</strong> {m.text}
            </div>
          ))}

        {streaming && (
          <div className="typing-indicator" style={{ marginLeft: 0 }}>
            <span /><span /><span />
          </div>
        )}
      </div>
    </div>
  );
}
