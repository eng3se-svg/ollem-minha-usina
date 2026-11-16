# Decisões e histórico do app (roteiro)

Versão 1.10 do roteiro, 16/11/2026. Fonte: skill `ollem-app-cliente` + decisões com a Thays (nov/2026).

**Nome do app: Ollem - Minha usina** (decidido em 16/11/2026). Na loja: "Ollem: Minha Usina Solar" (até 30 caracteres); embaixo do ícone: "Ollem". A Ollivia segue como assistente dentro do app. Pendente: conferir INPI e se não há app com nome parecido nas lojas.

Stack decidida: **Vue 3 + Vite + Capacitor** (iOS, Android e PWA com um código só). Backend em Python (Flask), na linha do servidor da Ollivia.

**Prioridade atual (16/11/2026):** primeiro o visual e as funcionalidades do app; detalhes técnicos de implementação depois.

Regra de fluxo em todas as fases: montar a prévia → screenshots/link → Thays aprova ("aprovado"/"pode") → só então instalar, publicar ou abrir PR.

---

## Estado atual (16/11/2026)
- **Prévia 0.4 publicada** (mesmo link). Ajustes pedidos pela Thays em 16/11:
  - **Navegação:** o símbolo da Ollem no meio da barra abre o Início. Abas: Geração · Serviços · [símbolo = Início] · Economia · Perfil.
  - **Início:** aprovado (objetiva).
  - **Geração:** refeita (ela achou crua/simples demais): cartão-resumo escuro com total, selo "% do esperado" e uma frase em linguagem simples; gráfico com toque; média, melhor dia, dias fracos; comparação com os mesmos dias do ano passado. **Ainda em evolução.**
  - **Serviços** (era Ajuda): conversar com a Ollivia **dentro do app**, mensagem para o pós-venda (vira chamado), pedir manutenção/limpeza/visita (vira oportunidade em Serviços do Hub), "Meus pedidos" com situação, sugestão automática pelo monitoramento. **Documentos da usina removidos** (desnecessários).
  - **Serviços → Pedir relatório de geração** (prévia 0.5): período (último mês, 3 meses, 12 meses, 7 dias, 15 dias ou datas livres), anexar contas de luz (PDF ou foto, várias), receber no app e/ou WhatsApp; aparece em "Meus pedidos" com "Abrir PDF" quando pronto. No real: fila `pedidos_relatorio` da Ollivia → Hub gera o PDF (`relatorio_geracao.py`) com análise das faturas.
  - **Login completo** (prévia 0.6): 3 telas de boas-vindas (pular), celular, "número não encontrado" com atalho para a Ollivia, código em 6 casas (avança sozinho, colar, sugestão do WhatsApp, reenviar em 60 s, erro com tremida), aceite de termos/privacidade (LGPD), permissão de avisos explicada com exemplos, Face ID/digital, escolha da usina (só se tiver mais de uma). Termos/avisos/biometria só no 1º acesso. Troca de usina pelo topo do app (toque no nome).
  - **Decisão (prévia 0.9): volta o fluxo da 0.6 com várias telas** ("várias telas preparam o cliente"), agora com as animações da 0.8: boas-vindas em 3 telas (ilustrações animadas, arrastar para o lado), celular, código, termos, avisos, Face ID, escolher usina. Mantida da 0.7 só a tela "Olá de novo!" (Face ID com 1 toque) para quem volta.
  - ~~Login enxuto~~ (prévia 0.7, descartado): de 7 telas para 3 no 1º acesso → (1) entrada com o nome, 3 benefícios e o celular, aceite dos termos em uma linha ("Ao continuar, você aceita…"); (2) código; (3) "Tudo certo! Só mais um detalhe" com avisos e Face ID ligados por padrão (dá para desligar) → Início. Sem tela de escolher usina (troca no topo). Quem volta com biometria: "Olá de novo!" + Entrar com Face ID (1 toque), ou código.
  - **Movimento e abertura** (prévia 0.8): a Thays quer o app **bem fluido**, com transições bonitas (o problema não era o número de telas). Abertura de ~1,3 s (símbolo gira e aparece, anel lima se desenha, "Ollem Minha usina"), saída com zoom e desfoque; login → app com escala; abas deslizam na direção da barra; etapas do login deslizam; cartões entram em sequência; o sol nasce e anda pelo arco até a hora atual; números contam (kWh, R$, %); barras crescem; barras de progresso enchem; botões encolhem ao toque; ícone da aba ativa dá um pulinho; menu de usinas desliza. Respeita "reduzir movimento". No app nativo, usar as mesmas animações (CSS/Vue) + tela de abertura nativa do Capacitor (Splash Screen) com a mesma logo.
  - **Economia:** premissa aprovada; melhorada com economia mês a mês em R$, neste mês / 12 meses, retorno do investimento (valor investido de EXEMPLO na prévia; no real vem do contrato/projeto), CO₂ e "calcular com a sua tarifa" (enviar conta de luz à Ollivia).
  - Impacto técnico anotado: a Ollivia precisa de um **canal do app** além do WhatsApp (chat no app + mensagens ao pós-venda); valor investido por usina precisa vir de algum lugar (contrato/Bitrix/Hub).
