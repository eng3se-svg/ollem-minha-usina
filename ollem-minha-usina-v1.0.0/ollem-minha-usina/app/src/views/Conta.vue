<script setup>
import { ref, computed, watch } from 'vue'
import { estado, usinas, usina, mascararTel, modoDemo } from '../store'
import { api } from '../api'
import { fmt, reais } from '../lib/calc'
import Chave from '../components/Chave.vue'
import Segmento from '../components/Segmento.vue'

const confirmar = ref(false)
const excluida = ref(false)
const folha = ref(null) // 'tarifa' | 'familiar' | 'aparelhos' | null
const aviso = ref('')
const mostrar = t => { aviso.value = t; setTimeout(() => (aviso.value = ''), 3500) }
const sair = async () => { if (!modoDemo) await api.sair().catch(() => {}); estado.logado = false; estado.aba = 'inicio' }
const excluir = async () => {
  if (!modoDemo) { try { await api.excluirConta() } catch (e) { confirmar.value = false; return mostrar(e.message) } }
  confirmar.value = false; excluida.value = true; estado.primeiroAcesso = true
  setTimeout(() => { estado.logado = false; estado.aba = 'inicio' }, 1800)
}
const sairOutros = async () => { if (!modoDemo) await api.sairOutros().catch(e => mostrar(e.message)); folha.value = null; mostrar('Os outros aparelhos foram desconectados.') }

// preferências vão para o servidor (para os avisos respeitarem o que o cliente escolheu)
if (!modoDemo) {
  let t = null
  watch(() => [estado.push, estado.silencio, estado.canais, estado.tema, estado.textoGrande, estado.biometria], () => {
    clearTimeout(t)
    t = setTimeout(() => api.salvarPreferencias({ push: estado.push, silencio: estado.silencio, canais: estado.canais, tema: estado.tema,
      texto_grande: estado.textoGrande, biometria: estado.biometria }).catch(() => {}), 800)
  }, { deep: true })
}

// tarifa: lida da conta (prévia simula a leitura) ou digitada
const arq = ref(null)
const lendo = ref(false)
const lida = ref(null)
const lerConta = async e => {
  if (!e.target.files.length) return
  const arquivo = e.target.files[0]
  e.target.value = ''; folha.value = null; lendo.value = true
  if (!modoDemo) {
    try {
      const j = await api.contaDeLuz(usina.value.id, arquivo)
      estado.tarifa = j.tarifa; estado.origemTarifa = 'conta'; estado.contaMes = j.referencia || 'a conta enviada'
      lida.value = { tarifa: j.tarifa, mes: estado.contaMes }; setTimeout(() => (lida.value = null), 3500)
    } catch (err) { mostrar(err.message) } finally { lendo.value = false }
    return
  }
  setTimeout(() => {
    lendo.value = false
    estado.tarifa = 0.98; estado.origemTarifa = 'conta'; estado.contaMes = 'outubro/2026'
    lida.value = { tarifa: 0.98, mes: 'outubro/2026' }
    setTimeout(() => (lida.value = null), 3500)
  }, 1600)
}
const digitar = ref(false)
const tarifaTxt = ref('')
const abrirTarifa = () => { tarifaTxt.value = estado.tarifa ? String(estado.tarifa).replace('.', ',') : ''; digitar.value = false; folha.value = 'tarifa' }
const salvarTarifa = async () => {
  const v = parseFloat(tarifaTxt.value.replace(',', '.'))
  if (!modoDemo) { try { await api.tarifa(usina.value.id, tarifaTxt.value) } catch (e) { return mostrar(e.message) } }
  estado.tarifa = v > 0.3 && v < 3 ? v : null
  estado.origemTarifa = estado.tarifa ? 'digitada' : ''
  folha.value = null
}
const tarifaOk = computed(() => { const v = parseFloat(tarifaTxt.value.replace(',', '.')); return !tarifaTxt.value || (v > 0.3 && v < 3) })

