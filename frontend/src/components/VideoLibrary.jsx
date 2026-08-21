import React, { useEffect, useState } from 'react';
import { Layers, Video, Clock, CheckCircle, AlertCircle, RefreshCw, ExternalLink, Scissors } from 'lucide-react';
import { getVideos, getShortsForVideo } from '../services/api';

export default function VideoLibrary({ activeVideoId, onSelectVideo, onVideoLoaded }) {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadVideos = async () => {
    try {
      setLoading(true);
      const data = await getVideos();
      setVideos(data);
    } catch (err) {
      console.error('Failed to load video library:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVideos();
  }, []);

  const formatDuration = (secs) => {
    if (!secs) return 'N/A';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}m ${s < 10 ? '0' : ''}${s}s`;
  };

  return (
    <div className="library-container glass-panel">
      <div className="library-header">
        <div className="library-title-group">
          <Layers size={22} className="text-brand" />
          <div>
            <h3 className="library-title">Ingested Videos Library</h3>
            <p className="library-subtitle">
              All processed YouTube sources with stored transcripts, pgvector embeddings, and generated Shorts.
            </p>
          </div>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={loadVideos} disabled={loading}>
          <RefreshCw className={loading ? 'animate-spin' : ''} size={15} />
          <span>Refresh Library</span>
        </button>
      </div>

      {loading && videos.length === 0 ? (
        <div className="library-loading">
          <RefreshCw className="animate-spin text-brand" size={28} />
          <span>Loading video database...</span>
        </div>
      ) : videos.length === 0 ? (
        <div className="library-empty">
          <Video size={40} className="empty-icon" />
          <p className="empty-title">No videos ingested yet</p>
          <p className="empty-desc">Paste a YouTube URL in the Shorts Studio above to start generating viral shorts.</p>
        </div>
      ) : (
        <div className="library-grid">
          {videos.map((vid) => {
            const isActive = activeVideoId === vid.id;
            return (
              <div
                key={vid.id}
                className={`library-video-card glass-panel-elevated ${isActive ? 'active' : ''}`}
                onClick={() => onSelectVideo(vid)}
              >
                <div className="video-thumb-wrapper">
                  <img
                    src={vid.thumbnail_url || `https://i.ytimg.com/vi/${vid.youtube_id}/hqdefault.jpg`}
                    alt={vid.title || 'Video thumbnail'}
                    className="video-thumbnail"
                    onError={(e) => {
                      e.target.src = `https://i.ytimg.com/vi/${vid.youtube_id}/hqdefault.jpg`;
                    }}
                  />
                  <div className="duration-tag">
                    <Clock size={11} />
                    <span>{formatDuration(vid.duration_seconds)}</span>
                  </div>
                  {vid.status === 'READY' && (
                    <span className="status-badge badge-ready">READY</span>
                  )}
                </div>

                <div className="video-card-body">
                  <h4 className="video-card-title">{vid.title || `YouTube Video #${vid.youtube_id}`}</h4>
                  <p className="video-channel-name">{vid.channel_name || 'YouTube Creator'}</p>

                  <div className="video-meta-pills">
                    <span className="meta-pill">
                      <strong>{vid.chunk_count || 0}</strong> Chunks
                    </span>
                    <span className="meta-pill meta-pill-viral">
                      <strong>{vid.shorts_count || 0}</strong> Shorts
                    </span>
                  </div>

                  <div className="video-card-actions">
                    <button className="btn btn-primary btn-xs w-full">
                      <Scissors size={13} />
                      <span>{isActive ? 'Active Video' : 'Open Shorts'}</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
