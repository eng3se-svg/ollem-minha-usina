<script setup>
import simbolo from '../assets/simbolo.png'
</script>

<template>
  <div class="abertura" aria-label="Abrindo Ollem - Minha usina">
    <div class="marca">
      <svg class="anel" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="54" pathLength="1" />
      </svg>
      <img :src="simbolo" alt="Ollem" />
    </div>
    <div class="nome">Ollem <span>Minha usina</span></div>
  </div>
</template>

<style scoped>
.abertura { position: absolute; inset: 0; z-index: 100; background: #0c100e; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 22px; }
.marca { position: relative; width: 120px; height: 120px; display: grid; place-items: center; }
.marca img { width: 58px; animation: simbolo .7s cubic-bezier(.2, 1.4, .3, 1) both; }
.anel { position: absolute; inset: 0; transform: rotate(-90deg); }
.anel circle { fill: none; stroke: var(--lima); stroke-width: 2; stroke-linecap: round; stroke-dasharray: 1; stroke-dashoffset: 1; animation: anel .8s .15s cubic-bezier(.6, 0, .2, 1) forwards; }
.nome { color: #fff; font-size: 17px; font-weight: 700; letter-spacing: -.3px; animation: nome .5s .45s ease both; }
.nome span { color: var(--lima); }
@keyframes simbolo { from { opacity: 0; transform: scale(.55) rotate(-25deg); } to { opacity: 1; transform: none; } }
@keyframes anel { to { stroke-dashoffset: 0; } }
@keyframes nome { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
</style>
