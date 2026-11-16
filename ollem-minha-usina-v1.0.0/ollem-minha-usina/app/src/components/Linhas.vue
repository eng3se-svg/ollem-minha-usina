<script setup>
// Ondas vivas: cada linha é redesenhada a cada quadro (canvas), com forma que respira e se curva,
// em vez de uma imagem deslizando. Estilo "fio de seda": as linhas andam juntas e se abrem e fecham.
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { semMovimento } from '../lib/anima'

const tela = ref(null)
let raf = 0, ctx, w = 0, h = 0, dpr = 1, t0 = 0, ro

const N = 11
const medir = () => {
  const c = tela.value
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  w = c.clientWidth; h = c.clientHeight
  c.width = w * dpr; c.height = h * dpr
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

const desenhar = agora => {
  const t = (agora - t0) / 1000
  ctx.clearRect(0, 0, w, h)
  const grad = ctx.createLinearGradient(0, 0, w, 0)
  grad.addColorStop(0, 'rgba(17,201,10,0)')
  grad.addColorStop(0.18, 'rgba(17,201,10,.55)')
  grad.addColorStop(0.5, 'rgba(142,247,5,.95)')
  grad.addColorStop(0.82, 'rgba(17,201,10,.55)')
  grad.addColorStop(1, 'rgba(17,201,10,0)')
  ctx.strokeStyle = grad
  for (let i = 0; i < N; i++) {
    const f = i / (N - 1)                      // 0 → 1 entre a primeira e a última linha
    const base = h * (0.42 + 0.34 * f)
    const abre = 0.55 + 0.45 * Math.sin(t * 0.35 + f * 2.2) // o feixe abre e fecha devagar
    const a1 = h * 0.16 * abre * (0.6 + f * 0.6)
    const a2 = h * 0.06 * (1 - f * 0.5)
    ctx.globalAlpha = 0.25 + 0.75 * (1 - Math.abs(f - 0.45) * 1.4)
    ctx.lineWidth = i % 3 === 0 ? 1.4 : 1
    ctx.beginPath()
    for (let x = -10; x <= w + 10; x += 6) {
      const u = x / w
      const y = base
        + a1 * Math.sin(u * 4.2 + t * 0.55 + f * 1.6)
        + a2 * Math.sin(u * 9.0 - t * 0.9 + f * 3.1)
        + h * 0.03 * Math.sin(u * 2.0 + t * 0.25 + f * 5.0)
      x === -10 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
    }
    ctx.stroke()
  }
  ctx.globalAlpha = 1
  if (!semMovimento()) raf = requestAnimationFrame(desenhar)
}

onMounted(() => {
  ctx = tela.value.getContext('2d')
  medir()
  t0 = performance.now() - 4000
  ro = new ResizeObserver(medir); ro.observe(tela.value)
  raf = requestAnimationFrame(desenhar)
})
onBeforeUnmount(() => { cancelAnimationFrame(raf); ro?.disconnect() })
</script>

<template>
  <canvas ref="tela" class="linhas" aria-hidden="true"></canvas>
</template>

<style scoped>
.linhas { position: absolute; left: 0; right: 0; bottom: 0; width: 100%; height: 260px; pointer-events: none;
  -webkit-mask-image: linear-gradient(to bottom, transparent 0%, #000 35%, #000 80%, transparent 100%);
          mask-image: linear-gradient(to bottom, transparent 0%, #000 35%, #000 80%, transparent 100%);
  animation: surge 1.2s ease both; }
@keyframes surge { from { opacity: 0; } }
</style>
