import React, { useEffect, useState } from 'react';
import { Sparkles, Activity, Layers, Cpu, Scissors, CheckCircle, Database } from 'lucide-react';
import { checkHealth } from '../services/api';

export default function Navbar({ onSelectTab, activeTab }) {
  const [healthy, setHealthy] = useState(null);

  const verifyHealth = () => {
    checkHealth()
      .then((data) => {
        const isOk =
          data?.status === 'ok' ||
          data?.status === 'HEALTHY' ||
          data?.status === 'healthy' ||
          data?.database === 'healthy';
        setHealthy(isOk);
      })
      .catch(() => setHealthy(false));
  };

  useEffect(() => {
    verifyHealth();
    const timer = setInterval(verifyHealth, 10000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="navbar-container glass-panel">
      <div className="navbar-brand">
        <div className="brand-logo-glow">
          <Sparkles className="brand-icon" size={24} />
        </div>
        <div>
          <div className="brand-title">
            <span>ShortsForge</span>
            <span className="brand-ai-badge">AI</span>
          </div>
          <p className="brand-tagline">RAG Long-to-Shorts Pipeline</p>
        </div>
      </div>

      <nav className="navbar-nav">
        <button
          className={`nav-item ${activeTab === 'create' ? 'active' : ''}`}
          onClick={() => onSelectTab('create')}
        >
          <Scissors size={17} />
          <span>Shorts Studio</span>
        </button>
        <button
          className={`nav-item ${activeTab === 'library' ? 'active' : ''}`}
          onClick={() => onSelectTab('library')}
        >
          <Layers size={17} />
          <span>Video Library</span>
        </button>
      </nav>

      <div className="navbar-status">
        <div className="pipeline-chips">
          <span className="pipeline-chip"><Database size={13} /> pgvector</span>
          <span className="pipeline-chip"><Cpu size={13} /> Groq LLaMA/GPT</span>
          <span className="pipeline-chip"><Scissors size={13} /> FFmpeg 9:16</span>
        </div>
        <div
          className={`health-indicator ${healthy === true ? 'online' : healthy === false ? 'offline' : 'connecting'}`}
          title="Backend API & Database Health"
        >
          <span className="status-dot"></span>
          <span className="status-text">
            {healthy === true ? 'System Ready' : healthy === false ? 'Server Offline' : 'Connecting...'}
          </span>
        </div>
      </div>
    </header>
  );
}
