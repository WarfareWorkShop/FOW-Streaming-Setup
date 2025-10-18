import React, { useCallback, useEffect, useMemo, useState } from 'react';

import VoiceInteraction from './VoiceInteraction';
import {
  AUTH_ENDPOINTS,
  CHAT_ENDPOINT,
  MATCHES_ENDPOINT,
  DICE_SCAN_ENDPOINT,
  apiClient,
  setAuthToken,
} from './config';

const speechSupported =
  typeof window !== 'undefined' && typeof window.speechSynthesis !== 'undefined';

const speakText = (text) => {
  if (!speechSupported || !text) {
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new window.SpeechSynthesisUtterance(text);
  utterance.lang = 'es-ES';
  window.speechSynthesis.speak(utterance);
};

const defaultCredentials = { username: '', email: '', password: '' };

function App() {
  const [authMode, setAuthMode] = useState('login');
  const [credentials, setCredentials] = useState(defaultCredentials);
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [matches, setMatches] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [matchState, setMatchState] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [diceResult, setDiceResult] = useState(null);
  const [dicePreview, setDicePreview] = useState(null);

  const resetFeedback = () => {
    setStatusMessage('');
    setError(null);
  };

  const fetchProfile = useCallback(async () => {
    try {
      const response = await apiClient.get(AUTH_ENDPOINTS.me);
      setUser(response.data);
    } catch (profileError) {
      console.error(profileError);
      setUser(null);
    }
  }, []);

  const fetchMatches = useCallback(async () => {
    if (!token) {
      setMatches([]);
      return;
    }
    try {
      const response = await apiClient.get(MATCHES_ENDPOINT);
      setMatches(response.data.matches || []);
    } catch (matchError) {
      console.error(matchError);
      setError('No se pudieron cargar las partidas.');
    }
  }, [token]);

  const handleAuthChange = (event) => {
    const { name, value } = event.target;
    setCredentials((prev) => ({ ...prev, [name]: value }));
  };

  const handleAuthSubmit = async (event) => {
    event.preventDefault();
    resetFeedback();

    if (!credentials.username || !credentials.password) {
      setError('Debes indicar usuario y contraseña.');
      return;
    }

    if (authMode === 'register' && !credentials.email) {
      setError('El correo electrónico es obligatorio para registrarse.');
      return;
    }

    setIsSubmitting(true);
    try {
      if (authMode === 'register') {
        await apiClient.post(AUTH_ENDPOINTS.register, {
          username: credentials.username,
          password: credentials.password,
          email: credentials.email,
        });
        setStatusMessage('Registro completado. Iniciando sesión...');
      }

      const loginResponse = await apiClient.post(AUTH_ENDPOINTS.login, {
        username: credentials.username,
        password: credentials.password,
      });

      setToken(loginResponse.data.token);
      setStatusMessage('Sesión iniciada correctamente.');
      setCredentials(defaultCredentials);
    } catch (authError) {
      console.error(authError);
      setError('No se pudo completar la operación de autenticación.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateMatchState = useCallback((match, state) => {
    setSelectedMatch(match);
    setMatchState(state);
    setMatches((existing) => {
      const map = new Map(existing.map((item) => [item.id, item]));
      map.set(match.id, match);
      return Array.from(map.values());
    });
  }, []);

  const selectMatch = useCallback(
    async (matchId) => {
      if (!matchId) {
        return;
      }
      resetFeedback();
      try {
        const response = await apiClient.get(`${MATCHES_ENDPOINT}/${matchId}`);
        const match = response.data.match;
        updateMatchState(match, match.state);
      } catch (selectionError) {
        console.error(selectionError);
        setError('No se pudo cargar la partida seleccionada.');
      }
    },
    [updateMatchState],
  );

  const handleCreateMatch = async (event) => {
    event.preventDefault();
    if (!token) {
      setError('Debes iniciar sesión para crear una partida.');
      return;
    }

    const formData = new FormData(event.target);
    const name = formData.get('matchName');
    const opponentType = formData.get('opponentType');
    const scenario = formData.get('scenario');
    const inviteeUsername = formData.get('inviteeUsername');

    if (!name) {
      setError('Debes indicar un nombre para la partida.');
      return;
    }

    resetFeedback();
    setIsSubmitting(true);
    try {
      const payload = {
        name,
        opponent_type: opponentType,
        scenario,
      };
      if (opponentType === 'human') {
        payload.invitee_username = inviteeUsername;
      }

      const response = await apiClient.post(MATCHES_ENDPOINT, payload);
      const newMatch = response.data.match;
      setStatusMessage('Partida creada correctamente.');
      updateMatchState(newMatch, newMatch.state);
      await fetchMatches();
    } catch (creationError) {
      console.error(creationError);
      setError('No se pudo crear la partida.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAction = async (actionPayload) => {
    if (!selectedMatch) {
      setError('Selecciona una partida activa.');
      return;
    }

    setIsActionLoading(true);
    resetFeedback();
    try {
      const response = await apiClient.post(
        `${MATCHES_ENDPOINT}/${selectedMatch.id}/actions`,
        actionPayload,
      );
      const { match, state } = response.data;
      updateMatchState(match, state);
      const lastLog = state.log?.slice().reverse().find((entry) => entry.actor === 'ai');
      if (lastLog) {
        setStatusMessage(lastLog.text);
        speakText(lastLog.text);
      }
    } catch (actionError) {
      console.error(actionError);
      setError('No se pudo registrar la acción.');
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleVoiceTranscript = (transcript) => {
    if (!transcript) {
      return;
    }
    setStatusMessage(`Comando de voz recibido: ${transcript}`);
    handleAction({ transcript });
  };

  const handleDiceUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const form = new FormData();
    form.append('image', file);

    resetFeedback();
    try {
      const response = await apiClient.post(DICE_SCAN_ENDPOINT, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const { pip_count: pipCount, preview_image: previewImage } = response.data;
      setDiceResult(pipCount);
      setDicePreview(previewImage ? `data:image/jpeg;base64,${previewImage}` : null);
      setStatusMessage(`Lectura de dados completada: ${pipCount} impactos.`);
    } catch (diceError) {
      console.error(diceError);
      setError('No se pudo procesar la imagen de los dados.');
    }
  };

  const handleChatSubmit = async (event) => {
    event.preventDefault();
    const trimmed = chatMessage.trim();
    if (!trimmed) {
      setError('Escribe un mensaje antes de enviarlo.');
      return;
    }

    resetFeedback();
    setIsActionLoading(true);
    try {
      const response = await apiClient.post(CHAT_ENDPOINT, { message: trimmed });
      const assistantReply = response?.data?.response ?? '';
      setChatLog((current) => [
        ...current,
        { sender: 'Tú', text: trimmed },
        { sender: 'Asistente', text: assistantReply },
      ]);
      setChatMessage('');
      speakText(assistantReply);
    } catch (chatError) {
      console.error(chatError);
      setError('No se pudo contactar al asistente táctico.');
    } finally {
      setIsActionLoading(false);
    }
  };

  const availableActions = useMemo(
    () => [
      { key: 'attack', label: 'Atacar', payload: { action: { type: 'attack', intensity: 3 } } },
      { key: 'defend', label: 'Defender', payload: { action: { type: 'defend', intensity: 2 } } },
      { key: 'regroup', label: 'Reorganizar', payload: { action: { type: 'regroup' } } },
      { key: 'recon', label: 'Reconocimiento', payload: { action: { type: 'recon' } } },
    ],
    [],
  );

  useEffect(() => {
    if (token) {
      setAuthToken(token);
      fetchProfile();
      fetchMatches();
    } else {
      setAuthToken(null);
      setUser(null);
      setMatches([]);
      setSelectedMatch(null);
      setMatchState(null);
    }
  }, [token, fetchMatches, fetchProfile]);

  return (
    <div className="app">
      <header>
        <h1>Flames of War - Centro de Mando</h1>
        {user && <p>Sesión iniciada como {user.username}</p>}
      </header>

      <section aria-label="Autenticación">
        <h2>{authMode === 'login' ? 'Iniciar sesión' : 'Registro'}</h2>
        <form onSubmit={handleAuthSubmit} className="auth-form">
          <label htmlFor="username">Usuario</label>
          <input
            id="username"
            name="username"
            type="text"
            value={credentials.username}
            onChange={handleAuthChange}
            autoComplete="username"
          />

          {authMode === 'register' && (
            <>
              <label htmlFor="email">Correo electrónico</label>
              <input
                id="email"
                name="email"
                type="email"
                value={credentials.email}
                onChange={handleAuthChange}
                autoComplete="email"
              />
            </>
          )}

          <label htmlFor="password">Contraseña</label>
          <input
            id="password"
            name="password"
            type="password"
            value={credentials.password}
            onChange={handleAuthChange}
            autoComplete={authMode === 'login' ? 'current-password' : 'new-password'}
          />

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Procesando...' : authMode === 'login' ? 'Entrar' : 'Registrarme'}
          </button>
        </form>
        <button
          type="button"
          onClick={() => {
            setAuthMode((mode) => (mode === 'login' ? 'register' : 'login'));
            resetFeedback();
          }}
        >
          {authMode === 'login'
            ? '¿No tienes cuenta? Regístrate'
            : '¿Ya tienes cuenta? Inicia sesión'}
        </button>
      </section>

      {token && (
        <section aria-label="Gestión de partidas">
          <h2>Partidas disponibles</h2>
          <form onSubmit={handleCreateMatch} className="match-form">
            <label htmlFor="matchName">Nombre de la partida</label>
            <input id="matchName" name="matchName" type="text" placeholder="Operación Market" />

            <label htmlFor="scenario">Escenario</label>
            <input id="scenario" name="scenario" type="text" placeholder="Desierto del Norte" />

            <label htmlFor="opponentType">Tipo de oponente</label>
            <select id="opponentType" name="opponentType" defaultValue="ai">
              <option value="ai">Inteligencia Artificial</option>
              <option value="human">Jugador humano</option>
            </select>

            <label htmlFor="inviteeUsername">Usuario a invitar (solo humano)</label>
            <input id="inviteeUsername" name="inviteeUsername" type="text" placeholder="nombre_jugador" />

            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creando...' : 'Crear partida'}
            </button>
          </form>

          <div className="match-list">
            <h3>Mis partidas</h3>
            <ul>
              {matches.map((match) => (
                <li key={match.id}>
                  <button type="button" onClick={() => selectMatch(match.id)}>
                    {match.name} — {match.status}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {selectedMatch && (
        <section aria-label="Detalle de partida" className="match-details">
          <h2>{selectedMatch.name}</h2>
          <p>
            Escenario: {selectedMatch.scenario || 'General'} | Estado: {selectedMatch.status} | Turno:{' '}
            {matchState?.turn}
          </p>
          <div className="scoreboard">
            <div>
              <h3>Aliados</h3>
              <p>Unidades: {matchState?.player?.units}</p>
              <p>Morale: {matchState?.player?.morale}</p>
              <p>Puntos de victoria: {matchState?.player?.victory_points}</p>
            </div>
            <div>
              <h3>Oponente</h3>
              <p>Unidades: {matchState?.ai?.units}</p>
              <p>Morale: {matchState?.ai?.morale}</p>
              <p>Puntos de victoria: {matchState?.ai?.victory_points}</p>
            </div>
          </div>
          <div className="action-panel">
            <h3>Acciones rápidas</h3>
            <div className="actions">
              {availableActions.map((action) => (
                <button
                  key={action.key}
                  type="button"
                  disabled={isActionLoading}
                  onClick={() => handleAction(action.payload)}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
          <div className="match-log">
            <h3>Registro de combate</h3>
            <ul>
              {(matchState?.log || []).map((entry, index) => (
                <li key={index}>
                  <strong>{entry.actor}:</strong> {entry.text}
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      <section aria-label="Interacción por voz y dados" className="support-tools">
        <div>
          <VoiceInteraction onTranscript={handleVoiceTranscript} />
        </div>
        <div className="dice-uploader">
          <h2>Lectura automática de dados</h2>
          <input type="file" accept="image/*" onChange={handleDiceUpload} />
          {diceResult !== null && <p>Resultado estimado: {diceResult} pips detectados.</p>}
          {dicePreview && (
            <figure>
              <img src={dicePreview} alt="Vista previa procesada de los dados" />
              <figcaption>Detección de impactos en tiempo real.</figcaption>
            </figure>
          )}
        </div>
      </section>

      <section aria-label="Asistente táctico">
        <h2>Chat de apoyo táctico</h2>
        <form onSubmit={handleChatSubmit} className="chat-form">
          <label htmlFor="chatMessage">Mensaje</label>
          <input
            id="chatMessage"
            type="text"
            value={chatMessage}
            onChange={(event) => setChatMessage(event.target.value)}
            placeholder="Solicita un informe de situación..."
          />
          <button type="submit" disabled={isActionLoading}>
            {isActionLoading ? 'Enviando...' : 'Enviar'}
          </button>
        </form>
        <ul className="chat-log">
          {chatLog.map((entry, index) => (
            <li key={index}>
              <strong>{entry.sender}:</strong> {entry.text}
            </li>
          ))}
        </ul>
      </section>

      <footer>
        {statusMessage && (
          <p role="status" aria-live="polite">
            {statusMessage}
          </p>
        )}
        {error && (
          <p role="alert" style={{ color: 'red' }}>
            {error}
          </p>
        )}
      </footer>
    </div>
  );
}

export default App;
