<script setup>
import Segmento from '../components/Segmento.vue'
import { ref, computed, nextTick, onMounted } from 'vue'
import { estado, r, usina, modoDemo } from '../store'
import { api } from '../api'
import { fmt, reais } from '../lib/calc'

const ir = v => { estado.servico = v; enviado.value = false }

// Sugestão automática a partir do monitoramento (no app real vem de servicos.py do Hub)
const sugestao = computed(() => {
  const x = r.value
  if (x.situacao === 'sem_comunicacao') return { tipo: 'Visita técnica', txt: 'Sua usina está sem comunicação. Uma visita técnica confere o equipamento e a internet dele.' }
  if (x.desemp7 != null && x.desemp7 < 0.85) return { tipo: 'Limpeza das placas', txt: `Nos últimos 7 dias a usina gerou ${fmt(x.desemp7 * 100)}% do esperado. Uma limpeza costuma recuperar parte dessa perda.` }
  return null
})

// ---- Ollivia no app (prévia: respostas simuladas) ----
const texto = ref('')
const digitando = ref(false)
const lista = ref(null)
const resposta = q => {
  const t = q.toLowerCase()
  const x = r.value
  if (/gera|produz|hoje|kwh/.test(t)) return `Hoje sua usina já gerou ${fmt(x.hojeKwh, 1)} kWh (atualizado às ${x.atualizadoHora}). Em ${x.agora.d > 1 ? 'novembro' : 'este mês'} ela está em ${fmt((x.desempMes || 0) * 100)}% do esperado.`
  if (/conta|fatura|luz|cobran/.test(t)) return 'Posso analisar a sua conta de luz. Me mande uma foto ou o PDF da conta que eu explico os créditos da usina e o quanto você economizou.'
  if (/limp|suj|visita|manuten/.test(t)) return 'Posso solicitar isso para você agora. Toque em "Solicitar manutenção ou visita" e escolha o melhor período, que a equipe confirma o dia.'
  if (/econom|r\$|dinheiro/.test(t)) return `Desde o início, a sua usina já gerou o equivalente a cerca de ${reais(x.totalKwh * x.tarifa)} de energia.`
  return 'Entendi! Vou passar isso para a equipe do pós-venda, que responde em horário comercial (seg a sex, 8h às 17h). Quer que eu chame alguém agora?'
}
const enviarChat = async () => {
  const q = texto.value.trim()
  if (!q) return
  estado.chat.push({ de: 'eu', txt: q }); texto.value = ''
  digitando.value = true; await rolar()
  if (modoDemo) {
    setTimeout(async () => { digitando.value = false; estado.chat.push({ de: 'ollivia', txt: resposta(q) }); await rolar() }, 900)
    return
  }
  let txt
  try { txt = (await api.chat(q, estado.chat.slice(-20))).resposta } catch (e) { txt = e.message }
  digitando.value = false; estado.chat.push({ de: 'ollivia', txt }); await rolar()
}
const rolar = async () => { await nextTick(); if (lista.value) lista.value.scrollTop = lista.value.scrollHeight }
const atalhos = ['Quanto gerei hoje?', 'Quero entender minha conta de luz', 'Preciso de uma limpeza']

// ---- Pós-venda ----
const assuntoPV = ref('Dúvida')
const msgPV = ref('')
const enviado = ref(false)
const enviandoS = ref(false)
const erroS = ref('')
const mandar = async fn => {
  erroS.value = ''; enviandoS.value = true
  try { if (!modoDemo) await fn(); enviado.value = true; carregar() } catch (e) { erroS.value = e.message } finally { enviandoS.value = false }
}
const enviarPV = async () => {
  await mandar(() => api.solicitar({ tipo: 'mensagem', usina_id: usina.value.id, assunto: assuntoPV.value, texto: msgPV.value }))
  if (enviado.value) { if (modoDemo) estado.pedidos.unshift({ tipo: `Mensagem: ${assuntoPV.value}`, status: 'Recebido', quando: 'hoje' }); msgPV.value = '' }
}

