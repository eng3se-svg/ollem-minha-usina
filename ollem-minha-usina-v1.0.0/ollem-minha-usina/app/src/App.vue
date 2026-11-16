<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import Abertura from './components/Abertura.vue'
import Tour from './components/Tour.vue'
import { estado, usinas, usina, r, temaEscuro } from './store'
import { fmt, resumo } from './lib/calc'
const corSit = s => ({ gerando: 'var(--verde)', noite: '#8b9cff', sem_comunicacao: 'var(--vermelho)', aviso: 'var(--ambar)' }[s])
import simbolo from './assets/simbolo.png'
import Login from './views/Login.vue'
import Inicio from './views/Inicio.vue'
import Graficos from './views/Graficos.vue'
import Economia from './views/Economia.vue'
import Ajuda from './views/Ajuda.vue'
import Conta from './views/Conta.vue'

const abas = [
  { id: 'graficos', nome: 'Geração', ic: 'M4 20V10M10 20V4M16 20v-8M22 20H2' },
  { id: 'ajuda', nome: 'Serviços', ic: 'M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z' },
  { id: 'inicio', fab: true },
  { id: 'economia', nome: 'Economia', ic: 'M12 2v20M17 6H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6' },
  { id: 'conta', nome: 'Perfil', ic: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-8 9a8 8 0 0 1 16 0' }
]
const views = { inicio: Inicio, graficos: Graficos, economia: Economia, ajuda: Ajuda, conta: Conta }
const titulos = { inicio: 'Minha usina', graficos: 'Geração', economia: 'Economia', ajuda: 'Serviços', conta: 'Perfil' }
const trocar = ref(false)

// Abertura rápida (≈1,3 s) com a logo
const abrindo = ref(true)
onMounted(() => setTimeout(() => (abrindo.value = false), 1300))

// Direção da transição entre abas (segue a ordem da barra de baixo)
const ordem = ['graficos', 'ajuda', 'inicio', 'economia', 'conta']
const dir = ref('aba-dir')
watch(() => estado.aba, (n, o) => { dir.value = ordem.indexOf(n) >= ordem.indexOf(o) ? 'aba-dir' : 'aba-esq'; trocar.value = false })
const main = ref(null)
const rolarTopo = () => main.value && (main.value.scrollTop = 0)
const nAlertas = computed(() => r.value.alertas.length)
</script>

<template>
  <div class="tela" :class="{ escuro: temaEscuro, 'texto-grande': estado.textoGrande }">
    <Transition name="abre"><Abertura v-if="abrindo" /></Transition>
    <Tour v-if="estado.tour && estado.logado" />
    <Transition name="troca" mode="out-in">
    <Login v-if="!estado.logado" key="login" />
    <div v-else key="app" class="app">
      <header>
        <img :src="simbolo" alt="Ollem" class="simb" />
        <button class="t" @click="trocar = !trocar">
          <b>{{ titulos[estado.aba] }}<span v-if="usinas.length > 1" class="chev" :class="{ aberto: trocar }"><svg viewBox="0 0 12 12"><path d="M3 4.5l3 3 3-3" /></svg></span></b>
          <small>{{ usina.bairro }} · {{ fmt(usina.kwp, 2) }} kWp</small>
        </button>
        <Transition name="menu">
        <div v-if="trocar" class="menu-usinas" @click.self="trocar = false">
          <div class="mu">
            <small>Suas usinas</small>
            <button v-for="(u, i) in usinas" :key="u.id" :class="{ on: estado.usinaIdx === i }" @click="estado.usinaIdx = i; trocar = false">
              <i class="ponto" :style="{ background: corSit(resumo(u).situacao) }"></i>
              <span>Usina em {{ u.bairro }}</span><em>{{ fmt(u.kwp, 2) }} kWp</em>
              <svg v-if="estado.usinaIdx === i" class="ok" viewBox="0 0 12 12"><path d="M2.5 6.2l2.3 2.3 4.7-5" /></svg>
            </button>
          </div>
        </div>
        </Transition>
        <button class="sino" @click="estado.aba = 'inicio'" aria-label="Avisos">
          <svg viewBox="0 0 24 24"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10 21h4" /></svg>
          <i v-if="nAlertas">{{ nAlertas }}</i>
        </button>
      </header>
      <main ref="main">
        <Transition :name="dir" mode="out-in" @before-enter="rolarTopo">
          <component :is="views[estado.aba]" :key="estado.aba + '-' + estado.usinaIdx" />
        </Transition>
      </main>
      <nav>
        <template v-for="a in abas" :key="a.id">
          <button v-if="a.fab" class="fab" :class="{ on: estado.aba === a.id }" @click="estado.aba = a.id" aria-label="Início">
            <img :src="simbolo" alt="" />
          </button>
          <button v-else :class="{ on: estado.aba === a.id }" @click="estado.aba = a.id">
            <svg viewBox="0 0 24 24"><path :d="a.ic" /></svg>
            <span>{{ a.nome }}</span>
          </button>
        </template>
      </nav>
    </div>
    </Transition>
  </div>
</template>

<style scoped>
.tela { position: relative; width: 100%; max-width: 430px; min-height: 100vh; background: var(--fundo); color: var(--texto); display: flex; flex-direction: column; overflow: hidden; }
@media (min-width: 600px) {
  .tela { margin: 24px 0; min-height: 0; height: 860px; border-radius: 44px; box-shadow: 0 24px 60px rgba(0,0,0,.16); border: 9px solid #0c0e0d; }
}
header { display: flex; align-items: center; gap: 10px; padding: 18px 20px 4px; }
.app { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.simb { height: 26px; }
/* abertura */
.abre-leave-active { transition: opacity .35s ease, transform .35s ease, filter .35s ease; }
.abre-leave-to { opacity: 0; transform: scale(1.08); filter: blur(6px); }
/* login → app */
.troca-enter-active, .troca-leave-active { transition: opacity .35s ease, transform .35s cubic-bezier(.2,.8,.2,1); }
.troca-enter-from { opacity: 0; transform: scale(.97); }
.troca-leave-to { opacity: 0; transform: scale(1.03); }
/* abas */
.aba-dir-enter-active, .aba-dir-leave-active, .aba-esq-enter-active, .aba-esq-leave-active { transition: opacity .22s ease, transform .26s cubic-bezier(.2,.8,.2,1); }
.aba-dir-enter-from { opacity: 0; transform: translateX(22px); }
.aba-dir-leave-to { opacity: 0; transform: translateX(-14px); }
.aba-esq-enter-from { opacity: 0; transform: translateX(-22px); }
.aba-esq-leave-to { opacity: 0; transform: translateX(14px); }
/* menu de usinas */
.menu-enter-active, .menu-leave-active { transition: opacity .2s ease; }
.menu-enter-active .mu, .menu-leave-active .mu { transition: transform .25s cubic-bezier(.2,.8,.2,1), opacity .2s; }
.menu-enter-from, .menu-leave-to { opacity: 0; }
.menu-enter-from .mu, .menu-leave-to .mu { transform: translateY(-10px) scale(.98); opacity: 0; }
.t { line-height: 1.15; background: none; border: 0; padding: 0; text-align: left; color: inherit; font: inherit; }
.t b { display: inline-flex; align-items: center; gap: 6px; }
.chev { width: 20px; height: 20px; border-radius: 50%; background: var(--trilho); display: inline-grid; place-items: center; transition: transform .3s cubic-bezier(.3,1.4,.5,1), background .2s; }
.chev svg { width: 11px; height: 11px; fill: none; stroke: var(--texto); stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.chev.aberto { transform: rotate(180deg); background: var(--linha); }
.t:active .chev { transform: scale(.88); }
.mu button { align-items: center; gap: 10px; }
.mu button span { flex: 1; text-align: left; }
.mu .ok { width: 14px; height: 14px; fill: none; stroke: var(--acento); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.menu-usinas { position: absolute; inset: 0; z-index: 30; background: rgba(0,0,0,.25); }
.mu { position: absolute; top: 64px; left: 16px; right: 16px; background: var(--card); border: 1px solid var(--linha); border-radius: 18px; padding: 10px; box-shadow: 0 12px 40px rgba(0,0,0,.18); }
.mu small { display: block; font-size: 11.5px; color: var(--sub); padding: 4px 8px 6px; }
.mu button { display: flex; justify-content: space-between; width: 100%; border: 0; background: none; color: var(--texto); padding: 11px 8px; border-radius: 12px; font-size: 14px; font-weight: 500; }
.mu button.on { background: var(--trilho); font-weight: 600; }
.mu em { font-style: normal; color: var(--sub); font-size: 12.5px; }
.t b { font-size: 15px; font-weight: 700; letter-spacing: -.2px; }
.t small { display: block; font-size: 12px; color: var(--sub); }
.sino { margin-left: auto; width: 38px; height: 38px; border-radius: 50%; border: 1px solid var(--linha); background: var(--card); display: grid; place-items: center; position: relative; padding: 0; }
.sino svg { width: 18px; height: 18px; stroke: var(--texto); fill: none; stroke-width: 1.7; }
.sino i { position: absolute; top: -3px; right: -3px; min-width: 17px; height: 17px; border-radius: 99px; background: var(--vermelho); color: #fff; font-size: 10px; font-style: normal; font-weight: 700; display: grid; place-items: center; border: 2px solid var(--fundo); }
.previa { display: flex; align-items: center; gap: 6px; padding: 6px 20px 0; font-size: 11px; color: var(--sub); }
.previa button { border: 1px solid var(--linha); background: var(--card); color: var(--sub); border-radius: 99px; width: 24px; height: 20px; font-size: 10.5px; padding: 0; }
.previa button.on { background: var(--texto); color: var(--fundo); border-color: var(--texto); font-weight: 700; }
main { scrollbar-width: none; }
main::-webkit-scrollbar { display: none; }
.texto-grande main { zoom: 1.12; }
main { flex: 1; overflow-y: auto; padding: 12px 16px 24px; }
nav { display: flex; align-items: center; justify-content: space-around; padding: 10px 10px 20px; background: var(--nav); border-top: 1px solid var(--linha); }
nav button { border: 0; background: none; display: flex; flex-direction: column; align-items: center; gap: 4px; color: var(--navtx); font-size: 10.5px; font-weight: 500; width: 60px; padding: 0; }
nav button { transition: color .2s, transform .15s; }
nav button:active { transform: scale(.9); }
nav button.on { color: var(--texto); font-weight: 600; }
nav button.on svg { animation: pula .35s cubic-bezier(.2,1.6,.4,1); }
@keyframes pula { 40% { transform: translateY(-3px) scale(1.08); } }
nav button:not(.fab).on::after { content: ''; width: 4px; height: 4px; border-radius: 50%; background: var(--verde); margin-top: -1px; }
nav svg { width: 22px; height: 22px; fill: none; stroke: currentColor; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; }
.fab { width: 52px !important; height: 52px; border-radius: 50%; background: var(--escuro) !important; display: grid !important; place-items: center; margin-top: -6px; }
.escuro .fab { background: #1d2420 !important; }
.fab.on { outline: 2px solid var(--verde); outline-offset: 2px; }
.fab { transition: transform .2s cubic-bezier(.2,1.4,.4,1), outline-color .2s; }
.fab:active { transform: scale(.88); }
.fab.on img { animation: gira .5s cubic-bezier(.2,1.2,.4,1); }
@keyframes gira { from { transform: rotate(-30deg) scale(.8); } }
.fab img { width: 26px; }
</style>
