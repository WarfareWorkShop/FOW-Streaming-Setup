import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');

  const sendMessage = async () => {
    try {
      const res = await axios.post('http://localhost:5000/api/chat', { message });
      setResponse(res.data.response);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <h1>Flames of War - AI Opponent</h1>
      <input 
        type="text" 
        value={message} 
        onChange={(e) => setMessage(e.target.value)} 
        placeholder="Type your message..." 
      />
      <button onClick={sendMessage}>Send</button>
      <p>Response: {response}</p>
    </div>
  );
}

export default App;