// ---- Pedido de serviço ----
const tipos = ['Limpeza das placas', 'Manutenção preventiva', 'Visita técnica', 'Outro serviço']
const tipo = ref(tipos[0])
const periodo = ref('Qualquer')
const obs = ref('')
const abrirPedido = t => { tipo.value = t || tipos[0]; ir('pedido') }
const CODIGO_TIPO = { 'Limpeza das placas': 'limpeza', 'Manutenção preventiva': 'preventiva', 'Visita técnica': 'visita', 'Outro serviço': 'outro' }
const enviarPedido = async () => {
  await mandar(() => api.solicitar({ tipo: CODIGO_TIPO[tipo.value], usina_id: usina.value.id, periodo: periodo.value, texto: obs.value }))
  if (enviado.value) { if (modoDemo) estado.pedidos.unshift({ tipo: tipo.value, status: 'Recebido', quando: 'hoje', periodo: periodo.value }); obs.value = '' }
}
const etapasDe = p => (p.tipo.startsWith('Relatório') ? ['Recebido', 'Gerando', 'Pronto'] : p.tipo.startsWith('Mensagem') ? ['Recebido', 'Respondido'] : ['Recebido', 'Agendado', 'Feito'])
const passoDe = p => Math.max(0, etapasDe(p).indexOf(p.status))
const corStatus = s => ({ Recebido: 'var(--sub)', Agendado: 'var(--ambar)', Feito: 'var(--verde)', Pronto: 'var(--verde)' }[s] || 'var(--sub)')
const exemplosDemo = [
  { tipo: 'Relatório de geração · outubro/2026', status: 'Pronto', quando: '03/11/2026', abrir: true },
  { tipo: 'Limpeza das placas', status: 'Feito', quando: 'mar/2026' }
]
// app real: lista vem do servidor (GET /solicitacoes)
const doServidor = ref([])
const ESTADOS = { recebido: 'Recebido', agendado: 'Agendado', feito: 'Feito', gerando: 'Gerando', pronto: 'Pronto', respondido: 'Respondido', cancelado: 'Cancelado' }
const carregar = async () => {
  if (modoDemo) return
  try {
    doServidor.value = (await api.solicitacoes()).solicitacoes.map(x => ({
      id: x.id, tipo: x.tipo === 'mensagem' ? `Mensagem: ${x.detalhes.assunto || 'pós-venda'}` : x.titulo, status: ESTADOS[x.estado] || x.estado,
      quando: new Date(x.criado * 1000).toLocaleDateString('pt-BR'), contas: x.contas, abrir: x.pdf
    }))
  } catch { /* sem conexão: mantém a lista anterior */ }
}
onMounted(carregar)
const lista2 = computed(() => (modoDemo ? [...estado.pedidos, ...exemplosDemo] : doServidor.value))
const abrirPdf = async p => {
  if (modoDemo || !p.id) return
  const b = await api.relatorioPdf(p.id)
  window.open(URL.createObjectURL(b), '_blank')   // >>> TI: no app nativo, abrir com @capacitor/filesystem + share/preview
}

// ---- Relatório de geração ----
const periodos = ['Último mês', 'Últimos 3 meses', 'Últimos 12 meses', 'Últimos 7 dias', 'Últimos 15 dias', 'Outro período']
const periodoRel = ref('Último mês')
const de = ref(''), ate = ref('')
const contas = ref([])
const entrega = ref({ app: true, whats: true })
const campoArq = ref(null)
const anexar = e => { for (const f of e.target.files) contas.value.push({ nome: f.name, kb: Math.round(f.size / 1024), arquivo: f }); e.target.value = '' }
const nomePeriodo = computed(() => periodoRel.value === 'Outro período' && de.value && ate.value
  ? `${de.value.split('-').reverse().join('/')} a ${ate.value.split('-').reverse().join('/')}` : periodoRel.value.toLowerCase())
