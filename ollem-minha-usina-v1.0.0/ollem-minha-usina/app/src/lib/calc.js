// Cálculos do app do cliente, portados das regras do monitoramento do Ollem Hub.
// Na versão com servidor, esses números vêm prontos da API /api/app/...

export const TZ = 'America/Sao_Paulo'
export const TARIFA_PADRAO = 1.06 // R$/kWh (servicos.tarifa_de, nível 3)
// Fator de emissão do SIN em kg CO2/kWh. PROVISÓRIO: conferir o valor oficial atual antes de fixar.
export const FATOR_CO2 = 0.0385
export const LIMITE_7D = 0.7 // MONITOR_LIMITE

// Sazonalidade RJ (CRESESB, kWh/m²·dia)
const IRR = [5.8, 6.0, 5.2, 4.6, 3.9, 3.6, 3.7, 4.4, 4.5, 5.0, 5.4, 5.6]
const MEDIA = IRR.reduce((a, b) => a + b, 0) / 12
export const SAZ = IRR.map(x => x / MEDIA)

export const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
export const MESES_LONGOS = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']

export const diasNoMes = (y, m0) => new Date(y, m0 + 1, 0).getDate()
const pad = n => String(n).padStart(2, '0')
export const iso = (y, m0, d) => `${y}-${pad(m0 + 1)}-${pad(d)}`

// Data/hora "agora" no fuso de Brasília a partir de um timestamp (s)
export function partesBR(ts) {
  const f = new Intl.DateTimeFormat('pt-BR', {
    timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: false, weekday: 'short'
  })
  const p = Object.fromEntries(f.formatToParts(new Date(ts * 1000)).map(x => [x.type, x.value]))
  return { y: +p.year, m0: +p.month - 1, d: +p.day, h: +p.hour % 24, min: +p.minute, sem: p.weekday.replace('.', '') }
}
export const horaBR = ts => { const p = partesBR(ts); return `${pad(p.h)}:${pad(p.min)}` }
export const dataBR = ts => { const p = partesBR(ts); return `${pad(p.d)}/${pad(p.m0 + 1)}` }

// Esperado diário (kWh). Prioridade do Hub: projeto > sistema > esperado_mes > PVGIS > kWp × HSP × PR
export function esperadoDia(u, y, m0) {
  if (u.esperado_meses) return { kwh: u.esperado_meses[m0] / diasNoMes(y, m0), fonte: 'pelo seu projeto' }
  if (u.pvgis) return { kwh: (u.pvgis[m0] * u.kwp) / diasNoMes(y, m0), fonte: 'estimado pela localização' }
  return { kwh: (u.kwp * 4.8 * 0.78) * SAZ[m0], fonte: 'estimado pelo tamanho da usina' }
}
export const esperadoMes = (u, y, m0) => esperadoDia(u, y, m0).kwh * diasNoMes(y, m0)

export const fmt = (v, casas = 0) =>
  v == null || isNaN(v) ? '—' : v.toLocaleString('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas })
export const reais = v => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: v >= 1000 ? 0 : 2 })

