<script setup>
import { ref, computed, nextTick, onUnmounted, watch } from 'vue'
import { estado, usinas, mascararTel, carregarUsinas, modoDemo } from '../store'
import { api, temSessao } from '../api'
import { onMounted } from 'vue'
import { ativarNotificacoes, plataforma } from '../nativo'
import { resumo, fmt } from '../lib/calc'
import simbolo from '../assets/simbolo.png'
import Linhas from '../components/Linhas.vue'

// Etapas: boas → tel → codigo → termos → avisos → bio → usina (as do meio só no 1º acesso)
// 1º acesso: boas-vindas → celular → código → termos → avisos → biometria → usina
// Volta com biometria ligada: "Olá de novo!" + Face ID (1 toque)
const etapa = ref(estado.primeiroAcesso ? 'boas' : estado.biometria ? 'volta' : 'tel')
const lendo = ref(false)
// app real: se já existe sessão guardada no aparelho, abre direto no "Olá de novo!"
onMounted(async () => { if (!modoDemo && (await temSessao())) etapa.value = 'volta' })
// >>> PARA O TI: no app nativo, pedir a biometria (plugin de Face ID/digital) antes de liberar a sessão guardada.
const faceId = () => {
  lendo.value = true
  setTimeout(async () => {
    try { await carregarUsinas(); estado.aba = 'inicio'; estado.logado = true } catch { lendo.value = false; etapa.value = 'tel' }
  }, modoDemo ? 900 : 300)
}
// arrastar para o lado nas boas-vindas
let x0 = null
const toque = e => (x0 = e.changedTouches[0].clientX)
const solta = e => {
  if (x0 == null) return
  const dx = e.changedTouches[0].clientX - x0; x0 = null
  if (dx < -40) slide.value < ultimo ? slide.value++ : (etapa.value = 'tel')
  else if (dx > 40 && slide.value > 0) slide.value--
}
const slide = ref(0)
const slides = [
  { t: 'Bem-vindo à sua usina', d: 'Este é o app da Ollem para você acompanhar a energia que a sua usina solar produz, de qualquer lugar.', ic: 'marca' },
  { t: 'Veja a usina gerando', d: 'O caminho do sol mostra a hora do dia e quanto a usina já gerou. Tudo atualizado ao longo do dia.', ic: 'sol' },
  { t: 'Entenda cada número', d: 'Compare a geração com o esperado, dia a dia, mês a mês e no ano, com explicações em palavras simples.', ic: 'barras' },
  { t: 'Saiba quanto economizou', d: 'A economia em reais, quanto do investimento já voltou e quanto CO₂ você deixou de emitir.', ic: 'rs' },
  { t: 'Avisos na hora certa', d: 'Se a usina parar ou gerar abaixo do esperado, você e a Ollem ficam sabendo na hora.', ic: 'aviso' },
  { t: 'Serviços e a Ollivia', d: 'Solicite limpeza, visita ou relatório e tire dúvidas com a Ollivia, a assistente da Ollem, a qualquer hora.', ic: 'chat' }
]
const ultimo = slides.length - 1

// ---- celular ----
const tel = ref('')
const enviando = ref(false)
const naoAchou = ref(false)
const formatar = e => {
  const d = e.target.value.replace(/\D/g, '').slice(0, 11)
  let s = d
  if (d.length > 2) s = `(${d.slice(0, 2)}) ${d.slice(2)}`
  if (d.length > 7) s = `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`
  tel.value = s; naoAchou.value = false
}
const telOk = computed(() => tel.value.replace(/\D/g, '').length >= 10)

// ---- CPF ou CNPJ do titular ----
const doc = ref('')
const docTocado = ref(false)
const formatarDoc = e => {
  const d = e.target.value.replace(/\D/g, '').slice(0, 14)
  let s = d
  if (d.length <= 11) {
    if (d.length > 3) s = `${d.slice(0, 3)}.${d.slice(3)}`
    if (d.length > 6) s = `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`
    if (d.length > 9) s = `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`
  } else {
    s = `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}`
    if (d.length > 12) s += `-${d.slice(12)}`
  }
  doc.value = s; naoAchou.value = false
}
const cpfValido = c => {
  if (c.length !== 11 || /^(\d)\1+$/.test(c)) return false
  const dv = n => { let t = 0; for (let i = 0; i < n; i++) t += +c[i] * (n + 1 - i); const r = (t * 10) % 11; return r === 10 ? 0 : r }
  return dv(9) === +c[9] && dv(10) === +c[10]
}
const cnpjValido = c => {
  if (c.length !== 14 || /^(\d)\1+$/.test(c)) return false
  const dv = n => { const p = n === 12 ? [5,4,3,2,9,8,7,6,5,4,3,2] : [6,5,4,3,2,9,8,7,6,5,4,3,2]; let t = 0; for (let i = 0; i < n; i++) t += +c[i] * p[i]; const r = t % 11; return r < 2 ? 0 : 11 - r }
  return dv(12) === +c[12] && dv(13) === +c[13]
}
const docNum = computed(() => doc.value.replace(/\D/g, ''))
const docOk = computed(() => cpfValido(docNum.value) || cnpjValido(docNum.value))
const docErro = computed(() => docTocado.value && docNum.value.length >= 11 && !docOk.value && (docNum.value.length === 11 || docNum.value.length === 14))
const tipoDoc = computed(() => (docNum.value.length > 11 ? 'CNPJ' : 'CPF'))
const erroTel = ref('')
const enviar = async () => {
  enviando.value = true; erroTel.value = ''
  if (modoDemo) {
    setTimeout(() => {
      enviando.value = false
      // demonstração: celular terminado em 0000 simula dados que não conferem com o cadastro
      if (tel.value.replace(/\D/g, '').endsWith('0000')) { naoAchou.value = true; return }
      irCodigo()
    }, 700)
    return
  }
  try {
    await api.pedirCodigo(docNum.value, tel.value, canal.value === 'sms' ? 'sms' : 'whatsapp')
    irCodigo(false)
  } catch (e) {
    if (e.codigo === 'dados_nao_conferem') naoAchou.value = true
    else erroTel.value = e.message
  } finally { enviando.value = false }
}

