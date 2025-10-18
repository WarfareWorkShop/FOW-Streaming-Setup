import React, { useEffect, useMemo, useState } from 'react';

import './App.css';

import VoiceInteraction from './VoiceInteraction';
import {
  AUTH_ENDPOINTS,
  CHAT_ENDPOINT,
  DICE_SCAN_ENDPOINT,
  MATCHES_ENDPOINT,
  apiClient,
} from './config';
import { clearTokens, isAuthenticated, setTokens } from './auth';

const extractErrorMessage = (error, fallback = 'Ocurrió un error inesperado.') => {
  if (!error) {
    return fallback;
  }
  const responseMessage = error?.response?.data?.message || error?.response?.data?.error;
  if (typeof responseMessage === 'string' && responseMessage.trim()) {
    return responseMessage;
  }
  if (error.message) {
    return error.message;
  }
  return fallback;
};

const modeSettings = {
  solo: {
    label: 'Solo',
    description: 'Planifica entrenamientos individuales sin oponentes humanos.',
    playerSlots: 1,
    min: 1,
    max: 1,
    opponentType: 'ai',
  },
  solo_ai: {
    label: 'Solo vs IA',
    description: 'Enfrentamientos rápidos contra la inteligencia artificial.',
    playerSlots: 2,
    min: 2,
    max: 2,
    opponentType: 'ai',
  },
  versus: {
    label: 'Versus',
    description: 'Partidas estándar entre 2 y 8 jugadores.',
    playerSlots: 2,
    min: 2,
    max: 8,
    opponentType: 'human',
  },
  tournament: {
    label: 'Torneo',
    description: 'Organiza brackets competitivos de hasta 10 jugadores.',
    playerSlots: 8,
    min: 4,
    max: 10,
    opponentType: 'human',
  },
};

const initialMatchConfig = {
  name: '',
  scenario: '',
  opponentType: 'ai',
  mode: 'solo_ai',
  playerSlots: modeSettings.solo_ai.playerSlots,
  invitee: '',
};

const MatchGrid = ({ playerSlots, mode }) => {
  if (!playerSlots || playerSlots < 1) {
    return null;
  }

  const slots = Array.from({ length: playerSlots });
  const modeLabel = modeSettings[mode]?.label ?? 'Partida';

  return (
    <div className="match-grid" aria-label={`Plantilla visual para ${modeLabel}`}>
      {slots.map((_, index) => (
        <div key={index} className="match-grid__slot">
          <span>Jugador {index + 1}</span>
        </div>
      ))}
    </div>
  );
};

