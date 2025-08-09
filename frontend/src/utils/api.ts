import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export const uploadData = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/upload-data', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const getStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};

export const getChart = async (chartType: string) => {
  const response = await api.get(`/charts/${chartType}`);
  return response.data;
};

export const useSampleData = async () => {
  const response = await api.post('/use-sample-data');
  return response.data;
};