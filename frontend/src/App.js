import React, { useCallback, useMemo, useState } from 'react';

import VoiceInteraction from './VoiceInteraction';
import { CHAT_ENDPOINT, apiClient } from './config';
import {
  DEFAULT_LANGUAGE,
  SUPPORTED_LANGUAGES,
  getLanguageLabel,
  getSpeechRecognitionLocale,
  normaliseLanguage,
  translate,
} from './i18n';

function App() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorKey, setErrorKey] = useState(null);
  const [language, setLanguage] = useState(DEFAULT_LANGUAGE);

  const normalisedLanguage = useMemo(() => normaliseLanguage(language), [language]);

  const t = useCallback(
    (key, replacements) => translate(key, normalisedLanguage, replacements),
    [normalisedLanguage]
  );

  const speechLocale = useMemo(
    () => getSpeechRecognitionLocale(normalisedLanguage),
    [normalisedLanguage]
  );

  const errorMessage = errorKey ? t(errorKey) : null;

  const handleLanguageChange = useCallback((event) => {
    setLanguage(normaliseLanguage(event.target.value));
  }, []);

  const sendMessage = async (messageToSend = message) => {
    const trimmedMessage = messageToSend.trim();

    if (!trimmedMessage) {
      setErrorKey('app.errors.emptyMessage');
      return;
    }

    setIsLoading(true);
    setErrorKey(null);

    try {
      const res = await apiClient.post(
        CHAT_ENDPOINT,
        { message: trimmedMessage },
        { headers: { 'Accept-Language': normalisedLanguage } }
      );
      setResponse(res?.data?.response ?? '');
      setMessage('');
    } catch (err) {
      console.error(err);
      setErrorKey('app.errors.sendFailed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceTranscript = (transcript) => {
    if (!transcript || !transcript.trim()) {
      return;
    }

    setMessage(transcript);
    sendMessage(transcript);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    sendMessage();
  };

  return (
    <div>
      <h1>{t('app.title')}</h1>
      <div>
        <label htmlFor="language-select">{t('languageSelector.label')}</label>{' '}
        <select
          id="language-select"
          value={normalisedLanguage}
          onChange={handleLanguageChange}
        >
          {SUPPORTED_LANGUAGES.map((code) => (
            <option key={code} value={code}>
              {getLanguageLabel(code)}
            </option>
          ))}
        </select>
      </div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={t('app.placeholder')}
          aria-label={t('app.labels.message')}
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? t('app.buttons.sending') : t('app.buttons.send')}
        </button>
      </form>
      {isLoading && <p role="status">{t('app.status.sending')}</p>}
      {errorMessage && (
        <p role="alert" style={{ color: 'red' }}>
          {errorMessage}
        </p>
      )}
      <p>{t('app.response', { response: response || t('app.status.noResponse') })}</p>
      <VoiceInteraction
        speechLocale={speechLocale}
        onTranscript={handleVoiceTranscript}
        t={t}
      />
    </div>
  );
}

export default App;
