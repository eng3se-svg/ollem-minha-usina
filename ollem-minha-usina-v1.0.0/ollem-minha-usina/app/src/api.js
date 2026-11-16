// Cliente da API do app (servidor em /servidor).
// Sem VITE_API_URL o app roda em MODO DEMONSTRAÇÃO (dados fictícios embutidos, nada sai do aparelho).
import { guardar, ler, apagar } from './nativo'

export const BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
export const DEMO = !BASE
const V1 = `${BASE}/api/app/v1`

let token = null
export const temSessao = async () => !!(token = token || (await ler('sessao')))

export class ErroApi extends Error {
  constructor(msg, codigo, http) { super(msg); this.codigo = codigo; this.http = http }
}

async function chamar(caminho, { metodo = 'GET', json, form, bruto } = {}) {
  const h = {}
  if (token) h.Authorization = `Bearer ${token}`
  if (json) h['Content-Type'] = 'application/json'
  let r
  try {
    r = await fetch(V1 + caminho, { method: metodo, headers: h, body: json ? JSON.stringify(json) : form })
  } catch {
    throw new ErroApi('Sem conexão com a internet. Tente de novo.', 'rede', 0)
  }
  if (bruto && r.ok) return r.blob()
  const j = await r.json().catch(() => ({}))
  if (!r.ok) {
    if (r.status === 401 && j.codigo === 'sessao') { token = null; await apagar('sessao') }
    throw new ErroApi(j.erro || 'Algo deu errado. Tente de novo.', j.codigo || 'erro', r.status)
  }
  return j
}

export const api = {
  pedirCodigo: (doc, telefone, canal) => chamar('/login/codigo', { metodo: 'POST', json: { doc, telefone, canal } }),
  async entrar(doc, telefone, codigo, aparelho) {
    const j = await chamar('/login/entrar', { metodo: 'POST', json: { doc, telefone, codigo, aparelho } })
    token = j.token
    await guardar('sessao', j.token)       // no celular: armazenamento seguro do aparelho (ver nativo.js)
    return j
  },
  async sair() { try { await chamar('/sair', { metodo: 'POST' }) } finally { token = null; await apagar('sessao') } },
  sairOutros: () => chamar('/sair-outros', { metodo: 'POST' }),
  eu: () => chamar('/eu'),
  usinas: () => chamar('/usinas'),
  geracao: (id, de, ate) => chamar(`/usinas/${encodeURIComponent(id)}/geracao?de=${de}&ate=${ate}`),
  solicitar: dados => chamar('/solicitacoes', { metodo: 'POST', json: dados }),
  solicitacoes: () => chamar('/solicitacoes'),
  relatorioPdf: id => chamar(`/solicitacoes/${id}/pdf`, { bruto: true }),
  pedirRelatorio({ usina_id, de, ate, entrega, contas }) {
    const f = new FormData()
    f.append('usina_id', usina_id); f.append('de', de); f.append('ate', ate); f.append('entrega', entrega.join(','))
    for (const c of contas || []) f.append('contas', c)
    return chamar('/relatorios', { metodo: 'POST', form: f })
  },
  chat: (texto, historico) => chamar('/chat', { metodo: 'POST', json: { texto, historico } }),
  contaDeLuz(usina_id, arquivo) {
    const f = new FormData()
    f.append('usina_id', usina_id); f.append('arquivo', arquivo)
    return chamar('/conta-de-luz', { metodo: 'POST', form: f })
  },
  tarifa: (usina_id, valor) => chamar('/tarifa', { metodo: 'PUT', json: { usina_id, valor } }),
  preferencias: () => chamar('/preferencias'),
  salvarPreferencias: p => chamar('/preferencias', { metodo: 'PUT', json: p }),
  registrarPush: (tk, plataforma) => chamar('/push/registrar', { metodo: 'POST', json: { token: tk, plataforma } }),
  avisos: () => chamar('/avisos'),
  convidar: (nome, telefone) => chamar('/familiares', { metodo: 'POST', json: { nome, telefone } }),
  excluirConta: async () => { await chamar('/conta', { metodo: 'DELETE' }); token = null; await apagar('sessao') }
}
