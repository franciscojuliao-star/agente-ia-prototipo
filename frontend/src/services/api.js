import axios from 'axios';

const API_URL = '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para tratar erros
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = (email, senha) => api.post('/auth/login', { email, senha });
export const registrar = (data) => api.post('/auth/registrar', data);
export const getMe = () => api.get('/auth/me');

// Materiais (Professor)
export const uploadPDF = (formData) => api.post('/materiais/upload/pdf', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
export const uploadVideo = (data) => api.post('/materiais/upload/video', data);
export const uploadLink = (data) => api.post('/materiais/upload/link', data);
export const uploadTexto = (data) => api.post('/materiais/upload/texto', data);
export const getMateriais = (disciplina) => api.get('/materiais', { params: { disciplina } });
export const getMaterial = (id) => api.get(`/materiais/${id}`);
export const deleteMaterial = (id) => api.delete(`/materiais/${id}`);

// Conteúdos (Professor)
export const gerarQuiz = (data) => api.post('/conteudos/gerar/quiz', data);
export const gerarResumo = (data) => api.post('/conteudos/gerar/resumo', data);
export const gerarFlashcards = (data) => api.post('/conteudos/gerar/flashcards', data);
export const getConteudosPendentes = () => api.get('/conteudos/pendentes');
export const getConteudosAprovados = (disciplina) => api.get('/conteudos/aprovados', { params: { disciplina } });
export const getConteudo = (id) => api.get(`/conteudos/${id}`);
export const aprovarConteudo = (id, modificacoes) => api.put(`/conteudos/${id}/aprovar`, { modificacoes });
export const rejeitarConteudo = (id, motivo) => api.put(`/conteudos/${id}/rejeitar`, { motivo });
export const deleteConteudo = (id) => api.delete(`/conteudos/${id}`);

// Aluno
export const getDisciplinas = () => api.get('/aluno/disciplinas');
export const getMateriaisDisciplina = (disciplina, tipo) => api.get(`/aluno/materiais/${disciplina}`, { params: { tipo } });
export const getQuiz = (id) => api.get(`/aluno/quiz/${id}`);
export const responderQuiz = (id, respostas) => api.post(`/aluno/quiz/${id}/responder`, { respostas });
export const getFlashcards = (id) => api.get(`/aluno/flashcards/${id}`);
export const getResumo = (id) => api.get(`/aluno/resumo/${id}`);
export const buscarSemantica = (disciplina, pergunta) => api.post('/aluno/buscar', { disciplina, pergunta });
export const getHistorico = () => api.get('/aluno/historico');

export default api;
