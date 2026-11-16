<script setup>
import { ref, computed, watch } from 'vue'
import BarChart from '../components/BarChart.vue'
import { useContador } from '../lib/anima'
import { usina, r } from '../store'
import { serieMes, serie12, MESES_LONGOS, MESES, fmt, iso, esperadoDia, diasNoMes } from '../lib/calc'

const modo = ref('mes')
const ref0 = () => ({ y: r.value.agora.y, m0: r.value.agora.m0 })
const cursor = ref(ref0())
watch(usina, () => (cursor.value = ref0()))

const primeiro = computed(() => {
  const k = Object.keys(usina.value.g).sort()[0]
  return { y: +k.slice(0, 4), m0: +k.slice(5, 7) - 1 }
})
const idx = c => c.y * 12 + c.m0
const podeVoltar = computed(() => modo.value === 'mes' && idx(cursor.value) > idx(primeiro.value))
const podeIr = computed(() => modo.value === 'mes' && idx(cursor.value) < idx(ref0()))
const mover = d => { const t = new Date(cursor.value.y, cursor.value.m0 + d, 1); cursor.value = { y: t.getFullYear(), m0: t.getMonth() } }
const semana = d => { const [y, m, dd] = d.split('-').map(Number); return new Date(y, m - 1, dd).toLocaleDateString('pt-BR', { weekday: 'short' }).replace('.', '') }
const diaTxt = d => { const [, m, dd] = d.split('-').map(Number); return `${dd} de ${MESES_LONGOS[m - 1]}` }

// Período escolhido pelo cliente
const hojeD = () => new Date(r.value.agora.y, r.value.agora.m0, r.value.agora.d)
const isoD = d => iso(d.getFullYear(), d.getMonth(), d.getDate())
const somaDias = (d, n) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n)
const livre = ref({ de: isoD(somaDias(hojeD(), -30)), ate: isoD(somaDias(hojeD(), -1)) })
const rascunho = ref({ ...livre.value })
const folha = ref(false)
const abrirLivre = () => { rascunho.value = { ...livre.value }; folha.value = true }
const atalho = n => { const h = hojeD(); rascunho.value = { de: isoD(somaDias(h, -n)), ate: isoD(somaDias(h, -1)) } }
const aplicarLivre = () => { if (rascunho.value.de && rascunho.value.ate && rascunho.value.de <= rascunho.value.ate) { livre.value = { ...rascunho.value }; modo.value = 'livre'; folha.value = false } }
const minData = computed(() => Object.keys(usina.value.g).sort()[0])
const dataCurta = d => d.split('-').reverse().slice(0, 2).join('/') + '/' + d.slice(2, 4)
const diasEntre = (a, b) => Math.round((new Date(b) - new Date(a)) / 864e5) + 1

const serieDias = (de, ate) => {
  const out = []
  for (let d = new Date(de + 'T12:00'); isoD(d) <= ate; d = somaDias(d, 1)) {
    const k = isoD(d)
    out.push({ data: k, kwh: usina.value.g[k] ?? null, esp: esperadoDia(usina.value, d.getFullYear(), d.getMonth()).kwh, rotulo: String(d.getDate()), rotuloLongo: `${semana(k)}, ${diaTxt(k)}` })
  }
  return out
}
const serieMesesLivre = (de, ate) => {
  const out = []
  let d = new Date(de.slice(0, 7) + '-01T12:00')
  while (isoD(d).slice(0, 7) <= ate.slice(0, 7)) {
    const y = d.getFullYear(), m0 = d.getMonth(), pref = isoD(d).slice(0, 7)
    const dias = Object.entries(usina.value.g).filter(([k]) => k.startsWith(pref) && k >= de && k <= ate)
    const nDias = Math.min(diasNoMes(y, m0), diasEntre(pref + '-01' < de ? de : pref + '-01', (pref + '-' + diasNoMes(y, m0)) > ate ? ate : pref + '-' + String(diasNoMes(y, m0)).padStart(2, '0')))
    out.push({ data: pref, kwh: dias.length ? dias.reduce((a, [, v]) => a + v, 0) : null, esp: esperadoDia(usina.value, y, m0).kwh * nDias, rotulo: MESES[m0], rotuloLongo: `${MESES_LONGOS[m0]} de ${y}` })
    d = new Date(y, m0 + 1, 1, 12)
  }
  return out
}
const livreMensal = computed(() => diasEntre(livre.value.de, livre.value.ate) > 62)

