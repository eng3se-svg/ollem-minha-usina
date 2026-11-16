<script setup>
// Seletor de opções com destaque que desliza até a opção escolhida.
import { computed } from 'vue'
const props = defineProps({ modelValue: [String, Number], opcoes: Array }) // opcoes: [[valor, texto], ...]
const emit = defineEmits(['update:modelValue'])
const i = computed(() => Math.max(0, props.opcoes.findIndex(o => o[0] === props.modelValue)))
</script>

<template>
  <div class="segm" role="radiogroup" :style="{ '--n': opcoes.length, '--i': i }">
    <i class="marca"></i>
    <button v-for="o in opcoes" :key="o[0]" type="button" role="radio" :aria-checked="o[0] === modelValue" :class="{ on: o[0] === modelValue }" @click="emit('update:modelValue', o[0])">{{ o[1] }}</button>
  </div>
</template>

<style scoped>
.segm { position: relative; display: grid; grid-template-columns: repeat(var(--n), 1fr); background: var(--trilho); border-radius: 99px; padding: 3px; box-shadow: inset 0 0 0 1px var(--linha); }
.marca { position: absolute; top: 3px; bottom: 3px; left: 3px; width: calc((100% - 6px) / var(--n)); border-radius: 99px; background: var(--card);
  box-shadow: 0 1px 3px rgba(0,0,0,.1), 0 0 0 .5px rgba(0,0,0,.04); transform: translateX(calc(100% * var(--i))); transition: transform .35s cubic-bezier(.3,1.3,.5,1); }
button { position: relative; z-index: 1; border: 0; background: none; padding: 9px 6px; border-radius: 99px; font-size: 13px; font-weight: 500; color: var(--sub); transition: color .25s; cursor: pointer; }
button.on { color: var(--texto); font-weight: 600; }
button:active { transform: scale(.96); }
button:focus { outline: none; }
button:focus-visible { outline: 2px solid var(--lima); outline-offset: -2px; }
:global(.escuro) .marca { background: #2a332e; }
</style>
