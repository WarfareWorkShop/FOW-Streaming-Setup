import React, { useCallback, useEffect, useRef, useState } from 'react';

const SpeechRecognition =
  (typeof window !== 'undefined' &&
    (window.SpeechRecognition || window.webkitSpeechRecognition || null)) ||
  null;

const VoiceInteraction = ({ onTranscript = () => {} }) => {
  const recognitionRef = useRef(null);
  const [text, setText] = useState('');
  const [isSupported, setIsSupported] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!SpeechRecognition) {
      setIsSupported(false);
      return undefined;
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'es-ES';

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
      let message = 'Ocurrió un problema con el reconocimiento de voz.';
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        message = 'No se concedieron permisos para usar el micrófono.';
      } else if (event.error === 'no-speech') {
        message = 'No se detectó audio. Intenta nuevamente.';
      }
      setError(message);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    return () => {
      recognition.stop();
      recognitionRef.current = null;
    };
  }, [onTranscript]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) {
      return;
    }

    try {
      setError(null);
      recognitionRef.current.start();
      setIsListening(true);
    } catch (err) {
      console.error('Unable to start speech recognition:', err);
      setError('No se pudo iniciar el reconocimiento de voz.');
    }
  }, []);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) {
      return;
    }
    recognitionRef.current.stop();
  }, []);

  if (!isSupported) {
    return <p>La interacción por voz no es compatible con este navegador.</p>;
  }

  return (
    <div>
      <h2>Interacción por voz</h2>
      <p>{text || 'Presiona "Iniciar voz" y habla para enviar un mensaje automáticamente.'}</p>
      <div>
        <button type="button" onClick={startListening} disabled={isListening}>
          Iniciar voz
        </button>
        <button type="button" onClick={stopListening} disabled={!isListening}>
          Detener
        </button>
      </div>
      {error && (
        <p role="alert" aria-live="assertive" style={{ color: 'red' }}>
          {error}
        </p>
      )}
    </div>
  );
};

export default VoiceInteraction;