const podeRel = computed(() => periodoRel.value !== 'Outro período' || (de.value && ate.value && de.value <= ate.value))
// período → datas (de, ate) contadas até ontem
const datasRel = () => {
  const h = new Date(r.value.agora.y, r.value.agora.m0, r.value.agora.d), iso = d => d.toISOString().slice(0, 10)
  const menos = n => new Date(h.getFullYear(), h.getMonth(), h.getDate() - n, 12)
  if (periodoRel.value === 'Outro período') return [de.value, ate.value]
  if (periodoRel.value === 'Último mês') return [iso(new Date(h.getFullYear(), h.getMonth() - 1, 1, 12)), iso(new Date(h.getFullYear(), h.getMonth(), 0, 12))]
  const dias = { 'Últimos 3 meses': 91, 'Últimos 12 meses': 365, 'Últimos 7 dias': 7, 'Últimos 15 dias': 15 }[periodoRel.value]
  return [iso(menos(dias)), iso(menos(1))]
}
const enviarRel = async () => {
  const [d1, d2] = datasRel()
  await mandar(() => api.pedirRelatorio({ usina_id: usina.value.id, de: d1, ate: d2, contas: contas.value.map(c => c.arquivo).filter(Boolean),
    entrega: [entrega.value.app && 'app', entrega.value.whats && 'whatsapp'].filter(Boolean) }))
  if (enviado.value && modoDemo) estado.pedidos.unshift({ tipo: `Relatório de geração · ${nomePeriodo.value}`, status: 'Recebido', quando: 'hoje', contas: contas.value.length })
}
const novoRel = () => { contas.value = []; periodoRel.value = 'Último mês'; enviado.value = false }
</script>

