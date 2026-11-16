<script setup>
import { computed } from 'vue'
import { fmt, horaBR, dataBR } from '../lib/calc'
import { useContador } from '../lib/anima'

const props = defineProps({ r: Object, u: Object })

// Arco: 6h (esquerda) até 18h (direita)
const CX = 160, CY = 132, RX = 142, RY = 118
const fracAlvo = computed(() => {
  const h = props.r.agora.h + props.r.agora.min / 60
  return Math.min(1, Math.max(0, (h - 6) / 12))
})
const frac = useContador(() => fracAlvo.value, 1300) // o sol "nasce" e anda até a hora atual
const kwh = useContador(() => props.r.hojeKwh, 1100)
const pos = computed(() => {
  const t = Math.PI * (1 - frac.value)
  return { x: CX + RX * Math.cos(t), y: CY - RY * Math.sin(t) }
})
const arcoFeito = computed(() => `M${CX - RX} ${CY} A${RX} ${RY} 0 0 1 ${pos.value.x.toFixed(1)} ${pos.value.y.toFixed(1)}`)

const st = computed(() => {
  const s = props.r.situacao
  if (s === 'gerando') return { txt: 'Gerando agora', cor: 'var(--lima)', txtCor: '#c7f59a' }
  if (s === 'noite') return { txt: 'Noite · volta a gerar amanhã', cor: '#8b9cff', txtCor: '#c3cbff' }
  if (s === 'sem_comunicacao') return { txt: `Sem comunicação desde ${dataBR(props.u.ultimo_online)}`, cor: 'var(--vermelho)', txtCor: '#ffb3b5' }
  return { txt: 'Aviso do equipamento', cor: 'var(--ambar)', txtCor: '#ffd38a' }
})
const ativo = computed(() => props.r.situacao === 'gerando')
const potencia = computed(() => props.u.potencia_kw == null ? '—' : `${fmt(props.u.potencia_kw, 1)} kW`)
</script>

<template>
  <div class="sol">
    <div class="l1">
      <span class="st" :style="{ color: st.txtCor }"><i class="ponto" :style="{ background: st.cor }"></i>{{ st.txt }}</span>
      <small>às {{ r.atualizadoHora }}</small>
    </div>
    <div class="arco">
      <svg viewBox="0 0 320 140">
        <path :d="`M${CX - RX} ${CY} A${RX} ${RY} 0 0 1 ${CX + RX} ${CY}`" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="2" />
        <template v-if="r.situacao !== 'noite'">
          <path :d="arcoFeito" fill="none" :stroke="ativo ? 'var(--lima)' : 'rgba(255,255,255,.35)'" stroke-width="2.5" stroke-linecap="round" />
          <circle :cx="pos.x" :cy="pos.y" r="16" :fill="ativo ? 'var(--sol)' : '#9aa69f'" opacity=".14" :class="{ halo: ativo }" />
          <circle :cx="pos.x" :cy="pos.y" r="8" :fill="ativo ? 'var(--sol)' : '#9aa69f'" />
        </template>
        <path v-else d="M160 36 a14 14 0 1 0 12 20 a11 11 0 1 1 -12 -20z" fill="#c3cbff" opacity=".9" />
        <circle :cx="CX - RX" :cy="CY" r="2.5" :fill="ativo ? 'var(--lima)' : 'rgba(255,255,255,.3)'" />
        <circle :cx="CX + RX" :cy="CY" r="2.5" fill="rgba(255,255,255,.3)" />
        <text :x="CX - RX" :y="CY + 14" class="hx" text-anchor="middle">6h</text>
        <text :x="CX + RX" :y="CY + 14" class="hx" text-anchor="middle">18h</text>
      </svg>
      <div class="num">
        <b>{{ fmt(kwh, 1) }}<span>kWh</span></b>
        <small>{{ r.situacao === 'noite' ? 'gerados hoje' : 'gerados hoje até agora' }}</small>
      </div>
    </div>
    <div class="trio">
      <div><small>Agora</small><b>{{ potencia }}</b></div>
      <div><small>Esperado hoje</small><b>{{ fmt(r.esp.kwh) }} kWh</b></div>
      <div><small>No mês</small><b>{{ r.desempMes != null ? fmt(r.desempMes * 100) + '%' : '—' }}</b></div>
    </div>
  </div>
</template>

<style scoped>
.sol { border-radius: 24px; padding: 16px 16px 14px; background: #111714; color: #fff; }
:global(.escuro) .sol { background: #141a17; border: 1px solid #1d2420; }
.l1 { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.st { display: inline-flex; align-items: center; gap: 7px; font-size: 12px; font-weight: 600; }
.l1 small { font-size: 11.5px; color: #7f8b84; flex-shrink: 0; }
.arco { height: 150px; position: relative; margin-top: 4px; }
.arco svg { width: 100%; height: 100%; overflow: visible; }
.halo { transform-box: fill-box; transform-origin: center; animation: halo 2.6s ease-in-out 1.3s infinite; }
@keyframes halo { 50% { transform: scale(1.35); opacity: .06; } }
.trio div { animation: sobe .5s cubic-bezier(.2,.8,.2,1) both; }
.trio div:nth-child(2) { animation-delay: .08s } .trio div:nth-child(3) { animation-delay: .16s }
.hx { font-size: 9.5px; fill: #5f6b64; font-family: inherit; }
.num { position: absolute; left: 0; right: 0; bottom: 12px; text-align: center; }
.num b { font-size: 46px; font-weight: 700; letter-spacing: -2px; line-height: 1; }
.num b span { font-size: 15px; font-weight: 500; color: #9aa69f; margin-left: 5px; letter-spacing: 0; }
.num small { display: block; font-size: 12px; color: #9aa69f; margin-top: 4px; }
.trio { display: grid; grid-template-columns: repeat(3, 1fr); margin-top: 6px; border-top: 1px solid rgba(255,255,255,.08); padding-top: 12px; }
.trio div { text-align: center; }
.trio div + div { border-left: 1px solid rgba(255,255,255,.08); }
.trio small { display: block; font-size: 10.5px; color: #7f8b84; }
.trio b { font-size: 14px; font-weight: 600; }
</style>
