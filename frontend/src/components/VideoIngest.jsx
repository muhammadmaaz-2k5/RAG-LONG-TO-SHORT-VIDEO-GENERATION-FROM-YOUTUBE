import React, { useState } from 'react';
import { ArrowRight, Loader2, PlayCircle, Sparkles, Check, Clock, Video } from 'lucide-react';
import { createVideo, processVideo, extractErrorMessage } from '../services/api';

function YoutubeIcon({ size = 24, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
    >
      <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
    </svg>
  );
}

export default function VideoIngest({ onVideoProcessed, onError, onStageChange }) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  const sampleUrls = [
    {
      title: 'Victor Frankenstein Short Story',
      url: 'https://www.youtube.com/watch?v=X1B7-A66wUg',
      duration: '1m 22s',
    },
    {
      title: 'Veritasium Science Discovery',
      url: 'https://www.youtube.com/watch?v=bBC-nXj3Ng4',
      duration: '11m 40s',
    },
  ];

  const handleIngest = async (targetUrl = url) => {
    const finalUrl = targetUrl.trim();
    if (!finalUrl) {
      onError('Please provide a valid YouTube video URL.');
      return;
    }

    try {
      setLoading(true);
      onStageChange('ingest');
      setStatusMessage('Extracting YouTube metadata & captions...');

      // 1. Create Video Record
      const video = await createVideo(finalUrl);

      // 2. Process Transcript & Semantic Chunks & Vector Embeddings
      onStageChange('chunk');
      setStatusMessage('Chunking transcript into semantic overlapping windows...');
      
      setTimeout(() => onStageChange('embed'), 1200);
      setStatusMessage('Generating MiniLM-L6-v2 vector embeddings & storing in pgvector...');
      
      const processed = await processVideo(video.id);

      onStageChange('completed');
      setStatusMessage('Video processed & vectors indexed successfully!');
      
      if (onVideoProcessed) {
        onVideoProcessed(processed);
      }
    } catch (err) {
      console.error(err);
      onStageChange(null);
      const errMsg = extractErrorMessage(err);
      onError(errMsg);
    } finally {
      setLoading(false);
      setTimeout(() => setStatusMessage(''), 3000);
    }
  };

  return (
    <div className="ingest-card glass-panel-elevated">
      <div className="ingest-header">
        <div className="ingest-icon-box">
          <YoutubeIcon className="yt-icon" size={28} />
        </div>
        <div>
          <h2 className="ingest-title">Ingest YouTube Video</h2>
          <p className="ingest-subtitle">
            Paste any YouTube URL to extract transcripts, build pgvector embeddings, and detect viral Short moments.
          </p>
        </div>
      </div>

      <form
        className="ingest-form"
        onSubmit={(e) => {
          e.preventDefault();
          handleIngest();
        }}
      >
        <div className="input-wrapper">
          <YoutubeIcon className="input-icon" size={20} />
          <input
            type="url"
            className="url-input"
            placeholder="https://www.youtube.com/watch?v=..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            className="btn btn-primary ingest-btn"
            disabled={loading || !url.trim()}
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                <span>Processing Video...</span>
              </>
            ) : (
              <>
                <Sparkles size={18} />
                <span>Ingest & Vectorize</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </div>
      </form>

      {statusMessage && (
        <div className="status-banner">
          <Loader2 className="animate-spin" size={16} />
          <span>{statusMessage}</span>
        </div>
      )}

      <div className="sample-section">
        <span className="sample-label">Try instant samples:</span>
        <div className="sample-chips">
          {sampleUrls.map((sample) => (
            <button
              key={sample.url}
              type="button"
              className="sample-chip"
              disabled={loading}
              onClick={() => {
                setUrl(sample.url);
                handleIngest(sample.url);
              }}
            >
              <PlayCircle size={14} />
              <span className="sample-title">{sample.title}</span>
              <span className="sample-duration">{sample.duration}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