const pontos = computed(() => {
  if (modo.value === 'semana') return r.value.dias7.map(d => ({ ...d, rotulo: semana(d.data), rotuloLongo: `${semana(d.data)}, ${diaTxt(d.data)}` }))
  if (modo.value === 'quinze') { const h = hojeD(); return serieDias(isoD(somaDias(h, -15)), isoD(somaDias(h, -1))) }
  if (modo.value === 'livre') return livreMensal.value ? serieMesesLivre(livre.value.de, livre.value.ate) : serieDias(livre.value.de, livre.value.ate)
  if (modo.value === 'mes') {
    const { y, m0 } = cursor.value
    return serieMes(usina.value, y, m0)
      .filter(p => p.data <= r.value.hojeIso || true)
      .map(p => ({ ...p, rotuloLongo: diaTxt(p.data), futuro: p.data > r.value.hojeIso }))
  }
  const { y, m0 } = ref0()
  return serie12(usina.value, y, m0, r.value.agora.d).map(p => ({ ...p, rotuloLongo: `${MESES_LONGOS[MESES.indexOf(p.rotulo)]} de ${p.data.slice(0, 4)}${p.parcial ? ' (até ontem)' : ''}` }))
})

// Só dias/meses completos entram na comparação (hoje ainda está acontecendo)
const completos = computed(() => pontos.value.filter(p => p.kwh != null && p.data !== r.value.hojeIso && !p.futuro))
const total = computed(() => pontos.value.reduce((a, p) => a + (p.kwh || 0), 0))
const totalAnim = useContador(() => total.value, 700)
const totalComp = computed(() => completos.value.reduce((a, p) => a + p.kwh, 0))
const totalEsp = computed(() => completos.value.reduce((a, p) => a + p.esp, 0))
const pct = computed(() => (totalEsp.value ? totalComp.value / totalEsp.value : null))
const porMes = computed(() => modo.value === 'ano' || (modo.value === 'livre' && livreMensal.value))
const unidade = computed(() => (porMes.value ? 'mês' : 'dia'))
const media = computed(() => (completos.value.length ? totalComp.value / completos.value.length : null))
const melhor = computed(() => completos.value.reduce((b, p) => (!b || p.kwh > b.kwh ? p : b), null))
const fracos = computed(() => completos.value.filter(p => p.kwh > 0 && p.kwh / p.esp < 0.7).length)
const parados = computed(() => completos.value.filter(p => p.kwh === 0).length)
const semDado = computed(() => pontos.value.filter(p => p.kwh == null && p.data < r.value.hojeIso && !p.futuro && !porMes.value).length)

