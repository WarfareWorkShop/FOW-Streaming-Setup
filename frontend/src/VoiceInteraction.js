import React, { useEffect, useState } from 'react';

const SpeechRecognition =
  (typeof window !== 'undefined' &&
    (window.SpeechRecognition || window.webkitSpeechRecognition || null)) ||
  null;

const VoiceInteraction = ({ onTranscript = () => {} }) => {
  const [text, setText] = useState('');
  const [isSupported, setIsSupported] = useState(true);

  useEffect(() => {
    if (!SpeechRecognition) {
      setIsSupported(false);
      return undefined;
    }

    const recognition = new SpeechRecognition();
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
    };

    recognition.start();

    return () => {
      recognition.stop();
    };
  }, [onTranscript]);

  if (!isSupported) {
    return <p>La interacción por voz no es compatible con este navegador.</p>;
  }

  return (
    <div>
      <h2>Interacción por voz</h2>
      <p>{text || 'Habla para enviar un mensaje automáticamente.'}</p>
    </div>
  );
};

export default VoiceInteraction;
