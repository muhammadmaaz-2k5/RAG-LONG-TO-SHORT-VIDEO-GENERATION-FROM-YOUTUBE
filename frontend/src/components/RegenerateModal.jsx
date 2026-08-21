import React, { useState } from 'react';
import { X, RefreshCw, Sparkles, Clock, Sliders } from 'lucide-react';
import { regenerateShort } from '../services/api';

export default function RegenerateModal({ short, onClose, onUpdated, onError, onToast }) {
  const [duration, setDuration] = useState(short.duration_seconds || 15);
  const [style, setStyle] = useState(short.style || 'VIRAL');
  const [loading, setLoading] = useState(false);

  const styleOptions = [
    { value: 'VIRAL', label: 'Viral High-Energy', emoji: '🚀' },
    { value: 'DRAMATIC', label: 'Dramatic / Mystery', emoji: '🎭' },
    { value: 'STORYTELLING', label: 'Narrative Story', emoji: '✨' },
    { value: 'EDUCATIONAL', label: 'Educational / Fact', emoji: '🧠' },
    { value: 'BEHIND_THE_SCENES', label: 'Behind-the-Scenes', emoji: '🎬' },
  ];

  const handleRegenerate = async () => {
    try {
      setLoading(true);
      const updated = await regenerateShort(short.id, {
        duration: parseInt(duration, 10),
        style,
      });
      if (onUpdated) onUpdated(updated);
      if (onToast) onToast('Short script regenerated successfully!');
      onClose();
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || err.message || 'Failed to regenerate short.';
      onError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content glass-panel-elevated" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <Sparkles size={20} className="text-brand" />
            <h3 className="modal-title">Regenerate Script for Short #{short.id}</h3>
          </div>
          <button className="btn-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {/* Duration Selector */}
          <div className="form-group">
            <label className="form-label">
              <Clock size={15} />
              <span>Target Duration</span>
            </label>
            <div className="modal-btn-row">
              {[15, 30, 60].map((dur) => (
                <button
                  key={dur}
                  type="button"
                  className={`modal-toggle-btn ${duration === dur ? 'active' : ''}`}
                  onClick={() => setDuration(dur)}
                >
                  {dur} Seconds
                </button>
              ))}
            </div>
          </div>

          {/* Style Selector */}
          <div className="form-group">
            <label className="form-label">
              <Sliders size={15} />
              <span>Script Tone & Style</span>
            </label>
            <div className="modal-style-grid">
              {styleOptions.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  className={`modal-style-card ${style === opt.value ? 'active' : ''}`}
                  onClick={() => setStyle(opt.value)}
                >
                  <span className="emoji">{opt.emoji}</span>
                  <span className="name">{opt.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={handleRegenerate} disabled={loading}>
            {loading ? (
              <>
                <RefreshCw className="animate-spin" size={16} />
                <span>Regenerating with Groq...</span>
              </>
            ) : (
              <>
                <Sparkles size={16} />
                <span>Regenerate Script</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
