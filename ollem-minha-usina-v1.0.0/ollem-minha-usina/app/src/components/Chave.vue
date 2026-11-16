<script setup>
// Chave liga/desliga no estilo do app: trilho com degradê verde, bolinha que "estica" ao tocar
// e um ícone (✓ ou –) dentro da bolinha. Acessível: role="switch" + aria-checked.
const props = defineProps({ modelValue: Boolean, rotulo: String })
const emit = defineEmits(['update:modelValue'])
const alternar = () => emit('update:modelValue', !props.modelValue)
</script>

<template>
  <button type="button" class="chave" :class="{ on: modelValue }" role="switch" :aria-checked="modelValue" :aria-label="rotulo" @click.stop="alternar">
    <span class="bola">
      <svg viewBox="0 0 12 12"><path v-if="modelValue" d="M2.5 6.2l2.3 2.3 4.7-5" /><path v-else d="M3.5 6h5" /></svg>
    </span>
  </button>
</template>

<style scoped>
.chave { position: relative; width: 52px; height: 32px; border-radius: 99px; border: 0; padding: 0; flex-shrink: 0; cursor: pointer;
  background: var(--trilho); box-shadow: inset 0 0 0 1px var(--linha); transition: background .3s ease, box-shadow .3s ease; }
.chave.on { background: linear-gradient(90deg, var(--verde2), var(--verde)); box-shadow: inset 0 0 0 1px rgba(0,0,0,.04), 0 2px 10px rgba(17,201,10,.28); }
.bola { position: absolute; top: 3px; left: 3px; width: 26px; height: 26px; border-radius: 99px; background: #fff; display: grid; place-items: center;
  box-shadow: 0 2px 6px rgba(0,0,0,.18), 0 0 0 .5px rgba(0,0,0,.04);
  transition: left .35s cubic-bezier(.3,1.5,.5,1), width .2s ease, transform .2s; }
.chave.on .bola { left: 23px; }
.chave:active .bola { width: 32px; }            /* estica ao segurar, como no iPhone */
.chave.on:active .bola { left: 17px; }
.bola svg { width: 12px; height: 12px; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; stroke: #b4bdb8; transition: stroke .3s; }
.chave.on .bola svg { stroke: var(--verde2); animation: marca .3s ease; }
@keyframes marca { from { opacity: 0; transform: scale(.4); } }
.chave:focus { outline: none; }
.chave:focus-visible { outline: 2px solid var(--lima); outline-offset: 3px; }
:global(.escuro) .chave:not(.on) { background: #232b26; box-shadow: inset 0 0 0 1px #2c3530; }
:global(.escuro) .chave:not(.on) .bola { background: #d9e0dc; }
</style>
