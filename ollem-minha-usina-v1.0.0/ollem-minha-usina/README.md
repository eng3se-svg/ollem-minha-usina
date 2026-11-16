# Ollem - Minha usina

App da **Ollem do Brasil** para o cliente acompanhar a própria usina solar: geração do dia, gráficos, economia em reais,
avisos, serviços (limpeza, visita, relatório) e conversa com a Ollivia.

Um código só para **iPhone, Android e web**: Vue 3 + Vite, empacotado com **Capacitor**.
O servidor (Python/Flask) cuida do login, dos dados e das solicitações, e busca as informações no **Ollem FieldOps**.

```
app/        aplicativo (Vue 3 + Capacitor)       → app/README.md
servidor/   API do app  /api/app/v1  (Flask)     → servidor/README.md
docs/       documentação para o TI               → comece por docs/PARA-O-TI.md
```

## Rodar em 2 minutos (modo demonstração, sem nenhuma chave)

```bash
# servidor (fonte de demonstração + código de acesso no console)
cd servidor && pip install -r requirements-dev.txt && pytest -q && python wsgi.py     # http://127.0.0.1:8090

# app ligado ao servidor local
cd app && npm install && echo "VITE_API_URL=http://127.0.0.1:8090" > .env.local && npm run dev
```

Login de demonstração: CPF **529.982.247-25** · celular **(22) 98123-4567** · o código aparece no terminal do servidor.
Sem `VITE_API_URL`, o app roda sozinho com dados fictícios (é o modo usado nas prévias).

## Documentação
| Arquivo | Para quê |
|---|---|
| [docs/PARA-O-TI.md](docs/PARA-O-TI.md) | **Passo a passo para colocar no ar** (servidor, FieldOps, SMS, Firebase, lojas) |
| [docs/FONTE-FIELDOPS.md](docs/FONTE-FIELDOPS.md) | O que o FieldOps precisa responder (contrato proposto) |
| [docs/API.md](docs/API.md) | Todas as rotas do servidor do app |
| [docs/SEGURANCA-E-LGPD.md](docs/SEGURANCA-E-LGPD.md) | Regras de segurança e proteção de dados |
| [docs/DECISOES.md](docs/DECISOES.md) | Decisões de produto e visual já tomadas (histórico das prévias) |

## Regras que não podem ser quebradas
- O cliente vê **só as usinas dele** (CPF/CNPJ + celular do mesmo cadastro).
- **Nenhum segredo no repositório** (`.env`, chaves, certificados). Use `.env.exemplo` como modelo.
- O app **nunca** fala com portais de fabricante e **nunca** mostra o nome do portal (SolisCloud, FusionSolar etc.).
- Textos em português do Brasil, simples, sem jargão. Usar **"Solicitar"** (não "Pedir").
