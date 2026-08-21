import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes for long-running video render/embeddings
});

export const extractErrorMessage = (err) => {
  if (!err) return 'An unexpected error occurred.';
  const detail = err.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join('; ');
  }
  if (typeof detail === 'string') {
    return detail;
  }
  if (typeof detail === 'object' && detail !== null) {
    return JSON.stringify(detail);
  }
  return err.message || 'Request failed.';
};

export const checkHealth = async () => {
  const { data } = await api.get('/health');
  return data;
};

export const getVideos = async () => {
  const { data } = await api.get('/videos');
  return Array.isArray(data) ? data : data.items || [];
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
    video_id: parseInt(video_id, 10),
    count: parseInt(count, 10),
    duration: parseInt(duration, 10),
    style: style.toUpperCase(),
  });
  return data;
};

export const getShortsForVideo = async (videoId) => {
  try {
    const { data } = await api.get(`/shorts/video/${videoId}`);
    return Array.isArray(data) ? data : data.items || [];
  } catch (err) {
    // Fallback to query param
    try {
      const { data } = await api.get(`/shorts?video_id=${videoId}&limit=50`);
      return Array.isArray(data) ? data : data.items || [];
    } catch {
      return [];
    }
  }
};

export const getShort = async (shortId) => {
  const { data } = await api.get(`/shorts/${shortId}`);
  return data;
};

export const regenerateShort = async (shortId, { style, duration }) => {
  const payload = {};
  if (style) payload.style = style.toUpperCase();
  if (duration) payload.duration = parseInt(duration, 10);

  const { data } = await api.post(`/shorts/${shortId}/regenerate`, payload);
  return data;
};

export const renderShortVideo = async (shortId) => {
  const { data } = await api.post(`/shorts/${shortId}/render`);
  return data;
};

export default api;