// Resumo completo de uma usina para as telas
export function resumo(u) {
  const agora = partesBR(u.atualizado)
  const hojeIso = iso(agora.y, agora.m0, agora.d)
  const g = u.g
  const ontem = new Date(agora.y, agora.m0, agora.d - 1)
  const ontemIso = iso(ontem.getFullYear(), ontem.getMonth(), ontem.getDate())
  const esp = esperadoDia(u, agora.y, agora.m0)

  // Situação (estado_real)
  const semComHoras = (u.atualizado - u.ultimo_online) / 3600
  const gerouRecente = (g[hojeIso] || 0) > 0.05 || (g[ontemIso] || 0) > 0.05
  const noturno = agora.h >= 17 || agora.h < 8
  let situacao
  if (u.estado === 'online') situacao = (agora.h >= 18 || agora.h < 6) ? 'noite' : 'gerando'
  else if (noturno && gerouRecente && semComHoras < 16) situacao = 'noite'
  else if (semComHoras > 1) situacao = 'sem_comunicacao'
  else situacao = 'aviso'

  // Últimos 7 dias completos (ignora dias sem dado)
  let g7 = 0, e7 = 0, dias7 = []
  for (let i = 7; i >= 1; i--) {
    const dt = new Date(agora.y, agora.m0, agora.d - i)
    const k = iso(dt.getFullYear(), dt.getMonth(), dt.getDate())
    const e = esperadoDia(u, dt.getFullYear(), dt.getMonth()).kwh
    dias7.push({ data: k, kwh: g[k] ?? null, esp: e })
    if (g[k] != null) { g7 += g[k]; e7 += e }
  }
  const desemp7 = e7 ? g7 / e7 : null

  // Mês até ontem
  let gm = 0, em = 0
  for (let d = 1; d < agora.d; d++) {
    const k = iso(agora.y, agora.m0, d)
    if (g[k] != null) { gm += g[k]; em += esp.kwh }
  }
  const mesKwh = u.mes_kwh ?? (gm + (g[hojeIso] || 0)) // total do portal quando houver (Renac não traz)
  const desempMes = em ? gm / em : null

  // Ano corrente
  const anoKwh = Object.entries(g).filter(([k]) => k.startsWith(String(agora.y))).reduce((a, [, v]) => a + v, 0)

  // Alertas em linguagem simples
  const alertas = []
  if (situacao === 'sem_comunicacao') {
    alertas.push({
      nivel: 'alta', titulo: 'Usina sem comunicação',
      texto: `Não recebemos notícias da sua usina desde ${dataBR(u.ultimo_online)} às ${horaBR(u.ultimo_online)}. Pode ser a internet do equipamento ou uma falha. Fale com a Ollivia que a gente verifica para você.`,
      acao: 'ollivia'
    })
  } else if (situacao === 'aviso') {
    alertas.push({ nivel: 'media', titulo: 'O equipamento registrou um aviso', texto: 'Nossa equipe vai analisar. Se quiser, fale com a Ollivia.', acao: 'ollivia' })
  }
  if (u.estado === 'online' && agora.h >= 14 && !(g[hojeIso] > 0)) {
    alertas.push({ nivel: 'alta', titulo: 'Sem geração hoje', texto: 'Sua usina está ligada, mas não gerou energia hoje. Fale com a Ollivia.', acao: 'ollivia' })
  }
  if (desemp7 != null && desemp7 < LIMITE_7D) {
    alertas.push({
      nivel: 'media', titulo: 'Geração abaixo do esperado',
      texto: `Nos últimos 7 dias sua usina gerou ${fmt(desemp7 * 100)}% do esperado. Pode ser tempo nublado ou sujeira nas placas.`,
      acao: 'limpeza'
    })
  }

  return {
    agora, hojeIso, esp, situacao, desemp7, desempMes, dias7,
    hojeKwh: g[hojeIso] ?? u.hoje_kwh ?? 0,
    mesKwh, anoKwh, totalKwh: u.total_kwh, alertas,
    atualizadoHora: horaBR(u.atualizado),
    tarifa: TARIFA_PADRAO, fonteTarifa: 'tarifa média aproximada'
  }
}

// Série diária de um mês
export function serieMes(u, y, m0) {
  const n = diasNoMes(y, m0), e = esperadoDia(u, y, m0).kwh
  return Array.from({ length: n }, (_, i) => {
    const k = iso(y, m0, i + 1)
    return { rotulo: String(i + 1), data: k, kwh: u.g[k] ?? null, esp: e }
  })
}

// Série mensal dos últimos 12 meses (terminando no mês atual)
export function serie12(u, y, m0, d) {
  const out = []
  for (let i = 11; i >= 0; i--) {
    const dt = new Date(y, m0 - i, 1), yy = dt.getFullYear(), mm = dt.getMonth()
    const pref = iso(yy, mm, 1).slice(0, 7)
    const dias = Object.entries(u.g).filter(([k]) => k.startsWith(pref))
    const kwh = dias.length ? dias.reduce((a, [, v]) => a + v, 0) : null
    const esp = i === 0 ? esperadoDia(u, yy, mm).kwh * (d - 1) : esperadoMes(u, yy, mm) // mês atual: esperado até ontem
    out.push({ rotulo: MESES[mm], data: pref, kwh, esp, parcial: i === 0 })
  }
  return out
}