<template>
  <div class="pg">
    <!-- MENU -->
    <template v-if="estado.servico === 'menu'">
      <div v-if="sugestao" class="sug">
        <small>Recomendado para a sua usina</small>
        <b>{{ sugestao.tipo }}</b>
        <p>{{ sugestao.txt }}</p>
        <button class="btn lima" @click="abrirPedido(sugestao.tipo)">Solicitar {{ sugestao.tipo.toLowerCase() }}</button>
      </div>

      <!-- Ollivia em destaque -->
      <div class="olli">
        <div class="ol1">
          <span class="avo">O<i></i></span>
          <div><b>Ollivia</b><small>Assistente da Ollem · responde na hora</small></div>
        </div>
        <button class="pergunta" @click="ir('chat')">Pergunte qualquer coisa sobre a sua usina…<span>↑</span></button>
        <div class="rapidas">
          <button v-for="a in atalhos" :key="a" @click="ir('chat'); texto = a; enviarChat()">{{ a }}</button>
        </div>
      </div>

      <!-- Blocos de serviço -->
      <div class="rot"><span>Solicitar</span></div>
      <div class="blocos">
        <button class="bloco" @click="abrirPedido('Limpeza das placas')">
          <span class="bi agua"><svg viewBox="0 0 24 24"><path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z" /></svg></span>
          <b>Limpeza das placas</b><small>Recupera a geração perdida com sujeira</small>
        </button>
        <button class="bloco" @click="abrirPedido('Visita técnica')">
          <span class="bi"><svg viewBox="0 0 24 24"><path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z" /></svg></span>
          <b>Visita técnica</b><small>Algo estranho? Um técnico confere</small>
        </button>
        <button class="bloco" @click="abrirPedido('Manutenção preventiva')">
          <span class="bi"><svg viewBox="0 0 24 24"><path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z M9 12l2 2 4-4" /></svg></span>
          <b>Manutenção preventiva</b><small>Revisão completa, uma vez por ano</small>
        </button>
        <button class="bloco" @click="ir('relatorio')">
          <span class="bi"><svg viewBox="0 0 24 24"><path d="M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6" /></svg></span>
          <b>Relatório de geração</b><small>Com análise das suas contas de luz</small>
        </button>
      </div>
      <button class="card linha-pv" @click="ir('posvenda')">
        <span class="bi"><svg viewBox="0 0 24 24"><path d="M4 5h16v11H8l-4 4z" /></svg></span>
        <span class="tx"><b>Falar com o pós-venda</b><small>Mensagem para a equipe da Ollem, com foto ou conta</small></span>
        <span class="seta">›</span>
      </button>

      <!-- Minhas solicitações em cartões com etapas -->
      <div class="rot" style="margin-top:4px"><span>Minhas solicitações</span></div>
      <div v-for="(p, i) in lista2" :key="'p' + i" class="card sol">
        <div class="s1"><b>{{ p.tipo }}</b><span class="status" :style="{ color: corStatus(p.status) }">{{ p.status }}</span></div>
        <small>{{ p.quando }}{{ p.contas ? ` · ${p.contas} ${p.contas === 1 ? 'conta anexada' : 'contas anexadas'}` : '' }}</small>
        <div class="etapas">
          <template v-for="(e, k) in etapasDe(p)" :key="e">
            <i :class="{ on: k <= passoDe(p) }"></i><span :class="{ on: k <= passoDe(p) }">{{ e }}</span>
          </template>
        </div>
        <button v-if="p.abrir" class="abrir" @click="abrirPdf(p)">Abrir PDF ›</button>
      </div>
      <p class="sub nota">Atendimento da equipe: segunda a sexta, das 8h às 17h. A Ollivia responde a qualquer hora.</p>
    </template>

    <!-- CHAT OLLIVIA -->
    <div v-else-if="estado.servico === 'chat'" class="chat">
      <button class="voltar" @click="ir('menu')">‹ Serviços</button>
      <div class="cabchat"><span class="ic verde">O</span><div><b>Ollivia</b><small>Assistente virtual da Ollem · online</small></div></div>
      <div class="msgs" ref="lista">
        <div v-for="(m, i) in estado.chat" :key="i" class="msg" :class="m.de">{{ m.txt }}</div>
        <div v-if="digitando" class="msg ollivia dig"><i></i><i></i><i></i></div>
      </div>
      <div class="atalhos" v-if="estado.chat.length < 3">
        <button v-for="a in atalhos" :key="a" @click="texto = a; enviarChat()">{{ a }}</button>
      </div>
      <form class="enviar" @submit.prevent="enviarChat">
        <input v-model="texto" placeholder="Escreva sua mensagem" />
        <button type="submit" aria-label="Enviar">↑</button>
      </form>
      <p v-if="modoDemo" class="previa">Prévia: respostas simuladas. No app de verdade, quem responde é a Ollivia do servidor, com os dados reais da usina.</p>
    </div>

    <!-- PÓS-VENDA -->
    <template v-else-if="estado.servico === 'posvenda'">
      <button class="voltar" @click="ir('menu')">‹ Serviços</button>
      <div class="card form" v-if="!enviado">
        <b class="h">Mensagem para o pós-venda</b>
        <div class="chips">
          <button v-for="a in ['Dúvida', 'Problema na usina', 'Conta de luz', 'Outro']" :key="a" :class="{ on: assuntoPV === a }" @click="assuntoPV = a">{{ a }}</button>
        </div>
        <textarea v-model="msgPV" rows="5" placeholder="Conte o que aconteceu ou o que você precisa"></textarea>
        <button class="btn sec anexo">Anexar foto ou conta de luz</button>
        <button class="btn primario" :disabled="!msgPV.trim() || enviandoS" @click="enviarPV">{{ enviandoS ? 'Enviando…' : 'Enviar mensagem' }}</button>
        <p v-if="erroS" class="erro-s">{{ erroS }}</p>
      </div>
      <div class="card ok" v-else>
        <div class="check">✓</div><b>Mensagem enviada</b>
        <p class="sub">A equipe responde aqui no app e pelo WhatsApp, em horário comercial.</p>
        <p v-if="modoDemo" class="previa">Prévia: no app de verdade, a mensagem abre um chamado no Pós-Vendas do Hub.</p>
        <button class="btn sec" @click="ir('menu')">Voltar para Serviços</button>
      </div>
    </template>

    <!-- RELATÓRIO -->
    <template v-else-if="estado.servico === 'relatorio'">
      <button class="voltar" @click="ir('menu')">‹ Serviços</button>
      <div class="card form" v-if="!enviado">
        <b class="h">Solicitar relatório de geração</b>
        <p class="sub" style="margin:-4px 0 0;line-height:1.45">Um PDF com a geração da usina, o esperado e o que isso significou na sua conta de luz.</p>
        <label class="sub">Período</label>
        <div class="chips">
          <button v-for="pr in periodos" :key="pr" :class="{ on: periodoRel === pr }" @click="periodoRel = pr">{{ pr }}</button>
        </div>
        <div v-if="periodoRel === 'Outro período'" class="datas">
          <label><span class="sub">De</span><input type="date" v-model="de" /></label>
          <label><span class="sub">Até</span><input type="date" v-model="ate" /></label>
        </div>

        <label class="sub">Contas de luz do período <span style="font-weight:400">(opcional)</span></label>
        <div class="anexos">
          <div v-for="(c, i) in contas" :key="i" class="arq">
            <span class="doc">PDF</span><span class="nm">{{ c.nome }}</span>
            <button @click="contas.splice(i, 1)" aria-label="Remover">×</button>
          </div>
          <button class="btn sec anexo" @click="campoArq.click()">+ Anexar conta (PDF ou foto)</button>
          <input ref="campoArq" type="file" accept="application/pdf,image/*" multiple hidden @change="anexar" />
          <p class="dica">Com as contas, o relatório mostra os créditos de energia, a compensação e quanto você economizou de verdade.</p>
        </div>

        <label class="sub">Receber por</label>
        <div class="chips">
          <button :class="{ on: entrega.app }" @click="entrega.app = !entrega.app">Aqui no app</button>
          <button :class="{ on: entrega.whats }" @click="entrega.whats = !entrega.whats">WhatsApp</button>
        </div>
        <button class="btn primario" :disabled="!podeRel || !(entrega.app || entrega.whats)" :class="{ x: enviandoS }" @click="enviarRel">{{ enviandoS ? 'Enviando…' : 'Solicitar relatório' }}</button>
        <p v-if="erroS" class="erro-s">{{ erroS }}</p>
      </div>
      <div class="card ok" v-else>
        <div class="check">✓</div><b>Solicitação recebida!</b>
        <p class="sub">O relatório ({{ nomePeriodo }}) fica pronto em até 1 dia útil{{ entrega.app ? ' e aparece em Minhas solicitações' : '' }}{{ entrega.whats ? (entrega.app ? ', e também' : '') + ' chega pelo WhatsApp' : '' }}.</p>
        <p v-if="modoDemo" class="previa">Prévia: no app de verdade, a solicitação vai para a fila de relatórios da Ollivia e o Hub gera o PDF (com a análise das contas, se houver).</p>
        <button class="btn sec" @click="novoRel(); ir('menu')">Ver minhas solicitações</button>
      </div>
    </template>

    <!-- PEDIDO -->
    <template v-else>
      <button class="voltar" @click="ir('menu')">‹ Serviços</button>
      <div class="card form" v-if="!enviado">
        <b class="h">Solicitar manutenção ou visita</b>
        <div class="opcoes">
          <button v-for="t in tipos" :key="t" :class="{ on: tipo === t }" @click="tipo = t">{{ t }}</button>
        </div>
        <label class="sub">Melhor período</label>
        <Segmento v-model="periodo" :opcoes="[['Manhã', 'Manhã'], ['Tarde', 'Tarde'], ['Qualquer', 'Qualquer']]" />
        <textarea v-model="obs" rows="3" placeholder="Algum detalhe? (opcional)"></textarea>
        <button class="btn primario" :disabled="enviandoS" @click="enviarPedido">{{ enviandoS ? 'Enviando…' : 'Enviar solicitação' }}</button>
        <p v-if="erroS" class="erro-s">{{ erroS }}</p>
        <p class="sub" style="margin:0;font-size:12px">A Ollem envia o orçamento e combina o dia com você.</p>
      </div>
      <div class="card ok" v-else>
        <div class="check">✓</div><b>Solicitação recebida!</b>
        <p class="sub">Vamos falar com você para enviar o orçamento e combinar o dia.</p>
        <p v-if="modoDemo" class="previa">Prévia: no app de verdade, a solicitação vira uma oportunidade na aba Serviços do Hub.</p>
        <button class="btn sec" @click="ir('menu')">Ver minhas solicitações</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.pg { display: flex; flex-direction: column; gap: 10px; }