function App() {
  const [authMode, setAuthMode] = useState('login');
  const [loginForm, setLoginForm] = useState({ username: '', password: '', captchaToken: '' });
  const [registerForm, setRegisterForm] = useState({
    username: '',
    email: '',
    password: '',
    captchaToken: '',
  });

  const [authState, setAuthState] = useState({
    status: isAuthenticated() ? 'pending' : 'anonymous',
    profile: null,
    error: null,
  });

  const [chatProvider, setChatProvider] = useState('openai');
  const [chatMessage, setChatMessage] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [isSendingChat, setIsSendingChat] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const [matches, setMatches] = useState([]);
  const [isLoadingMatches, setIsLoadingMatches] = useState(false);
  const [matchError, setMatchError] = useState(null);
  const [matchConfig, setMatchConfig] = useState(initialMatchConfig);

  const [dicePreview, setDicePreview] = useState(null);
  const [diceResult, setDiceResult] = useState(null);
  const [diceError, setDiceError] = useState(null);

  const [activeSection, setActiveSection] = useState('command');

  const isLoggedIn = useMemo(() => authState.status === 'ready', [authState.status]);

  const sectionTabs = [
    { id: 'command', label: 'Centro de mando', description: 'Tu resumen estratégico y próximos pasos.' },
    { id: 'matches', label: 'Partidas', description: 'Configura partidas versátiles y torneos.' },
    { id: 'tactics', label: 'Tácticas y voz', description: 'Consulta al asistente y usa comandos por voz.' },
    { id: 'tools', label: 'Herramientas', description: 'Utilidades de apoyo como escáner de dados.' },
  ];

  const resetFeedback = () => {
    setFeedback(null);
    setAuthState((previous) => ({ ...previous, error: null }));
  };

  const loadProfile = async () => {
    try {
      const { data } = await apiClient.get(AUTH_ENDPOINTS.me);
      setAuthState({ status: 'ready', profile: data, error: null });
    } catch (error) {
      clearTokens();
      setAuthState({ status: 'anonymous', profile: null, error: extractErrorMessage(error) });
    }
  };

  useEffect(() => {
    if (authState.status === 'pending') {
      loadProfile();
    }
  }, [authState.status]);

  const loadMatches = async () => {
    if (!isLoggedIn) {
      return;
    }
    setIsLoadingMatches(true);
    try {
      const { data } = await apiClient.get(MATCHES_ENDPOINT);
      setMatches(data?.matches ?? []);
      setMatchError(null);
    } catch (error) {
      setMatchError(extractErrorMessage(error, 'No se pudieron cargar las partidas.'));
    } finally {
      setIsLoadingMatches(false);
    }
  };

  useEffect(() => {
    if (isLoggedIn) {
      loadMatches();
    }
  }, [isLoggedIn]);

  const handleLoginChange = (event) => {
    const { name, value } = event.target;
    setLoginForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleRegisterChange = (event) => {
    const { name, value } = event.target;
    setRegisterForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleLoginSubmit = async (event) => {
    event.preventDefault();
    resetFeedback();
    try {
      const { data } = await apiClient.post(AUTH_ENDPOINTS.login, loginForm);
      setTokens({
        accessToken: data.accessToken,
        refreshToken: data.refreshToken,
        expiresIn: data.expiresIn,
      });
      setAuthState({ status: 'pending', profile: null, error: null });
      setFeedback('Sesión iniciada correctamente.');
      setLoginForm({ username: '', password: '', captchaToken: '' });
    } catch (error) {
      setAuthState((prev) => ({ ...prev, error: extractErrorMessage(error) }));
    }
  };

  const handleRegisterSubmit = async (event) => {
    event.preventDefault();
    resetFeedback();
    try {
      await apiClient.post(AUTH_ENDPOINTS.register, registerForm);
      setFeedback('Registro completado. Ahora puedes iniciar sesión.');
      setRegisterForm({ username: '', email: '', password: '', captchaToken: '' });
      setAuthMode('login');
    } catch (error) {
      setAuthState((prev) => ({ ...prev, error: extractErrorMessage(error) }));
    }
  };

  const handleLogout = () => {
    clearTokens();
    setAuthState({ status: 'anonymous', profile: null, error: null });
    setMatches([]);
    setChatLog([]);
    setFeedback('Sesión cerrada.');
  };

  const handleChatSubmit = async (event) => {
    event.preventDefault();
    const trimmedMessage = chatMessage.trim();
    if (!trimmedMessage) {
      return;
    }

    setIsSendingChat(true);
    setFeedback(null);

    const newLog = [...chatLog, { role: 'user', message: trimmedMessage }];
    setChatLog(newLog);

    try {
      const { data } = await apiClient.post(CHAT_ENDPOINT, {
        message: trimmedMessage,
        provider: chatProvider,
      });
      setChatLog([...newLog, { role: 'assistant', message: data?.response ?? '' }]);
      setChatMessage('');
    } catch (error) {
      setFeedback(extractErrorMessage(error));
      setChatLog(newLog);
    } finally {
      setIsSendingChat(false);
    }
  };

  const handleVoiceTranscript = (transcript) => {
    if (!transcript) {
      return;
    }
    setChatMessage((previous) => (previous ? `${previous}\n${transcript}` : transcript));
  };

  const handleMatchFieldChange = (event) => {
    const { name, value } = event.target;
    setMatchConfig((prev) => ({ ...prev, [name]: value }));
  };

  const updateMode = (mode) => {
    const settings = modeSettings[mode];
    if (!settings) {
      return;
    }

    setMatchConfig((prev) => ({
      ...prev,
      mode,
      opponentType: settings.opponentType,
      playerSlots: settings.playerSlots,
    }));
  };

  const handleModeChange = (event) => {
    updateMode(event.target.value);
  };

  const handlePlayerSlotsChange = (event) => {
    const value = Number.parseInt(event.target.value, 10) || matchConfig.playerSlots;
    setMatchConfig((prev) => ({ ...prev, playerSlots: value }));
  };

  const handleMatchCreate = async (event) => {
    event.preventDefault();
    setFeedback(null);
    setMatchError(null);

    if (!isLoggedIn) {
      setFeedback('Debes iniciar sesión para crear partidas.');
      return;
    }

    const payload = {
      name: matchConfig.name.trim(),
      scenario: matchConfig.scenario.trim() || undefined,
      opponent_type: matchConfig.opponentType,
      mode: matchConfig.mode,
      player_slots: matchConfig.playerSlots,
    };

    if (matchConfig.opponentType === 'human' && matchConfig.invitee.trim()) {
      payload.invitee_username = matchConfig.invitee.trim();
    }

    try {
      const { data } = await apiClient.post(MATCHES_ENDPOINT, payload);
      setMatches((prev) => [data.match, ...prev]);
      setMatchConfig({ ...initialMatchConfig });
      setFeedback('Partida creada correctamente.');
    } catch (error) {
      setMatchError(extractErrorMessage(error));
    }
  };

  const handleDiceUpload = async (event) => {
    event.preventDefault();
    const file = event.target.elements.image?.files?.[0];
    if (!file) {
      setDiceError('Debes seleccionar una imagen.');
      return;
    }

    setDiceError(null);
    setDicePreview(null);
    setDiceResult(null);

    const formData = new FormData();
    formData.append('image', file);

    try {
      const { data } = await apiClient.post(DICE_SCAN_ENDPOINT, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setDiceResult(data);
      if (data?.preview_image) {
        setDicePreview(`data:image/jpeg;base64,${data.preview_image}`);
      }
    } catch (error) {
      setDiceError(extractErrorMessage(error));
    }
  };

  const activeModeSettings = modeSettings[matchConfig.mode] ?? modeSettings.versus;
  const requiresInvite = matchConfig.opponentType === 'human' && matchConfig.mode !== 'solo';

  return (
    <div className="app-container">
      <header>
        <h1>Flames of War - Comando digital</h1>
        <p>Gestiona partidas, tácticas y utilidades de apoyo desde una sola pantalla.</p>
      </header>

      <nav className="section-tabs" aria-label="Secciones principales">
        {sectionTabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={tab.id === activeSection ? 'active' : ''}
            onClick={() => setActiveSection(tab.id)}
          >
            <span className="tab-label">{tab.label}</span>
            <span className="tab-description">{tab.description}</span>
          </button>
        ))}
      </nav>

      {feedback && (
        <div role="status" className="status-message">
          {feedback}
        </div>
      )}

      {authState.error && (
        <div role="alert" className="error-message">
          {authState.error}
        </div>
      )}

      {activeSection === 'command' && (
        <section>
          <h2>Estado del comandante</h2>
          {isLoggedIn ? (
            <div className="profile-card">
              <p>
                Sesión iniciada como <strong>{authState.profile?.username}</strong>.
              </p>
              <p>{authState.profile?.email}</p>
              <button type="button" onClick={handleLogout}>
                Cerrar sesión
              </button>
            </div>
          ) : (
            <div className="auth-panels">
              <div className="auth-toggle">
                <button
                  type="button"
                  className={authMode === 'login' ? 'active' : ''}
                  onClick={() => setAuthMode('login')}
                >
                  Iniciar sesión
                </button>
                <button
                  type="button"
                  className={authMode === 'register' ? 'active' : ''}
                  onClick={() => setAuthMode('register')}
                >
                  Registrarse
                </button>
              </div>

              {authMode === 'login' ? (
                <form onSubmit={handleLoginSubmit} className="form-grid">
                  <label htmlFor="login-username">Usuario</label>
                  <input
                    id="login-username"
                    name="username"
                    value={loginForm.username}
                    onChange={handleLoginChange}
                    required
                    autoComplete="username"
                  />
                  <label htmlFor="login-password">Contraseña</label>
                  <input
                    id="login-password"
                    name="password"
                    type="password"
                    value={loginForm.password}
                    onChange={handleLoginChange}
                    required
                    autoComplete="current-password"
                  />
                  <button type="submit">Entrar</button>
                </form>
              ) : (
                <form onSubmit={handleRegisterSubmit} className="form-grid">
                  <label htmlFor="register-username">Usuario</label>
                  <input
                    id="register-username"
                    name="username"
                    value={registerForm.username}
                    onChange={handleRegisterChange}
                    required
                  />
                  <label htmlFor="register-email">Correo</label>
                  <input
                    id="register-email"
                    name="email"
                    type="email"
                    value={registerForm.email}
                    onChange={handleRegisterChange}
                    required
                  />
                  <label htmlFor="register-password">Contraseña</label>
                  <input
                    id="register-password"
                    name="password"
                    type="password"
                    value={registerForm.password}
                    onChange={handleRegisterChange}
                    required
                  />
                  <button type="submit">Crear cuenta</button>
                </form>
              )}
            </div>
          )}
        </section>
      )}

      {activeSection === 'matches' && (
        <section>
          <h2>Planificador de partidas</h2>
          <p>Define el modo de juego y el número de participantes para adaptar la experiencia.</p>

          <form onSubmit={handleMatchCreate} className="form-grid">
            <label htmlFor="match-name">Nombre de la partida</label>
            <input
              id="match-name"
              name="name"
              value={matchConfig.name}
              onChange={handleMatchFieldChange}
              required
            />

            <label htmlFor="match-scenario">Escenario (opcional)</label>
            <input
              id="match-scenario"
              name="scenario"
              value={matchConfig.scenario}
              onChange={handleMatchFieldChange}
            />

            <label htmlFor="match-mode">Modo</label>
            <select id="match-mode" name="mode" value={matchConfig.mode} onChange={handleModeChange}>
              {Object.entries(modeSettings).map(([id, settings]) => (
                <option key={id} value={id}>
                  {settings.label}
                </option>
              ))}
            </select>
            <p className="field-hint">{activeModeSettings.description}</p>

            {activeModeSettings.min !== activeModeSettings.max && (
              <>
                <label htmlFor="match-slots">Número de jugadores</label>
                <input
                  id="match-slots"
                  type="range"
                  min={activeModeSettings.min}
                  max={activeModeSettings.max}
                  value={matchConfig.playerSlots}
                  onChange={handlePlayerSlotsChange}
                />
                <span className="field-hint">
                  {matchConfig.playerSlots} plazas configuradas (mínimo {activeModeSettings.min}, máximo{' '}
                  {activeModeSettings.max}).
                </span>
              </>
            )}

            {activeModeSettings.min === activeModeSettings.max && (
              <p className="field-hint">Este modo fija automáticamente {activeModeSettings.playerSlots} plazas.</p>
            )}

            <label htmlFor="match-opponent">Tipo de oponente</label>
            <select
              id="match-opponent"
              name="opponentType"
              value={matchConfig.opponentType}
              onChange={handleMatchFieldChange}
              disabled={matchConfig.mode === 'solo' || matchConfig.mode === 'solo_ai' || matchConfig.mode === 'tournament'}
            >
              <option value="ai">Inteligencia artificial</option>
              <option value="human">Jugador humano</option>
            </select>

            {requiresInvite && (
              <>
                <label htmlFor="match-invitee">Invitar a</label>
                <input
                  id="match-invitee"
                  name="invitee"
                  value={matchConfig.invitee}
                  onChange={handleMatchFieldChange}
                  placeholder="Nombre de usuario"
                />
              </>
            )}

            <button type="submit" disabled={!isLoggedIn}>
              {isLoggedIn ? 'Crear partida' : 'Inicia sesión para crear partidas'}
            </button>
          </form>

          <MatchGrid playerSlots={matchConfig.playerSlots} mode={matchConfig.mode} />

          <h3>Historial de partidas</h3>
          {isLoadingMatches && <p>Cargando partidas...</p>}
          {matchError && (
            <p role="alert" className="error-message">
              {matchError}
            </p>
          )}
          {!isLoadingMatches && !matches.length && <p>No hay partidas registradas todavía.</p>}
          <div className="match-list">
            {matches.map((match) => (
              <article key={match.id} className="match-card">
                <header>
                  <h4>{match.name}</h4>
                  <span className={`match-card__badge match-card__badge--${match.mode}`}>
                    {modeSettings[match.mode]?.label ?? match.mode}
                  </span>
                </header>
                <p>Escenario: {match.scenario || 'Libre'}</p>
                <p>Plazas configuradas: {match.player_slots}</p>
                <p>Tipo de oponente: {match.opponent_type === 'human' ? 'Humano' : 'Automatizado'}</p>
                <p>Estado: {match.status}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      {activeSection === 'tactics' && (
        <section>
          <h2>Centro táctico</h2>
          <form onSubmit={handleChatSubmit} className="form-grid">
            <label htmlFor="chat-provider">Proveedor</label>
            <select
              id="chat-provider"
              value={chatProvider}
              onChange={(event) => setChatProvider(event.target.value)}
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="lm_studio">LM Studio</option>
            </select>

            <label htmlFor="chat-message">Mensaje</label>
            <textarea
              id="chat-message"
              value={chatMessage}
              onChange={(event) => setChatMessage(event.target.value)}
              placeholder="Describe tu situación táctica o pide consejos específicos."
            />

            <button type="submit" disabled={isSendingChat}>
              {isSendingChat ? 'Enviando...' : 'Enviar consulta'}
            </button>
          </form>

          <div className="chat-log" aria-live="polite">
            {chatLog.map((entry, index) => (
              <div key={`${entry.role}-${index}`} className={`chat-log__entry chat-log__entry--${entry.role}`}>
                <strong>{entry.role === 'user' ? 'Comandante' : 'Asistente'}:</strong> {entry.message}
              </div>
            ))}
          </div>

          <VoiceInteraction onTranscript={handleVoiceTranscript} speechLocale="es-ES" />
        </section>
      )}

      {activeSection === 'tools' && (
        <section>
          <h2>Herramientas de apoyo</h2>
          <form onSubmit={handleDiceUpload} className="form-grid" encType="multipart/form-data">
            <label htmlFor="dice-image">Escáner de dados</label>
            <input id="dice-image" name="image" type="file" accept="image/*" />
            <button type="submit">Analizar imagen</button>
          </form>
          {diceError && (
            <p role="alert" className="error-message">
              {diceError}
            </p>
          )}
          {diceResult && (
            <div className="dice-results">
              <p>Puntos detectados: {diceResult.pip_count}</p>
              {!!diceResult.bounding_boxes?.length && (
                <details>
                  <summary>Áreas detectadas</summary>
                  <ul>
                    {diceResult.bounding_boxes.map((box, index) => (
                      <li key={`box-${index}`}>
                        x: {box.x}, y: {box.y}, ancho: {box.width}, alto: {box.height}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          )}
          {dicePreview && (
            <figure className="dice-preview">
              <img src={dicePreview} alt="Vista previa de los dados analizados" />
              <figcaption>Vista previa con contornos detectados.</figcaption>
            </figure>
          )}
        </section>
      )}
    </div>
  );
}

export default App;
