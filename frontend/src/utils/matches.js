export const modeSettings = {
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

export const createInitialMatchConfig = () => ({
  name: '',
  scenario: '',
  opponentType: 'ai',
  mode: 'solo_ai',
  playerSlots: modeSettings.solo_ai.playerSlots,
  invitee: '',
});

export const initialMatchConfig = createInitialMatchConfig();

export const updateConfigForMode = (currentConfig, mode) => {
  const settings = modeSettings[mode];
  if (!settings) {
    return currentConfig;
  }

  return {
    ...currentConfig,
    mode,
    opponentType: settings.opponentType,
    playerSlots: settings.playerSlots,
  };
};

export const sanitiseText = (value) => (typeof value === 'string' ? value.trim() : '');

export const buildMatchPayload = (config) => {
  const baseSettings = modeSettings[config.mode] ?? modeSettings.versus;

  const payload = {
    name: sanitiseText(config.name),
    scenario: sanitiseText(config.scenario) || undefined,
    opponent_type: config.opponentType ?? baseSettings.opponentType,
    mode: config.mode,
    player_slots:
      Number.isFinite(config.playerSlots) && config.playerSlots > 0
        ? Number(config.playerSlots)
        : baseSettings.playerSlots,
  };

  const invitee = sanitiseText(config.invitee);
  if (payload.opponent_type === 'human' && invitee) {
    payload.invitee_username = invitee;
  }

  return payload;
};

export const requiresInvitee = (config) =>
  (config.opponentType ?? modeSettings[config.mode]?.opponentType) === 'human' &&
  (config.mode ?? 'versus') !== 'solo';

export default {
  modeSettings,
  createInitialMatchConfig,
  initialMatchConfig,
  updateConfigForMode,
  buildMatchPayload,
  requiresInvitee,
  sanitiseText,
};