// ---- código ----
const casas = ref(['', '', '', '', '', ''])
const refs = ref([])
const sugestao = ref(false)
const erroCod = ref(false)
const espera = ref(0)
let timer = null
const CODIGO = '482917'
const canal = computed({ get: () => estado.canalCodigo, set: v => (estado.canalCodigo = v) })
const outroCanal = computed(() => (canal.value === 'sms' ? 'whats' : 'sms'))
const nomeCanal = c => (c === 'sms' ? 'SMS' : 'WhatsApp')
const trocarCanal = () => { canal.value = outroCanal.value; reenviar() }
const reenviar = () => (modoDemo ? irCodigo() : enviar())
const irCodigo = async (simular = true) => {
  etapa.value = 'codigo'; casas.value = ['', '', '', '', '', '']; erroCod.value = false
  espera.value = 60; clearInterval(timer); timer = setInterval(() => { if (espera.value > 0) espera.value-- }, 1000)
  sugestao.value = false; if (modoDemo && simular) setTimeout(() => (sugestao.value = true), 1500)
  await nextTick(); refs.value[0]?.focus()
}
onUnmounted(() => clearInterval(timer))
const digitar = (i, e) => {
  const v = e.target.value.replace(/\D/g, '')
  if (v.length > 1) return colar(v)
  casas.value[i] = v; erroCod.value = false
  if (v && i < 5) refs.value[i + 1]?.focus()
}
const apagar = (i, e) => { if (e.key === 'Backspace' && !casas.value[i] && i > 0) refs.value[i - 1]?.focus() }
const colar = v => { v.slice(0, 6).split('').forEach((c, k) => (casas.value[k] = c)); refs.value[Math.min(5, v.length - 1)]?.focus() }
const aoColar = e => { e.preventDefault(); colar((e.clipboardData?.getData('text') || '').replace(/\D/g, '')) }
const codigo = computed(() => casas.value.join(''))
watch(codigo, c => { if (c.length === 6) setTimeout(confirmar, 700) })
const conferindo = ref(false)
const msgCod = ref('')
const confirmar = async () => {
  if (codigo.value.length < 6 || conferindo.value) return
  msgCod.value = ''
  if (modoDemo) {
    // demonstração: aceita qualquer código, menos 000000 (simula código errado)
    if (codigo.value === '000000') { erroCod.value = true; return }
  } else {
    conferindo.value = true
    try {
      const j = await api.entrar(docNum.value, tel.value, codigo.value, plataforma())
      estado.nome = j.cliente.nome
      await carregarUsinas()
    } catch (e) {
      erroCod.value = true; msgCod.value = e.message; conferindo.value = false
      if (e.codigo === 'codigo_expirado' || e.codigo === 'muitas_tentativas') espera.value = 0
      return
    }
    conferindo.value = false
  }
  clearInterval(timer)
  estado.telefone = tel.value
  // só a versão mascarada fica no app (LGPD)
  estado.doc = docNum.value.length === 11 ? `${docNum.value.slice(0, 3)}.•••.•••-${docNum.value.slice(9)}` : `${docNum.value.slice(0, 2)}.•••.•••/••••-${docNum.value.slice(12)}`
  doc.value = ''
  etapa.value = estado.primeiroAcesso ? 'termos' : (usinas.length > 1 ? 'usina' : (escolher(0), 'usina'))
}

// ---- termos / permissões ----
const aceite = ref(false)
const ativarAvisos = async sim => {
  estado.avisosAtivos = sim; Object.keys(estado.push).forEach(k => (estado.push[k] = sim)); etapa.value = 'bio'
  if (sim && !modoDemo) { const tk = await ativarNotificacoes(); if (tk) api.registrarPush(tk, plataforma()).catch(() => {}) }
}
const ativarBio = sim => { estado.biometria = sim; if (usinas.length > 1) etapa.value = 'usina'; else escolher(0) }

// ---- escolher usina ----
const lista = computed(() => usinas.map((u, i) => ({ u, i, r: resumo(u) })))
const corSit = s => ({ gerando: 'var(--lima)', noite: '#8b9cff', sem_comunicacao: 'var(--vermelho)', aviso: 'var(--ambar)' }[s])
const txtSit = s => ({ gerando: 'Gerando agora', noite: 'Noite', sem_comunicacao: 'Sem comunicação', aviso: 'Aviso' }[s])
const escolher = i => { const primeiro = estado.primeiroAcesso; estado.usinaIdx = i; estado.primeiroAcesso = false; estado.aba = 'inicio'; estado.logado = true; if (primeiro) estado.tour = true }

const passos = ['termos', 'avisos', 'bio', 'usina']
const passoN = computed(() => passos.indexOf(etapa.value))
</script>

