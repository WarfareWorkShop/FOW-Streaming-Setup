import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';

const SpeechRecognition =
  (typeof window !== 'undefined' &&
    (window.SpeechRecognition || window.webkitSpeechRecognition || null)) ||
  null;

const VoiceInteraction = ({ onTranscript = () => {}, speechLocale = 'es-ES', t }) => {
  const recognitionRef = useRef(null);
  const [text, setText] = useState('');
  const [isSupported, setIsSupported] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [errorKey, setErrorKey] = useState(null);

  const errorMessage = useMemo(() => (errorKey && t ? t(errorKey) : null), [errorKey, t]);

  useEffect(() => {
    if (!SpeechRecognition) {
      setIsSupported(false);
      return undefined;
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = speechLocale;

    recognition.onresult = (event) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }

      if (finalTranscript) {
        const normalizedTranscript = finalTranscript.trim();
        setText(normalizedTranscript);
        onTranscript(normalizedTranscript);
      }
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      let messageKey = 'voice.errors.generic';
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        messageKey = 'voice.errors.notAllowed';
      } else if (event.error === 'no-speech') {
        messageKey = 'voice.errors.noSpeech';
      }
      setErrorKey(messageKey);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    return () => {
      recognition.stop();
      recognitionRef.current = null;
    };
  }, [onTranscript, speechLocale]);

  useEffect(() => {
    if (recognitionRef.current) {
      recognitionRef.current.lang = speechLocale;
    }
  }, [speechLocale]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) {
      return;
    }

    try {
      setErrorKey(null);
      recognitionRef.current.start();
      setIsListening(true);
    } catch (err) {
      console.error('Unable to start speech recognition:', err);
      setErrorKey('voice.errors.startFailure');
    }
  }, []);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) {
      return;
    }
    recognitionRef.current.stop();
  }, []);

  if (!isSupported) {
    return <p>{t ? t('voice.unsupported') : 'Voice interaction not supported.'}</p>;
  }

  return (
    <div>
      <h2>{t ? t('voice.title') : 'Voice interaction'}</h2>
      <p>{text || (t ? t('voice.instructions') : '')}</p>
      <div>
        <button type="button" onClick={startListening} disabled={isListening}>
          {t ? t('voice.buttons.start') : 'Start voice'}
        </button>
        <button type="button" onClick={stopListening} disabled={!isListening}>
          {t ? t('voice.buttons.stop') : 'Stop'}
        </button>
      </div>
      {errorMessage && (
        <p role="alert" aria-live="assertive" style={{ color: 'red' }}>
          {errorMessage}
        </p>
      )}
    </div>
  );
};

export default VoiceInteraction;
