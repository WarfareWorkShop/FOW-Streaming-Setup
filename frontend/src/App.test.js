import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

import App from './App';
import { DEFAULT_LANGUAGE, translate } from './i18n';

jest.mock('./auth', () => ({
  clearTokens: jest.fn(),
  isAuthenticated: jest.fn(() => true),
  setTokens: jest.fn(),
}));

jest.mock('./config', () => {
  const post = jest.fn();
  const get = jest.fn(() => Promise.resolve({ data: { username: 'Tester' } }));
  const del = jest.fn(() => Promise.resolve({}));
  return {
    apiClient: { post, get, delete: del },
    CHAT_ENDPOINT: '/api/chat',
  };
});

jest.mock('./config', () => ({
  AUTH_ENDPOINTS: {
    register: '/api/auth/register',
    login: '/api/auth/login',
    me: '/api/auth/me',
  },
  MATCHES_ENDPOINT: '/api/matches',
  DICE_SCAN_ENDPOINT: '/api/dice/scan',
  CHAT_ENDPOINT: '/api/chat',
  apiClient: {
    post: (...args) => mockPost(...args),
    get: (...args) => mockGet(...args),
    defaults: { headers: { common: {} } },
  },
  setAuthToken: (...args) => mockSetAuthToken(...args),
}));

describe('App', () => {
  beforeAll(() => {
    window.speechSynthesis = {
      cancel: jest.fn(),
      speak: jest.fn(),
    };
    window.SpeechSynthesisUtterance = function SpeechSynthesisUtterance(text) {
      this.text = text;
    };
  });

  beforeEach(() => {
    jest.clearAllMocks();
    mockGet.mockImplementation((url) => {
      if (url === '/api/auth/me') {
        return Promise.resolve({ data: { username: 'commander', email: 'cmd@example.com' } });
      }
      if (url === '/api/matches') {
        return Promise.resolve({ data: { matches: [] } });
      }
      return Promise.resolve({ data: {} });
    });
    mockPost.mockImplementation((url, payload) => {
      if (url === '/api/auth/login') {
        return Promise.resolve({ data: { token: 'token-123' } });
      }
      if (url === '/api/matches') {
        return Promise.resolve({
          data: {
            match: {
              id: 1,
              name: payload.name,
              scenario: payload.scenario,
              status: 'active',
              state: {
                turn: 'player',
                player: { units: 6, morale: 10, victory_points: 0 },
                ai: { units: 6, morale: 10, victory_points: 0 },
                log: [],
              },
              participants: [],
              invitations: [],
              events: [],
            },
          },
        });
      }
      if (url === '/api/matches/1/actions') {
        return Promise.resolve({
          data: {
            match: {
              id: 1,
              name: 'Escaramuza',
              scenario: 'Campo abierto',
              status: 'active',
              participants: [],
              invitations: [],
              events: [],
              state: {
                turn: 'player',
                player: { units: 6, morale: 10, victory_points: 1 },
                ai: { units: 5, morale: 10, victory_points: 0 },
                log: [{ actor: 'ai', text: 'Contraataque enemigo' }],
              },
            },
            state: {
              turn: 'player',
              player: { units: 6, morale: 10, victory_points: 1 },
              ai: { units: 5, morale: 10, victory_points: 0 },
              log: [{ actor: 'ai', text: 'Contraataque enemigo' }],
            },
          },
        });
      }
      if (url === '/api/chat') {
        return Promise.resolve({ data: { response: 'Informe táctico listo.' } });
      }
      return Promise.resolve({ data: {} });
    });
  });

  it('permite iniciar sesión y crear una partida contra la IA', async () => {
    render(<App />);

    await screen.findByText(/Sesión iniciada como/i);

    const input = screen.getByLabelText(/mensaje/i);
    fireEvent.change(input, { target: { value: 'Hola' } });

    fireEvent.click(screen.getByRole('button', { name: /Entrar/i }));

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith('/api/chat', {
        message: 'Hola',
        provider: 'openai',
      })
    );

    expect(screen.getByText(/Respuesta/i)).toBeInTheDocument();
    expect(screen.getByText('Hola comandante')).toBeInTheDocument();
  });

  it('muestra un mensaje de error cuando la petición falla', async () => {
    apiClient.post.mockRejectedValueOnce({ message: 'Network error' });

  it('envía mensajes al asistente táctico', async () => {
    render(<App />);

    await screen.findByText(/Sesión iniciada como/i);

    fireEvent.change(screen.getByLabelText(/mensaje/i), { target: { value: 'Hola' } });
    fireEvent.click(screen.getByRole('button', { name: /enviar/i }));

    const chatInput = screen.getByLabelText(/Mensaje/i);
    fireEvent.change(chatInput, { target: { value: 'Necesito un informe' } });
    fireEvent.click(screen.getByRole('button', { name: /Enviar/i }));

    await waitFor(() => expect(mockPost).toHaveBeenCalledWith('/api/chat', { message: 'Necesito un informe' }));
    expect(screen.getByText(/Informe táctico listo/i)).toBeInTheDocument();
  });
});
