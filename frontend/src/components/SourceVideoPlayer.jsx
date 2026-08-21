import React, { useState } from 'react';
import { Play, Pause, ExternalLink, Clock, Database, Film, Volume2, Maximize } from 'lucide-react';

export default function SourceVideoPlayer({ video, activeChunkRange }) {
  const [isPlaying, setIsPlaying] = useState(false);

  if (!video) return null;

  const embedUrl = `https://www.youtube.com/embed/${video.youtube_id}?autoplay=1&rel=0`;

  return (
    <div className="source-player-card glass-panel">
      <div className="source-player-header">
        <div className="source-title-group">
          <div className="source-badge">
            <Film size={15} />
            <span>Active Source Video</span>
          </div>
          <h3 className="source-title">{video.title || `YouTube Video #${video.youtube_id}`}</h3>
          <p className="source-channel">{video.channel_name || 'YouTube Creator'}</p>
        </div>

        <div className="source-meta-row">
          <div className="source-pill">
            <Clock size={13} />
            <span>{video.duration_seconds ? `${Math.floor(video.duration_seconds / 60)}m ${Math.floor(video.duration_seconds % 60)}s` : 'Full Duration'}</span>
          </div>
          <div className="source-pill">
            <Database size={13} />
            <span>{video.chunk_count || 0} Vector Chunks</span>
          </div>
          <a
            href={`https://www.youtube.com/watch?v=${video.youtube_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-ghost btn-xs"
            title="Open on YouTube"
          >
            <ExternalLink size={13} />
            <span>YouTube</span>
          </a>
        </div>
      </div>

      <div className="source-player-screen-wrapper">
        {isPlaying ? (
          <iframe
            src={embedUrl}
            title={video.title || 'YouTube Player'}
            className="source-iframe"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        ) : (
          <div
            className="source-thumb-screen"
            onClick={() => setIsPlaying(true)}
            style={{
              backgroundImage: `url(${video.thumbnail_url || `https://i.ytimg.com/vi/${video.youtube_id}/hqdefault.jpg`})`,
            }}
          >
            <div className="source-play-overlay">
              <div className="play-button-circle">
                <Play size={28} className="text-white fill-white" />
              </div>
              <span className="play-prompt-text">Click to Play Source Video</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
