import axios from 'axios'

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api`,
  headers: { 'Content-Type': 'application/json' },
})

export const sorteiosAPI = {
  listar: (skip = 0, limit = 50) => api.get(`/sorteios/?skip=${skip}&limit=${limit}`),
  ultimo: () => api.get('/sorteios/ultimo'),
  obter: (numeroConcurso) => api.get(`/sorteios/${numeroConcurso}`),
  criar: (data) => api.post('/sorteios/', data),
  atualizar: () => api.get('/sorteios/atualizar'),
  proposta: () => api.get('/sorteios/proposta'),
  analisar: (dezenas) => api.post('/sorteios/analisar', { dezenas }),
}

export const analiseAPI = {
  radar: () => api.get('/analise/radar'),
  ciclo: () => api.get('/analise/ciclo'),
  paridade: () => api.get('/analise/paridade'),
  repetidas: () => api.get('/analise/repetidas'),
  frequencia: () => api.get('/analise/frequencia'),
}

export const iaAPI = {
  gerarJogos: (data) => api.post('/ia/gerar-jogos', data),
}

export const motorAPI = {
  gerar: (data) => api.post('/motor/gerar', data),
}

export const apostasAPI = {
  listar: () => api.get('/apostas/'),
  obter: (id) => api.get(`/apostas/${id}`),
  criar: (data) => api.post('/apostas/', data),
  deletar: (id) => api.delete(`/apostas/${id}`),
  conferir: (id) => api.post(`/apostas/${id}/conferir`),
  conferirTodas: () => api.post('/apostas/conferir-todas'),
  resumo: () => api.get('/apostas/resumo'),
  exportarPdf: (numeroConcursoAlvo) =>
    api.get('/apostas/exportar-pdf', {
      params: numeroConcursoAlvo ? { numero_concurso_alvo: numeroConcursoAlvo } : {},
      responseType: 'blob',
    }),
}

export const jogosAPI = {
  listar: () => api.get('/jogos/'),
  porAposta: (apostaId) => api.get(`/jogos/aposta/${apostaId}`),
}

export default api
