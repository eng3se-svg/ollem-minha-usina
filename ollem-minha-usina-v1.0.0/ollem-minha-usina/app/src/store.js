import { reactive, computed } from 'vue'
import demo from './data/usinas_previa.json'
import { resumo } from './lib/calc'
import { api, DEMO } from './api'

// Usinas do cliente. No modo demonstração: 3 usinas fictícias. Com servidor: vêm de GET /usinas depois do login.
export const usinas = reactive(DEMO ? [...demo] : [])
export const modoDemo = DEMO
export async function carregarUsinas() {
  if (DEMO) return usinas
  const j = await api.usinas()
  usinas.splice(0, usinas.length, ...j.usinas)
  if (estado.usinaIdx >= usinas.length) estado.usinaIdx = 0
  // tarifa da usina (lida da conta, digitada ou média) passa a valer na Economia
  const u = usinas[estado.usinaIdx]
  if (u && u.tarifa_origem && u.tarifa_origem !== 'media') { estado.tarifa = u.tarifa; estado.origemTarifa = u.tarifa_origem; estado.contaMes = u.tarifa_referencia || '' }
  return usinas
}

export const estado = reactive({
  logado: false,
  primeiroAcesso: true,
  tour: false, // passo a passo do 1º acesso
  avisosAtivos: false,
  telefone: '',
  canalCodigo: 'whats', // whats | sms (o app lembra a escolha)
  doc: '', // CPF/CNPJ só mascarado
  nome: '',
  carregando: false,
  erro: '',
  usinaIdx: 0,
  aba: 'inicio',
  tema: 'claro', // claro | escuro | auto
  textoGrande: false,
  tarifa: null, // R$/kWh lido da conta ou digitado (senão, média)
  origemTarifa: '', // 'conta' | 'digitada'
  contaMes: '',
  distribuidora: 'Enel Rio',
  silencio: true, // sem avisos das 22h às 7h (menos usina parada)
  canais: { app: true, whats: true },
  email: '',
  biometria: true,
  push: { parada: true, abaixo: true, mensal: true, relatorio: true, visita: true },
  pedidos: [],
  servico: 'menu', // menu | chat | posvenda | pedido
  chat: [{ de: 'ollivia', txt: 'Oi! Eu sou a Ollivia, assistente da Ollem. Posso explicar a geração da sua usina, tirar dúvidas sobre a conta de luz ou chamar a equipe. Como posso ajudar?' }],
  msgsPosVenda: []
})

export const usina = computed(() => usinas[estado.usinaIdx] || usinas[0])
export const r = computed(() => {
  const x = resumo(usina.value)
  if (estado.tarifa) { x.tarifa = estado.tarifa; x.fonteTarifa = estado.origemTarifa === 'conta' ? `a sua conta de ${estado.contaMes}` : 'a tarifa que você informou' }
  return x
})
const escuroSistema = typeof matchMedia !== 'undefined' && matchMedia('(prefers-color-scheme: dark)').matches
export const temaEscuro = computed(() => estado.tema === 'escuro' || (estado.tema === 'auto' && escuroSistema))

export const OLLIVIA_WA = 'https://wa.me/552231990081'
export const mascararTel = t => {
  const d = t.replace(/\D/g, '')
  return d.length >= 10 ? `(${d.slice(0, 2)}) ${d.length === 11 ? '9' : ''}••••-${d.slice(-4)}` : t
}