<template>
  <div class="login" :class="'e-' + etapa">
    <Transition name="fade"><Linhas v-if="['boas', 'tel', 'codigo', 'volta'].includes(etapa)" /></Transition>

    <Transition name="passo" mode="out-in">
    <!-- BOAS-VINDAS -->
    <div v-if="etapa === 'boas'" key="boas" class="in boas" @touchstart="toque" @touchend="solta">
      <div class="topo"><img :src="simbolo" alt="Ollem" class="simb pq" /><button class="pular" @click="etapa = 'tel'">Pular</button></div>
      <Transition name="slide" mode="out-in">
      <div :key="slide" class="sl">
      <div class="ilus">
        <div v-if="slides[slide].ic === 'marca'" class="marcaIl">
          <svg viewBox="0 0 120 120" class="anelIl"><circle cx="60" cy="60" r="54" pathLength="1" /></svg>
          <img :src="simbolo" alt="" />
        </div>
        <svg v-else-if="slides[slide].ic === 'sol'" viewBox="0 0 220 130">
          <path d="M20 118 A90 90 0 0 1 200 118" fill="none" stroke="rgba(255,255,255,.14)" stroke-width="2" />
          <path d="M20 118 A90 90 0 0 1 82 33" fill="none" stroke="#8ef705" stroke-width="3" stroke-linecap="round" pathLength="1" class="desenha" />
          <g class="solzinho"><circle cx="82" cy="33" r="18" fill="#ffd23a" opacity=".15" /><circle cx="82" cy="33" r="9" fill="#ffd23a" /></g>
          <text x="110" y="104" text-anchor="middle" fill="#fff" font-size="30" font-weight="700" font-family="Inter">7,2</text>
        </svg>
        <svg v-else-if="slides[slide].ic === 'barras'" viewBox="0 0 220 130">
          <line x1="12" y1="118" x2="208" y2="118" stroke="rgba(255,255,255,.12)" />
          <g v-for="(h, k) in [56, 66, 24, 61, 70, 51, 64, 58, 69]" :key="k"><rect :x="16 + k * 21.5" :y="118 - h" width="13" :height="h" rx="3" :fill="h < 50 ? '#f2a516' : '#11c90a'" class="cresce" :style="{ animationDelay: (k * 0.05) + 's' }" /></g>
          <path d="M10 54 L210 54" stroke="#eef3f0" stroke-dasharray="5 4" stroke-width="1.4" opacity=".7" pathLength="1" class="desenha devagar" />
          <text x="210" y="40" text-anchor="end" fill="#9aa69f" font-size="10" font-family="Inter">esperado</text>
        </svg>
        <svg v-else-if="slides[slide].ic === 'aviso'" viewBox="0 0 220 130">
          <g class="sino"><path d="M96 58a14 14 0 0 1 28 0c0 16 7 21 7 21H89s7-5 7-21M106 86h8" fill="none" stroke="#8ef705" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" /></g>
          <circle cx="126" cy="44" r="7" fill="#e5484d" class="ponto-vermelho" />
          <g class="notif"><rect x="24" y="96" width="172" height="30" rx="12" fill="#1d2420" /><rect x="34" y="104" width="14" height="14" rx="4" fill="#11c90a" /><rect x="56" y="104" width="96" height="5" rx="2.5" fill="#eef3f0" /><rect x="56" y="113" width="70" height="5" rx="2.5" fill="#5f6b64" /></g>
        </svg>
        <svg v-else-if="slides[slide].ic === 'rs'" viewBox="0 0 220 130">
          <g v-for="(h, k) in [40, 52, 48, 66, 74, 70, 92]" :key="k"><rect :x="22 + k * 26" :y="118 - h" width="16" :height="h" rx="4" :fill="k === 6 ? '#8ef705' : '#11c90a'" :opacity="k === 6 ? 1 : .55" class="cresce" :style="{ animationDelay: (k * 0.06) + 's' }" /></g>
          <text x="196" y="18" text-anchor="end" fill="#8ef705" font-size="18" font-weight="700" font-family="Inter">R$</text>
        </svg>
        <svg v-else viewBox="0 0 220 130">
          <g class="bolha b1"><rect x="22" y="18" width="128" height="38" rx="16" fill="#1d2420" /><rect x="34" y="31" width="80" height="6" rx="3" fill="#8a968f" /><rect x="34" y="41" width="56" height="6" rx="3" fill="#5f6b64" /></g>
          <g class="bolha b2"><rect x="70" y="68" width="128" height="38" rx="16" fill="#11c90a" /><rect x="84" y="81" width="90" height="6" rx="3" fill="#fff" opacity=".9" /><rect x="84" y="91" width="60" height="6" rx="3" fill="#fff" opacity=".6" /></g>
        </svg>
      </div>
      <h1 class="ttl">{{ slides[slide].t }}</h1>
      <p class="slog">{{ slides[slide].d }}</p>
      </div>
      </Transition>
      <div class="rodape">
        <div class="pontos"><i v-for="k in slides.length" :key="k" :class="{ on: slide === k - 1 }" @click="slide = k - 1"></i></div>
        <button class="btn lima" @click="slide < ultimo ? slide++ : (etapa = 'tel')">{{ slide < ultimo ? 'Continuar' : 'Começar' }}</button>
      </div>
    </div>

    <!-- CELULAR -->
    <div v-else-if="etapa === 'tel'" key="tel" class="in">
      <img :src="simbolo" alt="Ollem" class="simb" />
      <h1>Ollem<br /><span>Minha usina</span></h1>
      <p class="slog">Entre com os dados do titular da usina, os mesmos do contrato com a Ollem.</p>
      <div class="form">
        <label>CPF ou CNPJ do titular</label>
        <input :value="doc" @input="formatarDoc" @blur="docTocado = true" inputmode="numeric" placeholder="000.000.000-00" autocomplete="off" class="linha" :class="{ ruim: docErro }" />
        <p v-if="docErro" class="msgcampo">Confira o {{ tipoDoc }}: algum número está diferente.</p>
        <label class="seg2">Celular cadastrado na Ollem</label>
        <input :value="tel" @input="formatar" inputmode="tel" placeholder="(22) 9____-____" autocomplete="tel" class="linha" />
        <div v-if="naoAchou" class="erro">
          <b>Os dados não conferem com o cadastro</b>
          <p>O CPF/CNPJ ou o celular pode estar cadastrado de outro jeito na Ollem. A Ollivia confere e libera o seu acesso.</p>
          <a href="https://wa.me/552231990081" target="_blank" class="btn sec escuro">Falar com a Ollivia no WhatsApp</a>
        </div>
        <template v-else>
          <label class="seg2">Receber o código por</label>
          <div class="canais">
            <button :class="{ on: canal === 'whats' }" @click="canal = 'whats'"><svg viewBox="0 0 24 24"><path d="M20 12a8 8 0 0 1-11.7 7.1L4 20l1-4.1A8 8 0 1 1 20 12z" /></svg>WhatsApp</button>
            <button :class="{ on: canal === 'sms' }" @click="canal = 'sms'"><svg viewBox="0 0 24 24"><path d="M4 5h16v11H9l-5 4z M8 10h8" /></svg>SMS</button>
            <i class="marcador" :class="canal"></i>
          </div>
          <button class="btn lima" :disabled="!telOk || !docOk || enviando" @click="enviar">{{ enviando ? 'Enviando…' : canal === 'sms' ? 'Receber código por SMS' : 'Receber código no WhatsApp' }}</button>
        </template>
        <p class="seguro"><svg viewBox="0 0 24 24"><path d="M6 10V8a6 6 0 0 1 12 0v2M5 10h14v11H5z" /></svg>O código só é enviado se o CPF/CNPJ e o celular forem do mesmo cadastro.</p>
        <p v-if="erroTel" class="msgcampo" style="margin-top:12px">{{ erroTel }}</p>
        <p v-if="modoDemo" class="rod">Demonstração: CPF 529.982.247-25 (ou qualquer CPF/CNPJ válido). Celular terminado em 0000 = dados não conferem.</p>
      </div>
    </div>

    <!-- CÓDIGO -->
    <div v-else-if="etapa === 'codigo'" key="codigo" class="in">
      <button class="voltar" @click="etapa = 'tel'">‹ Voltar</button>
      <h2>Digite o código</h2>
      <p class="slog">Enviamos um código de 6 dígitos {{ canal === 'sms' ? 'por SMS' : 'pelo WhatsApp da Ollivia' }} para <b>{{ mascararTel(tel) }}</b>.</p>
      <div class="casas" :class="{ erro: erroCod }" @paste="aoColar">
        <input v-for="(c, i) in casas" :key="i" :ref="el => (refs[i] = el)" :value="c" @input="digitar(i, $event)" @keydown="apagar(i, $event)"
          inputmode="numeric" maxlength="6" :autocomplete="i === 0 ? 'one-time-code' : 'off'" :class="{ cheia: c }" />
      </div>
      <p v-if="erroCod" class="msgerro">{{ msgCod || 'Código incorreto. Confira e tente de novo.' }}</p>
      <button v-if="sugestao && !codigo" class="sug" @click="colar(CODIGO)">
        <span class="wa" :class="{ sms: canal === 'sms' }">{{ canal === 'sms' ? 'Das Mensagens' : 'WhatsApp' }}</span><span class="cd">Código <b>482 917</b></span><span class="pre">Preencher</span>
      </button>
      <div class="reenviar">
        <span v-if="espera > 0">Reenviar código em 0:{{ String(espera).padStart(2, '0') }}</span>
        <template v-else>
          <button @click="reenviar">Reenviar por {{ nomeCanal(canal) }}</button>
          <div class="outro">Não recebeu? <button @click="trocarCanal">Enviar por {{ nomeCanal(outroCanal) }}</button></div>
        </template>
      </div>
      <p v-if="modoDemo" class="rod">Demonstração: qualquer código entra (000000 mostra o erro).</p>
    </div>

    <!-- TERMOS -->
    <div v-else-if="etapa === 'termos'" key="termos" class="in cfg">
      <div class="passos"><i v-for="(p, k) in passos" :key="p" :class="{ on: k <= passoN }"></i></div>
      <div class="ilus2">
        <svg viewBox="0 0 120 120"><path d="M60 14 L96 28 V58 C96 82 80 98 60 106 C40 98 24 82 24 58 V28 Z" class="traco" pathLength="1" />
          <path d="M44 60 L56 72 L78 48" class="traco check" pathLength="1" /></svg>
      </div>
      <h2>Seus dados, com cuidado</h2>
      <p class="slog">O app usa só o seu cadastro na Ollem e os dados de geração que a Ollem já acompanha.</p>
      <ul class="lista">
        <li><b>Só você vê a sua usina.</b> Ninguém mais tem acesso pelo app.</li>
        <li><b>Nada de senha de portal.</b> Os dados vêm direto da Ollem.</li>
        <li><b>Você pode excluir a sua conta</b> quando quiser, em Perfil.</li>
      </ul>
      <div class="acoes">
        <label class="aceite"><input type="checkbox" v-model="aceite" /><span>Li e aceito os <a href="#" @click.prevent>Termos de uso</a> e a <a href="#" @click.prevent>Política de privacidade</a>.</span></label>
        <button class="btn lima" :disabled="!aceite" @click="etapa = 'avisos'">Continuar</button>
      </div>
    </div>

    <!-- AVISOS -->
    <div v-else-if="etapa === 'avisos'" key="avisos" class="in cfg">
      <div class="passos"><i v-for="(p, k) in passos" :key="p" :class="{ on: k <= passoN }"></i></div>
      <div class="ilus2">
        <svg viewBox="0 0 120 120">
          <path d="M28 40 a40 40 0 0 0 0 40" class="onda o1" /><path d="M92 40 a40 40 0 0 1 0 40" class="onda o1" />
          <path d="M18 30 a54 54 0 0 0 0 60" class="onda o2" /><path d="M102 30 a54 54 0 0 1 0 60" class="onda o2" />
          <g class="sino2"><path d="M46 56a14 14 0 0 1 28 0c0 16 7 21 7 21H39s7-5 7-21M55 84h10" class="traco cheio" /></g>
          <circle cx="76" cy="42" r="6" fill="#e5484d" class="bolinha" />
        </svg>
      </div>
      <h2>Quer receber avisos?</h2>
      <p class="slog">Avisamos só o que importa. Nada de propaganda.</p>
      <div class="notifs">
        <div class="nt"><img :src="simbolo" alt="" /><div><b>Sua usina parou de gerar</b><small>Já avisamos a equipe. Toque para ver.</small></div><em>agora</em></div>
        <div class="nt"><img :src="simbolo" alt="" /><div><b>Seu relatório de outubro está pronto</b><small>Toque para abrir o PDF.</small></div><em>ontem</em></div>
        <div class="nt"><img :src="simbolo" alt="" /><div><b>Novembro: você economizou R$ 932</b><small>Veja o resumo do mês.</small></div><em>1 dez</em></div>
      </div>
      <div class="acoes">
        <button class="btn lima" @click="ativarAvisos(true)">Ativar avisos</button>
        <button class="btn txt" @click="ativarAvisos(false)">Agora não</button>
      </div>
    </div>

    <!-- BIOMETRIA -->
    <div v-else-if="etapa === 'bio'" key="bio" class="in cfg">
      <div class="passos"><i v-for="(p, k) in passos" :key="p" :class="{ on: k <= passoN }"></i></div>
      <div class="ilus2">
        <div class="scan">
          <svg viewBox="0 0 48 48"><path d="M8 16V10a2 2 0 0 1 2-2h6M32 8h6a2 2 0 0 1 2 2v6M40 32v6a2 2 0 0 1-2 2h-6M16 40h-6a2 2 0 0 1-2-2v-6" class="cantos" /><path d="M18 19v3M30 19v3M24 19v8h-2M19 32c3 2 7 2 10 0" class="rosto" /></svg>
          <i class="feixe"></i>
        </div>
      </div>
      <h2>Entrar com Face ID ou digital</h2>
      <p class="slog">Na próxima vez, é só olhar para o celular ou encostar o dedo. Sem digitar código.</p>
      <ul class="lista">
        <li><b>Mais rápido:</b> abre a sua usina em um toque.</li>
        <li><b>Mais seguro:</b> só você consegue abrir o app.</li>
      </ul>
      <div class="acoes">
        <button class="btn lima" @click="ativarBio(true)">Ativar</button>
        <button class="btn txt" @click="ativarBio(false)">Agora não</button>
      </div>
    </div>

    <!-- VOLTA COM BIOMETRIA -->
    <div v-else-if="etapa === 'volta'" key="volta" class="in volta">
      <img :src="simbolo" alt="Ollem" class="simb grande" />
      <h2>Olá de novo!</h2>
      <p class="slog">Toque para entrar na sua usina.</p>
      <button class="bioic escuro" :class="{ lendo }" @click="faceId" aria-label="Entrar com Face ID">
        <svg viewBox="0 0 48 48"><path d="M8 16V10a2 2 0 0 1 2-2h6M32 8h6a2 2 0 0 1 2 2v6M40 32v6a2 2 0 0 1-2 2h-6M16 40h-6a2 2 0 0 1-2-2v-6M18 19v3M30 19v3M24 19v8h-2M19 32c3 2 7 2 10 0" /></svg>
      </button>
      <button class="btn lima" @click="faceId">{{ lendo ? 'Reconhecendo…' : 'Entrar com Face ID' }}</button>
      <button class="link" @click="etapa = 'tel'">Entrar com código</button>
    </div>

    <!-- ESCOLHER USINA -->
    <div v-else key="usina" class="in cfg">
      <div v-if="passoN >= 0" class="passos"><i v-for="(p, k) in passos" :key="p" class="on"></i></div>
      <div class="ilus2">
        <svg viewBox="0 0 120 120">
          <circle cx="88" cy="30" r="9" fill="#ffd23a" class="bolinha" /><circle cx="88" cy="30" r="16" fill="#ffd23a" opacity=".12" class="bolinha" />
          <path d="M18 64 L60 34 L102 64" class="traco" pathLength="1" />
          <path d="M28 58 V96 H92 V58" class="traco" pathLength="1" />
          <g class="placas"><path d="M36 58 L60 41 L84 58 Z" fill="#11c90a" opacity=".85" /><path d="M48 50 L72 50 M42 54 L78 54 M60 41 V58 M50 48 L46 58 M70 48 L74 58" stroke="#0c100e" stroke-width="1.2" /></g>
        </svg>
      </div>
      <h2>Qual usina você quer ver?</h2>
      <p class="slog">Encontramos {{ lista.length }} usinas no seu cadastro. Dá para trocar depois, no topo do app.</p>
      <button v-for="x in lista" :key="x.u.id" class="card usina" @click="escolher(x.i)">
        <div><b>Usina em {{ x.u.bairro }}</b><small>{{ fmt(x.u.kwp, 2) }} kWp · hoje {{ fmt(x.r.hojeKwh, 1) }} kWh</small></div>
        <span class="sit"><i class="ponto" :style="{ background: corSit(x.r.situacao) }"></i>{{ txtSit(x.r.situacao) }}</span>
      </button>
      <p class="rod">Quem tem uma usina só pula esta tela.</p>
    </div>
      </Transition>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity .4s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.passo-enter-active, .passo-leave-active { transition: opacity .28s ease, transform .32s cubic-bezier(.2,.8,.2,1); }
