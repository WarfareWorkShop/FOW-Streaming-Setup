import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

import App from './App';

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

const { apiClient } = require('./config');

describe('App', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('envía un mensaje y muestra la respuesta del backend', async () => {
    apiClient.post.mockResolvedValueOnce({ data: { response: 'Hola comandante' } });

    render(<App />);

    await screen.findByText(/Sesión iniciada como/i);

    const input = screen.getByLabelText(/mensaje/i);
    fireEvent.change(input, { target: { value: 'Hola' } });

    const sendButton = screen.getByRole('button', { name: /enviar/i });
    fireEvent.click(sendButton);

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

    render(<App />);

    await screen.findByText(/Sesión iniciada como/i);

    fireEvent.change(screen.getByLabelText(/mensaje/i), { target: { value: 'Hola' } });
    fireEvent.click(screen.getByRole('button', { name: /enviar/i }));

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent('No se pudo enviar el mensaje')
    );

    expect(screen.getByText(/Aún no hay respuesta/)).toBeInTheDocument();
  });
});
