import React, { useState } from 'react';

import VoiceInteraction from './VoiceInteraction';
import { CHAT_ENDPOINT, apiClient } from './config';

function App() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = async (messageToSend = message) => {
    const trimmedMessage = messageToSend.trim();

    if (!trimmedMessage) {
      setError('Por favor ingresa un mensaje antes de enviar.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const res = await apiClient.post(CHAT_ENDPOINT, { message: trimmedMessage });
      setResponse(res?.data?.response ?? '');
      setMessage('');
    } catch (err) {
      console.error(err);
      setError('No se pudo enviar el mensaje. Inténtalo nuevamente.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceTranscript = (transcript) => {
    if (!transcript || !transcript.trim()) {
      return;
    }

    setMessage(transcript);
    sendMessage(transcript);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    sendMessage();
  };

  return (
    <div>
      <h1>Flames of War - AI Opponent</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Escribe tu mensaje..."
          aria-label="mensaje"
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Enviando...' : 'Enviar'}
        </button>
      </form>
      {isLoading && <p role="status">Enviando mensaje...</p>}
      {error && (
        <p role="alert" style={{ color: 'red' }}>
          {error}
        </p>
      )}
      <p>Respuesta: {response || 'Aún no hay respuesta.'}</p>
      <VoiceInteraction onTranscript={handleVoiceTranscript} />
    </div>
  );
}

export default App;
