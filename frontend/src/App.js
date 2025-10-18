import React, { useEffect, useMemo, useState } from 'react';

import './App.css';

import VoiceInteraction from './VoiceInteraction';
import { CHAT_ENDPOINT, apiClient } from './config';
import { clearTokens, isAuthenticated, setTokens } from './auth';

const initialBattleState = {
  turn: '',
  player: '',
  objective: '',
  enemyDisposition: '',
  weather: '',
  terrain: '',
  unitsText: '',
};

const initialArmyState = {
  faction: '',
  points: '',
  unitsText: '',
};

const initialCoachState = {
  role: '',
  focus: '',
  goal: '',
  message: '',
};

const parseUnits = (text) =>
  text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [name = '', role = '', strength = ''] = line.split('|');
      return { name: name.trim(), role: role.trim(), strength: strength.trim() };
    });

const extractErrorMessage = (error, fallback = 'Ocurrió un error inesperado.') => {
  if (!error) {
    return fallback;
  }
  const message = error?.response?.data?.error || error?.response?.data?.message;
  if (typeof message === 'string' && message.trim()) {
    return message;
  }
  if (error.message) {
    return error.message;
  }
  return fallback;
};

function App() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [chatProvider, setChatProvider] = useState('openai');
  const [isLoading, setIsLoading] = useState(false);
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

  const [authState, setAuthState] = useState({
    status: isAuthenticated() ? 'pending' : 'anonymous',
    profile: null,
    error: null,
  });
  const [loginForm, setLoginForm] = useState({ username: '', password: '', captchaToken: '' });
  const [registerForm, setRegisterForm] = useState({
    username: '',
    email: '',
    password: '',
    captchaToken: '',
  });

  const [battleState, setBattleState] = useState(initialBattleState);
  const [scenarioAdvice, setScenarioAdvice] = useState('');
  const [armyState, setArmyState] = useState(initialArmyState);
  const [armyFeedback, setArmyFeedback] = useState('');
  const [coachState, setCoachState] = useState(initialCoachState);
  const [coachAdvice, setCoachAdvice] = useState('');

  const [turnEntries, setTurnEntries] = useState([]);
  const [logTitle, setLogTitle] = useState('Partida amistosa');
  const [logScenario, setLogScenario] = useState('');
  const [logs, setLogs] = useState([]);
  const [logsError, setLogsError] = useState(null);
  const [autoSendVoice, setAutoSendVoice] = useState(true);
  const [activeSection, setActiveSection] = useState('command');

  const sectionTabs = [
    { id: 'command', label: 'Centro de mando', description: 'Vista general y accesos rápidos.' },
    { id: 'tournaments', label: 'Torneos', description: 'Configura partidas competitivas.' },
    { id: 'solo', label: 'Solo mode', description: 'Entrena y perfecciona tus listas.' },
    { id: 'solo-ai', label: 'Solo vs IA', description: 'Practica con el asistente virtual.' },
  ];

  const isLoggedIn = useMemo(() => authState.status === 'ready', [authState.status]);

  const loadProfile = async () => {
    try {
      const { data } = await apiClient.get('/api/auth/me');
      setAuthState({ status: 'ready', profile: data, error: null });
    } catch (profileError) {
      clearTokens();
      setAuthState({ status: 'anonymous', profile: null, error: null });
    }
  };

  useEffect(() => {
    if (authState.status === 'pending') {
      loadProfile();
    }
  }, [authState.status]);

  const loadLogs = async () => {
    if (!isLoggedIn) {
      return;
    }
    try {
      const { data } = await apiClient.get('/api/tactics/logs');
      setLogs(data?.logs ?? []);
      setLogsError(null);
    } catch (fetchError) {
      setLogsError(extractErrorMessage(fetchError, 'No se pudieron cargar los registros.'));
    }
  };

  useEffect(() => {
    if (isLoggedIn) {
      loadLogs();
    }
  }, [isLoggedIn]);

  const sendMessage = async (messageToSend = message) => {
    const trimmedMessage = messageToSend.trim();

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
      const res = await apiClient.post(CHAT_ENDPOINT, {
        message: trimmedMessage,
        provider: chatProvider,
      });
      setResponse(res?.data?.response ?? '');
      setMessage('');
      setTurnEntries((entries) => [
        ...entries,
        {
          timestamp: new Date().toISOString(),
          source: 'chat',
          content: trimmedMessage,
          reply: res?.data?.response ?? '',
        },
      ]);
    } catch (err) {
      setError(extractErrorMessage(err, 'No se pudo enviar el mensaje. Inténtalo nuevamente.'));
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

    setTurnEntries((entries) => [
      ...entries,
      {
        timestamp: new Date().toISOString(),
        source: 'voice',
        content: transcript.trim(),
      },
    ]);

    if (autoSendVoice) {
      setMessage(transcript);
      sendMessage(transcript);
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

  const handleLogin = async (event) => {
    event.preventDefault();
    try {
      const { data } = await apiClient.post('/api/auth/login', loginForm, { skipAuth: true });
      setTokens({
        accessToken: data?.accessToken,
        refreshToken: data?.refreshToken,
        expiresIn: data?.expiresIn,
      });
      setAuthState((state) => ({ ...state, status: 'pending', error: null }));
      setLoginForm({ username: '', password: '', captchaToken: '' });
    } catch (loginError) {
      setAuthState({ status: 'anonymous', profile: null, error: extractErrorMessage(loginError) });
    }
  };

  const handleRegister = async (event) => {
    event.preventDefault();
    try {
      await apiClient.post('/api/auth/register', registerForm, { skipAuth: true });
      setRegisterForm({ username: '', email: '', password: '', captchaToken: '' });
      setAuthState((state) => ({ ...state, error: null }));
    } catch (registerError) {
      setAuthState((state) => ({
        ...state,
        error: extractErrorMessage(registerError, 'No se pudo registrar al usuario.'),
      }));
    }
  };

  const handleLogout = async () => {
    try {
      await apiClient.post('/api/auth/logout');
    } catch (logoutError) {
      console.warn('Error revoking token', logoutError);
    }
    clearTokens();
    setAuthState({ status: 'anonymous', profile: null, error: null });
  };

  const requestScenarioAdvice = async () => {
    setScenarioAdvice('');
    try {
      const { data } = await apiClient.post('/api/tactics/scenario-advice', {
        provider: chatProvider,
        battleState: {
          turn: battleState.turn,
          player: battleState.player,
          objective: battleState.objective,
          enemyDisposition: battleState.enemyDisposition,
          weather: battleState.weather,
          terrain: battleState.terrain,
          units: parseUnits(battleState.unitsText),
        },
      });
      setScenarioAdvice(data?.analysis ?? '');
    } catch (scenarioError) {
      setScenarioAdvice(extractErrorMessage(scenarioError));
    }
  };

  const requestArmyFeedback = async () => {
    setArmyFeedback('');
    try {
      const { data } = await apiClient.post('/api/tactics/army-list', {
        provider: chatProvider,
        faction: armyState.faction,
        points: armyState.points,
        units: parseUnits(armyState.unitsText),
      });
      setArmyFeedback(data?.analysis ?? '');
    } catch (armyError) {
      setArmyFeedback(extractErrorMessage(armyError));
    }
  };

  const requestCoachAdvice = async () => {
    setCoachAdvice('');
    try {
      const { data } = await apiClient.post('/api/tactics/coach', {
        provider: chatProvider,
        ...coachState,
      });
      setCoachAdvice(data?.coaching ?? '');
    } catch (coachError) {
      setCoachAdvice(extractErrorMessage(coachError));
    }
  };

  const saveLog = async () => {
    if (turnEntries.length === 0) {
      setLogsError('Necesitas al menos una entrada para guardar un registro.');
      return;
    }

    try {
      await apiClient.post('/api/tactics/logs', {
        title: logTitle,
        scenario: logScenario,
        entries: turnEntries,
      });
      setTurnEntries([]);
      setLogScenario('');
      setLogsError(null);
      await loadLogs();
    } catch (saveError) {
      setLogsError(extractErrorMessage(saveError, 'No se pudo guardar el registro.'));
    }
  };

  const deleteLog = async (id) => {
    try {
      await apiClient.delete(`/api/tactics/logs/${id}`);
      await loadLogs();
    } catch (deleteError) {
      setLogsError(extractErrorMessage(deleteError, 'No se pudo eliminar el registro.'));
    }
  };

  const renderAuthSection = () => (
    <section>
      <h2>Acceso</h2>
      {authState.error && (
        <p role="alert" style={{ color: 'red' }}>
          {authState.error}
        </p>
      )}
      {isLoggedIn ? (
        <div>
          <p>
            Sesión iniciada como <strong>{authState.profile?.username}</strong>
          </p>
          <button type="button" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
          <form onSubmit={handleLogin} style={{ minWidth: '260px' }}>
            <h3>Iniciar sesión</h3>
            <label htmlFor="login-username">Usuario</label>
            <input
              id="login-username"
              type="text"
              value={loginForm.username}
              onChange={(event) =>
                setLoginForm((form) => ({ ...form, username: event.target.value }))
              }
              required
            />
            <label htmlFor="login-password">Contraseña</label>
            <input
              id="login-password"
              type="password"
              value={loginForm.password}
              onChange={(event) =>
                setLoginForm((form) => ({ ...form, password: event.target.value }))
              }
              required
            />
            <button type="submit">Entrar</button>
          </form>

          <form onSubmit={handleRegister} style={{ minWidth: '260px' }}>
            <h3>Crear cuenta</h3>
            <label htmlFor="register-username">Usuario</label>
            <input
              id="register-username"
              type="text"
              value={registerForm.username}
              onChange={(event) =>
                setRegisterForm((form) => ({ ...form, username: event.target.value }))
              }
              required
            />
            <label htmlFor="register-email">Correo</label>
            <input
              id="register-email"
              type="email"
              value={registerForm.email}
              onChange={(event) =>
                setRegisterForm((form) => ({ ...form, email: event.target.value }))
              }
              required
            />
            <label htmlFor="register-password">Contraseña</label>
            <input
              id="register-password"
              type="password"
              value={registerForm.password}
              onChange={(event) =>
                setRegisterForm((form) => ({ ...form, password: event.target.value }))
              }
              required
            />
            <button type="submit">Registrarme</button>
          </form>
        </div>
      )}
    </section>
  );

  const renderChatSection = () => (
    <section>
      <h2>Asistente táctico en vivo</h2>
      <form onSubmit={handleSubmit}>
        <label htmlFor="chat-message">Mensaje</label>
        <input
          id="chat-message"
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Describe tu situación de batalla..."
          aria-label="mensaje"
          disabled={!isLoggedIn}
        />
        <label htmlFor="chat-provider">Proveedor de IA</label>
        <select
          id="chat-provider"
          value={chatProvider}
          onChange={(event) => setChatProvider(event.target.value)}
        >
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic</option>
          <option value="lmstudio">LM Studio</option>
        </select>
        <button type="submit" disabled={isLoading || !isLoggedIn}>
          {isLoading ? 'Enviando...' : 'Enviar'}
        </button>
      </form>
      {!isLoggedIn && <p>Inicia sesión para conversar con el asistente.</p>}
      {isLoading && <p role="status">Enviando mensaje...</p>}
      {error && (
        <p role="alert" style={{ color: 'red' }}>
          {errorMessage}
        </p>
      )}
      <article>
        <h3>Respuesta</h3>
        <p>{response || 'Aún no hay respuesta.'}</p>
      </article>
      <div>
        <label htmlFor="auto-send-voice">
          <input
            id="auto-send-voice"
            type="checkbox"
            checked={autoSendVoice}
            onChange={(event) => setAutoSendVoice(event.target.checked)}
            disabled={!isLoggedIn}
          />
          Enviar automáticamente las transcripciones de voz al chat
        </label>
      </div>
      <VoiceInteraction onTranscript={handleVoiceTranscript} />
    </section>
  );

  const renderScenarioSection = () => (
    <section>
      <h2>Consejero de escenario</h2>
      <div className="form-grid">
        <label htmlFor="battle-turn">Turno</label>
        <input
          id="battle-turn"
          type="text"
          value={battleState.turn}
          onChange={(event) =>
            setBattleState((state) => ({ ...state, turn: event.target.value }))
          }
          disabled={!isLoggedIn}
        />
        <label htmlFor="battle-player">Jugador</label>
        <input
          id="battle-player"
          type="text"
          value={battleState.player}
          onChange={(event) =>
            setBattleState((state) => ({ ...state, player: event.target.value }))
          }
          disabled={!isLoggedIn}
        />
        <label htmlFor="battle-objective">Objetivo</label>
        <input
          id="battle-objective"
          type="text"
          value={battleState.objective}
          onChange={(event) =>
            setBattleState((state) => ({ ...state, objective: event.target.value }))
          }
          disabled={!isLoggedIn}
        />
        <label htmlFor="battle-enemy">Disposición enemiga</label>
        <textarea
          id="battle-enemy"
          value={battleState.enemyDisposition}
          onChange={(event) =>
            setBattleState((state) => ({ ...state, enemyDisposition: event.target.value }))
          }
          disabled={!isLoggedIn}
        />
        <label htmlFor="battle-weather">Clima</label>
        <input
          id="battle-weather"
          type="text"
          value={battleState.weather}
          onChange={(event) =>
            setBattleState((state) => ({ ...state, weather: event.target.value }))
          }
          disabled={!isLoggedIn}
        />
        <label htmlFor="battle-terrain">Terreno</label>
        <textarea
          id="battle-terrain"
          value={battleState.terrain}
          onChange={(event) =>
            setBattleState((state) => ({ ...state, terrain: event.target.value }))
          }
          disabled={!isLoggedIn}
        />
        <label htmlFor="battle-units">Unidades aliadas (nombre|rol|estado)</label>
        <textarea
          id="battle-units"
          value={battleState.unitsText}
          onChange={(event) =>
            setBattleState((state) => ({ ...state, unitsText: event.target.value }))
          }
          placeholder="Sherman Platoon|Blindados|4 tanques operativos"
          disabled={!isLoggedIn}
        />
      </div>
      <button type="button" onClick={requestScenarioAdvice} disabled={!isLoggedIn}>
        Analizar escenario
      </button>
      <article>
        <h3>Sugerencias tácticas</h3>
        <p>{scenarioAdvice || 'Describe el estado de la batalla para recibir recomendaciones.'}</p>
      </article>
    </section>
  );

  const renderArmySection = () => (
    <section>
      <h2>Analizador de listas de ejército</h2>
      <label htmlFor="army-faction">Facción</label>
      <input
        id="army-faction"
        type="text"
        value={armyState.faction}
        onChange={(event) => setArmyState((state) => ({ ...state, faction: event.target.value }))}
        disabled={!isLoggedIn}
      />
      <label htmlFor="army-points">Puntos totales</label>
      <input
        id="army-points"
        type="number"
        value={armyState.points}
        onChange={(event) => setArmyState((state) => ({ ...state, points: event.target.value }))}
        disabled={!isLoggedIn}
      />
      <label htmlFor="army-units">Unidades (nombre|rol|detalles)</label>
      <textarea
        id="army-units"
        value={armyState.unitsText}
        onChange={(event) =>
          setArmyState((state) => ({ ...state, unitsText: event.target.value }))
        }
        placeholder="Infantería Motorizada|Línea|2 pelotones completos"
        disabled={!isLoggedIn}
      />
      <button type="button" onClick={requestArmyFeedback} disabled={!isLoggedIn}>
        Evaluar lista
      </button>
      <article>
        <h3>Retroalimentación</h3>
        <p>{armyFeedback || 'Obtén consejos sobre sinergias y mejoras potenciales.'}</p>
      </article>
    </section>
  );

  const renderCoachSection = () => (
    <section>
      <h2>Entrenador táctico</h2>
      <label htmlFor="coach-role">Rol táctico deseado</label>
      <input
        id="coach-role"
        type="text"
        value={coachState.role}
        onChange={(event) => setCoachState((state) => ({ ...state, role: event.target.value }))}
        disabled={!isLoggedIn}
      />
      <label htmlFor="coach-focus">Enfoque estratégico</label>
      <input
        id="coach-focus"
        type="text"
        value={coachState.focus}
        onChange={(event) => setCoachState((state) => ({ ...state, focus: event.target.value }))}
        disabled={!isLoggedIn}
      />
      <label htmlFor="coach-goal">Meta del jugador</label>
      <input
        id="coach-goal"
        type="text"
        value={coachState.goal}
        onChange={(event) => setCoachState((state) => ({ ...state, goal: event.target.value }))}
        disabled={!isLoggedIn}
      />
      <label htmlFor="coach-message">Situación actual</label>
      <textarea
        id="coach-message"
        value={coachState.message}
        onChange={(event) => setCoachState((state) => ({ ...state, message: event.target.value }))}
        disabled={!isLoggedIn}
      />
      <button type="button" onClick={requestCoachAdvice} disabled={!isLoggedIn}>
        Solicitar orientación
      </button>
      <article>
        <h3>Consejos del entrenador</h3>
        <p>{coachAdvice || 'Solicita al entrenador que refuerce tu plan de juego.'}</p>
      </article>
    </section>
  );

  const renderLogSection = () => (
    <section>
      <h2>Bitácora de turnos y repeticiones</h2>
      <p>
        Usa la transcripción de voz para registrar órdenes, impactos y bajas. Guarda la partida para
        construir tu biblioteca de análisis.
      </p>
      <div className="form-grid">
        <label htmlFor="log-title">Título</label>
        <input
          id="log-title"
          type="text"
          value={logTitle}
          onChange={(event) => setLogTitle(event.target.value)}
          disabled={!isLoggedIn}
        />
        <label htmlFor="log-scenario">Escenario / Misión</label>
        <input
          id="log-scenario"
          type="text"
          value={logScenario}
          onChange={(event) => setLogScenario(event.target.value)}
          disabled={!isLoggedIn}
        />
      </div>
      <button type="button" onClick={saveLog} disabled={!isLoggedIn}>
        Guardar registro de la partida
      </button>
      {logsError && (
        <p role="alert" style={{ color: 'red' }}>
          {logsError}
        </p>
      )}
      <article>
        <h3>Eventos recientes</h3>
        <ul>
          {turnEntries.map((entry) => (
            <li key={`${entry.timestamp}-${entry.source}`}>
              <strong>{new Date(entry.timestamp).toLocaleTimeString()}:</strong> {entry.source} –{' '}
              {entry.content}
              {entry.reply ? (
                <em>
                  {' '}
                  → IA: {entry.reply}
                </em>
              ) : null}
            </li>
          ))}
          {turnEntries.length === 0 && <li>Aún no hay eventos registrados.</li>}
        </ul>
      </article>
      <article>
        <h3>Replays almacenados</h3>
        <ul>
          {logs.map((log) => (
            <li key={log.id}>
              <strong>{log.title}</strong> — {new Date(log.createdAt).toLocaleString()} —{' '}
              {log.scenario || 'Escenario no especificado'}
              <button type="button" onClick={() => deleteLog(log.id)} style={{ marginLeft: '1rem' }}>
                Eliminar
              </button>
              <details>
                <summary>Ver entradas</summary>
                <ul>
                  {(log.entries || []).map((entry, index) => (
                    <li key={`${log.id}-${index}`}>
                      <strong>{entry.source}</strong>: {entry.content}
                      {entry.reply ? <em> → IA: {entry.reply}</em> : null}
                    </li>
                  ))}
                </ul>
              </details>
            </li>
          ))}
          {logs.length === 0 && <li>No hay registros guardados todavía.</li>}
        </ul>
      </article>
    </section>
  );

  const renderToolLinks = () => (
    <section>
      <h2>Herramientas Flames of War recomendadas</h2>
      <div className="tool-buttons">
        <a
          className="tool-button"
          href="https://warfareworkshop.com/generators/fow-tools/fow-card-generator/"
          target="_blank"
          rel="noreferrer"
        >
          Generador de cartas
        </a>
        <a
          className="tool-button"
          href="https://warfareworkshop.com/generators/fow-tools/miniature-generator/"
          target="_blank"
          rel="noreferrer"
        >
          Generador de miniaturas
        </a>
        <a
          className="tool-button"
          href="https://warfareworkshop.com/generators/fow-tools/fow-mission-generator/"
          target="_blank"
          rel="noreferrer"
        >
          Generador de misiones
        </a>
      </div>
    </section>
  );

  const renderNavigation = () => (
    <nav className="section-tabs" aria-label="Modos principales">
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
  );

  const renderCommandCenter = () => (
    <>
      <section>
        <h2>Centro de mando</h2>
        <p>
          Todo lo esencial en un solo lugar: inicia sesión, configura tus herramientas preferidas y
          revisa de un vistazo lo que puedes hacer con el asistente de Flames of War. Este panel está
          pensado para comandantes que quieren resultados rápidos sin perderse en menús avanzados.
        </p>
        <ol>
          <li>Accede con tu cuenta o crea una nueva en segundos.</li>
          <li>Elige tus herramientas favoritas y guárdalas como referencia.</li>
          <li>Vuelve cuando quieras para retomar tus partidas o preparar nuevas misiones.</li>
        </ol>
      </section>
      {renderAuthSection()}
      {renderToolLinks()}
    </>
  );

  const renderTournaments = () => (
    <>
      <section>
        <h2>Preparación para torneos</h2>
        <p>
          Organiza partidas competitivas con plantillas claras para escenarios, anotaciones y
          replays. Usa estas herramientas para dejar todo registrado y compartirlo con tus compañeros
          de equipo antes y después del evento.
        </p>
        <ul>
          <li>Define el contexto del enfrentamiento con el Consejero de escenario.</li>
          <li>Registra turnos clave y replays en la bitácora integrada.</li>
          <li>Conserva todo en tu cuenta para consultar historiales cuando los necesites.</li>
        </ul>
      </section>
      {renderScenarioSection()}
      {renderLogSection()}
    </>
  );

  const renderSoloMode = () => (
    <>
      <section>
        <h2>Solo mode</h2>
        <p>
          Entrena sin presión, ajusta tus listas y recibe consejos personalizados para mejorar tus
          maniobras. Está diseñado para jugadores que quieren experimentar con estrategias a su ritmo
          y documentar aprendizajes clave.
        </p>
        <ul>
          <li>Analiza tus listas y detecta sinergias con el Analizador de ejército.</li>
          <li>Simula situaciones específicas y pide orientación al Entrenador táctico.</li>
          <li>Combina ambos análisis para diseñar sesiones de práctica efectivas.</li>
        </ul>
      </section>
      {renderArmySection()}
      {renderCoachSection()}
    </>
  );

  const renderSoloVsAI = () => (
    <>
      <section>
        <h2>Solo vs IA</h2>
        <p>
          Conversa con el asistente táctico para simular órdenes, recibir contraataques sugeridos y
          perfeccionar tus respuestas. Controla la experiencia con voz o texto y guarda los turnos
          memorables para repasar después.
        </p>
        <ul>
          <li>Describe la situación actual y deja que la IA responda al instante.</li>
          <li>Activa la transcripción de voz para un flujo de juego más inmersivo.</li>
          <li>Revisa el historial de turnos guardado automáticamente en la sección de torneos.</li>
        </ul>
      </section>
      {renderChatSection()}
    </>
  );

  return (
    <div className="app-container">
      <header>
        <h1>Flames of War - Centro táctico asistido por IA</h1>
        <p>
          Diseñado para comandantes de Flames of War que buscan consejos rápidos, evaluaciones de
          listas y control histórico de sus partidas.
        </p>
      </header>

      {renderNavigation()}

      <main>
        {activeSection === 'command' && renderCommandCenter()}
        {activeSection === 'tournaments' && renderTournaments()}
        {activeSection === 'solo' && renderSoloMode()}
        {activeSection === 'solo-ai' && renderSoloVsAI()}
      </main>
    </div>
  );
}

export default App;
