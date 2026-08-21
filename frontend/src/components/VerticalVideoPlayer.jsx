import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, RotateCcw, Maximize, Film } from 'lucide-react';

export default function VerticalVideoPlayer({ videoUrl, durationSeconds = 15, title = '' }) {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(durationSeconds);
  const [isMuted, setIsMuted] = useState(false);
  const [showControls, setShowControls] = useState(true);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
  };

  const toggleMute = (e) => {
    e.stopPropagation();
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
      if (videoRef.current.duration && !isNaN(videoRef.current.duration)) {
        setDuration(videoRef.current.duration);
      }
    }
  };

  const handleSeek = (e) => {
    e.stopPropagation();
    const seekTime = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.currentTime = seekTime;
      setCurrentTime(seekTime);
    }
  };

  const toggleFullscreen = (e) => {
    e.stopPropagation();
    if (!videoRef.current) return;
    if (videoRef.current.requestFullscreen) {
      videoRef.current.requestFullscreen();
    }
  };

  const formatTime = (secs) => {
    if (isNaN(secs) || secs < 0) return '00:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div
      className="custom-vertical-player"
      onClick={togglePlay}
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => isPlaying && setShowControls(false)}
    >
      <video
        ref={videoRef}
        src={videoUrl}
        className="vertical-video-element"
        playsInline
        preload="metadata"
        loop
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleTimeUpdate}
      />

      {/* Top Overlay Badge */}
      <div className="player-top-overlay">
        <span className="player-badge">9:16 HD</span>
        <span className="player-time-badge">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>
      </div>

      {/* Big Center Play/Pause Button Overlay */}
      {!isPlaying && (
        <div className="center-play-overlay">
          <div className="center-play-btn">
            <Play size={28} className="fill-white text-white" />
          </div>
        </div>
      )}

      {/* Bottom Controls Bar */}
      <div className={`player-bottom-controls ${showControls || !isPlaying ? 'visible' : ''}`} onClick={(e) => e.stopPropagation()}>
        {/* Scrub Bar */}
        <div className="timeline-container">
          <div className="timeline-fill" style={{ width: `${progressPercent}%` }} />
          <input
            type="range"
            min="0"
            max={duration || 15}
            step="0.1"
            value={currentTime}
            onChange={handleSeek}
            className="timeline-slider"
          />
        </div>

        {/* Action Row */}
        <div className="controls-row">
          <button className="ctrl-btn" onClick={togglePlay} title={isPlaying ? 'Pause' : 'Play'}>
            {isPlaying ? <Pause size={16} /> : <Play size={16} />}
          </button>

          <button className="ctrl-btn" onClick={toggleMute} title={isMuted ? 'Unmute' : 'Mute'}>
            {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
          </button>

          <span className="ctrl-time">{formatTime(currentTime)}</span>

          <div className="ctrl-spacer" />

          <button className="ctrl-btn" onClick={toggleFullscreen} title="Fullscreen">
            <Maximize size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
