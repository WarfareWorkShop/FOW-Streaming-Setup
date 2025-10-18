import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');

  const sendMessage = async () => {
    if (!message.trim()) {
      return;
    }

    try {
      const res = await axios.post('http://localhost:5000/api/chat', { message });
      setResponse(res.data.response);
      setMessage('');
    } catch (error) {
      console.error(error);
      setResponse('⚠️ Unable to reach the tactical AI. Confirm the command server is running.');
    }
  };

  return (
    <div className="app">
      <div className="background-flare" />

      <header className="hero">
        <span className="badge">Live battle briefing</span>
        <h1>Flames of War Command Center</h1>
        <p>
          Deploy an immersive stream overlay for your Flames of War broadcasts. Track both
          commanders, highlight decisive maneuvers, and narrate the frontline with AI-driven
          insights.
        </p>
        <div className="hero-actions">
          <button type="button">Start broadcast layout</button>
          <button type="button" className="secondary">Download overlay pack</button>
        </div>
      </header>

      <main className="dashboard">
        <section className="card">
          <h2>Battle overview</h2>
          <div className="grid-two-column">
            <div className="stat-pill">
              <span className="label">Scenario</span>
              <span className="value">Breakthrough Assault</span>
            </div>
            <div className="stat-pill">
              <span className="label">Round</span>
              <span className="value">Turn 3 / 8</span>
            </div>
            <div className="stat-pill">
              <span className="label">Weather</span>
              <span className="value">Overcast, Muddy Fields</span>
            </div>
            <div className="stat-pill">
              <span className="label">Intel Feed</span>
              <span className="value">Recon Planes Active</span>
            </div>
          </div>
          <h3>Timeline cues</h3>
          <div className="timeline">
            <div className="timeline-item">
              Axis Panzers cross the river under smoke cover. Prepare slow-motion replay.
            </div>
            <div className="timeline-item">
              Allied artillery zeroes in on objective Bravo. Queue lower-third graphic.
            </div>
            <div className="timeline-item">
              Close-up on infantry assault. Trigger dramatic score stinger.
            </div>
          </div>
        </section>

        <section className="card">
          <h2>Commanders &amp; scores</h2>
          <div className="team-status">
            <div className="team-row">
              <div className="team-name">
                <span>Allied forces</span>
                <strong>Task Force Liberty</strong>
              </div>
              <div className="team-score">12</div>
            </div>
            <div className="team-row">
              <div className="team-name">
                <span>Axis forces</span>
                <strong>9th Panzergruppe</strong>
              </div>
              <div className="team-score">9</div>
            </div>
          </div>

          <div className="objectives">
            <div className="objective-row">
              <span>Objective Alpha</span>
              <span className="status success">Secured</span>
            </div>
            <div className="objective-row">
              <span>Objective Bravo</span>
              <span className="status danger">Contested</span>
            </div>
            <div className="objective-row">
              <span>Objective Charlie</span>
              <span className="status">Pending</span>
            </div>
          </div>
        </section>

        <section className="card">
          <h2>AI control room</h2>
          <div className="control-room">
            <label htmlFor="message">Send tactical prompt</label>
            <textarea
              id="message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Request battlefield narration, camera cues, or strategic insights..."
              rows={4}
            />
            <button type="button" onClick={sendMessage}>Deploy command</button>
            <div className="response-panel">
              <strong>AI Response</strong>
              <div>{response || 'Awaiting your command...'}</div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
