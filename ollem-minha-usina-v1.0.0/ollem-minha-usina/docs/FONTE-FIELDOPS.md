# Fonte dos dados: Ollem FieldOps — contrato proposto

O servidor do app pergunta tudo ao FieldOps por HTTPS, com `Authorization: Bearer <FIELDOPS_TOKEN>`.
Este é o **contrato proposto**. Se o FieldOps já tiver algo parecido, ajuste só `ROTAS` e `_limpar` em
`servidor/ollem_app/fontes/fieldops.py` — o resto do sistema não muda.

Regras gerais
- `404` = não encontrado (o app trata como "não existe" sem erro). `5xx` = fora do ar (o app mostra "tente de novo").
- Datas `AAAA-MM-DD`; horários em epoch (segundos); energia em kWh; potência em kW/kWp; dinheiro em R$.
- **Nunca** devolver nome do portal do fabricante, login/senha de portal, endereço completo, CPF ou telefone dentro de usina.
- Tempo de resposta alvo: < 1 s (o app espera até `FIELDOPS_TIMEOUT`, padrão 20 s).

---

### 1. Identificar o cliente (login)
`POST /api/app-cliente/clientes/identificar`
```json
{ "doc": "52998224725", "telefone": "22981234567" }
```
- `doc`: CPF (11) ou CNPJ (14) **do titular**, só dígitos. `telefone`: DDD + número, só dígitos, sem 55.
- Responder **200 só se os dois forem do mesmo cadastro**; senão **404** (sem dizer qual dos dois não bateu).
```json
{ "id": "cli-123", "nome": "Maria Silva", "usinas": ["u-1", "u-2"] }
```

### 2. Dados do cliente
`GET /api/app-cliente/clientes/{cliente_id}` → mesmo formato do item 1.

### 3. Usinas do cliente (com geração)
`GET /api/app-cliente/clientes/{cliente_id}/usinas?dias=400`
```json
{ "usinas": [ {
  "id": "u-1",
  "bairro": "Itatiquara",
  "kwp": 14.85,
  "estado": "online",
  "potencia_kw": 4.46,
  "hoje_kwh": 7.2, "mes_kwh": 880.1, "total_kwh": 29298.0,
  "atualizado": 1794831203, "ultimo_online": 1794831203,
  "esperado_meses": [1650,1590,1530,1320,1180,1080,1150,1300,1340,1480,1520,1640],
  "pvgis": null,
  "distribuidora": "Enel Rio", "tarifa": 1.06,
  "investido": 45000,
  "g": { "2026-11-14": 55.4, "2026-11-15": 60.1, "2026-11-16": 7.2 }
} ] }
```
| Campo | Obrigatório | Observação |
|---|---|---|
| `estado` | sim | `online` · `offline` (sem comunicação) · `alarme` (aviso do equipamento) |
| `atualizado` / `ultimo_online` | sim | o app mostra "atualizado às HH:MM" e "sem comunicação desde…" |
| `esperado_meses` | recomendado | kWh/mês do **projeto** (12 valores). Sem ele, o app usa `pvgis` (kWh/kWp/mês) ou estima pelo kWp |
| `g` | sim | geração diária dos últimos `dias` dias; dia sem dado = ausente (não mandar 0) |
| `tarifa` | não | R$/kWh com impostos; se o cliente informar outra no app, a do app vale |
| `investido` | não | R$ do contrato; sem ele o cartão "Retorno do investimento" não aparece |
| `potencia_kw` | não | `null` se o portal não informa |

Sistemas com vários inversores: mandar como **uma usina só** (somada), como já faz o Hub com `sis:`.

### 4. Geração por período
`GET /api/app-cliente/clientes/{cliente_id}/usinas/{usina_id}/geracao?de=2026-01-01&ate=2026-03-31`
→ `{ "g": { "2026-01-01": 72.4, ... } }` · **404** se a usina não for desse cliente.

### 5. Criar solicitação
`POST /api/app-cliente/solicitacoes`
```json
{ "cliente_id": "cli-123", "usina_id": "u-1", "tipo": "limpeza",
  "detalhes": { "periodo": "Manhã", "texto": "", "assunto": "" } }
```
`tipo`: `limpeza` · `visita` · `preventiva` · `outro` · `mensagem` (pós-venda) · `relatorio`.
Para `relatorio`, `detalhes` = `{ "de", "ate", "entrega": ["app","whatsapp"], "contas": [{arquivo, nome_original, tipo}] }`
(os arquivos ficam no servidor do app em `APP_ANEXOS`; combinar com o TI se o FieldOps deve buscá-los ou recebê-los).
Resposta: `{ "id": "os-987" }` (id da ordem de serviço / oportunidade / pedido no FieldOps).

Sugestão de destino no FieldOps: serviços → oportunidade/OS do Pós-Venda; `mensagem` → chamado; `relatorio` → fila de relatórios.

### 6. Situação das solicitações
`GET /api/app-cliente/clientes/{cliente_id}/solicitacoes?ids=os-987,os-988`
```json
{ "situacoes": { "os-987": "agendado", "os-988": "pronto" } }
```
Estados aceitos: `recebido` · `agendado` · `feito` · `gerando` · `pronto` · `respondido` · `cancelado`.
(Alternativa: o FieldOps avisa o app por `POST /api/app/v1/interno/solicitacoes/{id}/estado` — ver API.md.)

### 7. PDF do relatório pronto
`GET /api/app-cliente/solicitacoes/{id}/arquivo` → `application/pdf` (404 se ainda não estiver pronto).

### 8. Cliente excluiu a conta do app (opcional)
`POST /api/app-cliente/clientes/{cliente_id}/excluir-app` → `{ "ok": true }`. Só registro; a usina continua monitorada.

---

## Do FieldOps para o app (avisos)
Quando algo acontecer (usina parou, geração baixa, relatório pronto, visita agendada, resumo do mês), o FieldOps chama:
```
POST https://api.app.ollem.com.br/api/app/v1/interno/avisos
X-Token: <APP_TOKEN_INTERNO>
{ "cliente_id": "cli-123", "usina_id": "u-1", "tipo": "parada",
  "titulo": "Sua usina parou de gerar", "texto": "Já avisamos a equipe. Toque para ver." }
```
O aviso fica na central do app e vai para o celular (se o Firebase estiver configurado e o cliente permitiu).
Textos para o cliente: simples, sem números técnicos demais e **sem nome de portal**.
