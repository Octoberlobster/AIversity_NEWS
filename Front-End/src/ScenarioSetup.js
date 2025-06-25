import React, { useState } from 'react';
import './css/ScenarioSetup.css';

export default function ScenarioSetup({ allRoles, onStart }) {
  const [scenario, setScenario] = useState('');
  const [checked, setChecked] = useState({});

  const toggle = role => setChecked(p => ({ ...p, [role]: !p[role] }));
  const selectedRoles = Object.keys(checked).filter(r => checked[r]);

  return (
    <div className="scenario-setup">
      <h2>情境模擬設定</h2>

      <label>情境描述：</label>
      <textarea
        value={scenario}
        onChange={e => setScenario(e.target.value)}
        placeholder="輸入你想讓角色討論的情境…"
      />

      <label style={{ marginTop: '1rem' }}>選擇參與角色（至少兩位）：</label>
      <div className="role-checkboxes">
        {allRoles.map(r => (
          <label key={r} className="role-item">
            <input
              type="checkbox"
              checked={!!checked[r]}
              onChange={() => toggle(r)}
            />
            {r}
          </label>
        ))}
      </div>

      <button
        className="primary-btn"
        disabled={!scenario.trim() || selectedRoles.length < 2}
        onClick={() => onStart({ scenario, roles: selectedRoles })}
      >
        開始模擬
      </button>
    </div>
  );
}
