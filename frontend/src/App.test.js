import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

import App from './App';

jest.mock('./config', () => {
  const post = jest.fn();
  return {
    apiClient: { post },
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

    const input = screen.getByLabelText(/mensaje/i);
    fireEvent.change(input, { target: { value: 'Hola' } });

    const sendButton = screen.getByRole('button', { name: /enviar/i });
    fireEvent.click(sendButton);

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith('/api/chat', { message: 'Hola' })
    );

    expect(screen.getByText(/Respuesta: Hola comandante/i)).toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('muestra un mensaje de error cuando la petición falla', async () => {
    apiClient.post.mockRejectedValueOnce(new Error('Network error'));

    render(<App />);

    fireEvent.change(screen.getByLabelText(/mensaje/i), { target: { value: 'Hola' } });
    fireEvent.click(screen.getByRole('button', { name: /enviar/i }));

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent('No se pudo enviar el mensaje')
    );

    expect(screen.getByText(/Aún no hay respuesta/)).toBeInTheDocument();
  });
});
