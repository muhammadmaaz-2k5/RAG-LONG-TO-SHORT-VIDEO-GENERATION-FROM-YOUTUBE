import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import PipelineVisualizer from './components/PipelineVisualizer';
import RealtimeProgressTracker from './components/RealtimeProgressTracker';
import SourceVideoPlayer from './components/SourceVideoPlayer';
import VideoIngest from './components/VideoIngest';
import ShortsStudio from './components/ShortsStudio';
import ShortCard from './components/ShortCard';
import VideoLibrary from './components/VideoLibrary';
import RegenerateModal from './components/RegenerateModal';
import Toast from './components/Toast';
import { getVideos, getShortsForVideo } from './services/api';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('create');
  const [pipelineStage, setPipelineStage] = useState(null);
  const [activeVideo, setActiveVideo] = useState(null);
  const [shorts, setShorts] = useState([]);
  const [regenerateShort, setRegenerateShort] = useState(null);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    const text = typeof message === 'string' ? message : JSON.stringify(message);
    setToast({ message: text, type });
  };

  const showError = (message) => {
    const text = typeof message === 'string' ? message : JSON.stringify(message);
    setToast({ message: text, type: 'error' });
  };

  // Initial load: pick the most recent video and load its shorts if available
  useEffect(() => {
    getVideos()
      .then(async (videos) => {
        if (videos && videos.length > 0) {
          const latest = videos[0];
          setActiveVideo(latest);
          const shortsData = await getShortsForVideo(latest.id);
          setShorts(shortsData);
        }
      })
      .catch((err) => {
        console.error('Failed to preload videos:', err);
      });
  }, []);

  const handleVideoProcessed = async (processedVideo) => {
    setActiveVideo(processedVideo);
    showToast(`Video #${processedVideo.id} processed with ${processedVideo.chunks_created || 0} chunks!`);
    try {
      const shortsData = await getShortsForVideo(processedVideo.id);
      setShorts(shortsData);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSelectVideoFromLibrary = async (video) => {
    setActiveVideo(video);
    setActiveTab('create');
    try {
      const shortsData = await getShortsForVideo(video.id);
      setShorts(shortsData);
      showToast(`Loaded Video: ${video.title || video.youtube_id}`);
    } catch (err) {
      console.error(err);
    }
  };

  const handleShortsGenerated = (newShorts) => {
    setShorts(newShorts);
    showToast(`Successfully generated ${newShorts.length} Short scripts with Groq RAG!`);
  };

  const handleShortUpdated = (updatedShort) => {
    setShorts((prev) =>
      prev.map((s) => (s.id === updatedShort.id ? updatedShort : s))
    );
  };

  return (
    <div className="app-container">
      {/* 1. Top Navigation & System Health */}
      <Navbar onSelectTab={setActiveTab} activeTab={activeTab} />

      {/* 2. RAG Pipeline Stage Visualizer */}
      <PipelineVisualizer
        currentStage={pipelineStage}
        videoStats={
          activeVideo
            ? {
                chunks_created: activeVideo.chunk_count,
                shorts_count: shorts.length,
              }
            : null
        }
      />

      {/* 3. Real-Time Pipeline Progress Tracker (Live Tracing & Terminal Logs) */}
      <RealtimeProgressTracker activeStage={pipelineStage} />

      {activeTab === 'create' ? (
        <>
          {/* 4. YouTube URL Ingestion */}
          <VideoIngest
            onVideoProcessed={handleVideoProcessed}
            onError={showError}
            onStageChange={setPipelineStage}
          />

          {/* 5. Active Source Video Player */}
          {activeVideo && <SourceVideoPlayer video={activeVideo} />}

          {/* 6. Generation Controls Studio (15s, 30s, 60s & Styles) */}
          <ShortsStudio
            activeVideo={activeVideo}
            onShortsGenerated={handleShortsGenerated}
            onError={showError}
            onStageChange={setPipelineStage}
          />

          {/* 7. Generated Shorts Feed with 9:16 Video Player */}
          {shorts && shorts.length > 0 && (
            <div className="shorts-feed">
              <div className="feed-header">
                <div>
                  <h3 className="feed-title">
                    Generated Shorts Feed ({shorts.length} Candidates)
                  </h3>
                  <p className="pipeline-subtitle">
                    Watch rendered 9:16 vertical video clips, preview scroll-stopping hooks, and export MP4s.
                  </p>
                </div>
              </div>

              {shorts.map((short) => (
                <ShortCard
                  key={short.id}
                  short={short}
                  onRegenerateClick={(s) => setRegenerateShort(s)}
                  onShortUpdated={handleShortUpdated}
                  onError={showError}
                  onToast={showToast}
                />
              ))}
            </div>
          )}
        </>
      ) : (
        /* 8. Video Database Library Tab */
        <VideoLibrary
          activeVideoId={activeVideo?.id}
          onSelectVideo={handleSelectVideoFromLibrary}
        />
      )}

      {/* 9. Script Regeneration Modal */}
      {regenerateShort && (
        <RegenerateModal
          short={regenerateShort}
          onClose={() => setRegenerateShort(null)}
          onUpdated={handleShortUpdated}
          onError={showError}
          onToast={showToast}
        />
      )}

      {/* 10. Toast Feedback */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
