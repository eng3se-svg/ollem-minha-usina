# Para o TI: como colocar o app no ar

Tudo que depende de conta, chave ou servidor ficou **indicado e pronto para preencher**. Nada disso está no código.
Ordem sugerida (cada etapa funciona sozinha; dá para testar a anterior antes de seguir):

| # | Etapa | Quem | Resultado |
|---|---|---|---|
| 1 | Rodar tudo em demonstração | TI | ver o app e a API funcionando localmente |
| 2 | Expor as rotas no **FieldOps** | TI do FieldOps | dados reais das usinas e das solicitações |
| 3 | Servidor do app 24 h com HTTPS | TI | `https://api.app.ollem.com.br` (exemplo) |
| 4 | Envio do código (SMS) | TI + financeiro | login real |
| 5 | Ollivia no app (chat e leitura da conta) | TI | conversar com a Ollivia dentro do app |
| 6 | Notificações (Firebase) | TI | avisos no celular |
| 7 | App nativo (Capacitor) e lojas | TI | Play Store e App Store |
| 8 | Piloto com ~10 clientes | Ollem | ajustes antes de abrir para todos |

---

## 1. Demonstração local
Veja o README da raiz. Com `APP_FONTE=demo` e `VERIFICACAO=console`, nada sai da máquina.
Testes do servidor: `cd servidor && pytest -q` (login, limites, máscaras, solicitações, tarifa, avisos, exclusão de conta, adaptador do FieldOps).

## 2. FieldOps (fonte dos dados) — **principal pendência**
O app não guarda dados de usina: pergunta tudo ao **Ollem FieldOps**. O adaptador já está escrito em
`servidor/ollem_app/fontes/fieldops.py`, com as rotas que o FieldOps precisa responder **num lugar só** (`ROTAS`).
O contrato completo, com exemplos de pedido e resposta, está em **[FONTE-FIELDOPS.md](FONTE-FIELDOPS.md)**.

- Se o FieldOps já tiver rotas parecidas, **ajuste só o dicionário `ROTAS`** e a função `_limpar`.
- Gerar um **token de serviço** no FieldOps para o servidor do app → `FIELDOPS_TOKEN`.
- Os dados de geração podem continuar vindo do monitoramento do Ollem Hub/Ollivia para o FieldOps; para o app, o
  que importa é o FieldOps responder no formato do contrato.
- O cadastro precisa ter, por cliente: **CPF/CNPJ do titular**, **celular**, e a lista de usinas. Sem isso o cliente não entra.
  (Hoje o monitoramento do Hub ainda não tem CPF no vínculo das usinas.)

## 3. Servidor do app
`servidor/` tem `Dockerfile` e `docker-compose.yml` (API + Caddy com HTTPS automático).
```bash
cd servidor
cp .env.exemplo .env          # preencher (ver tabela abaixo) — nunca subir o .env
docker compose up -d --build
curl https://api.app.ollem.com.br/api/app/v1/saude
```
Com `APP_PRODUCAO=1` o servidor **se recusa a iniciar** se faltar algo essencial (segredo, token do FieldOps,
ou se ainda estiver em demonstração/console). Banco: SQLite em `/dados/app.db` (volume `dados-producao/`). Fazer **backup diário** desse volume.

| Variável | O que é |
|---|---|
| `APP_SEGREDO` | 64 caracteres aleatórios. Embaralha CPF/telefone no banco. **Nunca trocar depois de no ar** (invalida os logins). |
| `APP_FONTE` / `FIELDOPS_URL` / `FIELDOPS_TOKEN` | Fonte dos dados (etapa 2). |
| `APP_TOKEN_INTERNO` | Token que o FieldOps/Hub usam para mandar avisos aos clientes (`/interno/*`). |
| `APP_ORIGENS` | Origens liberadas (CORS): `capacitor://localhost`, `https://localhost` e o domínio web, se houver. |
| `VERIFICACAO`, `CANAIS_CODIGO`, `TWILIO_*` / `ZENVIA_*` | Envio do código (etapa 4). |
| `REVISOR_DOC`, `REVISOR_TEL`, `REVISOR_CODIGO` | Conta de demonstração para a revisão das lojas (etapa 7). |
| `OLLIVIA_URL`, `OLLIVIA_TOKEN` | Ollivia (etapa 5). |
| `FCM_PROJETO`, `FCM_CREDENCIAIS` | Firebase (etapa 6). |

## 4. Código de acesso (SMS / WhatsApp)
O login é **CPF/CNPJ do titular + celular + código de 6 dígitos**. Escolher um provedor:
- **Twilio Verify** (`VERIFICACAO=twilio`): gera, envia e confere o código; faz SMS e WhatsApp na mesma conta.
- **Zenvia** (`VERIFICACAO=zenvia`): empresa brasileira; aqui usado só para SMS.
- **Firebase Authentication** (telefone) também serve, mas exigiria trocar o fluxo no app; não foi implementado.

Levantar os preços atuais em R$ antes de contratar. O volume é baixo: com o Face ID ligado, o cliente quase não pede código.

**WhatsApp:** só ligar (`CANAIS_CODIGO=sms,whatsapp`) depois que o número da Ollivia **(22) 3199-0081** estiver na
API oficial do WhatsApp com uma mensagem-modelo de autenticação aprovada (decisão de 04/11/2026: o número ainda não foi migrado).
Enquanto isso, o app mostra as duas opções, mas o servidor manda por SMS.

