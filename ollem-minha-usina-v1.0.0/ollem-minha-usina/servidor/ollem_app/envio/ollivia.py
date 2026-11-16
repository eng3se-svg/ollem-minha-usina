# -*- coding: utf-8 -*-
"""Conversa com o servidor da Ollivia (assistente da Ollem).
- ler_fatura: usa a rota que JÁ EXISTE na Ollivia (/api/monitor/ler_fatura).
- conversar: usa uma rota NOVA que precisa ser criada na Ollivia (/api/app/chat). Ver docs/PARA-O-TI.md, item "Ollivia".
Autenticação: cabeçalho X-Token = HUB_TOKEN da Ollivia (OLLIVIA_TOKEN aqui)."""
import base64, requests
from .. import config


def configurada():
    return bool(config.OLLIVIA_URL and config.OLLIVIA_TOKEN)


def _post(caminho, j, timeout=60):
    r = requests.post(config.OLLIVIA_URL + caminho, json=j, timeout=timeout,
                      headers={'X-Token': config.OLLIVIA_TOKEN, 'X-Atendente': 'App%20Minha%20usina'})
    r.raise_for_status()
    return r.json()


def conversar(cliente, usinas_resumo, historico, texto):
    """historico: [{'de': 'eu'|'ollivia', 'txt': str}] das últimas mensagens."""
    j = _post('/api/app/chat', {'cliente_id': cliente['id'], 'nome': cliente.get('nome'), 'usinas': usinas_resumo,
                                'historico': historico[-20:], 'texto': texto})
    return j.get('resposta') or ''


def ler_fatura(arquivo: bytes, nome: str):
    j = _post('/api/monitor/ler_fatura', {'arquivo_b64': base64.b64encode(arquivo).decode(), 'nome': nome}, timeout=120)
    return j.get('faturas') or []
