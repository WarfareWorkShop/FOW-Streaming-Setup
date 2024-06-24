import React, { useState, useEffect } from 'react';

const VoiceInteraction = () => {
  const [text, setText] = useState('');

  useEffect(() => {
    const recognition = new window.webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      setText(finalTranscript);
    };

    recognition.start();

    return () => {
      recognition.stop();
    };
  }, []);

  return (
    <div>
      <h1>Voice Interaction</h1>
      <p>{text}</p>
    </div>
  );
};

export default VoiceInteraction;