const titulo = computed(() =>
  ({ semana: 'Últimos 7 dias', quinze: 'Últimos 15 dias', ano: 'Últimos 12 meses', livre: `${dataCurta(livre.value.de)} a ${dataCurta(livre.value.ate)}` })[modo.value]
    || `${MESES_LONGOS[cursor.value.m0]} de ${cursor.value.y}`
)
const selo = computed(() => {
  if (pct.value == null) return null
  const d = Math.round((pct.value - 1) * 100)
  return { txt: `${Math.round(pct.value * 100)}% do esperado`, cor: pct.value >= 0.9 ? 'ok' : pct.value >= 0.7 ? 'meio' : 'baixo' }
})
const frase = computed(() => {
  const p = pct.value
  if (p == null) return 'Ainda não há dias completos neste período.'
  const per = { ano: 'Nos últimos 12 meses', mes: 'Neste mês', semana: 'Nesta semana', quinze: 'Nos últimos 15 dias', livre: 'Neste período' }[modo.value]
  let f
  if (p >= 1) f = `${per} a usina gerou acima do esperado. Bastante sol!`
  else if (p >= 0.9) f = `${per} a usina gerou dentro do esperado.`
  else if (p >= 0.7) f = `${per} a usina gerou um pouco abaixo do esperado, o que é normal quando há dias nublados ou chuvosos.`
  else f = `${per} a usina gerou bem abaixo do esperado. Pode ser tempo ruim, sujeira nas placas ou alguma falha.`
  if (parados.value) f += ` Em ${parados.value} ${parados.value === 1 ? 'dia' : 'dias'} ela não gerou nada.`
  return f
})

// Mesmo período do ano anterior (modo mês)
const anoPassado = computed(() => {
  if (modo.value !== 'mes') return null
  const { y, m0 } = cursor.value
  const pref = iso(y - 1, m0, 1).slice(0, 7)
  // mês atual: compara só os mesmos dias (1 até ontem)
  const atual = y === r.value.agora.y && m0 === r.value.agora.m0
  const ate = atual ? r.value.agora.d - 1 : 31
  if (ate < 1) return null
  const dias = Object.entries(usina.value.g).filter(([k]) => k.startsWith(pref) && +k.slice(8) <= ate)
  if (dias.length < Math.min(ate, 20) * 0.8) return null
  const kwh = dias.reduce((a, [, v]) => a + v, 0)
  const agora = Object.entries(usina.value.g).filter(([k]) => k.startsWith(iso(y, m0, 1).slice(0, 7)) && +k.slice(8) <= ate).reduce((a, [, v]) => a + v, 0)
  return { ano: y - 1, kwh, ate: atual ? ate : null, dif: kwh ? agora / kwh - 1 : null }
})
</script>

