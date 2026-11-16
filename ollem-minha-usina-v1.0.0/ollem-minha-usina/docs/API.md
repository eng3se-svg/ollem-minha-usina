# API do app · `/api/app/v1`

JSON em UTF-8. Erros: `{"erro": "mensagem para o cliente", "codigo": "codigo_curto"}` com o status HTTP adequado.
Rotas marcadas 🔒 exigem `Authorization: Bearer <token>` (recebido no login). Rotas `/interno/*` exigem `X-Token: <APP_TOKEN_INTERNO>`.

## Login
| Método | Rota | Corpo | Resposta |
|---|---|---|---|
| POST | `/login/codigo` | `{doc, telefone, canal: "sms"\|"whatsapp"}` | `{ok, canal, enviado_para: "(22) 9••••-4567", validade_min}` |
| POST | `/login/entrar` | `{doc, telefone, codigo, aparelho}` | `{token, cliente: {id, nome, doc, telefone, usinas}}` (doc e telefone mascarados) |
| POST 🔒 | `/sair` | — | `{ok}` |
| POST 🔒 | `/sair-outros` | — | `{ok}` desconecta os outros aparelhos |
| GET 🔒 | `/eu` | — | `{cliente, aparelhos: [{aparelho, criado, visto}]}` |

Códigos de erro do login: `doc_invalido` (400), `telefone_invalido` (400), `dados_nao_conferem` (404, genérico),
`muitas_tentativas` (429), `codigo_expirado` (401), `codigo_incorreto` (401), `fonte` (503, FieldOps fora do ar).

## Usinas
| Método | Rota | Resposta |
|---|---|---|
| GET 🔒 | `/usinas` | `{usinas: [USINA], gerado_em}` — formato em FONTE-FIELDOPS.md, com `tarifa`, `tarifa_origem` (`media`\|`conta`\|`digitada`) e `tarifa_referencia` |
| GET 🔒 | `/usinas/{id}/geracao?de=AAAA-MM-DD&ate=AAAA-MM-DD` | `{g: {data: kWh}}` (máximo 2 anos; 404 se a usina não for do cliente) |

## Solicitações
| Método | Rota | Corpo | Resposta |
|---|---|---|---|
| POST 🔒 | `/solicitacoes` | `{tipo: limpeza\|visita\|preventiva\|outro\|mensagem, usina_id, periodo, texto, assunto}` | `{ok, id}` |
| POST 🔒 | `/relatorios` | multipart: `usina_id, de, ate, entrega="app,whatsapp", contas[]` (PDF/foto, até 15 MB cada, até 12) | `{ok, id, contas}` |
| GET 🔒 | `/solicitacoes` | — | `{solicitacoes: [{id, tipo, titulo, usina_id, estado, criado, detalhes, contas, pdf}]}` |
| GET 🔒 | `/solicitacoes/{id}/pdf` | — | PDF do relatório pronto |

Se o FieldOps estiver fora do ar na hora, a solicitação fica guardada no app com erro e aparece em `/interno/pendentes`.

## Ollivia e conta de luz
| Método | Rota | Corpo | Resposta |
|---|---|---|---|
| POST 🔒 | `/chat` | `{texto, historico: [{de, txt}]}` | `{resposta}` (sem Ollivia configurada: orienta ir ao WhatsApp) |
| POST 🔒 | `/conta-de-luz` | multipart: `usina_id, arquivo` | `{ok, tarifa, referencia}` — a Ollivia lê a conta |
| PUT 🔒 | `/tarifa` | `{usina_id, valor: "0,98"}` (vazio = volta à média) | `{ok, tarifa}` — aceita R$ 0,30 a 3,00/kWh |

## Preferências, avisos, família e conta
| Método | Rota | Corpo | Resposta |
|---|---|---|---|
| GET/PUT 🔒 | `/preferencias` | `{push:{parada,abaixo,mensal,relatorio,visita}, silencio, canais:{app,whats}, tema, texto_grande, biometria}` | `{ok}` |
| POST 🔒 | `/push/registrar` | `{token, plataforma: ios\|android\|web}` | `{ok}` |
| GET 🔒 | `/avisos` | — | `{avisos: [{id, usina_id, tipo, titulo, texto, lido, criado}]}` |
| POST 🔒 | `/avisos/lidos` | — | `{ok}` |
| POST 🔒 | `/familiares` | `{nome, telefone}` | `{ok, id}` (envio do convite: pendente) |
| DELETE 🔒 | `/conta` | — | `{ok}` apaga sessões, aparelhos, preferências, tarifas, familiares e avisos do app |

## Internas (FieldOps / Hub → app)
| Método | Rota | Corpo |
|---|---|---|
| POST | `/interno/avisos` | `{cliente_id, usina_id?, tipo, titulo, texto}` → grava na central e envia notificação |
| POST | `/interno/solicitacoes/{id}/estado` | `{estado: recebido\|agendado\|feito\|gerando\|pronto\|respondido\|cancelado}` |
| GET | `/interno/pendentes` | solicitações que não chegaram ao FieldOps |

## Outras
`GET /saude` → `{ok, fonte, canais, versao}` (monitoramento do servidor).
