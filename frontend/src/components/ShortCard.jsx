import React, { useState } from 'react';
import {
  Play,
  Pause,
  Film,
  Scissors,
  RefreshCw,
  Copy,
  Check,
  Download,
  ExternalLink,
  Clock,
  Sparkles,
  Flame,
  Volume2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { renderShortVideo } from '../services/api';

export default function ShortCard({ short, onRegenerateClick, onShortUpdated, onError, onToast }) {
  const [rendering, setRendering] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [expandedScript, setExpandedScript] = useState(true);

  const handleCopyScript = () => {
    navigator.clipboard.writeText(short.script);
    setCopied(true);
    if (onToast) onToast('Short script copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRenderVideo = async () => {
    try {
      setRendering(true);
      if (onToast) onToast(`Rendering 9:16 vertical video with FFmpeg & Cloudinary...`);
      const updated = await renderShortVideo(short.id);
      if (onShortUpdated) {
        onShortUpdated(updated);
      }
      if (onToast) onToast('Short video rendered and uploaded to Cloudinary successfully!');
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || err.message || 'Failed to render short video.';
      onError(msg);
    } finally {
      setRendering(false);
    }
  };

  const parseScriptSections = (scriptText) => {
    if (!scriptText) return [];
    const sectionHeaders = ['[HOOK]', '[CONTEXT]', '[MAIN IDEA]', '[PAYOFF]', '[CTA]'];
    const lines = scriptText.split('\n');
    const sections = [];
    let currentSection = null;

    lines.forEach((line) => {
      const trimmed = line.trim();
      const matchedHeader = sectionHeaders.find((h) => trimmed.startsWith(h));

      if (matchedHeader) {
        if (currentSection) sections.push(currentSection);
        currentSection = {
          header: matchedHeader,
          content: trimmed.replace(matchedHeader, '').trim(),
        };
      } else if (currentSection && trimmed) {
        currentSection.content += (currentSection.content ? ' ' : '') + trimmed;
      } else if (!currentSection && trimmed) {
        currentSection = { header: '[SCRIPT]', content: trimmed };
      }
    });

    if (currentSection) sections.push(currentSection);
    return sections.length > 0 ? sections : [{ header: '[SCRIPT]', content: scriptText }];
  };

  const scriptSections = parseScriptSections(short.script);

  const getSectionBadgeClass = (header) => {
    switch (header) {
      case '[HOOK]':
        return 'badge-hook';
      case '[CONTEXT]':
        return 'badge-context';
      case '[MAIN IDEA]':
        return 'badge-main';
      case '[PAYOFF]':
        return 'badge-payoff';
      case '[CTA]':
        return 'badge-cta';
      default:
        return 'badge-brand';
    }
  };

  const firstSource = short.sources && short.sources.length > 0 ? short.sources[0] : null;

  return (
    <div className="short-card glass-panel-elevated">
      {/* Top Meta Bar */}
      <div className="short-card-header">
        <div className="short-title-block">
          <div className="short-badges">
            <span className="badge badge-viral">
              <Flame size={12} /> {short.duration_seconds || 15}s Short
            </span>
            <span className="badge badge-brand">{short.style || 'VIRAL'}</span>
            {short.score && (
              <span className="badge badge-ready">
                <Sparkles size={12} /> Score: {short.score.toFixed(1)}/100
              </span>
            )}
          </div>
          <h4 className="short-card-title">{short.title}</h4>
        </div>

        <div className="short-header-actions">
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => onRegenerateClick(short)}
            title="Regenerate script"
          >
            <RefreshCw size={15} />
            <span>Regenerate</span>
          </button>
        </div>
      </div>

      <div className="short-body-grid">
        {/* Left Column: 9:16 Video Player or Render Placeholder */}
        <div className="short-video-container">
          {short.video_url ? (
            <div className="rendered-video-wrapper">
              <video
                src={short.video_url}
                className="vertical-video-player"
                controls
                playsInline
                preload="metadata"
                loop
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
              />
              <div className="video-overlay-badge">
                <span>9:16 HD</span>
              </div>
            </div>
          ) : (
            <div className="video-placeholder-box">
              <div className="placeholder-phone-frame">
                <div className="phone-screen">
                  <Film size={36} className="placeholder-icon" />
                  <span className="placeholder-duration">{short.duration_seconds || 15}s MP4</span>
                  <p className="placeholder-text">
                    Ready to cut from source at {firstSource ? `${firstSource.start_time.toFixed(1)}s` : '0s'}
                  </p>
                  <button
                    className="btn btn-viral render-btn"
                    onClick={handleRenderVideo}
                    disabled={rendering}
                  >
                    {rendering ? (
                      <>
                        <RefreshCw className="animate-spin" size={15} />
                        <span>Rendering 9:16...</span>
                      </>
                    ) : (
                      <>
                        <Scissors size={15} />
                        <span>Render 9:16 Video</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Hook, Script Flow, & Grounding Timestamps */}
        <div className="short-content-col">
          {/* Scroll-Stopping Hook Callout */}
          <div className="hook-callout-card">
            <div className="hook-label">
              <Sparkles size={14} />
              <span>Scroll-Stopping Hook (0–3s)</span>
            </div>
            <p className="hook-text">"{short.hook}"</p>
          </div>

          {/* Script Section Breakdown */}
          <div className="script-breakdown-card">
            <div className="script-header-row">
              <span className="script-section-title">Spoken Script Flow</span>
              <button
                className="btn btn-ghost btn-xs"
                onClick={handleCopyScript}
                title="Copy entire script"
              >
                {copied ? <Check size={14} className="text-emerald" /> : <Copy size={14} />}
                <span>{copied ? 'Copied' : 'Copy Script'}</span>
              </button>
            </div>

            <div className="script-sections-list">
              {scriptSections.map((sec, idx) => (
                <div key={idx} className="script-section-item">
                  <span className={`section-tag ${getSectionBadgeClass(sec.header)}`}>
                    {sec.header.replace('[', '').replace(']', '')}
                  </span>
                  <p className="section-speech">{sec.content}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Source Grounding References */}
          {short.sources && short.sources.length > 0 && (
            <div className="grounding-section">
              <span className="grounding-label">Grounding Citations:</span>
              <div className="source-chips">
                {short.sources.map((src, i) => (
                  <span key={i} className="source-chip" title={`Source Chunk #${src.chunk_id}`}>
                    <Clock size={12} />
                    <span>
                      {src.start_time.toFixed(1)}s – {src.end_time.toFixed(1)}s
                    </span>
                    <span className="chunk-id-tag">Chunk #{src.chunk_id}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Footer Action Bar */}
          <div className="short-footer-actions">
            {short.video_url ? (
              <>
                <a
                  href={short.video_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary btn-sm"
                >
                  <ExternalLink size={15} />
                  <span>Open Video in Cloudinary</span>
                </a>
                <a
                  href={short.video_url}
                  download={`short_${short.id}.mp4`}
                  className="btn btn-primary btn-sm"
                >
                  <Download size={15} />
                  <span>Download 9:16 MP4</span>
                </a>
              </>
            ) : (
              <button
                className="btn btn-viral btn-sm w-full"
                onClick={handleRenderVideo}
                disabled={rendering}
              >
                {rendering ? (
                  <>
                    <RefreshCw className="animate-spin" size={15} />
                    <span>Cutting & Formatting 9:16 Video...</span>
                  </>
                ) : (
                  <>
                    <Scissors size={15} />
                    <span>Render & Trim 9:16 Video Clip</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