<template>
  <div class="pg">
    <div class="periodos">
      <button v-for="pp in [['semana', '7 dias'], ['quinze', '15 dias'], ['mes', 'Mês'], ['ano', '12 meses']]" :key="pp[0]" :class="{ on: modo === pp[0] }" @click="modo = pp[0]">{{ pp[1] }}</button>
      <button class="cal" :class="{ on: modo === 'livre' }" @click="abrirLivre" aria-label="Escolher período"><svg viewBox="0 0 24 24"><path d="M4 6h16v14H4zM4 10h16M8 3v4M16 3v4" /></svg></button>
    </div>

    <div class="resumo">
      <div class="cab">
        <button class="nav" :class="{ oculto: modo !== 'mes' }" :disabled="!podeVoltar" @click="mover(-1)" aria-label="Mês anterior">‹</button>
        <div class="tt">
          <div class="nome">{{ titulo }}</div>
          <div class="linha1">
            <span class="big">{{ fmt(totalAnim) }}<span>kWh</span></span>
            <Transition name="selo" mode="out-in"><span v-if="selo" :key="selo.txt" class="selo" :class="selo.cor">{{ selo.txt }}</span></Transition>
          </div>
        </div>
        <button class="nav" :class="{ oculto: modo !== 'mes' }" :disabled="!podeIr" @click="mover(1)" aria-label="Próximo mês">›</button>
      </div>
      <Transition name="selo" mode="out-in"><p class="frase" :key="frase">{{ frase }}</p></Transition>
    </div>

    <div class="card graf">
      <BarChart compacto :pontos="pontos" :rotulo-cada="modo === 'mes' ? 5 : pontos.length > 16 ? Math.ceil(pontos.length / 7) : pontos.length > 8 ? 2 : 1" :destaque="r.hojeIso" />
    </div>

    <div class="card nums">
      <div class="k3">
        <div><small>Média por {{ unidade }}</small><b>{{ fmt(media, media < 100 ? 1 : 0) }}<em> kWh</em></b></div>
        <div><small>Melhor {{ unidade }}</small><b>{{ melhor ? fmt(melhor.kwh, melhor.kwh < 100 ? 1 : 0) : '—' }}<em> {{ melhor ? (porMes ? melhor.rotulo : melhor.data.slice(8) + '/' + melhor.data.slice(5, 7)) : '' }}</em></b></div>
        <div><small>{{ porMes ? 'Meses' : 'Dias' }} fracos</small><b>{{ fracos + parados }}<em> abaixo de 70%</em></b></div>
      </div>
      <div v-if="anoPassado" class="comp">
        <span>{{ MESES_LONGOS[cursor.m0] }} de {{ anoPassado.ano }}{{ anoPassado.ate ? ` (1 a ${anoPassado.ate})` : '' }}: <b>{{ fmt(anoPassado.kwh) }} kWh</b></span>
        <span v-if="anoPassado.dif != null" class="dif" :class="anoPassado.dif >= 0 ? 'mais' : 'menos'">{{ anoPassado.dif >= 0 ? '+' : '' }}{{ fmt(anoPassado.dif * 100) }}% este ano</span>
      </div>
      <div v-if="semDado" class="comp aviso"><span>{{ semDado }} {{ semDado === 1 ? 'dia' : 'dias' }} sem informação da usina</span></div>
    </div>
    <Teleport to=".tela"><Transition name="folha">
      <div v-if="folha" class="fundo-folha" @click.self="folha = false">
        <div class="folha">
          <i class="pegador"></i>
          <b class="h">Escolher período</b>
          <div class="atalhos">
            <button @click="atalho(30)">Últimos 30 dias</button>
            <button @click="atalho(90)">Últimos 3 meses</button>
            <button @click="atalho(180)">Últimos 6 meses</button>
          </div>
          <div class="datas">
            <label><span>De</span><input type="date" v-model="rascunho.de" :min="minData" :max="r.hojeIso" /></label>
            <label><span>Até</span><input type="date" v-model="rascunho.ate" :min="rascunho.de || minData" :max="r.hojeIso" /></label>
          </div>
          <p class="dica" v-if="rascunho.de && rascunho.ate && rascunho.de <= rascunho.ate">{{ diasEntre(rascunho.de, rascunho.ate) }} dias{{ diasEntre(rascunho.de, rascunho.ate) > 62 ? ' · o gráfico mostra mês a mês' : ' · o gráfico mostra dia a dia' }}</p>
          <p class="dica erro" v-else>A data final precisa ser depois da inicial.</p>
          <button class="btn primario" :disabled="!(rascunho.de && rascunho.ate && rascunho.de <= rascunho.ate)" @click="aplicarLivre">Ver período</button>
        </div>
      </div>
    </Transition></Teleport>
  </div>
</template>

