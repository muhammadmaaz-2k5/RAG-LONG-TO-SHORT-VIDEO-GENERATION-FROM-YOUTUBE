import React, { useState } from 'react';
import { Flame, Sparkles, Clock, Sliders, Layers, RefreshCw, Zap, Video, Check } from 'lucide-react';
import confetti from 'canvas-confetti';
import { generateShorts } from '../services/api';

export default function ShortsStudio({ activeVideo, onShortsGenerated, onError, onStageChange }) {
  const [duration, setDuration] = useState(15);
  const [style, setStyle] = useState('VIRAL');
  const [count, setCount] = useState(3);
  const [generating, setGenerating] = useState(false);

  const durationOptions = [
    { value: 15, label: '15 Seconds', desc: 'Fast micro-hook & punchline (~35 words)', badge: '⚡ High Pacing' },
    { value: 30, label: '30 Seconds', desc: 'Balanced hook & revelation (~70 words)', badge: '🔥 Most Popular' },
    { value: 60, label: '60 Seconds', desc: 'Full narrative retention arc (~140 words)', badge: '📖 Deep Story' },
  ];

  const styleOptions = [
    { value: 'VIRAL', label: 'Viral High-Energy', emoji: '🚀', desc: 'Aggressive curiosity gap hook' },
    { value: 'DRAMATIC', label: 'Dramatic / Mystery', emoji: '🎭', desc: 'Cinematic tension & suspense' },
    { value: 'STORYTELLING', label: 'Narrative Story', emoji: '✨', desc: 'Clear hero & conflict progression' },
    { value: 'EDUCATIONAL', label: 'Educational / Fact', emoji: '🧠', desc: 'Mind-blowing insight & fact breakdown' },
    { value: 'BEHIND_THE_SCENES', label: 'Behind-the-Scenes', emoji: '🎬', desc: 'Insider secret look & commentary' },
  ];

  const handleGenerate = async () => {
    if (!activeVideo) {
      onError('Please ingest or select a video first.');
      return;
    }

    try {
      setGenerating(true);
      onStageChange('rag');
      
      setTimeout(() => onStageChange('groq'), 800);

      const result = await generateShorts({
        video_id: activeVideo.id,
        count: parseInt(count, 10),
        duration: parseInt(duration, 10),
        style: style,
      });

      onStageChange('completed');
      
      // Celebrate with confetti
      try {
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#6366f1', '#ff3b5c', '#06b6d4', '#10b981'],
        });
      } catch (e) {
        // ignore
      }

      if (onShortsGenerated) {
        onShortsGenerated(result.shorts);
      }
    } catch (err) {
      console.error(err);
      onStageChange(null);
      const errMsg = err.response?.data?.detail || err.message || 'Failed to generate Shorts.';
      onError(errMsg);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="studio-container glass-panel">
      <div className="studio-header">
        <div className="studio-title-group">
          <div className="studio-icon-badge">
            <Flame size={20} />
          </div>
          <div>
            <h3 className="studio-title">AI Shorts Generation Controls</h3>
            <p className="studio-subtitle">
              Select your desired duration, pacing, and viral tone to extract optimal Short candidates.
            </p>
          </div>
        </div>

        {activeVideo && (
          <div className="active-video-pill">
            <Video size={15} />
            <span className="active-video-title">
              Video #{activeVideo.id}: {activeVideo.title || activeVideo.youtube_id}
            </span>
          </div>
        )}
      </div>

      <div className="studio-controls-grid">
        {/* 1. Duration Selector */}
        <div className="control-section">
          <label className="control-label">
            <Clock size={16} />
            <span>Target Duration</span>
          </label>
          <div className="duration-options">
            {durationOptions.map((opt) => (
              <button
                key={opt.value}
                type="button"
                className={`duration-card ${duration === opt.value ? 'selected' : ''}`}
                onClick={() => setDuration(opt.value)}
                disabled={generating}
              >
                <div className="duration-card-header">
                  <span className="duration-val">{opt.label}</span>
                  <span className="duration-badge">{opt.badge}</span>
                </div>
                <p className="duration-desc">{opt.desc}</p>
                {duration === opt.value && <div className="card-selected-glow" />}
              </button>
            ))}
          </div>
        </div>

        {/* 2. Style Selector */}
        <div className="control-section">
          <label className="control-label">
            <Sliders size={16} />
            <span>Viral Hook & Scripting Style</span>
          </label>
          <div className="style-grid">
            {styleOptions.map((opt) => (
              <button
                key={opt.value}
                type="button"
                className={`style-card ${style === opt.value ? 'selected' : ''}`}
                onClick={() => setStyle(opt.value)}
                disabled={generating}
              >
                <span className="style-emoji">{opt.emoji}</span>
                <div className="style-info">
                  <span className="style-title">{opt.label}</span>
                  <span className="style-desc">{opt.desc}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* 3. Batch Count */}
        <div className="control-section-row">
          <div className="count-selector-group">
            <label className="control-label">
              <Layers size={16} />
              <span>Generate Candidates</span>
            </label>
            <div className="count-buttons">
              {[1, 2, 3, 4, 5].map((num) => (
                <button
                  key={num}
                  type="button"
                  className={`count-btn ${count === num ? 'selected' : ''}`}
                  onClick={() => setCount(num)}
                  disabled={generating}
                >
                  {num} Short{num > 1 ? 's' : ''}
                </button>
              ))}
            </div>
          </div>

          {/* Action CTA */}
          <div className="cta-container">
            <button
              className="btn btn-viral generate-cta-btn"
              onClick={handleGenerate}
              disabled={generating || !activeVideo}
            >
              {generating ? (
                <>
                  <RefreshCw className="animate-spin" size={20} />
                  <span>RAG Engine Scripting Shorts...</span>
                </>
              ) : (
                <>
                  <Sparkles size={20} />
                  <span>Generate {count}x {duration}s Viral Shorts</span>
                  <Zap size={18} />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
