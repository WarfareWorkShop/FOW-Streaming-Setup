import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

import App from './App';
import { DEFAULT_LANGUAGE, translate } from './i18n';

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

  const t = (key, replacements) => translate(key, DEFAULT_LANGUAGE, replacements);

  it('envía un mensaje y muestra la respuesta del backend', async () => {
    apiClient.post.mockResolvedValueOnce({ data: { response: 'Hola comandante' } });

    render(<App />);

    const input = screen.getByLabelText(t('app.labels.message'));
    fireEvent.change(input, { target: { value: 'Hola' } });

    const sendButton = screen.getByRole('button', { name: t('app.buttons.send') });
    fireEvent.click(sendButton);

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/chat',
        { message: 'Hola' },
        { headers: { 'Accept-Language': DEFAULT_LANGUAGE } }
      )
    );

    expect(
      screen.getByText(t('app.response', { response: 'Hola comandante' }))
    ).toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('muestra un mensaje de error cuando la petición falla', async () => {
    apiClient.post.mockRejectedValueOnce(new Error('Network error'));

    render(<App />);

    fireEvent.change(screen.getByLabelText(t('app.labels.message')), {
      target: { value: 'Hola' },
    });
    fireEvent.click(screen.getByRole('button', { name: t('app.buttons.send') }));

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(t('app.errors.sendFailed'))
    );

    expect(screen.getByText(t('app.status.noResponse'))).toBeInTheDocument();
  });
});
