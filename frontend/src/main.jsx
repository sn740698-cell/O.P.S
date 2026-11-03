import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import SeparatePopupCockpit from './components/SeparatePopupCockpit.jsx';
import './index.css';

const isCockpitMode =
  window.location.search.includes('mode=cockpit') ||
  window.location.pathname === '/cockpit';

if (isCockpitMode) {
  document.documentElement.classList.add('cockpit-mode');
  document.body.classList.add('cockpit-mode');
} else {
  document.documentElement.classList.remove('cockpit-mode');
  document.body.classList.remove('cockpit-mode');
}

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error("Cockpit Error Boundary Caught:", error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 20, color: '#f87171', background: '#09090b', height: '100vh', fontFamily: 'monospace', boxSizing: 'border-box', border: '1px solid #7f1d1d' }}>
          <h2 style={{ fontSize: 13, fontWeight: 'bold', color: '#ef4444', marginBottom: 8 }}>[ O.P.S. RUNTIME ALERT ]</h2>
          <p style={{ fontSize: 11, color: '#d4d4d8', marginBottom: 12, wordBreak: 'break-all' }}>{this.state.error?.message || 'Render failure'}</p>
          <button
            onClick={() => window.location.reload()}
            style={{ padding: '6px 12px', background: '#dc2626', color: '#fff', border: '1px solid #ef4444', borderRadius: 4, cursor: 'pointer', fontSize: 11, fontWeight: 'bold' }}
          >
            [ RELOAD INTERFACE ]
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <ErrorBoundary>
    {isCockpitMode ? <SeparatePopupCockpit /> : <App />}
  </ErrorBoundary>
);
