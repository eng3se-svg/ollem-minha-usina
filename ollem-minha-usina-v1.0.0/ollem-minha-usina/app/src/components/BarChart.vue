<script setup>
import { computed, ref, watch } from 'vue'
import { fmt } from '../lib/calc'

const props = defineProps({
  pontos: Array, // [{rotulo, kwh, esp, parcial?, data}]
  unidade: { type: String, default: 'kWh' },
  rotuloCada: { type: Number, default: 1 },
  destaque: String, // data a destacar (hoje)
  valor: { type: Function, default: null }, // formatação própria (ex.: R$)
  compacto: Boolean // gráfico mais baixo e legenda na linha de cima
})
const W = 340, PL = 30, PB = 20, PT = 8
const H = props.compacto ? 140 : 190
const sel = ref(null)
watch(() => props.pontos, () => (sel.value = null))

const max = computed(() => {
  const m = Math.max(...props.pontos.map(p => Math.max(p.kwh ?? 0, p.esp ?? 0)))
  const passo = m > 1000 ? 500 : m > 400 ? 200 : m > 100 ? 50 : m > 40 ? 20 : 10
  return Math.ceil((m * 1.08) / passo) * passo || 10
})
const grade = computed(() => [0, 0.5, 1].map(f => f * max.value))
const bw = computed(() => (W - PL) / props.pontos.length)
const y = v => PT + (H - PT - PB) * (1 - v / max.value)
const linha = computed(() =>
  props.pontos.map((p, i) => `${i ? 'L' : 'M'}${PL + bw.value * i + bw.value / 2},${y(p.esp)}`).join(' ')
)
const cor = p => {
  if (p.kwh == null) return 'transparent'
  if (p.kwh === 0) return 'var(--vermelho)'
  const f = p.esp ? p.kwh / p.esp : 1
  if (p.parcial || p.data === props.destaque) return 'var(--trilho)'
  return f >= 0.7 ? 'var(--verde)' : 'var(--ambar)'
}
const mostra = v => (props.valor ? props.valor(v) : `${fmt(v, v < 100 ? 1 : 0)} ${props.unidade}`)
const info = computed(() => (sel.value == null ? null : props.pontos[sel.value]))
</script>

<template>
  <div class="chart">
    <div class="tip" :class="{ vazio: !info }">
      <template v-if="info">
        <b>{{ info.rotuloLongo || info.rotulo }}</b>
        <span v-if="info.kwh != null">{{ mostra(info.kwh) }}</span>
        <span v-else>{{ info.futuro ? 'ainda não chegou' : 'sem dado' }}</span>
        <span class="sub">esperado {{ mostra(info.esp) }}</span>
      </template>
      <div v-else-if="compacto" class="legenda topo">
        <span><i class="q" style="background:var(--verde)"></i>gerado</span>
        <span><i class="q" style="background:var(--ambar)"></i>abaixo de 70%</span>
        <span><i class="l"></i>esperado</span>
      </div>
      <span v-else class="sub">Toque numa barra para ver o valor</span>
    </div>
    <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Gráfico de geração">
      <g v-for="v in grade" :key="v">
        <line :x1="PL" :x2="W" :y1="y(v)" :y2="y(v)" class="grade" />
        <text :x="PL - 6" :y="y(v) + 3" class="eixo" text-anchor="end">{{ v >= 1000 ? fmt(v / 1000, 1) + 'k' : fmt(v) }}</text>
      </g>
      <g v-for="(p, i) in pontos" :key="p.data || i" @click="sel = i" style="cursor:pointer">
        <rect :x="PL + bw * i" :y="PT" :width="bw" :height="H - PT - PB" fill="transparent" />
        <rect v-if="p.kwh != null" :x="PL + bw * i + bw * 0.15" :y="y(p.kwh)" :width="bw * 0.7"
          :height="Math.max(p.kwh === 0 ? 3 : 0, y(0) - y(p.kwh))" :transform="p.kwh === 0 ? 'translate(0,-3)' : null" :fill="cor(p)" rx="3" class="barra" :style="{ animationDelay: (i * 0.018) + 's' }" :opacity="sel == null || sel === i ? 1 : 0.45" />
        <text v-if="i % rotuloCada === 0 || i === pontos.length - 1" :x="PL + bw * i + bw / 2" :y="H - 6"
          class="eixo" text-anchor="middle">{{ p.rotulo }}</text>
      </g>
      <path :d="linha" class="esp" />
    </svg>
    <div v-if="!compacto" class="legenda">
      <span><i class="q" style="background:var(--verde)"></i>gerado</span>
      <span><i class="q" style="background:var(--ambar)"></i>abaixo de 70%</span>
      <span><i class="l"></i>esperado</span>
      <span v-if="pontos.some(p => p.kwh === 0)"><i class="q" style="background:var(--vermelho);height:3px"></i>sem geração</span>
    </div>
  </div>
</template>

<style scoped>
.chart svg { width: 100%; height: auto; display: block; }
.grade { stroke: var(--linha); stroke-width: 1; }
.barra { transform-box: fill-box; transform-origin: bottom; animation: cresce .55s cubic-bezier(.2,.8,.2,1) both; transition: opacity .2s; }
.esp { animation: aparece .6s .3s both; }
@keyframes aparece { from { opacity: 0; } }
.tip { transition: opacity .2s; }
.eixo { font-size: 9px; fill: var(--sub); font-family: inherit; }
.esp { fill: none; stroke: var(--sub); stroke-width: 1.2; stroke-dasharray: 4 3; opacity: .8; }
.tip { display: flex; gap: 10px; align-items: baseline; min-height: 24px; font-size: 14px; margin-bottom: 6px; flex-wrap: wrap; }
.legenda.topo { margin: 0; gap: 10px; flex-wrap: nowrap; white-space: nowrap; width: 100%; }
.legenda .dica { margin-left: auto; font-style: italic; opacity: .8; }
.tip .sub, .sub { color: var(--sub); font-size: 12px; }
.legenda { display: flex; gap: 14px; font-size: 11px; color: var(--sub); margin-top: 6px; flex-wrap: wrap; }
.legenda span { display: flex; align-items: center; gap: 5px; }
.q { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
.l { width: 16px; border-top: 1.5px dashed var(--sub); display: inline-block; }
</style>