- Prévia 0.3 (artifact privado "Ollem - Minha usina": https://claude.ai/artifact/Ti92Lpg9vvvxXNpwxMfUWo), com o visual **D2** em todas as telas. **Aguardando aprovação da Thays.**
- **Visual escolhido: D2 "Ollem Hub, mais limpo"** (https://claude.ai/artifact/LFJbyBKsjL4kbTcWTU8nRX). Identidade do Ollem Hub (símbolo, #11c90a → #8ef705, fonte Inter) com efeitos limpos: ondas em linhas finas só na entrada; cartão escuro com o **caminho do sol** (arco 6h–18h, sol na hora atual, kWh de hoje no centro; noite = lua; sem comunicação = sol cinza); cartões brancos lisos; verde só em dado/ação; barra de baixo com ponto verde na aba ativa e botão central com o símbolo (abre Ajuda/Ollivia). Modos claro e escuro. Direções descartadas: A (Família Ollem Energy), B (claro), C (sol e céu), D (Hub com ondas grossas).
- Referências: app de carregadores **Ollem Energy** (com.ollem.energy, Google Play e App Store); CSS "Visual 2.0" do Hub (`hubfv/web/static/style.css`).
- Código-fonte e telas: `Documentos\Hub FV\_claude\app-cliente\` (`ollem-app-previa-0.3-fonte.zip`, `previa-0.3-telas-D2.png`, `direcao-D2-clean.png`, `usinas_previa.json`; versões anteriores ao lado).
- Dados: 3 usinas reais do `monitor.db` (cópia), sem nome/telefone/endereço; só bairro e kWp.
  - Exemplo 1: 14,85 kWp, online, com 25 dias parada em jun/2026 (bom para ver o gráfico de falha).
  - Exemplo 2: 6,3 kWp, esperado via PVGIS.
  - Exemplo 3: 13,2 kWp, sem comunicação desde 14/11 (alerta).
- Achados ao montar a prévia:
  - **Nenhuma usina tem vínculo** no `monitor.db` (campo `vinculo` = `{}` nas 1.428) e a pasta `Equipe\Monitoramento\vinculos` está vazia. Sem vínculo + telefone o cliente não entra no app → **cadastrar vínculos é pré-requisito do piloto**.
  - O banco só tem **geração diária**; a curva hora a hora do dia depende da coleta no servidor (Fase 2).
  - Há dias faltando na série (ex.: 15/11 em usinas Solis); o app mostra "sem dado" e usa o total do mês do portal quando existe.
  - Fator de CO₂ usado provisoriamente: 0,0385 kg/kWh. **Conferir o valor oficial atual** (MCTI/SIN) antes de lançar.
  - Tarifa: padrão R$ 1,06/kWh até haver tarifa no vínculo.

---

## Fase 0: Fundação (≈1 semana)
**Objetivo:** destravar decisões e burocracia que demoram.
- [x] Decidir a **marca** do app → **Ollem - Minha usina**.
- [ ] Conferir o nome no INPI e nas lojas; desenhar o ícone.
- [ ] Decidir **onde hospedar o backend** (servidor da Ollivia ou serviço separado), já pensando em VPS 24 h (Docker + Caddy já existem).
- [ ] Contas de desenvolvedor: a Ollem **já tem um app de carregadores veiculares publicado na Google Play e na App Store**, então as contas provavelmente já existem. Confirmar se estão no CNPJ da Ollem e quem administra.
- [ ] Redigir e publicar a **política de privacidade** e os **termos de uso** (LGPD) numa URL da Ollem (o login já tem o aceite).
- [x] Criar a estrutura do projeto Vue 3 + Vite, tokens de marca (verdes do Hub, Poppins, modo claro/escuro). Capacitor entra na Fase 4.
- [ ] Definir como teremos Mac para gerar o build iOS (Mac próprio ou build em nuvem, ex. Codemagic).
- [ ] **Novo:** começar a cadastrar vínculos (telefone, tarifa, esperado do projeto) das usinas dos clientes do piloto.

## Fase 1: Prévia navegável (≈2 semanas)
**Objetivo:** ver e aprovar o app antes de mexer em servidor.
- [x] Copiar o `monitor.db` (nunca gravar nele) e extrair 3 usinas reais para JSON, mascaradas.
- [x] Telas: Entrar (OTP simulado) → Minha usina → Geração (7 dias / mês / 12 meses, com linha do esperado) → Economia R$ e CO₂ → Alertas em frase simples → Ajuda (Ollivia, pedir limpeza/visita, documentos "em breve") → Conta (avisos, biometria, tema escuro, sair, excluir conta).
- [x] Estados: gerando, noite, sem comunicação, aviso do equipamento, dias sem dado, dias sem geração.
- [ ] Estado: sistema com vários inversores (`sis:`) — não há nenhum no banco hoje.
- [x] Cálculos portados do Hub: esperado (projeto > PVGIS > kWp×HSP×PR com sazonalidade), economia, desempenho 7 d e mês.
- [x] Screenshots em viewport de iPhone (Playwright).
- [x] Prévia 0.2 com o nome "Ollem - Minha usina".
- [ ] Aprovação da Thays → ajustes.

**Entrega:** PWA estática aprovada visualmente.

## Fase 2: Servidor (≈3–4 semanas)
**Objetivo:** dados reais, 24 h, com segurança por cliente.
- [ ] Servidor 24 h (VPS) em vez do PC da Ollem; HTTPS.
- [ ] **Coleta no servidor** (portar a coleta do `monitor_local.py` para os portais por API oficial; credenciais só no servidor), incluindo potência ao longo do dia. Transição: aceitar o snapshot do Hub, ampliado com série diária.
- [ ] **Login CPF/CNPJ + celular com código por SMS ou WhatsApp** (serviço de verificação; WhatsApp só depois da migração do número da Ollivia para a API oficial), com limite de tentativas, expiração e resposta genérica quando não confere.
- [ ] Tabelas de sessões e aparelhos; token de sessão por cliente.
- [ ] Rotas `/api/app/...` filtradas pelo **CPF/CNPJ + telefone do vínculo** (sem vínculo completo = fora do app). Adicionar CPF/CNPJ do titular ao vínculo (Bitrix).
- [ ] Séries diária e mensal por usina; esperado; economia; alertas traduzidos.
- [ ] Registro de token de push (APNs/FCM).
- [ ] Exclusão de conta.
- [ ] Pedido de serviço → oportunidade na aba Serviços do Hub (`servicos.salvar_oportunidade`).
- [ ] Testes de permissão: cliente A nunca vê usina do cliente B.

**Entrega:** API em produção + prévia ligada a ela.

## Fase 3: Piloto web/PWA (≈3–4 semanas)
**Objetivo:** validar com ~10 clientes reais.
- [ ] Escolher 10 clientes (mistura de portais, sistemas com vários inversores, uma usina com problema) — com vínculo cadastrado.
- [ ] Envio do link pela Ollivia; instalação na tela inicial.
- [ ] Coletar feedback (pela Ollivia) e métricas básicas de uso e erros.
- [ ] Ajustar textos, alertas e gráficos.

**Entrega:** versão estável e lista do que mudou com o piloto.

## Fase 4: Funções nativas + Play Store (≈2–3 semanas)
- [ ] Empacotar com Capacitor (Android).
- [ ] Push (FCM): usina parada, geração abaixo do esperado.
- [ ] Biometria (digital/rosto).
- [ ] Widget "geração de hoje" (exige código nativo Android, Kotlin).
- [ ] Ficha da loja, prints, classificação, formulário de segurança de dados.
- [ ] Teste interno → teste fechado → produção.

## Fase 5: App Store (≈2–4 semanas)
- [ ] Build iOS, push (APNs), Face ID.
- [ ] Widget iOS (WidgetKit, código nativo Swift).
- [ ] Conta de demonstração para o revisor da Apple (o OTP por WhatsApp precisa de um número/código de teste fixo).
- [ ] Exclusão de conta visível no app, política de privacidade, rótulos de privacidade.
- [ ] Envio para revisão → ajustes → publicação.

## Fase 6: Evolução contínua (depois do lançamento)
Ideias a priorizar com a Thays:
- Documentos (contrato, ART, projeto), se aprovado.
- Relatório mensal em PDF no estilo da proposta de vendas.
- Leitura da fatura Enel/Light (foto/PDF) para economia real.
- Comparação com usinas vizinhas como sugestão de limpeza.
- Mais de um usuário por usina (família, síndico).
- Integração com o Ollem Field/FieldOps para acompanhar a visita agendada.

---

## Riscos e pontos de atenção
- **Coleta 24 h fora do PC** é o ponto crítico: sem ela o app mostra dados velhos.
- **Vínculos vazios**: sem telefone vinculado não há login.
- **Widgets são nativos** (Swift/Kotlin), fora do Vue: planejar tempo extra.
- **Apple** pode recusar "site embrulhado": push, biometria e widget precisam estar prontos e úteis.
- **LGPD:** só a usina do próprio cliente; nunca mostrar nome do portal do fabricante.
- Fator de CO₂ do SIN: confirmar o valor atual antes de fixar.

## Registro de decisões e versões
| Data | Decisão / versão |
|---|---|
| nov/2026 | Vue 3 + Capacitor; ordem prévia → servidor → piloto web → Play → App Store; login OTP WhatsApp |
| 16/11/2026 | Roteiro v1 criado |
| 16/11/2026 | Prévia 0.1 publicada (artifact privado) |
| 16/11/2026 | Prévia 0.20: **Geração cabe numa tela só** (sem rolar, testado também em iPhone SE 375×667): períodos em 5 botões que cabem na largura (7 dias · 15 dias · Mês · 12 meses · ícone de calendário), resumo mais baixo com o selo ao lado do total, gráfico mais compacto com a legenda no lugar da dica (o valor aparece ao tocar), números (média, melhor, fracos), comparação com o ano passado e "dias sem informação" juntos num só cartão |
| 16/11/2026 | Prévia 0.19: passo a passo refeito — holofote alinhado (descontava a moldura da tela), mede só depois das animações e se ajusta a mudanças de tamanho; formato acompanha o arredondamento de cada elemento; pulso trocado por dois anéis que "respiram" para fora (só transform/opacity, sem travar); balão com 3 colunas fixas (Pular · pontos centralizados · voltar/Próximo à direita), bico apontando para o centro do alvo, pontos já vistos em verde-claro |
| 16/11/2026 | Prévia 0.18: **passo a passo (tour) no 1º acesso** ao entrar no app — holofote com borda lima pulsando passa por: cartão do sol, mês, troca de usina (se houver mais de uma), sino de avisos, Geração, Serviços, símbolo (Início), Economia e Perfil; balão com "n de 9", Pular, voltar e Próximo/Começar; tocar fora avança. "Rever o passo a passo" em Perfil → Ajuda e sobre |
| 16/11/2026 | Prévia 0.17: seta (círculo com ⌄) ao lado do título do topo indicando a troca de usina; gira ao abrir; o menu mostra a situação de cada usina (bolinha) e ✓ na atual |
| 16/11/2026 | Prévia 0.16: componentes novos **Chave** (liga/desliga com trilho em degradê verde, bolinha com ✓/– que estica ao segurar, mola na troca, acessível) e **Segmento** (destaque que desliza: tema e período da visita); "Receber por" em pílulas com ✓ (pelo menos um canal fica ligado); a linha inteira liga/desliga ao tocar |
| 16/11/2026 | Prévia 0.15: **Conta de luz no Perfil** — a distribuidora **não é escolhida pelo cliente** (vem do cadastro da Ollem, sem lista de todas as concessionárias; "Distribuidora errada? Fale com a Ollivia"); mostra a **tarifa usada e a origem** (média geral / sua conta de mês X / informada por você); "Atualizar com a minha conta de luz" (foto ou PDF → a Ollivia/Hub lê a tarifa; prévia simula R$ 0,98 de out/2026) e opção menor de digitar. Fase 2: tarifa por usina no vínculo + leitura de fatura (`ler_fatura`) pelo app |
| 16/11/2026 | Prévia 0.14: **código por WhatsApp ou SMS** (escolha no login, o app lembra; na tela do código, depois de 60 s: "Reenviar por …" e "Não recebeu? Enviar por SMS/WhatsApp"). Motivo: nem todo cliente usa WhatsApp; SMS tem preenchimento automático no iPhone/Android; e o número da Ollivia ainda não está na API oficial do WhatsApp (decisão de 04/11), então o **SMS pode ser o canal principal no começo**. Fase 2: escolher serviço de verificação que faça SMS + WhatsApp (ex.: Twilio Verify, Firebase Authentication, Zenvia) — levantar preços atuais em R$ antes |
| 16/11/2026 | Prévia 0.13: **Perfil completo** (cabeçalho com CPF/celular mascarados e selo Titular; Minhas usinas + dar acesso a familiar; Conta de luz: distribuidora e **minha tarifa**, que passa a valer na Economia; Avisos: 5 tipos + silêncio à noite + receber por App/WhatsApp; Aparência: tema Automático/Claro/Escuro, letras maiores, Face ID, aparelhos conectados; Ajuda e sobre; Sair; Excluir conta). **Serviços em blocos**: cartão da Ollivia com campo de pergunta e atalhos; 4 blocos (Limpeza, Visita técnica, Manutenção preventiva, Relatório); Falar com o pós-venda; Minhas solicitações em cartões com etapas (Recebido → Agendado → Feito / Gerando → Pronto). Barras de rolagem escondidas (no celular elas já não aparecem) |
| 16/11/2026 | Prévia 0.12: telas de configuração do 1º acesso (termos, avisos, Face ID, usina) **escuras**, no mesmo esqueleto (progresso no topo, ilustração animada, título, texto, conteúdo, botões fixos embaixo). **Geração com 5 períodos**: 7 dias · 15 dias · Mês · 12 meses · Escolher período (folha com atalhos 30 dias/3 meses/6 meses e datas De/Até; até 62 dias = dia a dia, acima = mês a mês) |
| 16/11/2026 | Prévia 0.11: **login por CPF/CNPJ do titular + celular** (código pelo WhatsApp só se os dois forem do mesmo cadastro; erro genérico "os dados não conferem", sem revelar se o CPF existe; CPF/CNPJ validado no aparelho; só a versão mascarada fica no app). Pendência do Hub: o vínculo da usina precisa ganhar o campo CPF/CNPJ do titular (puxar do card do Bitrix, como a Ollivia já faz). No início, login do titular; "dar acesso a um familiar" depois |
| 16/11/2026 | Prévia 0.10: **6 telas de boas-vindas** antes do login (Thays pediu pelo menos 5, explicativas): Bem-vindo · Veja a usina gerando · Entenda cada número · Saiba quanto economizou · Avisos na hora certa · Serviços e a Ollivia. Layout fixo: ilustração, título, texto, pontos e botão sempre na mesma altura em todas |
| 16/11/2026 | Prévia 0.9.1: ondas refeitas em canvas (linhas redesenhadas a cada quadro, formato muda: "fio de seda" que abre e fecha), no lugar das linhas que só deslizavam (a Thays achou que pareciam PNG passando) |
| 16/11/2026 | Prévia 0.9: boas-vindas em várias telas de volta (preferência da Thays), com movimento; "Olá de novo!" para quem volta |
| 16/11/2026 | Prévia 0.8: abertura com a logo e transições fluidas em todo o app |
| 16/11/2026 | Prévia 0.7: login enxuto (3 telas no 1º acesso; 1 toque na volta) |
| 16/11/2026 | Prévia 0.6: login completo e troca de usina no topo |
| 16/11/2026 | Texto: usar **"Solicitar"** (não "Pedir") e "Minhas solicitações" no app |
| 16/11/2026 | Prévia 0.5: pedir relatório de geração com período e contas anexadas, em Serviços |
| 16/11/2026 | Prévia 0.4: símbolo = Início; Geração refeita; Serviços com Ollivia no app, pós-venda e pedidos (sem documentos); Economia com mês a mês e retorno |
| 16/11/2026 | Visual D2 escolhido (Hub mais limpo + caminho do sol). Prévia 0.3 com D2 em todas as telas |
| 16/11/2026 | Foco agora: visual e funcionalidades primeiro; técnica depois. Ollem já tem app de carregadores nas duas lojas |
| 16/11/2026 | Nome do app: **Ollem - Minha usina** (loja: "Ollem: Minha Usina Solar"). Prévia 0.2 publicada com o nome |
