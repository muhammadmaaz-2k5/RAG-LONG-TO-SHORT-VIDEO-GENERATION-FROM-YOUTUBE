import React from 'react';
import { Video, AlignLeft, Database, Search, Cpu, Film, CheckCircle2, Loader2 } from 'lucide-react';

export default function PipelineVisualizer({ currentStage, videoStats }) {
  const stages = [
    { id: 'ingest', label: 'YouTube Fetch', desc: 'Metadata & Raw Captions', icon: Video },
    { id: 'chunk', label: 'Semantic Chunker', desc: 'Sliding Window + Overlap', icon: AlignLeft },
    { id: 'embed', label: 'Vector Store', desc: 'MiniLM 384-d pgvector', icon: Database },
    { id: 'rag', label: 'RAG Retrieval', desc: 'Cosine Distance Match', icon: Search },
    { id: 'groq', label: 'Groq LLM', desc: 'Moments & Viral Scripting', icon: Cpu },
    { id: 'render', label: 'FFmpeg 9:16', desc: 'Precision Crop & Cloudinary', icon: Film },
  ];

  const getStageStatus = (stageId, index) => {
    if (!currentStage) return 'idle';
    const stageOrder = ['ingest', 'chunk', 'embed', 'rag', 'groq', 'render'];
    const activeIndex = stageOrder.indexOf(currentStage);
    if (index < activeIndex || currentStage === 'completed') return 'completed';
    if (index === activeIndex) return 'active';
    return 'idle';
  };

  return (
    <div className="pipeline-visualizer glass-panel">
      <div className="pipeline-header">
        <div className="pipeline-title-group">
          <h3 className="pipeline-title">Autonomous RAG Video Processing Engine</h3>
          <p className="pipeline-subtitle">End-to-end multi-modal pipeline with timestamp-level citation & 9:16 rendering</p>
        </div>
        {videoStats && (
          <div className="pipeline-metrics">
            {videoStats.chunks_created && (
              <span className="metric-badge">
                <strong>{videoStats.chunks_created}</strong> Chunks Embedded
              </span>
            )}
            {videoStats.shorts_count !== undefined && (
              <span className="metric-badge metric-badge-viral">
                <strong>{videoStats.shorts_count}</strong> Shorts Generated
              </span>
            )}
          </div>
        )}
      </div>

      <div className="pipeline-track">
        {stages.map((stage, idx) => {
          const status = getStageStatus(stage.id, idx);
          const Icon = stage.icon;
          return (
            <div key={stage.id} className={`pipeline-node ${status}`}>
              <div className="node-icon-wrapper">
                {status === 'active' ? (
                  <Loader2 className="node-icon animate-spin" size={20} />
                ) : status === 'completed' ? (
                  <CheckCircle2 className="node-icon node-completed-icon" size={20} />
                ) : (
                  <Icon className="node-icon" size={20} />
                )}
              </div>
              <div className="node-info">
                <span className="node-label">{stage.label}</span>
                <span className="node-desc">{stage.desc}</span>
              </div>
              {idx < stages.length - 1 && <div className="pipeline-connector" />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
