<script setup>
import { computed } from 'vue'
import { usina, r, estado, OLLIVIA_WA } from '../store'
import { fmt, reais, MESES_LONGOS } from '../lib/calc'
import CartaoSol from '../components/CartaoSol.vue'
import { useContador } from '../lib/anima'
const mesAnim = useContador(() => r.value.mesKwh)
const ecoAnim = useContador(() => r.value.mesKwh * r.value.tarifa)

const mesNome = computed(() => MESES_LONGOS[r.value.agora.m0])
const dias = computed(() => {
  const max = Math.max(...r.value.dias7.map(d => Math.max(d.kwh ?? 0, d.esp)), 1) * 1.05
  return r.value.dias7.map(d => {
    const [y, m, dd] = d.data.split('-').map(Number)
    return {
      ...d,
      h: d.kwh == null ? 10 : Math.max(4, (d.kwh / max) * 100),
      cls: d.kwh == null ? 'na' : d.kwh === 0 ? 'zero' : d.kwh / d.esp < 0.7 ? 'low' : '',
      sem: new Date(y, m - 1, dd).toLocaleDateString('pt-BR', { weekday: 'short' }).replace('.', '')
    }
  })
})
const espPct = computed(() => {
  const max = Math.max(...r.value.dias7.map(d => Math.max(d.kwh ?? 0, d.esp)), 1) * 1.05
  return (r.value.esp.kwh / max) * 100
})
const abrir = v => { estado.servico = v; estado.aba = 'ajuda' }
const corAlerta = n => (n === 'alta' ? 'var(--vermelho)' : 'var(--ambar)')
</script>

<template>
  <div class="pg">
    <CartaoSol :r="r" :u="usina" />

    <div v-for="a in r.alertas" :key="a.titulo" class="card alerta">
      <div class="at"><i class="ponto" :style="{ background: corAlerta(a.nivel) }"></i>{{ a.titulo }}</div>
      <p>{{ a.texto }}</p>
      <button v-if="a.acao === 'ollivia'" class="acao" @click="abrir('chat')">Falar com a Ollivia ›</button>
      <button v-else class="acao" @click="abrir('pedido')">Solicitar limpeza ou visita ›</button>
    </div>

    <div class="rot"><span style="text-transform:capitalize">{{ mesNome }}</span><button @click="estado.aba = 'graficos'">Ver geração</button></div>
    <div class="k2">
      <div class="card kb">
        <small>Gerado no mês</small>
        <b>{{ fmt(mesAnim) }}<span>kWh</span></b>
        <div class="uso"><i :style="{ width: Math.min(100, (r.desempMes || 0) * 100) + '%', background: (r.desempMes || 0) < .7 ? 'var(--ambar)' : 'var(--verde)' }"></i></div>
        <div class="d">{{ fmt((r.desempMes || 0) * 100) }}% do esperado</div>
      </div>
      <div class="card kb eco" @click="estado.aba = 'economia'">
        <small>Economia no mês</small>
        <b>{{ reais(ecoAnim).replace(/,\d\d$/, '') }}</b>
        <div class="d" style="margin-top:13px">{{ reais(r.totalKwh * r.tarifa) }} desde o início</div>
      </div>
    </div>

    <div class="card">
      <div class="rot" style="padding:0 0 8px"><span>Últimos 7 dias</span><span style="font-weight:500">kWh por dia</span></div>
      <div class="bars">
        <div class="esp" :style="{ bottom: espPct + '%' }"></div>
        <i v-for="(d, k) in dias" :key="d.data" :class="d.cls" :style="{ height: d.h + '%', animationDelay: (0.25 + k * 0.05) + 's' }" :title="d.kwh == null ? 'sem dado' : fmt(d.kwh, 1) + ' kWh'"></i>
      </div>
      <div class="dd"><span v-for="d in dias" :key="d.data">{{ d.sem }}</span></div>
    </div>

    <a class="card ollivia" href="#" @click.prevent="abrir('chat')">
      <div class="av">O</div>
      <div><b>Falar com a Ollivia</b><small>Dúvidas, limpeza ou visita técnica</small></div>
      <span class="seta">›</span>
    </a>
  </div>
</template>

<style scoped>
.pg { display: flex; flex-direction: column; gap: 12px; }
.alerta .at { font-weight: 600; font-size: 14px; display: flex; align-items: center; gap: 8px; }
.alerta p { margin: 6px 0 8px; font-size: 13px; color: var(--sub); line-height: 1.45; }
.acao { color: var(--acento); font-weight: 600; font-size: 13px; text-decoration: none; background: none; border: 0; padding: 0; }
.rot { margin-top: 4px; }
.k2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.kb small { font-size: 11.5px; color: var(--sub); display: block; }
.kb b { display: block; font-size: 22px; font-weight: 700; letter-spacing: -.6px; margin-top: 4px; }
.kb b span { font-size: 12px; font-weight: 500; color: var(--sub); margin-left: 3px; letter-spacing: 0; }
.kb .uso { height: 4px; border-radius: 4px; background: var(--trilho); margin-top: 9px; overflow: hidden; }
.kb .uso i { display: block; height: 100%; border-radius: 4px; transform-origin: left; animation: enche .9s .2s cubic-bezier(.2,.8,.2,1) both; }
.kb .d { font-size: 11px; color: var(--sub); margin-top: 6px; }
.eco { cursor: pointer; }
.eco b { color: var(--acento); }
.bars { display: flex; align-items: flex-end; gap: 10px; height: 52px; position: relative; }
.bars i { flex: 1; border-radius: 6px; background: var(--verde); transform-origin: bottom; animation: cresce .6s cubic-bezier(.2,.8,.2,1) both; }
.bars i.low { background: var(--ambar); }
.bars i.zero { background: var(--vermelho); height: 4px !important; }
.bars i.na { background: var(--trilho); }
.bars .esp { position: absolute; left: 0; right: 0; border-top: 1px dashed var(--sub); opacity: .5; }
.dd { display: flex; gap: 10px; margin-top: 6px; }
.dd span { flex: 1; text-align: center; font-size: 10px; color: var(--sub); }
.ollivia { display: flex; align-items: center; gap: 12px; text-decoration: none; color: inherit; }
.av { width: 36px; height: 36px; border-radius: 50%; background: var(--verde); color: #fff; display: grid; place-items: center; font-weight: 700; flex-shrink: 0; }
.ollivia b { font-size: 13.5px; font-weight: 600; display: block; }
.ollivia small { font-size: 11.5px; color: var(--sub); }
.seta { margin-left: auto; color: var(--sub); font-size: 20px; }
</style>
