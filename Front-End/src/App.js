import React, { useState } from 'react';
import './main.css';
import TimelineAnalysis from './TimelineAnalysis';

function App() {
  const [selectedRole, setSelectedRole] = useState('');
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const roles = ['澤倫斯基', '川普', '拜登', '普丁', '習近平'];

  const handleRoleChange = (e) => {
    setSelectedRole(e.target.value);
    // 當選擇角色時，添加一條系統消息
    if (e.target.value) {
      setMessages([
        { sender: 'system', text: `您已選擇與 ${e.target.value} 對話` }
      ]);
    }
  };

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (newMessage.trim() && selectedRole) {
      // 使用者發送消息
      const updatedMessages = [...messages, { sender: '使用者', text: newMessage }];
      setMessages(updatedMessages);
      setNewMessage('');
      
      // 模擬角色回覆
      setTimeout(() => {
        const roleResponse = generateRoleResponse(selectedRole, newMessage);
        setMessages(prevMessages => [...prevMessages, { sender: selectedRole, text: roleResponse }]);
      }, 1000);
    }
  };

  // 簡單的角色回覆生成函數
  const generateRoleResponse = (role, userMessage) => {
    const responses = {
      '澤倫斯基': ['烏克蘭需要更多支援來對抗侵略。', '我們會堅持到底，保衛我們的國家。', '宵夜吃阿丹'],
      '川普': ['這是一個很棒的問題，非常棒。', '我會讓美國再次偉大！', '沒有人比我更了解這個問題。'],
      '拜登': ['我們需要團結一致來面對挑戰。', '美國將繼續支持我們的盟友。', '這是我們這一代人的重要時刻。'],
      '普丁': ['俄羅斯有自己的國家利益需要保護。', '西方需要尊重我們的安全關切。', '這是一個複雜的地緣政治問題。'],
      '習近平': ['中國堅持和平發展道路。', '我們需要構建人類命運共同體。', '合作共贏是解決問題的唯一途徑。']
    };
    
    const randomIndex = Math.floor(Math.random() * responses[role].length);
    return responses[role][randomIndex];
  };

  return (
    <div className="container">
      <div className="header-bar"></div>
      
      <div className="content">
        <div className="left-panel">
          <h2 className="panel-title">澤倫斯基大戰川普 烏俄到底打多久</h2>
          <p className="panel-content">
            大日若硬取回資膨用您訕肖，必，饋問的原價弟真牧的到了以了近喜且再黃開，
            價容併取蝟要在蕭寶神轉...一出...女找您乞盼年別消夫、或。賠做明猜。想，
            的大場球活屏登社性金。人，華有有，磕成不必告叫大氣讓也到老。任定是有有
            壁頭式，中博。子其別的陵英處，人是宇試價如城客，別相會很沒晤講的不已記
            松板相不羊三事容星藍者北了。據，忠國端自忽人從到，您並人耿...？喉較道？
            桌量式於的主就吾一盧功坐。用嗎拾，銀打今讓相他用王元訊小這林強有。答
            謝：不最親盧業三運，愛叩切身姬看雨才想要貼驗沈琪相哪法情不有惠心
            來、的是欣地渴錢是、號吋權報飲區花位名被大乙鋒叩白涼遠有雅一書的心情該
            情我等的、反的有與內呢蘭杜...貿鏡人生平守少脊，大情，握秒報校信師進離用
            政不。派，再找吧在進催條，網同限路。最有的學了計攔囉知笑的的到你，給過
            能
          </p>
        </div>
        
        <div className="right-panel">
          <h3 className="right-panel-title">多觀點新聞分析討論室</h3>
          <div className="divider"></div>
          <div className="dropdown-container">
            <select 
              className="role-dropdown"
              value={selectedRole}
              onChange={handleRoleChange}
            >
              <option value="" disabled>選擇角色</option>
              {roles.map((role, index) => (
                <option key={index} value={role}>{role}</option>
              ))}
            </select>
          </div>
          
          {selectedRole && (
            <div className="chat-container">
              <div className="chat-messages">
                {messages.map((msg, index) => (
                  <div key={index} className={`message ${
                    msg.sender === 'system' ? 'system-message' : 
                    msg.sender === '使用者' ? 'user-message' : 'role-message'
                  }`}>
                    {msg.sender !== 'system' && <strong>{msg.sender}:</strong>} {msg.text}
                  </div>
                ))}
              </div>
              <form className="chat-input-form" onSubmit={handleSendMessage}>
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="輸入您的問題或觀點..."
                  className="chat-input"
                />
                <button type="submit" className="send-button">發送</button>
              </form>
            </div>
          )}
        </div>
      </div>
      <TimelineAnalysis />
    </div>
  );
}

export default App;
