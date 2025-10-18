import React from 'react';
import ReactDOM from 'react-dom/client';

import App from './App';

const mount = () => {
  const container = document.getElementById('root');
  if (!container) {
    return;
  }
  const root = ReactDOM.createRoot(container);
  root.render(<App />);
};

mount();
