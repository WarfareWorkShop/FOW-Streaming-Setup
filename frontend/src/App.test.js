import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

import App from './App';

const mockPost = jest.fn();
const mockGet = jest.fn();
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

    fireEvent.change(screen.getByLabelText(/Usuario/i), {
      target: { value: 'commander' },
    });
    fireEvent.change(screen.getByLabelText(/Contraseña/i), {
      target: { value: 'Password1!' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Entrar/i }));

    await waitFor(() => expect(mockPost).toHaveBeenCalledWith('/api/auth/login', expect.any(Object)));
    await waitFor(() => expect(mockSetAuthToken).toHaveBeenCalledWith('token-123'));

    fireEvent.change(screen.getByLabelText(/Nombre de la partida/i), {
      target: { value: 'Escaramuza' },
    });
    fireEvent.change(screen.getByLabelText(/Escenario/i), {
      target: { value: 'Campo abierto' },
    });

    const matchForm = screen.getByText(/Crear partida/i).closest('form');
    fireEvent.submit(matchForm);

    await waitFor(() => expect(mockPost).toHaveBeenCalledWith('/api/matches', expect.any(Object)));
    expect(screen.getByText(/Escaramuza/i)).toBeInTheDocument();
  });

  it('envía mensajes al asistente táctico', async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText(/Usuario/i), {
      target: { value: 'commander' },
    });
    fireEvent.change(screen.getByLabelText(/Contraseña/i), {
      target: { value: 'Password1!' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Entrar/i }));

    await waitFor(() => expect(mockSetAuthToken).toHaveBeenCalledWith('token-123'));

    const chatInput = screen.getByLabelText(/Mensaje/i);
    fireEvent.change(chatInput, { target: { value: 'Necesito un informe' } });
    fireEvent.click(screen.getByRole('button', { name: /Enviar/i }));

    await waitFor(() => expect(mockPost).toHaveBeenCalledWith('/api/chat', { message: 'Necesito un informe' }));
    expect(screen.getByText(/Informe táctico listo/i)).toBeInTheDocument();
  });
});
