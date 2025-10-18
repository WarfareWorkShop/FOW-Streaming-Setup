import { strict as assert } from 'node:assert';
import test from 'node:test';

import extractErrorMessage, { DEFAULT_ERROR_MESSAGE } from '../src/utils/errors.js';
import {
  buildMatchPayload,
  createInitialMatchConfig,
  modeSettings,
  requiresInvitee,
  sanitiseText,
  updateConfigForMode,
} from '../src/utils/matches.js';

test('extractErrorMessage returns fallback for empty input', () => {
  assert.equal(extractErrorMessage(null), DEFAULT_ERROR_MESSAGE);
});

test('extractErrorMessage prefers API response message', () => {
  const error = { response: { data: { message: 'Custom error' } } };
  assert.equal(extractErrorMessage(error), 'Custom error');
});

test('extractErrorMessage falls back to error.message when response message missing', () => {
  const error = { message: 'Local error' };
  assert.equal(extractErrorMessage(error), 'Local error');
});

test('extractErrorMessage uses fallback when messages are blank', () => {
  const error = { response: { data: { message: '   ' } } };
  assert.equal(extractErrorMessage(error, 'Otro error'), 'Otro error');
});

test('createInitialMatchConfig provides a fresh copy', () => {
  const first = createInitialMatchConfig();
  const second = createInitialMatchConfig();
  assert.notEqual(first, second, 'Each call should return a new object');
  assert.equal(first.mode, 'solo_ai');
  assert.equal(first.playerSlots, modeSettings.solo_ai.playerSlots);
});

test('updateConfigForMode syncs opponent type and slots', () => {
  const base = createInitialMatchConfig();
  const updated = updateConfigForMode(base, 'versus');
  assert.equal(updated.mode, 'versus');
  assert.equal(updated.opponentType, 'human');
  assert.equal(updated.playerSlots, modeSettings.versus.playerSlots);
});

test('buildMatchPayload normalises fields and keeps invitee only for human opponents', () => {
  const config = {
    name: '  Escaramuza  ',
    scenario: '  Campo abierto  ',
    opponentType: 'human',
    mode: 'versus',
    playerSlots: 5,
    invitee: '  aliado  ',
  };

  const payload = buildMatchPayload(config);
  assert.deepEqual(payload, {
    name: 'Escaramuza',
    scenario: 'Campo abierto',
    opponent_type: 'human',
    mode: 'versus',
    player_slots: 5,
    invitee_username: 'aliado',
  });
});

test('buildMatchPayload omits optional values when they are empty', () => {
  const config = {
    name: 'Operación',
    scenario: '   ',
    opponentType: 'ai',
    mode: 'solo_ai',
    playerSlots: undefined,
    invitee: '   ',
  };

  const payload = buildMatchPayload(config);
  assert.deepEqual(payload, {
    name: 'Operación',
    scenario: undefined,
    opponent_type: 'ai',
    mode: 'solo_ai',
    player_slots: modeSettings.solo_ai.playerSlots,
  });
});

test('requiresInvitee detects when invitees are mandatory', () => {
  assert.equal(
    requiresInvitee({ opponentType: 'human', mode: 'versus' }),
    true,
    'human opponents in versus mode require invitees',
  );
  assert.equal(
    requiresInvitee({ opponentType: 'ai', mode: 'solo_ai' }),
    false,
    'AI opponents do not require invitees',
  );
  assert.equal(
    requiresInvitee({ opponentType: 'human', mode: 'solo' }),
    false,
    'Solo mode does not require invitees despite human type',
  );
});

test('sanitiseText trims strings and tolerates non-string input', () => {
  assert.equal(sanitiseText('  ready  '), 'ready');
  assert.equal(sanitiseText(undefined), '');
  assert.equal(sanitiseText(null), '');
});