// acesso de familiar
const famNome = ref(''), famTel = ref(''), convites = ref([])
const formatarTel = e => {
  const d = e.target.value.replace(/\D/g, '').slice(0, 11)
  let s = d
  if (d.length > 2) s = `(${d.slice(0, 2)}) ${d.slice(2)}`
  if (d.length > 7) s = `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`
  famTel.value = s
}
const convidar = async () => {
  if (!modoDemo) { try { await api.convidar(famNome.value, famTel.value) } catch (e) { return mostrar(e.message) } }
  convites.value.push({ nome: famNome.value, tel: mascararTel(famTel.value) }); famNome.value = ''; famTel.value = ''; folha.value = null
}

const nAvisos = computed(() => Object.values(estado.push).filter(Boolean).length)
const temas = [['auto', 'Automático'], ['claro', 'Claro'], ['escuro', 'Escuro']]
</script>

<template>
  <div class="pg">
    <!-- Cabeçalho -->
    <div class="perfil">
      <div class="av">C</div>
      <div class="pt">
        <b>{{ estado.nome || 'Cliente Ollem' }}</b>
        <small>{{ estado.doc || 'CPF •••' }}</small>
        <small>{{ mascararTel(estado.telefone) || '(22) 9••••-••••' }}</small>
      </div>
      <span class="selo">Titular</span>
    </div>

    <!-- Minhas usinas e acesso -->
    <div class="grupo">
      <p class="tg">Minhas usinas</p>
      <div class="card lista">
        <button v-for="(u, i) in usinas" :key="u.id" class="linha" @click="estado.usinaIdx = i; estado.aba = 'inicio'">
          <span class="ic sol"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg></span>
          <span class="tx"><b>Usina em {{ u.bairro }}</b><small>{{ fmt(u.kwp, 2) }} kWp</small></span>
          <span v-if="estado.usinaIdx === i" class="atual">vendo agora</span><span v-else class="seta">›</span>
        </button>
        <button class="linha" @click="folha = 'familiar'">
          <span class="ic"><svg viewBox="0 0 24 24"><path d="M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM2 21a7 7 0 0 1 14 0M19 8v6M16 11h6" /></svg></span>
          <span class="tx"><b>Dar acesso a um familiar</b><small>{{ convites.length ? `${convites.length} convite(s) enviado(s)` : 'Só para ver a usina, sem mudar nada' }}</small></span>
          <span class="seta">›</span>
        </button>
      </div>
    </div>

    <!-- Conta de luz -->
    <div class="grupo">
      <p class="tg">Conta de luz</p>
      <div class="card lista">
        <div class="linha">
          <span class="ic"><svg viewBox="0 0 24 24"><path d="M13 2L4 14h7l-1 8 9-12h-7z" /></svg></span>
          <span class="tx"><b>{{ estado.distribuidora }}</b><small>Distribuidora, conforme o seu cadastro na Ollem</small></span>
          <svg class="cad" viewBox="0 0 24 24"><path d="M7 11V8a5 5 0 0 1 10 0v3M5 11h14v10H5z" /></svg>
        </div>
        <button class="linha" @click="abrirTarifa">
          <span class="ic"><svg viewBox="0 0 24 24"><path d="M12 2v20M17 6H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg></span>
          <span class="tx"><b>Tarifa usada: {{ reais(estado.tarifa || 1.06) }}/kWh</b>
            <small>{{ estado.origemTarifa === 'conta' ? `Da sua conta de ${estado.contaMes}` : estado.origemTarifa === 'digitada' ? 'Informada por você' : 'Média geral (ainda sem a sua conta)' }}</small></span>
          <span class="seta">›</span>
        </button>
        <button class="linha" @click="arq.click()">
          <span class="ic verde"><svg viewBox="0 0 24 24"><path d="M12 16V4M7 9l5-5 5 5M5 20h14" /></svg></span>
          <span class="tx"><b>{{ lendo ? 'Lendo a sua conta…' : 'Atualizar com a minha conta de luz' }}</b><small>Foto ou PDF · a Ollivia lê a tarifa para você</small></span>
          <span v-if="lendo" class="giro"></span><span v-else class="seta">›</span>
        </button>
        <input ref="arq" type="file" accept="application/pdf,image/*" hidden @change="lerConta" />
      </div>
      <p class="nota">Distribuidora errada? <button @click="estado.servico = 'chat'; estado.aba = 'ajuda'">Fale com a Ollivia</button></p>
    </div>

    <!-- Avisos -->
    <div class="grupo">
      <p class="tg">Avisos <span>{{ nAvisos }} de 5 ligados</span></p>
      <div class="card lista">
        <div class="linha toque" @click="estado.push.parada = !estado.push.parada"><span class="tx"><b>Usina parada ou sem comunicação</b><small>Na hora, mesmo à noite</small></span><Chave v-model="estado.push.parada" /></div>
        <div class="linha toque" @click="estado.push.abaixo = !estado.push.abaixo"><span class="tx"><b>Geração abaixo do esperado</b><small>Quando a semana fica abaixo de 70%</small></span><Chave v-model="estado.push.abaixo" /></div>
        <div class="linha toque" @click="estado.push.mensal = !estado.push.mensal"><span class="tx"><b>Resumo do mês</b><small>Todo dia 1º, com a economia</small></span><Chave v-model="estado.push.mensal" /></div>
        <div class="linha toque" @click="estado.push.relatorio = !estado.push.relatorio"><span class="tx"><b>Relatório pronto</b></span><Chave v-model="estado.push.relatorio" /></div>
        <div class="linha toque" @click="estado.push.visita = !estado.push.visita"><span class="tx"><b>Visita e serviços</b><small>Confirmação e lembrete do dia</small></span><Chave v-model="estado.push.visita" /></div>
        <div class="linha toque" @click="estado.silencio = !estado.silencio"><span class="tx"><b>Silêncio à noite</b><small>Das 22h às 7h, só usina parada avisa</small></span><Chave v-model="estado.silencio" /></div>
        <div class="linha">
          <span class="tx"><b>Receber por</b></span>
          <div class="pilulas">
            <button v-for="c in [['app', 'App'], ['whats', 'WhatsApp']]" :key="c[0]" type="button" :class="{ on: estado.canais[c[0]] }" :aria-pressed="estado.canais[c[0]]"
              @click="(estado.canais[c[0]] && Object.values(estado.canais).filter(Boolean).length === 1) || (estado.canais[c[0]] = !estado.canais[c[0]])">
              <span class="ck"><svg viewBox="0 0 12 12"><path d="M2.5 6.2l2.3 2.3 4.7-5" /></svg></span>{{ c[1] }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Aparência e segurança -->
    <div class="grupo">
      <p class="tg">Aparência e segurança</p>
      <div class="card lista">
        <div class="linha col">
          <span class="tx"><b>Tema</b></span>
          <Segmento v-model="estado.tema" :opcoes="temas" />
        </div>
        <div class="linha toque" @click="estado.textoGrande = !estado.textoGrande"><span class="tx"><b>Letras maiores</b><small>Deixa os textos do app maiores</small></span><Chave v-model="estado.textoGrande" /></div>
        <div class="linha toque" @click="estado.biometria = !estado.biometria"><span class="tx"><b>Entrar com Face ID ou digital</b></span><Chave v-model="estado.biometria" /></div>
        <button class="linha" @click="folha = 'aparelhos'">
          <span class="tx"><b>Aparelhos conectados</b><small>1 aparelho · este celular</small></span><span class="seta">›</span>
        </button>
      </div>
    </div>

    <!-- Ajuda -->
    <div class="grupo">
      <p class="tg">Ajuda e sobre</p>
      <div class="card lista">
        <button class="linha" @click="estado.aba = 'inicio'; estado.tour = true"><span class="tx"><b>Rever o passo a passo</b><small>O tour pelas telas do app</small></span><span class="seta">›</span></button>
        <button class="linha" @click="estado.servico = 'chat'; estado.aba = 'ajuda'"><span class="tx"><b>Perguntas frequentes</b><small>A Ollivia responde</small></span><span class="seta">›</span></button>
        <a class="linha" href="https://wa.me/552231990081" target="_blank"><span class="tx"><b>Falar com a Ollem</b><small>(22) 98141-1164 · Araruama/RJ</small></span><span class="seta">›</span></a>
        <button class="linha"><span class="tx"><b>Política de privacidade</b></span><span class="seta">›</span></button>
        <button class="linha"><span class="tx"><b>Termos de uso</b></span><span class="seta">›</span></button>
      </div>
    </div>

    <button class="btn sec" @click="sair">Sair</button>
    <button class="excluir" @click="confirmar = true">Excluir minha conta</button>
    <p class="ver">Ollem - Minha usina · prévia 0.20<br />OLLEM DO BRASIL LTDA</p>

    <Teleport to=".tela">
      <Transition name="toast"><div v-if="aviso" class="toast">{{ aviso }}</div></Transition>
      <Transition name="toast"><div v-if="lida" class="toast"><b>Conta lida!</b> Tarifa de {{ reais(lida.tarifa) }}/kWh ({{ lida.mes }}). A Economia já foi atualizada.</div></Transition>
      <Transition name="folha">
        <div v-if="folha" class="fundo-folha" @click.self="folha = null">
          <div class="folha">
            <i class="pegador"></i>
            <template v-if="folha === 'tarifa'">
              <b class="h">Tarifa da sua conta de luz</b>
              <p class="sub">É o valor que você paga por kWh, com impostos. Com ela, a economia do app fica igual à da sua conta.</p>
              <div class="atual"><span>Hoje</span><b>{{ reais(estado.tarifa || 1.06) }}/kWh</b><small>{{ estado.origemTarifa === 'conta' ? `da conta de ${estado.contaMes}` : estado.origemTarifa === 'digitada' ? 'informada por você' : 'média geral' }}</small></div>
              <button class="btn primario" @click="arq.click()">Enviar foto ou PDF da conta</button>
              <template v-if="digitar">
                <div class="campo-rs"><span>R$</span><input v-model="tarifaTxt" inputmode="decimal" placeholder="0,98" /><span>/kWh</span></div>
                <p v-if="!tarifaOk" class="erro">Confira o valor (entre R$ 0,30 e R$ 3,00).</p>
                <button class="btn sec" :disabled="!tarifaOk || !tarifaTxt" @click="salvarTarifa">Salvar tarifa</button>
              </template>
              <button v-else class="link" @click="digitar = true">Sei o valor · digitar a tarifa</button>
            </template>
            <template v-else-if="folha === 'familiar'">
              <b class="h">Dar acesso a um familiar</b>
              <p class="sub">A pessoa recebe um convite no WhatsApp e só consegue ver a usina. Pedidos e configurações continuam com você.</p>
              <input v-model="famNome" placeholder="Nome" />
              <input :value="famTel" @input="formatarTel" inputmode="tel" placeholder="(22) 9____-____" />
              <button class="btn primario" :disabled="!famNome || famTel.replace(/\D/g, '').length < 10" @click="convidar">Enviar convite</button>
              <div v-for="c in convites" :key="c.tel" class="conv"><b>{{ c.nome }}</b><small>{{ c.tel }} · convite enviado</small></div>
            </template>
            <template v-else>
              <b class="h">Aparelhos conectados</b>
              <div class="conv"><b>Este celular</b><small>Conectado agora · Face ID {{ estado.biometria ? 'ligado' : 'desligado' }}</small></div>
              <button class="btn sec" @click="sairOutros">Sair dos outros aparelhos</button>
            </template>
          </div>
        </div>
      </Transition>
      <Transition name="folha">
        <div v-if="confirmar || excluida" class="fundo-folha">
          <div class="folha">
            <template v-if="!excluida">
              <b class="h">Excluir a sua conta?</b>
              <p class="sub">Você deixa de acessar o app e os seus dados de acesso são apagados. A usina continua sendo monitorada pela Ollem.</p>
              <button class="btn perigo" @click="excluir">Sim, excluir</button>
              <button class="btn sec" @click="confirmar = false">Cancelar</button>
            </template>
            <template v-else><b class="h">Conta excluída.</b><p class="sub">(prévia: nada foi apagado de verdade)</p></template>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.pg { display: flex; flex-direction: column; gap: 16px; }
.perfil { display: flex; align-items: center; gap: 14px; background: var(--escuro); color: #fff; border-radius: 22px; padding: 16px; }
:global(.escuro) .perfil { border: 1px solid #1d2420; }
.av { width: 52px; height: 52px; border-radius: 50%; background: linear-gradient(135deg, var(--verde), var(--lima)); color: #06200a; display: grid; place-items: center; font-weight: 700; font-size: 20px; flex-shrink: 0; }
.pt b { display: block; font-size: 16px; }
.pt small { display: block; font-size: 12px; color: #9aa69f; }
.selo { margin-left: auto; align-self: flex-start; font-size: 11px; font-weight: 600; color: var(--lima); background: rgba(142,247,5,.12); padding: 3px 9px; border-radius: 99px; }
.grupo { display: flex; flex-direction: column; gap: 6px; }
.tg { margin: 0 4px; font-size: 12px; font-weight: 600; color: var(--sub); display: flex; justify-content: space-between; }
.tg span { font-weight: 500; }
.lista { padding: 2px 14px; }
.linha { display: flex; align-items: center; gap: 12px; width: 100%; padding: 12px 0; border: 0; border-bottom: 1px solid var(--linha); background: none; color: inherit; font: inherit; text-align: left; text-decoration: none; cursor: pointer; }
.linha:last-child { border-bottom: 0; }
.linha.col { flex-direction: column; align-items: stretch; gap: 8px; }
.ic { width: 34px; height: 34px; border-radius: 10px; background: var(--trilho); display: grid; place-items: center; flex-shrink: 0; }
.ic svg { width: 17px; height: 17px; fill: none; stroke: var(--texto); stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.ic.sol { background: rgba(255,210,58,.16); } .ic.sol svg { stroke: #e0a800; }
.tx { flex: 1; min-width: 0; }
.tx b { display: block; font-size: 14px; font-weight: 600; }
.tx small { display: block; font-size: 12px; color: var(--sub); margin-top: 1px; }
.seta { color: var(--sub); font-size: 20px; }
.atual { font-size: 11px; font-weight: 600; color: var(--acento); }
.sel { width: auto; padding: 7px 10px; font-size: 13px; border-radius: 10px; }
.chips { display: flex; gap: 6px; }
.chips button { border: 1px solid var(--linha); background: var(--card); color: var(--sub); border-radius: 99px; padding: 6px 12px; font-size: 12.5px; }
.chips button.on { border-color: var(--verde); color: var(--acento); font-weight: 600; }
.excluir { background: none; border: 0; color: var(--vermelho); font-size: 13.5px; font-weight: 500; padding: 4px; margin-top: -6px; }
.ver { text-align: center; font-size: 11px; color: var(--sub); margin: 0 0 6px; line-height: 1.6; }
.fundo-folha { position: absolute; inset: 0; z-index: 40; background: rgba(0,0,0,.35); display: flex; align-items: flex-end; }
.folha { width: 100%; background: var(--card); color: var(--texto); border-radius: 26px 26px 0 0; padding: 10px 20px 28px; display: flex; flex-direction: column; gap: 12px; }
.pegador { width: 38px; height: 4px; border-radius: 4px; background: var(--linha); align-self: center; }
.folha .h { font-size: 17px; }
.folha .sub { margin: -4px 0 0; line-height: 1.45; }
.campo-rs { display: flex; align-items: center; gap: 8px; border: 1px solid var(--linha); border-radius: 14px; padding: 4px 14px; font-weight: 600; color: var(--sub); }
.campo-rs input { border: 0; font-size: 22px; font-weight: 700; padding: 8px 0; color: var(--texto); background: transparent; }
.campo-rs input:focus { outline: none; }
.erro { color: var(--vermelho); font-size: 12px; margin: -6px 0 0; }
.conv { border: 1px solid var(--linha); border-radius: 14px; padding: 10px 12px; }
.conv b { display: block; font-size: 14px; }
.conv small { font-size: 12px; color: var(--sub); }
.folha-enter-active, .folha-leave-active { transition: opacity .25s; }
.folha-enter-active .folha, .folha-leave-active .folha { transition: transform .32s cubic-bezier(.2,.8,.2,1); }
.folha-enter-from, .folha-leave-to { opacity: 0; }
.folha-enter-from .folha, .folha-leave-to .folha { transform: translateY(100%); }
.cad { width: 16px; height: 16px; fill: none; stroke: var(--sub); stroke-width: 1.8; stroke-linecap: round; }
.ic.verde { background: rgba(17,201,10,.12); } .ic.verde svg { stroke: var(--acento); }
.nota { margin: 2px 4px 0; font-size: 12px; color: var(--sub); }
.nota button { background: none; border: 0; padding: 0; color: var(--acento); font-weight: 600; font-size: 12px; }
.giro { width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--linha); border-top-color: var(--verde); animation: gira 0.8s linear infinite; }
@keyframes gira { to { transform: rotate(360deg); } }
.atual { display: flex; align-items: baseline; gap: 8px; background: var(--fundo); border-radius: 14px; padding: 12px 14px; }
.atual span { font-size: 12px; color: var(--sub); }
.atual b { font-size: 18px; }
.atual small { font-size: 12px; color: var(--sub); margin-left: auto; }
.link { background: none; border: 0; color: var(--acento); font-weight: 600; font-size: 14px; padding: 4px; }
.toast { position: absolute; left: 16px; right: 16px; bottom: 96px; z-index: 50; background: var(--escuro); color: #fff; border-radius: 16px; padding: 12px 14px; font-size: 13px; line-height: 1.4; box-shadow: 0 10px 30px rgba(0,0,0,.25); }
.toast b { color: var(--lima); }
.toast-enter-active, .toast-leave-active { transition: opacity .25s, transform .3s cubic-bezier(.2,.8,.2,1); }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(12px); }
.toque { cursor: pointer; -webkit-user-select: none; user-select: none; }
.toque:active { opacity: .85; }
.pilulas { display: flex; gap: 6px; }
.pilulas button { display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--linha); background: var(--card); color: var(--sub); border-radius: 99px; padding: 6px 12px 6px 7px; font-size: 13px; font-weight: 500; transition: background .25s, color .25s, border-color .25s, transform .15s; cursor: pointer; }
.pilulas button:active { transform: scale(.94); }
.pilulas .ck { width: 18px; height: 18px; border-radius: 50%; border: 1.5px solid var(--linha); display: grid; place-items: center; transition: background .25s, border-color .25s; }
.pilulas .ck svg { width: 10px; height: 10px; fill: none; stroke: #fff; stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; opacity: 0; transform: scale(.4); transition: opacity .2s, transform .3s cubic-bezier(.3,1.6,.5,1); }
.pilulas button.on { border-color: var(--verde); color: var(--texto); font-weight: 600; background: rgba(17,201,10,.07); }
.pilulas button.on .ck { background: var(--verde); border-color: var(--verde); }
.pilulas button.on .ck svg { opacity: 1; transform: none; }
</style>
