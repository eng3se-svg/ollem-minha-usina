<script setup>
// Passo a passo do 1º acesso: um "holofote" percorre as partes do app explicando cada uma.
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { estado, usinas } from '../store'

const todos = [
  { alvo: '.sol', folga: 0, t: 'A sua usina hoje', d: 'O sol anda pelo arco conforme a hora. No meio, quanto a usina já gerou hoje. Embaixo, a potência agora e o esperado para o dia.' },
  { alvo: '.k2', folga: 3, t: 'O mês em um olhar', d: 'Quanto a usina gerou no mês, se está dentro do esperado, e quanto você já economizou na conta de luz.' },
  { alvo: 'header .t', t: 'Suas usinas', d: 'Tem mais de uma usina? Toque aqui para trocar.', so: () => usinas.length > 1, folga: 8 },
  { alvo: 'header .sino', t: 'Avisos', d: 'Se a usina parar ou gerar abaixo do esperado, o aviso aparece aqui e no seu celular.' },
  { alvo: 'nav button:nth-child(1)', t: 'Geração', d: 'Gráficos de 7 dias, 15 dias, mês, 12 meses ou o período que você escolher, sempre comparando com o esperado.', folga: 4 },
  { alvo: 'nav button:nth-child(2)', t: 'Serviços', d: 'Converse com a Ollivia e solicite limpeza, visita técnica ou relatório de geração.', folga: 4 },
  { alvo: 'nav .fab', t: 'Volta para o início', d: 'O símbolo da Ollem sempre traz você de volta para esta tela.' },
  { alvo: 'nav button:nth-child(4)', t: 'Economia', d: 'Quanto você economizou, mês a mês, e quanto do investimento já voltou.', folga: 4 },
  { alvo: 'nav button:nth-child(5)', t: 'Perfil', d: 'Avisos, tarifa da conta de luz, tema, Face ID e acesso para a família. Dá para rever este passo a passo por lá.', folga: 4 }
]
const passos = todos.filter(p => !p.so || p.so())
const n = ref(0)
const caixa = ref({ x: 0, y: 0, w: 0, h: 0, r: 16 })
const tela = ref({ w: 390, h: 800 })
const pronto = ref(false)
let ro

const medir = async () => {
  await nextTick()
  const t = document.querySelector('.tela'), el = document.querySelector(passos[n.value].alvo)
  if (!t || !el) return
  const main = document.querySelector('main')
  if (main && main.contains(el)) {
    const rm = main.getBoundingClientRect(), re = el.getBoundingClientRect()
    if (re.top < rm.top + 8 || re.bottom > rm.bottom - 8) { el.scrollIntoView({ block: 'center', behavior: 'smooth' }); await new Promise(r => setTimeout(r, 380)) }
  }
  const rt = t.getBoundingClientRect(), r = el.getBoundingClientRect()
  const folga = passos[n.value].folga ?? 6
  const raio = parseFloat(getComputedStyle(el).borderTopLeftRadius) || 12
  // posição relativa à área interna da tela (desconta a moldura/borda)
  tela.value = { w: t.clientWidth, h: t.clientHeight }
  caixa.value = {
    x: r.left - rt.left - t.clientLeft - folga,
    y: r.top - rt.top - t.clientTop - folga,
    w: r.width + folga * 2, h: r.height + folga * 2,
    r: Math.min(raio + folga, (r.height + folga * 2) / 2)
  }
}
const ir = async d => { n.value = Math.min(passos.length - 1, Math.max(0, n.value + d)); await medir() }
const fim = () => { estado.tour = false }

const MARGEM = 16
const embaixo = computed(() => caixa.value.y + caixa.value.h / 2 < tela.value.h / 2) // balão abaixo do alvo?
const balao = computed(() => (embaixo.value
  ? { top: caixa.value.y + caixa.value.h + 14 + 'px' }
  : { bottom: tela.value.h - caixa.value.y + 14 + 'px' }))
// bico apontando para o centro do alvo (coordenada dentro do balão)
const bico = computed(() => {
  const centro = caixa.value.x + caixa.value.w / 2 - MARGEM - 8
  return Math.min(Math.max(centro, 18), tela.value.w - MARGEM * 2 - 34)
})

onMounted(() => {
  // espera as animações de entrada do Início terminarem antes de medir
  setTimeout(async () => { await medir(); pronto.value = true; setTimeout(medir, 400) }, 1000)
  window.addEventListener('resize', medir)
  ro = new ResizeObserver(() => pronto.value && medir()); ro.observe(document.querySelector('.tela'))
})
onBeforeUnmount(() => { window.removeEventListener('resize', medir); ro?.disconnect() })
</script>

