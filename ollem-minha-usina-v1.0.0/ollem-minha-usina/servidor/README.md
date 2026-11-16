# Servidor do app (Flask) · `/api/app/v1`

```bash
pip install -r requirements-dev.txt
pytest -q                   # 14 testes (login, segurança, usinas, solicitações, tarifa, avisos, conta, FieldOps)
python wsgi.py              # http://127.0.0.1:8090  (demonstração: APP_FONTE=demo, VERIFICACAO=console)
```
Produção: `cp .env.exemplo .env`, preencher e `docker compose up -d --build` (ver ../docs/PARA-O-TI.md).

| Pasta/arquivo | O que tem |
|---|---|
| `ollem_app/api.py` | rotas e criação do app Flask |
| `ollem_app/acesso.py` | login (CPF/CNPJ + celular + código), sessões, limites |
| `ollem_app/fontes/` | `base.py` (contrato), `fieldops.py` (produção), `demo.py` (testes) |
| `ollem_app/envio/` | código por SMS/WhatsApp, notificações (Firebase), Ollivia |
| `ollem_app/banco.py` | SQLite do app (sem CPF/telefone em texto) |
| `dados/demo.json` | 3 usinas fictícias para demonstração |
