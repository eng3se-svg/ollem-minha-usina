import { ref, watch, onMounted } from 'vue'

export const semMovimento = () => typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches
const suave = t => 1 - Math.pow(1 - t, 3) // ease-out cúbico

// Número que "conta" até o valor (ex.: 0 → 7,2 kWh)
export function useContador(fonte, ms = 900) {
  const v = ref(0)
  let raf = 0
  const ir = (de, para) => {
    cancelAnimationFrame(raf)
    if (semMovimento()) { v.value = para; return }
    const t0 = performance.now()
    const passo = agora => {
      const t = Math.min(1, (agora - t0) / ms)
      v.value = de + (para - de) * suave(t)
      if (t < 1) raf = requestAnimationFrame(passo)
    }
    raf = requestAnimationFrame(passo)
  }
  onMounted(() => ir(0, fonte() || 0))
  watch(fonte, (n, o) => ir(o || 0, n || 0))
  return v
}