.sug { background: var(--escuro); color: #fff; border-radius: 22px; padding: 16px; }
:global(.escuro) .sug { border: 1px solid #1d2420; }
.sug small { font-size: 11.5px; color: var(--lima); font-weight: 600; }
.sug b { display: block; font-size: 18px; margin-top: 4px; }
.sug p { font-size: 13px; color: #c9d2cd; margin: 6px 0 12px; line-height: 1.45; }
.op { display: flex; align-items: center; gap: 12px; text-align: left; color: inherit; font: inherit; width: 100%; }
.ic { width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center; background: var(--trilho); flex-shrink: 0; font-weight: 700; }
.ic.verde { background: var(--verde); color: #fff; }
.ic svg { width: 19px; height: 19px; fill: none; stroke: var(--texto); stroke-width: 1.7; stroke-linejoin: round; stroke-linecap: round; }
.tx b { display: block; font-size: 14px; font-weight: 600; }
.tx small { font-size: 12px; color: var(--sub); }
.seta { margin-left: auto; color: var(--sub); font-size: 20px; }
.ped { display: flex; justify-content: space-between; align-items: center; padding: 9px 0; border-bottom: 1px solid var(--linha); }
.ped:last-child { border-bottom: 0; }
.ped b { display: block; font-size: 13.5px; font-weight: 600; }
.ped small { font-size: 11.5px; color: var(--sub); }
.status { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; }
.nota { font-size: 12px; margin: 2px 6px; }
.voltar { align-self: flex-start; background: none; border: 0; color: var(--acento); font-weight: 600; font-size: 14px; padding: 0 2px; }
.form { display: flex; flex-direction: column; gap: 12px; }
.h { font-size: 16px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chips button, .atalhos button { border: 1px solid var(--linha); background: var(--card); color: var(--texto); border-radius: 99px; padding: 7px 12px; font-size: 13px; }
.chips button.on { border-color: var(--verde); color: var(--acento); font-weight: 600; }
.opcoes { display: flex; flex-direction: column; gap: 8px; }
.opcoes button { text-align: left; border: 1px solid var(--linha); background: var(--card); color: var(--texto); border-radius: 14px; padding: 12px 14px; font-size: 15px; }
.opcoes button.on { border-color: var(--verde); font-weight: 600; box-shadow: inset 3px 0 0 var(--verde); }
.anexo { font-size: 13px; padding: 11px; }
.datas { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.datas label { display: flex; flex-direction: column; gap: 4px; }
.datas input { font-size: 14px; padding: 10px; }
.anexos { display: flex; flex-direction: column; gap: 6px; }
.arq { display: flex; align-items: center; gap: 10px; border: 1px solid var(--linha); border-radius: 12px; padding: 8px 10px; font-size: 13px; }
.arq .doc { font-size: 10px; font-weight: 700; color: var(--vermelho); background: rgba(229,72,77,.1); border-radius: 6px; padding: 3px 5px; }
.arq .nm { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.arq button { border: 0; background: none; color: var(--sub); font-size: 18px; padding: 0 4px; }
.dica { font-size: 12px; color: var(--sub); margin: 0; line-height: 1.45; }
.abrir { display: block; margin-top: 4px; border: 0; background: none; color: var(--acento); font-weight: 600; font-size: 12px; padding: 0; }
.ok { text-align: center; display: flex; flex-direction: column; align-items: center; gap: 6px; }
.ok p { margin: 0 0 6px; }
.check { width: 52px; height: 52px; border-radius: 50%; background: var(--verde); color: #fff; font-size: 26px; display: grid; place-items: center; }
.previa { font-size: 11px; color: var(--sub); font-style: italic; margin: 0; }
.chat { display: flex; flex-direction: column; gap: 10px; }
.cabchat { display: flex; align-items: center; gap: 10px; }
.cabchat b { display: block; font-size: 15px; }
.cabchat small { font-size: 12px; color: var(--acento); }
.msgs { display: flex; flex-direction: column; gap: 8px; max-height: 390px; overflow-y: auto; padding: 4px 2px; }
.msg { max-width: 82%; padding: 10px 13px; border-radius: 18px; font-size: 14px; line-height: 1.45; }
.msg.ollivia { background: var(--card); border: 1px solid var(--linha); border-bottom-left-radius: 6px; align-self: flex-start; }
.msg.eu { background: var(--verde); color: #fff; border-bottom-right-radius: 6px; align-self: flex-end; }
.dig { display: flex; gap: 4px; padding: 14px; }
.dig i { width: 6px; height: 6px; border-radius: 50%; background: var(--sub); animation: pula 1s infinite; }
.dig i:nth-child(2) { animation-delay: .15s; } .dig i:nth-child(3) { animation-delay: .3s; }
@keyframes pula { 50% { transform: translateY(-4px); opacity: .5; } }
.atalhos { display: flex; flex-wrap: wrap; gap: 6px; }
.enviar { display: flex; gap: 8px; }
.enviar input { border-radius: 99px; }
.enviar button { width: 46px; height: 46px; border-radius: 50%; border: 0; background: var(--verde); color: #fff; font-size: 20px; font-weight: 700; flex-shrink: 0; }
.olli { background: var(--escuro); color: #fff; border-radius: 24px; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
:global(.escuro) .olli { border: 1px solid #1d2420; }
.ol1 { display: flex; align-items: center; gap: 12px; }
.ol1 b { display: block; font-size: 16px; }
.ol1 small { font-size: 12px; color: #9aa69f; }
.avo { position: relative; width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, var(--verde), var(--lima)); color: #06200a; display: grid; place-items: center; font-weight: 700; font-size: 18px; }
.avo i { position: absolute; right: 0; bottom: 0; width: 11px; height: 11px; border-radius: 50%; background: var(--lima); border: 2px solid var(--escuro); animation: online 2s ease-in-out infinite; }
@keyframes online { 50% { box-shadow: 0 0 0 5px rgba(142,247,5,.15); } }
.pergunta { display: flex; align-items: center; justify-content: space-between; gap: 8px; background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.08); color: #9aa69f; border-radius: 99px; padding: 6px 6px 6px 16px; font-size: 13.5px; text-align: left; }
.pergunta span { width: 34px; height: 34px; border-radius: 50%; background: var(--lima); color: #06200a; display: grid; place-items: center; font-weight: 700; flex-shrink: 0; }
.rapidas { display: flex; gap: 6px; overflow-x: auto; scrollbar-width: none; margin: 0 -16px; padding: 0 16px; }
.rapidas::-webkit-scrollbar { display: none; }
.rapidas button { flex-shrink: 0; border: 1px solid rgba(255,255,255,.1); background: transparent; color: #c9d2cd; border-radius: 99px; padding: 7px 12px; font-size: 12.5px; }
.blocos { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.bloco { background: var(--card); border: 1px solid var(--linha); border-radius: 20px; padding: 14px; text-align: left; color: inherit; font: inherit; display: flex; flex-direction: column; gap: 4px; min-height: 132px; }
.bloco b { font-size: 14px; font-weight: 600; margin-top: 8px; line-height: 1.25; }
.bloco small { font-size: 11.5px; color: var(--sub); line-height: 1.35; }
.bloco:active { transform: scale(.96); }
.bi { width: 38px; height: 38px; border-radius: 12px; background: rgba(17,201,10,.12); display: grid; place-items: center; flex-shrink: 0; }
.bi svg { width: 19px; height: 19px; fill: none; stroke: var(--acento); stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.bi.agua { background: rgba(59,160,255,.14); } .bi.agua svg { stroke: #3ba0ff; }
.linha-pv { display: flex; align-items: center; gap: 12px; text-align: left; color: inherit; font: inherit; width: 100%; }
.sol { display: flex; flex-direction: column; gap: 2px; }
.s1 { display: flex; justify-content: space-between; gap: 8px; align-items: baseline; }
.s1 b { font-size: 14px; font-weight: 600; }
.sol > small { font-size: 11.5px; color: var(--sub); }
.etapas { display: flex; align-items: center; gap: 6px; margin-top: 10px; }
.etapas i { width: 8px; height: 8px; border-radius: 50%; background: var(--linha); flex-shrink: 0; transition: background-color .3s; }
.etapas i.on { background: var(--verde); }
.etapas span { font-size: 11px; color: var(--sub); }
.etapas span.on { color: var(--texto); font-weight: 600; }
.etapas span:not(:last-child)::after { content: ''; display: inline-block; width: 14px; height: 1px; background: var(--linha); vertical-align: middle; margin-left: 6px; }
.sol .abrir { align-self: flex-start; margin-top: 8px; }
.erro-s { color: var(--vermelho); font-size: 13px; margin: 0; }
</style>
