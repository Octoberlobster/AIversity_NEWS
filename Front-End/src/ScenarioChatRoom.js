// src/ScenarioChatRoom.js
import React, { useEffect, useRef, useState } from 'react';
import './ChatRoom.css'; // 沿用原聊天室樣式

export default function ScenarioChatRoom({ scenario, roles, onReset }) {
  const [msgs, setMsgs] = useState([]);
  const [streaming, setStreaming] = useState(true);
  const endRef = useRef(null);
  /* ① 旗標：避免在同一組 scenario+roles 裡重複送 request */
  const requested = useRef(false);

  const pushMsg = (m, tag = '') => {
    if (!m || m.role === undefined || m.text === undefined) {
      console.warn('[EMPTY-MSG]', tag, m, new Error().stack);
      return;
    }
    setMsgs(prev => [...prev, m]);
  };

  /* ② 主要 effect：串後端 -------------------------------- */
  useEffect(() => {
    // 若同一組參數已送過，就跳過（除非 onReset 重新置回 false）
    if (requested.current) return;
    requested.current = true;

    const ac = new AbortController();   // 建立 AbortController
    setMsgs([]);
    setStreaming(true);

    (async () => {
      try {
        const res = await fetch('http://localhost:5001/scenario', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario, roles }),
          signal: ac.signal            // <-- 關鍵：可取消
        });
        const data = await res.json();

        if (ac.signal.aborted) return;  // 已取消就不做事

        if (Array.isArray(data)) {
          let i = 0;
          const tick = setInterval(() => {
            pushMsg(data[i], 'stream');
            i += 1;
            if (i === data.length || ac.signal.aborted) {
              clearInterval(tick);
              setStreaming(false);
            }
          }, 1200);
        } else if (data.error) {
          pushMsg({ role: 'SYSTEM', text: '❌ 後端錯誤：' + data.error }, 'error');
          setStreaming(false);
        } else {
          pushMsg({ role: 'SYSTEM', text: '後端回傳未知格式：' + JSON.stringify(data) }, 'unknown');
          setStreaming(false);
        }
      } catch (e) {
        if (e.name !== 'AbortError') {  // 正常取消不算錯
          pushMsg({ role: 'SYSTEM', text: '❌ 連線失敗：' + e.message }, 'fetch');
          setStreaming(false);
        }
      }
    })();

    // cleanup：中斷未完成 fetch；同時允許下次重新發送
    return () => {
      ac.abort();
      requested.current = false;
    };
  }, [scenario, roles]);


  /* 自動配淡色 -------------------------------------- */
  const bg = role => {
    if (role === 'SYSTEM') return '#d3d3d3';
    const h = [...role].reduce((s, c) => s + c.charCodeAt(0), 0) % 360;
    return `hsl(${h},60%,90%)`;
  };

  return (
    <div className="chat-container">
      <div className="scenario-header">
        <h3>情境：「{scenario}」</h3>
        <button onClick={onReset}>重新設定</button>
      </div>

      <div className="messages">
        {msgs
          .filter(Boolean) // 先過濾 null/undefined
          .filter(m => m.role !== '主持人')
          .map((m, idx) => (
            <div
              key={idx}
              className="message role-message"
              style={{
                background: bg(m.role),
                alignSelf: m.role === 'SYSTEM' ? 'center' : 'flex-start'
              }}
            >
              <strong>{m.role}：</strong> {m.text}
            </div>
          ))}

        {streaming && (
          <div className="typing-indicator" style={{ marginLeft: 0 }}>
            <span />
            <span />
            <span />
          </div>
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