.passo-enter-from { opacity: 0; transform: translateX(28px); }
.passo-leave-to { opacity: 0; transform: translateX(-20px); }
.slide-enter-active, .slide-leave-active { transition: opacity .25s ease, transform .3s cubic-bezier(.2,.8,.2,1); }
.slide-enter-from { opacity: 0; transform: translateX(36px); }
.slide-leave-to { opacity: 0; transform: translateX(-28px); }
.in:not(.boas) > * { animation: sobe .5s cubic-bezier(.2,.8,.2,1) both; }
.in:not(.boas) > *:nth-child(2) { animation-delay: .05s } .in:not(.boas) > *:nth-child(3) { animation-delay: .1s }
.in:not(.boas) > *:nth-child(4) { animation-delay: .15s } .in:not(.boas) > *:nth-child(n+5) { animation-delay: .2s }
.sl > * { animation: sobe .5s cubic-bezier(.2,.8,.2,1) both; }
.sl > *:nth-child(2) { animation-delay: .08s } .sl > *:nth-child(3) { animation-delay: .14s }
.desenha { stroke-dasharray: 1; stroke-dashoffset: 1; animation: desenha .9s .15s cubic-bezier(.6,0,.2,1) forwards; }
@keyframes desenha { to { stroke-dashoffset: 0; } }
.solzinho { transform-box: fill-box; transform-origin: center; animation: nasce .5s .8s cubic-bezier(.2,1.6,.4,1) both; }
@keyframes nasce { from { opacity: 0; transform: scale(.2); } }
.cresce { transform-box: fill-box; transform-origin: bottom; animation: cresce .6s cubic-bezier(.2,.8,.2,1) both; }
.bolha { transform-box: fill-box; animation: bolha .45s cubic-bezier(.2,1.5,.4,1) both; }
.b1 { transform-origin: left bottom; animation-delay: .1s } .b2 { transform-origin: right bottom; animation-delay: .45s }
@keyframes bolha { from { opacity: 0; transform: scale(.6); } }
.pontos i { transition: width .3s cubic-bezier(.2,.8,.2,1), background-color .3s; }
.casas input { transition: border-color .2s, transform .15s; }
.casas input.cheia { animation: digito .25s cubic-bezier(.2,1.6,.4,1); }
@keyframes digito { 50% { transform: scale(1.08); } }
.notifs .nt { animation: sobe .45s cubic-bezier(.2,.8,.2,1) both; }
.notifs .nt:nth-child(2) { animation-delay: .25s } .notifs .nt:nth-child(3) { animation-delay: .4s }
.usina { animation: sobe .45s cubic-bezier(.2,.8,.2,1) both; }
.passos i { transition: background-color .4s; }
.login { transition: background-color .35s ease, color .35s; }
.volta { align-items: stretch; text-align: center; padding-top: 110px; }
.simb.grande { height: 64px; align-self: center; }
.bioic.escuro { background: #141a17; border: 1px solid #232b26; margin: 34px auto 4px; width: 96px; height: 96px; border-radius: 28px; }
.bioic.lendo { animation: pulsa .9s ease-in-out infinite; }
@keyframes pulsa { 50% { box-shadow: 0 0 0 10px rgba(142,247,5,.12); } }
.link { align-self: center; margin-top: 16px; background: none; border: 0; color: #8a968f; font-size: 14px; }
.login { position: relative; min-height: 100%; flex: 1; background: #0c100e; color: #fff; overflow: hidden; display: flex; flex-direction: column; }
.login.e-termos, .login.e-avisos, .login.e-bio, .login.e-usina { background: radial-gradient(420px 260px at 50% 0%, rgba(142,247,5,.07), transparent 70%), #0c100e; }
.in { position: relative; padding: 70px 28px 240px; display: flex; flex-direction: column; flex: 1; }
.in.claro { padding: 54px 24px 32px; gap: 0; }
.in.centro { align-items: stretch; text-align: center; }
.simb { height: 44px; align-self: flex-start; }
.simb.pq { height: 30px; }
h1 { font-size: 34px; font-weight: 700; margin: 26px 0 0; letter-spacing: -1.2px; line-height: 1.05; }
h1 span { color: var(--lima); }
h2 { font-size: 26px; font-weight: 700; letter-spacing: -.8px; margin: 18px 0 0; line-height: 1.15; }
.slog { font-size: 14px; color: #8a968f; margin: 10px 0 0; line-height: 1.5; }
.claro .slog { color: var(--sub); }
.slog b { color: #eef3f0; }
/* boas-vindas */
.boas { padding-top: 54px; padding-bottom: 0; }
.sl { height: 400px; }               /* ilustração + título + texto sempre ocupam a mesma altura */
.sl .ttl { min-height: 64px; display: flex; align-items: flex-end; }
.sl .slog { min-height: 63px; }
.rodape { margin-top: 18px; }  /* pontos e botão sempre no mesmo lugar */
.marcaIl { position: relative; width: 130px; height: 130px; display: grid; place-items: center; }
.marcaIl img { position: relative; width: 62px; animation: nasce .6s .1s cubic-bezier(.2,1.5,.4,1) both; }
.ilus .anelIl { position: absolute; inset: 0; width: 100%; height: 100%; transform: rotate(-90deg); }
.anelIl circle { fill: none; stroke: var(--lima); stroke-width: 2; stroke-linecap: round; stroke-dasharray: 1; stroke-dashoffset: 1; animation: desenha 1s .2s cubic-bezier(.6,0,.2,1) forwards; }
.devagar { animation-duration: 1.2s !important; animation-delay: .45s !important; }
.sino { transform-box: fill-box; transform-origin: 50% 0; animation: balanca 1s .5s ease-in-out both; }
@keyframes balanca { 0%,100% { transform: rotate(0); } 20% { transform: rotate(14deg); } 40% { transform: rotate(-12deg); } 60% { transform: rotate(8deg); } 80% { transform: rotate(-4deg); } }
.ponto-vermelho { transform-box: fill-box; transform-origin: center; animation: nasce .4s .35s cubic-bezier(.2,1.6,.4,1) both; }
.notif { animation: notif .55s .7s cubic-bezier(.2,.9,.3,1) both; }
@keyframes notif { from { opacity: 0; transform: translateY(14px); } }
.topo { display: flex; justify-content: space-between; align-items: center; }
.pular { background: none; border: 0; color: #8a968f; font-size: 14px; }
.ilus { height: 170px; display: grid; place-items: center; margin: 36px 0 10px; }
.ilus svg { width: 240px; height: 150px; }
.ttl { font-size: 28px; margin-top: 14px; }
.pontos { display: flex; gap: 6px; margin: 0 0 22px; }
.pontos i { width: 6px; height: 6px; border-radius: 6px; background: #2a332e; transition: width .2s; cursor: pointer; }
.pontos i.on { width: 22px; background: var(--lima); }
/* celular */
.seg2 { margin-top: 20px; }
.linha.ruim { border-bottom-color: var(--vermelho); }
.msgcampo { color: #ffb3b5; font-size: 12px; margin: 6px 0 0; }
.seguro { display: flex; gap: 8px; align-items: flex-start; font-size: 12px; color: #8a968f; margin: 14px 0 0; line-height: 1.45; }
.seguro svg { width: 15px; height: 15px; flex-shrink: 0; fill: none; stroke: var(--lima); stroke-width: 1.8; margin-top: 1px; }
.form { margin-top: 36px; display: flex; flex-direction: column; }
label { font-size: 12px; color: #8a968f; }
.linha { background: transparent; border: 0; border-bottom: 1px solid #2a332e; border-radius: 0; padding: 10px 0; font-size: 20px; color: #eef3f0; margin-top: 4px; letter-spacing: .5px; }
.linha::placeholder { color: #4d5852; }
.linha:focus { outline: none; border-bottom-color: var(--lima); }
.btn { margin-top: 24px; }
.btn.txt { margin-top: 6px; background: none; color: var(--sub); }
.btn.sec.escuro { background: transparent; color: #fff; border-color: #2a332e; margin-top: 12px; }
.erro { margin-top: 20px; border: 1px solid rgba(229,72,77,.35); background: rgba(229,72,77,.08); border-radius: 16px; padding: 14px; }
.erro b { color: #ffb3b5; font-size: 14px; }
.erro p { font-size: 13px; color: #c9d2cd; margin: 6px 0 0; line-height: 1.45; }
.rod { margin: 14px 0 0; text-align: center; font-size: 11.5px; color: #5f6b64; }
/* código */
.voltar { align-self: flex-start; background: none; border: 0; color: var(--lima); font-size: 14px; font-weight: 600; padding: 0; }
.casas { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; margin-top: 30px; }
.casas input { height: 58px; text-align: center; font-size: 24px; font-weight: 700; background: #141a17; border: 1px solid #232b26; border-radius: 14px; color: #fff; padding: 0; }
.casas input:focus { outline: none; border-color: var(--lima); }
.casas input.cheia { border-color: #2f3a33; }
.casas.erro input { border-color: var(--vermelho); animation: treme .3s; }
@keyframes treme { 25% { transform: translateX(-4px); } 75% { transform: translateX(4px); } }
.msgerro { color: #ffb3b5; font-size: 13px; margin: 10px 0 0; }
.sug { margin-top: 18px; display: flex; align-items: center; gap: 8px; background: #141a17; border: 1px solid #232b26; color: #c9d2cd; border-radius: 14px; padding: 12px 14px; font-size: 13px; text-align: left; }
.sug .cd { white-space: nowrap; }
.sug b { color: #fff; letter-spacing: 1px; margin-left: 4px; }
.sug .wa { font-size: 10.5px; font-weight: 700; color: #06200a; background: #8ef705; padding: 2px 6px; border-radius: 6px; }
.sug .pre { margin-left: auto; color: var(--lima); font-weight: 600; }
.reenviar { margin-top: 22px; font-size: 13px; color: #8a968f; }
.outro { margin-top: 12px; display: flex; gap: 6px; align-items: center; }
.outro button { font-size: 13px !important; }
.canais { position: relative; display: grid; grid-template-columns: 1fr 1fr; margin-top: 8px; background: #141a17; border: 1px solid #232b26; border-radius: 99px; padding: 4px; }
.canais button { position: relative; z-index: 1; display: flex; align-items: center; justify-content: center; gap: 7px; background: none; border: 0; color: #8a968f; font-size: 14px; font-weight: 600; padding: 10px; border-radius: 99px; transition: color .25s; }
.canais button.on { color: #06200a; }
.canais svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.marcador { position: absolute; top: 4px; bottom: 4px; left: 4px; width: calc(50% - 4px); border-radius: 99px; background: var(--lima); transition: transform .3s cubic-bezier(.2,.8,.2,1); }
.marcador.sms { transform: translateX(100%); }
.sug .wa.sms { background: #3ba0ff; color: #fff; }
.reenviar button { background: none; border: 0; color: var(--lima); font-weight: 600; font-size: 14px; padding: 0; }
/* telas claras */
.passos { display: flex; gap: 6px; }
.passos i { flex: 1; height: 4px; border-radius: 4px; background: var(--trilho); }
.passos i.on { background: var(--verde); }
.lista { list-style: none; padding: 0; margin: 22px 0 0; display: flex; flex-direction: column; gap: 12px; }
.lista li { font-size: 14px; color: var(--sub); line-height: 1.45; padding-left: 26px; position: relative; }
.lista li::before { content: '✓'; position: absolute; left: 0; top: 0; width: 18px; height: 18px; border-radius: 50%; background: rgba(17,201,10,.14); color: var(--acento); font-size: 11px; font-weight: 700; display: grid; place-items: center; }
.lista b { color: var(--texto); }
.aceite { display: flex; gap: 10px; align-items: flex-start; margin-top: 26px; font-size: 13.5px; color: var(--texto); line-height: 1.45; }
.aceite input { width: 20px; height: 20px; accent-color: var(--verde); flex-shrink: 0; margin-top: 1px; padding: 0; }
.aceite a { color: var(--acento); font-weight: 600; }
.notifs { display: flex; flex-direction: column; gap: 8px; margin: 24px 0 6px; }
.nt { display: flex; gap: 10px; align-items: center; background: var(--card); border: 1px solid var(--linha); border-radius: 16px; padding: 10px 12px; }
.nt img { width: 28px; height: 28px; padding: 4px; border-radius: 8px; background: #111714; }
.nt b { display: block; font-size: 13px; }
.nt small { font-size: 11.5px; color: var(--sub); }
.bioic { width: 88px; height: 88px; border-radius: 26px; background: #111714; display: grid; place-items: center; margin: 46px auto 0; }
.bioic svg { width: 48px; height: 48px; fill: none; stroke: var(--lima); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.usina { display: flex; justify-content: space-between; align-items: center; gap: 10px; text-align: left; color: inherit; font: inherit; width: 100%; margin-top: 10px; }
.usina:first-of-type { margin-top: 22px; }
.usina b { display: block; font-size: 14.5px; }
.usina small { font-size: 12px; color: var(--sub); }
.sit { display: inline-flex; align-items: center; gap: 6px; font-size: 11.5px; color: var(--sub); flex-shrink: 0; }

/* ===== telas de configuração (escuras, mesmo esqueleto) ===== */
.cfg { padding: 54px 24px 34px; }
.cfg .passos i { background: #1d2420; position: relative; overflow: hidden; }
.cfg .passos i.on { background: #1d2420; }
.cfg .passos i.on::after { content: ''; position: absolute; inset: 0; background: var(--lima); border-radius: 4px; transform-origin: left; animation: enche .6s cubic-bezier(.2,.8,.2,1) both; }
.ilus2 { height: 120px; display: grid; place-items: center; margin: 30px 0 4px; }
.ilus2 svg { width: 120px; height: 120px; overflow: visible; }
.traco { fill: none; stroke: var(--lima); stroke-width: 2.4; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 1; stroke-dashoffset: 1; animation: desenha 1s .15s cubic-bezier(.6,0,.2,1) forwards; }
.traco.check { stroke-width: 3.2; animation-delay: .85s; animation-duration: .5s; }
.traco.cheio { stroke-dasharray: none; stroke-dashoffset: 0; animation: none; }
.onda { fill: none; stroke: var(--lima); stroke-width: 2; stroke-linecap: round; opacity: 0; animation: radar 2s ease-out infinite; }
.o1 { animation-delay: .5s; } .o2 { animation-delay: .8s; }
@keyframes radar { 0% { opacity: 0; } 30% { opacity: .7; } 100% { opacity: 0; } }
.sino2 { transform-box: fill-box; transform-origin: 50% 0; animation: balanca 1s .3s ease-in-out both; }
.bolinha { transform-box: fill-box; transform-origin: center; animation: nasce .45s .4s cubic-bezier(.2,1.6,.4,1) both; }
.placas { animation: aparece .6s .9s both; }
.scan { position: relative; width: 104px; height: 104px; border-radius: 30px; background: #141a17; border: 1px solid #232b26; display: grid; place-items: center; overflow: hidden; }
.scan svg { width: 56px; height: 56px; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.scan .cantos { stroke: var(--lima); }
.scan .rosto { stroke: #eef3f0; opacity: .85; }
.feixe { position: absolute; left: 10%; right: 10%; height: 2px; background: linear-gradient(90deg, transparent, var(--lima), transparent); box-shadow: 0 0 12px var(--lima); animation: varre 2s ease-in-out infinite; }
@keyframes varre { 0%,100% { top: 18%; } 50% { top: 80%; } }
.cfg h2 { margin-top: 18px; }
.cfg .lista { margin-top: 20px; }
.cfg .lista li { color: #8a968f; }
.cfg .lista b { color: #eef3f0; }
.cfg .lista li::before { background: rgba(142,247,5,.12); color: var(--lima); }
.cfg .lista li { animation: sobe .45s cubic-bezier(.2,.8,.2,1) both; }
.cfg .lista li:nth-child(2) { animation-delay: .15s } .cfg .lista li:nth-child(3) { animation-delay: .25s }
.acoes { margin-top: auto; padding-top: 18px; display: flex; flex-direction: column; }
.acoes .btn { margin-top: 0; }
.acoes .btn.txt { margin-top: 8px; color: #8a968f; }
.cfg .aceite { margin: 0 0 16px; color: #c9d2cd; }
.cfg .aceite a { color: var(--lima); }
.cfg .aceite input { appearance: none; width: 22px; height: 22px; border-radius: 7px; border: 1.5px solid #3a463f; background: transparent; position: relative; transition: background-color .2s, border-color .2s; }
.cfg .aceite input:checked { background: var(--lima); border-color: var(--lima); }
.cfg .aceite input:checked::after { content: ''; position: absolute; left: 6px; top: 2px; width: 6px; height: 11px; border: solid #06200a; border-width: 0 2.4px 2.4px 0; transform: rotate(45deg); animation: nasce .25s cubic-bezier(.2,1.6,.4,1); }
.cfg .notifs { margin-top: 18px; }
.cfg .nt { background: rgba(255,255,255,.04); border: 1px solid #1f2722; backdrop-filter: blur(8px); color: #eef3f0; position: relative; }
.cfg .nt img { background: #0c100e; }
.cfg .nt small { color: #8a968f; }
.cfg .nt em { font-style: normal; font-size: 10.5px; color: #5f6b64; margin-left: auto; align-self: flex-start; flex-shrink: 0; }
.cfg .usina { background: rgba(255,255,255,.04); border: 1px solid #1f2722; color: #eef3f0; }
.cfg .usina small, .cfg .sit { color: #8a968f; }
.cfg .usina:active { background: rgba(142,247,5,.08); border-color: var(--lima); }
.cfg .usina:nth-of-type(2) { animation-delay: .1s } .cfg .usina:nth-of-type(3) { animation-delay: .2s }
.cfg .rod { color: #5f6b64; }
@keyframes aparece { from { opacity: 0; } }
</style>