<template>
  <div class="tour" :class="{ pronto }" @click.self="ir(1)">
    <div class="holofote" :style="{ transform: `translate(${caixa.x}px, ${caixa.y}px)`, width: caixa.w + 'px', height: caixa.h + 'px', borderRadius: caixa.r + 'px' }">
      <i class="anel"></i><i class="anel a2"></i>
    </div>
    <Transition name="bal" mode="out-in">
      <div class="balao" :key="n" :style="balao" :class="{ embaixo }">
        <i class="bico" :style="{ left: bico + 'px' }"></i>
        <div class="cont">{{ n + 1 }} de {{ passos.length }}</div>
        <b>{{ passos[n].t }}</b>
        <p>{{ passos[n].d }}</p>
        <div class="acoes">
          <button class="pular" @click="fim">Pular</button>
          <div class="pts"><i v-for="(p, k) in passos" :key="k" :class="{ on: k === n, feito: k < n }"></i></div>
          <div class="dir">
            <button class="volta" :class="{ some: n === 0 }" :disabled="n === 0" @click="ir(-1)" aria-label="Anterior">
              <svg viewBox="0 0 12 12"><path d="M7.5 2.5L4 6l3.5 3.5" /></svg>
            </button>
            <button class="prox" @click="n < passos.length - 1 ? ir(1) : fim()">{{ n < passos.length - 1 ? 'Próximo' : 'Começar' }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.tour { position: absolute; inset: 0; z-index: 60; opacity: 0; transition: opacity .45s ease; }
.tour.pronto { opacity: 1; }
.holofote { position: absolute; left: 0; top: 0; pointer-events: none; box-shadow: 0 0 0 9999px rgba(6, 10, 8, .7);
  transition: transform .5s cubic-bezier(.3,1,.4,1), width .5s cubic-bezier(.3,1,.4,1), height .5s cubic-bezier(.3,1,.4,1), border-radius .5s; }
/* anéis que "respiram" para fora: só transform + opacity, sem travar */
.anel { position: absolute; inset: 0; border-radius: inherit; border: 2px solid var(--lima); will-change: transform, opacity; animation: respira 2.4s cubic-bezier(.2,.6,.3,1) infinite; }
.anel.a2 { animation-delay: 1.2s; }
@keyframes respira { 0% { transform: scale(1); opacity: .9; } 100% { transform: scale(1.12); opacity: 0; } }
.balao { position: absolute; left: 16px; right: 16px; background: #fff; color: #151b18; border-radius: 22px; padding: 16px 16px 14px; box-shadow: 0 18px 44px rgba(0,0,0,.35); }
.bico { position: absolute; width: 16px; height: 16px; background: #fff; transform: rotate(45deg); border-radius: 3px; bottom: -7px; transition: left .4s cubic-bezier(.3,1,.4,1); }
.embaixo .bico { bottom: auto; top: -7px; }
.cont { font-size: 11.5px; font-weight: 600; color: #0ea308; }
.balao b { display: block; font-size: 17px; margin-top: 2px; letter-spacing: -.3px; }
.balao p { font-size: 13.5px; color: #5d6964; line-height: 1.5; margin: 6px 0 14px; }
/* três colunas iguais: pontos sempre no centro, botões sempre à direita */
.acoes { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 8px; }
.pular { justify-self: start; background: none; border: 0; color: #78837d; font-size: 13.5px; font-weight: 500; padding: 8px 2px; }
.pts { display: flex; gap: 4px; justify-content: center; }
.pts i { width: 5px; height: 5px; border-radius: 5px; background: #dfe4e1; transition: width .3s cubic-bezier(.3,1,.4,1), background .3s; }
.pts i.feito { background: #a6e3a2; }
.pts i.on { width: 16px; background: #11c90a; }
.dir { justify-self: end; display: flex; align-items: center; gap: 6px; }
.volta { width: 38px; height: 38px; border-radius: 50%; border: 1px solid #e3e8e5; background: #fff; padding: 0; display: grid; place-items: center; transition: opacity .2s, transform .15s; }
.volta svg { width: 14px; height: 14px; fill: none; stroke: #151b18; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.volta.some { opacity: 0; pointer-events: none; }
.prox { border: 0; background: #151b18; color: #fff; border-radius: 99px; height: 38px; padding: 0 18px; font-size: 14px; font-weight: 600; min-width: 96px; }
.prox:active, .volta:active { transform: scale(.94); }
.bal-enter-active, .bal-leave-active { transition: opacity .2s, transform .3s cubic-bezier(.2,.8,.2,1); }
.bal-enter-from { opacity: 0; transform: translateY(8px) scale(.98); }
.bal-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) { .anel { animation: none; } }
</style>
