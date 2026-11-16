<script setup>
import { computed, ref } from 'vue'
import BarChart from '../components/BarChart.vue'
import { useContador } from '../lib/anima'
import { r, usina, estado, modoDemo } from '../store'
import { fmt, reais, FATOR_CO2, MESES_LONGOS, MESES, serie12 } from '../lib/calc'

const t = computed(() => r.value.tarifa)
const rs = v => reais(v).replace(/,\d\d$/, '')

// 12 meses em R$
const meses = computed(() =>
  serie12(usina.value, r.value.agora.y, r.value.agora.m0, r.value.agora.d).map(p => ({
    ...p, kwh: p.kwh == null ? null : p.kwh * t.value, esp: p.esp * t.value,
    rotuloLongo: `${MESES_LONGOS[MESES.indexOf(p.rotulo)]} de ${p.data.slice(0, 4)}${p.parcial ? ' (até agora)' : ''}`
  }))
)
const ano12 = computed(() => meses.value.reduce((a, p) => a + (p.kwh || 0), 0))
const mediaMes = computed(() => {
  const c = meses.value.filter(p => p.kwh != null && !p.parcial)
  return c.length ? c.reduce((a, p) => a + p.kwh, 0) / c.length : 0
})

// Retorno do investimento: valor investido vem da fonte (campo 'investido'); na demonstração usa um exemplo
const investido = computed(() => usina.value.investido || (modoDemo ? Math.round((usina.value.kwp * 3000) / 1000) * 1000 : 0))
const recuperado = computed(() => r.value.totalKwh * t.value)
const pctRet = computed(() => (investido.value ? Math.min(1, recuperado.value / investido.value) : 0))
const falta = computed(() => Math.max(0, investido.value - recuperado.value))
const mesesFalta = computed(() => (mediaMes.value ? Math.ceil(falta.value / mediaMes.value) : null))
const quandoTxt = computed(() => {
  const m = mesesFalta.value
  if (!m) return ''
  const y = Math.floor(m / 12), mm = m % 12
  return [y ? `${y} ${y === 1 ? 'ano' : 'anos'}` : '', mm ? `${mm} ${mm === 1 ? 'mês' : 'meses'}` : ''].filter(Boolean).join(' e ')
})

const totalAnim = useContador(() => recuperado.value, 1100)
const pctAnim = useContador(() => pctRet.value * 100, 1200)
const co2 = computed(() => (r.value.totalKwh * FATOR_CO2) / 1000)
const enviarConta = () => { estado.servico = 'chat'; estado.chat.push({ de: 'ollivia', txt: 'Me mande uma foto ou o PDF da sua conta de luz que eu calculo a economia com a sua tarifa real.' }); estado.aba = 'ajuda' }
</script>

<template>
  <div class="pg">
    <div class="hero">
      <small>Você já economizou</small>
      <div class="big">{{ rs(totalAnim) }}</div>
      <p>{{ fmt(r.totalKwh) }} kWh que você não precisou comprar da distribuidora</p>
      <div class="dois">
        <div><small>Neste mês</small><b>{{ rs(r.mesKwh * t) }}</b></div>
        <div><small>Últimos 12 meses</small><b>{{ rs(ano12) }}</b></div>
      </div>
    </div>

    <div class="card">
      <div class="rot" style="padding:0 0 6px"><span>Economia mês a mês</span><span style="font-weight:500">média {{ rs(mediaMes) }}/mês</span></div>
      <BarChart :pontos="meses" :valor="v => rs(v)" />
    </div>

    <div v-if="investido" class="card ret">
      <div class="rot" style="padding:0"><span>Retorno do investimento</span><span v-if="!usina.investido" class="ex">exemplo</span></div>
      <div class="linha"><b>{{ fmt(pctAnim) }}%</b><span>já voltou para o seu bolso</span></div>
      <div class="barra"><i :style="{ width: pctRet * 100 + '%' }"></i></div>
      <div class="pes"><span>{{ rs(recuperado) }} economizados</span><span>{{ rs(investido) }} investidos</span></div>
      <p class="sub" v-if="falta > 0">No ritmo atual, a usina se paga em cerca de <b>{{ quandoTxt }}</b>. Depois disso, é economia pura.</p>
      <p class="sub" v-else>A usina já se pagou. Daqui em diante, é economia pura.</p>
    </div>

    <div class="card co2">
      <div class="ic">CO₂</div>
      <div><b>{{ fmt(co2, 1) }} toneladas de CO₂</b><div class="sub">deixaram de ir para a atmosfera graças à sua usina</div></div>
    </div>

    <button class="card tarifa" @click="enviarConta">
      <div><b>Calcular com a sua tarifa</b>
        <div class="sub">{{ estado.tarifa ? `Usando ${reais(t)} por kWh, ${r.fonteTarifa.replace(/^a /, 'da ')}. Envie uma conta nova se a tarifa mudar.` : `Hoje usamos ${reais(t)} por kWh, uma média. Envie a sua conta de luz e a economia fica igual à da sua conta.` }}</div></div>
      <span class="seta">›</span>
    </button>
  </div>
</template>

<style scoped>
.pg { display: flex; flex-direction: column; gap: 12px; }
.hero { background: var(--escuro); color: #fff; border-radius: 24px; padding: 16px 16px 14px; }
:global(.escuro) .hero { border: 1px solid #1d2420; }
.hero small { font-size: 12px; color: #9aa69f; display: block; }
.big { font-size: 40px; font-weight: 700; letter-spacing: -1.6px; color: var(--lima); line-height: 1.1; margin-top: 2px; }
.hero p { font-size: 12.5px; color: #9aa69f; margin: 4px 0 0; }
.dois { display: grid; grid-template-columns: 1fr 1fr; margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,.08); }
.dois div + div { border-left: 1px solid rgba(255,255,255,.08); padding-left: 14px; }
.dois b { font-size: 17px; font-weight: 600; }
.ex { font-size: 10.5px !important; font-weight: 600; color: var(--ambar) !important; background: rgba(242,165,22,.14); padding: 2px 8px; border-radius: 99px; }
.ret .linha { display: flex; align-items: baseline; gap: 8px; margin-top: 8px; }
.ret .linha b { font-size: 28px; font-weight: 700; letter-spacing: -1px; color: var(--acento); }
.ret .linha span { font-size: 13px; color: var(--sub); }
.barra { height: 8px; border-radius: 8px; background: var(--trilho); margin-top: 8px; overflow: hidden; }
.barra i { display: block; height: 100%; background: linear-gradient(90deg, var(--verde), var(--lima)); border-radius: 8px; transform-origin: left; animation: enche 1.2s .25s cubic-bezier(.2,.8,.2,1) both; }
.pes { display: flex; justify-content: space-between; font-size: 11.5px; color: var(--sub); margin-top: 6px; }
.ret p { margin: 10px 0 0; font-size: 13px; line-height: 1.45; }
.ret p b { color: var(--texto); }
.co2 { display: flex; gap: 14px; align-items: center; }
.ic { width: 48px; height: 48px; flex-shrink: 0; border-radius: 50%; background: rgba(17,201,10,.12); color: var(--acento); display: grid; place-items: center; font-weight: 700; font-size: 13px; }
.co2 b { font-size: 14.5px; }
.tarifa { display: flex; align-items: center; gap: 10px; text-align: left; color: inherit; font: inherit; width: 100%; }
.tarifa b { font-size: 14px; font-weight: 600; }
.tarifa .sub { font-size: 12.5px; margin-top: 2px; line-height: 1.4; }
.seta { color: var(--sub); font-size: 20px; margin-left: auto; }
</style>
