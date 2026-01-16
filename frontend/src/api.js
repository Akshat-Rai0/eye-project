import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export const getDocuments = async (limit = 100, offset = 0) => {
  const response = await api.get('/documents', {
    params: { limit, offset },
  });
  return response.data;
};

export const searchDocuments = async (q) => {
  const response = await api.get('/documents/search', {
    params: { q },
  });
  return response.data;
};

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getDocument = async (id) => {
  const response = await api.get(`/documents/${id}`);
  return response.data;
};
export const deleteDocument = async (id) => {
  const response = await api.delete(`/documents/${id}`);
  return response.data;
};


export default api;