<style scoped>
.pg { display: flex; flex-direction: column; gap: 12px; }
.pg { gap: 10px !important; }
.resumo { background: var(--escuro); color: #fff; border-radius: 22px; padding: 12px 12px 12px; }
:global(.escuro) .resumo { border: 1px solid #1d2420; }
.cab { display: flex; align-items: center; gap: 8px; }
.tt { flex: 1; text-align: center; }
.nome { font-size: 12.5px; color: #9aa69f; }
.nome::first-letter { text-transform: uppercase; }
.linha1 { display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: 2px; }
.big { font-size: 34px; font-weight: 700; letter-spacing: -1.4px; line-height: 1.1; }
.big span { font-size: 14px; font-weight: 500; color: #9aa69f; margin-left: 4px; letter-spacing: 0; }
.selo { display: inline-block; white-space: nowrap; font-size: 11.5px; font-weight: 600; padding: 3px 9px; border-radius: 99px; }
.selo.ok { background: rgba(142,247,5,.14); color: var(--lima); }
.selo.meio { background: rgba(242,165,22,.16); color: #ffc65c; }
.selo.baixo { background: rgba(229,72,77,.18); color: #ff9a9d; }
.nav { border: 1px solid rgba(255,255,255,.12); background: transparent; color: #fff; width: 34px; height: 34px; border-radius: 50%; font-size: 19px; padding: 0; flex-shrink: 0; }
.nav:disabled { opacity: .25; }
.nav:active:not(:disabled) { transform: scale(.9); }
.nav.oculto { visibility: hidden; }
.frase { margin: 8px 6px 0; font-size: 12.5px; line-height: 1.45; color: #c9d2cd; text-align: center; }
.selo-enter-active, .selo-leave-active { transition: opacity .2s, transform .25s; }
.selo-enter-from { opacity: 0; transform: translateY(4px); }
.selo-leave-to { opacity: 0; }
.graf { padding: 10px 12px 8px; }
.nums { padding: 12px 14px; }
.k3 { display: grid; grid-template-columns: repeat(3, 1fr); }
.k3 > div + div { border-left: 1px solid var(--linha); padding-left: 12px; }
.k3 small { display: block; font-size: 11px; color: var(--sub); }
.k3 b { display: block; font-size: 18px; font-weight: 700; letter-spacing: -.5px; margin-top: 2px; }
.k3 em { font-style: normal; font-size: 10.5px; font-weight: 500; color: var(--sub); letter-spacing: 0; display: block; }
.comp { display: flex; justify-content: space-between; gap: 8px; align-items: baseline; border-top: 1px solid var(--linha); margin-top: 10px; padding-top: 9px; font-size: 12px; color: var(--sub); }
.comp b { color: var(--texto); }
.comp > span:first-child::first-letter { text-transform: uppercase; }
.dif { font-weight: 700; white-space: nowrap; }
.dif.mais { color: var(--acento); } .dif.menos { color: var(--ambar); }
.comp.aviso { margin-top: 8px; padding-top: 8px; }
.periodos { display: flex; gap: 6px; }
.periodos::-webkit-scrollbar { display: none; }
.periodos button { flex: 1; justify-content: center; padding-left: 0 !important; padding-right: 0 !important; display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--linha); background: var(--card); color: var(--sub); border-radius: 99px; padding: 8px 14px; font-size: 13px; font-weight: 500; transition: background-color .2s, color .2s, border-color .2s, transform .15s; }
.periodos button.on { background: var(--texto); color: var(--fundo); border-color: var(--texto); font-weight: 600; }
.periodos button:active { transform: scale(.95); }
.periodos .cal { flex: 0 0 38px; }
.periodos svg { width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; }
.fundo-folha { position: absolute; inset: 0; z-index: 40; background: rgba(0,0,0,.35); display: flex; align-items: flex-end; justify-content: center; }
.folha { width: 100%; max-width: 430px; background: var(--card); border-radius: 26px 26px 0 0; padding: 10px 20px 28px; display: flex; flex-direction: column; gap: 12px; }
.pegador { width: 38px; height: 4px; border-radius: 4px; background: var(--linha); align-self: center; margin-bottom: 4px; }
.folha .h { font-size: 17px; }
.atalhos { display: flex; gap: 6px; flex-wrap: wrap; }
.atalhos button { border: 1px solid var(--linha); background: var(--fundo); color: var(--texto); border-radius: 99px; padding: 7px 12px; font-size: 12.5px; }
.datas { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.datas label { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--sub); }
.datas input { font-size: 15px; padding: 11px; }
.dica { margin: 0; font-size: 12px; color: var(--sub); }
.dica.erro { color: var(--vermelho); }
.folha-enter-active, .folha-leave-active { transition: opacity .25s; }
.folha-enter-active .folha, .folha-leave-active .folha { transition: transform .32s cubic-bezier(.2,.8,.2,1); }
.folha-enter-from, .folha-leave-to { opacity: 0; }
.folha-enter-from .folha, .folha-leave-to .folha { transform: translateY(100%); }
</style>