## 5. Ollivia no app
O servidor do app conversa com o servidor da Ollivia (repositório `eng3se-svg/ollivia`) usando o mesmo `HUB_TOKEN`:
- **Leitura da conta de luz**: usa a rota que **já existe** `POST /api/monitor/ler_fatura`. Nada a fazer além de configurar.
- **Chat no app**: precisa de uma rota **nova** na Ollivia: `POST /api/app/chat`
  - entrada: `{cliente_id, nome, usinas:[{id,bairro,kwp,estado,hoje_kwh,mes_kwh}], historico:[{de:'eu'|'ollivia', txt}], texto}`
  - saída: `{resposta: "texto"}`
  - sugestão: reaproveitar o `cerebro` da Ollivia com o canal "app" (mesmo manual, mesmas regras: não citar portal,
    linguagem simples, transferir para a equipe quando necessário). Fazer por ramo + PR no repositório da Ollivia.
- Sem `OLLIVIA_URL`, o app responde "fale com a Ollivia pelo WhatsApp" (não quebra).

## 6. Notificações (avisos no celular)
1. Criar projeto no **Firebase** e adicionar os apps Android (`br.com.ollem.minhausina`) e iOS.
2. Subir a **chave APNs** (Apple Developer → Keys) no Firebase.
3. Baixar a conta de serviço (JSON) → `servidor/segredos/` (fora do Git) → `FCM_CREDENCIAIS` e `FCM_PROJETO`.
4. Colocar `google-services.json` (Android) e `GoogleService-Info.plist` (iOS) nos projetos nativos (fora do Git).
5. Quem dispara os avisos é o FieldOps (ou o Hub): `POST /api/app/v1/interno/avisos` com `X-Token: APP_TOKEN_INTERNO`
   (usina parada, geração abaixo do esperado, relatório pronto, visita agendada, resumo do mês). Ver [API.md](API.md).

## 7. App nativo e lojas
```bash
cd app
npm install
echo "VITE_API_URL=https://api.app.ollem.com.br" > .env.production
npx cap add android && npx cap add ios        # primeira vez
npm run cap:sync                               # a cada versão
npm run cap:android   |   npm run cap:ios      # abre no Android Studio / Xcode (Xcode precisa de Mac)
```
- **Identificador:** `br.com.ollem.minhausina` · **Nome na loja:** "Ollem: Minha Usina Solar" · **Nome no ícone:** "Ollem".
- **Ícone e tela de abertura:** usar o símbolo da Ollem sobre `#0c100e` (gerar com `@capacitor/assets`).
- **Face ID / digital:** instalar um plugin de biometria (ex.: `@aparajita/capacitor-biometric-auth`) e chamar antes de
  liberar a sessão guardada (ponto marcado em `app/src/views/Login.vue`, função `faceId`). No iOS, incluir
  `NSFaceIDUsageDescription` no Info.plist.
- **Sessão no aparelho:** hoje em `@capacitor/preferences`; recomendado trocar por cofre seguro (Keychain/Keystore) — `app/src/nativo.js`.
- **Widget "geração de hoje"** (ajuda na aprovação da Apple): código nativo (Swift/WidgetKit e Kotlin), lendo `GET /usinas`. Ainda não feito.
- **Contas de desenvolvedor:** a Ollem já publica o app *Ollem Energy* (`com.ollem.energy`) — usar as mesmas contas (CNPJ).
- **Exigências:** política de privacidade publicada (URL), **exclusão de conta dentro do app** (já existe em Perfil),
  conta de demonstração para o revisor (`REVISOR_*`, que precisa existir na fonte), rótulos de privacidade.

## 8. Piloto
Escolher ~10 clientes com cadastro completo no FieldOps (CPF/CNPJ + celular + usinas), mistura de portais, um com mais
de uma usina e um com problema conhecido. Distribuir pela versão de teste das lojas (TestFlight / teste interno do Google Play).

---

## Onde mexer no código
| Quero… | Arquivo |
|---|---|
| Ajustar as rotas do FieldOps | `servidor/ollem_app/fontes/fieldops.py` (`ROTAS`, `_limpar`) |
| Trocar o provedor de SMS | `servidor/ollem_app/envio/codigo.py` |
| Mudar regras do login (validade, tentativas, limites) | `.env` (`CODIGO_*`, `ENVIOS_*`, `SESSAO_DIAS`) e `servidor/ollem_app/acesso.py` |
| Ver todas as rotas | `servidor/ollem_app/api.py` e [API.md](API.md) |
| Cálculo do esperado, alertas e economia no app | `app/src/lib/calc.js` |
| Chamadas do app ao servidor | `app/src/api.js` |
| Recursos do celular (sessão, notificações) | `app/src/nativo.js` |

## Pendências conhecidas (o que ainda não está pronto)
- Rotas no **FieldOps** (etapa 2) e **CPF/CNPJ do titular** no cadastro das usinas.
- Rota `POST /api/app/chat` na **Ollivia** (etapa 5).
- **Central de avisos** no app (a API `/avisos` existe; falta a tela do sino).
- **Biometria nativa**, **widget** e **ícone/tela de abertura nativos** (etapa 7).
- **Convite de familiar**: a API registra; falta enviar o convite e criar o acesso só-leitura.
- Fator de **CO₂** do SIN no app é provisório (0,0385 kg/kWh, em `app/src/lib/calc.js`) — conferir o valor oficial atual.
- Curva **hora a hora** do dia: depende de a fonte enviar potência ao longo do dia.
