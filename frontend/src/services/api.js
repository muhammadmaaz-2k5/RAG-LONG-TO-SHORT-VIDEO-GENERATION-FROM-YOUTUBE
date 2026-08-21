import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes for long-running video render/embeddings
});

export const checkHealth = async () => {
  const { data } = await api.get('/health');
  return data;
};

export const getVideos = async () => {
  const { data } = await api.get('/videos');
  return data;
};

export const getVideo = async (id) => {
  const { data } = await api.get(`/videos/${id}`);
  return data;
};

export const createVideo = async (youtubeUrl) => {
  const { data } = await api.post('/videos', { youtube_url: youtubeUrl });
  return data;
};

export const processVideo = async (videoId) => {
  const { data } = await api.post(`/videos/${videoId}/process`);
  return data;
};

export const generateShorts = async ({ video_id, count = 3, duration = 15, style = 'VIRAL' }) => {
  const { data } = await api.post('/shorts/generate', {
    video_id,
    count,
    duration,
    style,
  });
  return data;
};

export const getShortsForVideo = async (videoId) => {
  const { data } = await api.get(`/shorts/video/${videoId}`);
  return data;
};

export const getShort = async (shortId) => {
  const { data } = await api.get(`/shorts/${shortId}`);
  return data;
};

export const regenerateShort = async (shortId, { style, duration }) => {
  const { data } = await api.post(`/shorts/${shortId}/regenerate`, {
    style,
    duration,
  });
  return data;
};

export const renderShortVideo = async (shortId) => {
  const { data } = await api.post(`/shorts/${shortId}/render`);
  return data;
};

export default api;
