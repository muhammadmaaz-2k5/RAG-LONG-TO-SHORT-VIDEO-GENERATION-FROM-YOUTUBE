import React, { useEffect, useState } from 'react';
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  Terminal,
  Clock,
  Sparkles,
  Zap,
  Video,
  AlignLeft,
  Database,
  Search,
  Cpu,
  Film,
} from 'lucide-react';

export default function RealtimeProgressTracker({
  activeStage, // 'ingest' | 'chunk' | 'embed' | 'rag' | 'groq' | 'render' | 'completed' | null
  customLogs = [],
  onDismiss,
}) {
  const [progressPercent, setProgressPercent] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [internalLogs, setInternalLogs] = useState([]);

  const stages = [
    { id: 'ingest', label: '1. Video Ingestion', desc: 'Fetching YouTube transcript & metadata', pct: 15, icon: Video },
    { id: 'chunk', label: '2. Semantic Chunking', desc: 'Sliding window chunking with timestamp bounds', pct: 35, icon: AlignLeft },
    { id: 'embed', label: '3. pgvector Embeddings', desc: 'Generating MiniLM-L6-v2 384d vector embeddings', pct: 55, icon: Database },
    { id: 'rag', label: '4. RAG Retrieval', desc: 'Querying vector store with cosine distance scoring', pct: 70, icon: Search },
    { id: 'groq', label: '5. Groq LLM Scripting', desc: 'Hook -> Context -> Main -> Payoff -> CTA copywriting', pct: 85, icon: Cpu },
    { id: 'render', label: '6. FFmpeg 9:16 Render', desc: 'Precision timestamp trim, crop & Cloudinary upload', pct: 95, icon: Film },
  ];

  // Stage order
  const stageIds = ['ingest', 'chunk', 'embed', 'rag', 'groq', 'render'];

  useEffect(() => {
    if (!activeStage) {
      setProgressPercent(0);
      setElapsedSeconds(0);
      setInternalLogs([]);
      return;
    }

    if (activeStage === 'completed') {
      setProgressPercent(100);
      addLog('All pipeline stages completed successfully! Shorts ready for viewing.');
      return;
    }

    const currentIdx = stageIds.indexOf(activeStage);
    if (currentIdx !== -1) {
      const targetPct = stages[currentIdx].pct;
      setProgressPercent(targetPct);
      addLog(`Started ${stages[currentIdx].label}: ${stages[currentIdx].desc}`);
    }
  }, [activeStage]);

  // Elapsed timer
  useEffect(() => {
    if (!activeStage || activeStage === 'completed') return;
    const interval = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [activeStage]);

  const addLog = (msg) => {
    const timestamp = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setInternalLogs((prev) => [...prev.slice(-15), { time: timestamp, msg }]);
  };

  const getStageState = (stageId, index) => {
    if (!activeStage) return 'pending';
    if (activeStage === 'completed') return 'completed';
    const activeIdx = stageIds.indexOf(activeStage);
    if (index < activeIdx) return 'completed';
    if (index === activeIdx) return 'running';
    return 'pending';
  };

  if (!activeStage) return null;

  return (
    <div className="progress-tracker-container glass-panel-elevated">
      {/* Header */}
      <div className="tracker-header">
        <div className="tracker-title-group">
          <div className="tracker-pulse-dot">
            {activeStage === 'completed' ? (
              <CheckCircle2 size={20} className="text-emerald" />
            ) : (
              <Zap size={20} className="text-brand animate-pulse" />
            )}
          </div>
          <div>
            <h3 className="tracker-title">
              {activeStage === 'completed'
                ? 'Processing Complete!'
                : 'Real-Time RAG Video Processing'}
            </h3>
            <p className="tracker-subtitle">
              {activeStage === 'completed'
                ? 'Shorts have been generated and timestamp-grounded'
                : 'Autonomous multi-modal pipeline in progress...'}
            </p>
          </div>
        </div>

        <div className="tracker-meta">
          <div className="timer-badge">
            <Clock size={14} />
            <span>{elapsedSeconds}s elapsed</span>
          </div>
          <div className="pct-badge">
            <span>{progressPercent}%</span>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="progress-bar-track">
        <div
          className={`progress-bar-fill ${activeStage === 'completed' ? 'fill-completed' : ''}`}
          style={{ width: `${progressPercent}%` }}
        >
          <div className="progress-shimmer" />
        </div>
      </div>

      {/* Stage Grid */}
      <div className="tracker-stages-grid">
        {stages.map((st, idx) => {
          const state = getStageState(st.id, idx);
          const Icon = st.icon;
          return (
            <div key={st.id} className={`stage-step-card ${state}`}>
              <div className="stage-icon-circle">
                {state === 'running' ? (
                  <Loader2 className="animate-spin text-brand" size={16} />
                ) : state === 'completed' ? (
                  <CheckCircle2 className="text-emerald" size={16} />
                ) : (
                  <Icon size={16} />
                )}
              </div>
              <div className="stage-text-block">
                <span className="stage-name">{st.label}</span>
                <span className="stage-sub">{st.desc}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Terminal Live Event Log */}
      <div className="tracker-terminal">
        <div className="terminal-top-bar">
          <div className="terminal-dots">
            <span className="dot dot-red" />
            <span className="dot dot-yellow" />
            <span className="dot dot-green" />
          </div>
          <div className="terminal-title">
            <Terminal size={13} />
            <span>Live Pipeline Trace Stream</span>
          </div>
        </div>
        <div className="terminal-body">
          {internalLogs.map((log, i) => (
            <div key={i} className="terminal-line">
              <span className="term-time">[{log.time}]</span>
              <span className="term-arrow">➜</span>
              <span className="term-msg">{log.msg}</span>
            </div>
          ))}
          {activeStage !== 'completed' && (
            <div className="terminal-line terminal-cursor-line">
              <span className="term-time">[{new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}]</span>
              <span className="term-arrow">➜</span>
              <span className="term-msg blink">Executing background pipeline worker...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
