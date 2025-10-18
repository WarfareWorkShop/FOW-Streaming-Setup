import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

import App from './App';

const mockClearTokens = jest.fn();
const mockIsAuthenticated = jest.fn(() => true);
const mockSetTokens = jest.fn();

jest.mock('./auth', () => ({
  clearTokens: (...args) => mockClearTokens(...args),
  isAuthenticated: (...args) => mockIsAuthenticated(...args),
  setTokens: (...args) => mockSetTokens(...args),
}));

const mockPost = jest.fn();
const mockGet = jest.fn();
const mockDelete = jest.fn();
const mockSetAuthToken = jest.fn();

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
    delete: (...args) => mockDelete(...args),
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

    mockIsAuthenticated.mockReturnValue(true);

    mockGet.mockImplementation((url) => {
      if (url === '/api/auth/me') {
        return Promise.resolve({ data: { username: 'commander', email: 'cmd@example.com' } });
      }
      if (url === '/api/matches') {
        return Promise.resolve({ data: { matches: [] } });
      }
      return Promise.resolve({ data: {} });
    });

    let matchId = 1;
    mockPost.mockImplementation((url, payload) => {
      if (url === '/api/chat') {
        return Promise.resolve({ data: { response: 'Informe táctico listo.' } });
      }
      if (url === '/api/matches') {
        return Promise.resolve({
          data: {
            match: {
              id: matchId++,
              name: payload.name,
              scenario: payload.scenario ?? '',
              status: 'active',
              mode: payload.mode,
              player_slots: payload.player_slots,
              opponent_type: payload.opponent_type,
            },
          },
        });
      }
      return Promise.resolve({ data: {} });
    });
  });

  it('renderiza el perfil y permite enviar una consulta táctica', async () => {
    render(<App />);

    await screen.findByText(/Sesión iniciada como/i);

    fireEvent.click(screen.getByRole('button', { name: /Tácticas y voz/i }));

    const textarea = await screen.findByLabelText(/Mensaje/i);
    fireEvent.change(textarea, { target: { value: 'Necesito un informe' } });

    fireEvent.click(screen.getByRole('button', { name: /Enviar consulta/i }));

    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith('/api/chat', {
        message: 'Necesito un informe',
        provider: 'openai',
      }),
    );

    expect(await screen.findByText(/Informe táctico listo/i)).toBeInTheDocument();
  });

  it('muestra un mensaje de error cuando la consulta falla', async () => {
    mockPost.mockImplementationOnce(() => Promise.reject(new Error('Network error')));

    render(<App />);

    await screen.findByText(/Sesión iniciada como/i);
    fireEvent.click(screen.getByRole('button', { name: /Tácticas y voz/i }));

    fireEvent.change(screen.getByLabelText(/Mensaje/i), { target: { value: 'Necesito apoyo' } });
    fireEvent.click(screen.getByRole('button', { name: /Enviar consulta/i }));

    expect(await screen.findByText('Network error')).toBeInTheDocument();
  });

  it('crea una partida contra la IA y la muestra en el historial', async () => {
    render(<App />);

    await screen.findByText(/Sesión iniciada como/i);
    fireEvent.click(screen.getByRole('button', { name: /Partidas/i }));

    fireEvent.change(screen.getByLabelText(/Nombre de la partida/i), { target: { value: 'Escaramuza' } });
    fireEvent.change(screen.getByLabelText(/Escenario \(opcional\)/i), { target: { value: 'Campo abierto' } });

    fireEvent.click(screen.getByRole('button', { name: /Crear partida/i }));

    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith(
        '/api/matches',
        expect.objectContaining({
          name: 'Escaramuza',
          mode: 'solo_ai',
          opponent_type: 'ai',
          player_slots: expect.any(Number),
        }),
      ),
    );

    expect(await screen.findByText('Escaramuza')).toBeInTheDocument();
    expect(screen.getByText(/Partida creada correctamente/i)).toBeInTheDocument();
  });
});
