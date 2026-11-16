# -*- coding: utf-8 -*-
"""Fonte OLLEM FIELDOPS (fieldops.ollem.com.br).

>>> PARA O TI: os caminhos abaixo são o CONTRATO PROPOSTO. O FieldOps precisa expor estas rotas
>>> (ou o TI ajusta o mapeamento aqui, em um só lugar). Detalhes, exemplos e respostas esperadas
>>> em docs/FONTE-FIELDOPS.md.

Autenticação: cabeçalho  Authorization: Bearer <FIELDOPS_TOKEN>  (token de serviço, só no servidor).
"""
import base64, requests
from .base import Fonte, ClienteFonte
from .. import config

ROTAS = {
    'buscar_cliente': ('POST', '/api/app-cliente/clientes/identificar'),   # {doc, telefone} -> {id, nome, usinas:[ids]} | 404
    'cliente':        ('GET',  '/api/app-cliente/clientes/{cliente_id}'),  # -> {id, nome, usinas:[ids]}
    'usinas':         ('GET',  '/api/app-cliente/clientes/{cliente_id}/usinas'),            # ?dias=400 -> {usinas:[USINA]}
    'geracao':        ('GET',  '/api/app-cliente/clientes/{cliente_id}/usinas/{usina_id}/geracao'),  # ?de&ate -> {g:{...}}
    'solicitar':      ('POST', '/api/app-cliente/solicitacoes'),           # {cliente_id, usina_id, tipo, detalhes} -> {id}
    'situacao':       ('GET',  '/api/app-cliente/clientes/{cliente_id}/solicitacoes'),       # ?ids=a,b -> {situacoes:{id: estado}}
    'relatorio_pdf':  ('GET',  '/api/app-cliente/solicitacoes/{id}/arquivo'),                # -> application/pdf
    'excluir':        ('POST', '/api/app-cliente/clientes/{cliente_id}/excluir-app'),        # -> {ok}
}


class ErroFonte(Exception):
    pass


class FonteFieldOps(Fonte):
    nome = 'fieldops'

    def __init__(self, sessao=None):
        self.s = sessao or requests.Session()
        self.s.headers.update({'Authorization': f'Bearer {config.FIELDOPS_TOKEN}', 'Accept': 'application/json',
                               'User-Agent': 'OllemMinhaUsina/1.0'})

    def _req(self, rota, json=None, params=None, bruto=False, **campos):
        metodo, caminho = ROTAS[rota]
        url = config.FIELDOPS_URL + caminho.format(**campos)
        try:
            r = self.s.request(metodo, url, json=json, params=params, timeout=config.FIELDOPS_TIMEOUT)
        except requests.RequestException as e:
            raise ErroFonte(f'FieldOps fora do ar: {e}') from e
        if r.status_code == 404:
            return None
        if r.status_code >= 400:
            raise ErroFonte(f'FieldOps respondeu {r.status_code} em {rota}')
        return r.content if bruto else (r.json() if r.content else {})

    @staticmethod
    def _cli(j):
        return ClienteFonte(id=str(j['id']), nome=j.get('nome') or '', usinas=[str(u) for u in j.get('usinas', [])]) if j else None

    def buscar_cliente(self, doc, telefone):
        return self._cli(self._req('buscar_cliente', json={'doc': doc, 'telefone': telefone}))

    def cliente(self, cliente_id):
        return self._cli(self._req('cliente', cliente_id=cliente_id))

    def usinas(self, cliente_id, dias):
        j = self._req('usinas', params={'dias': dias}, cliente_id=cliente_id) or {}
        return [_limpar(u) for u in j.get('usinas', [])]

    def geracao(self, cliente_id, usina_id, de, ate):
        j = self._req('geracao', params={'de': de, 'ate': ate}, cliente_id=cliente_id, usina_id=usina_id)
        return None if j is None else {k: v for k, v in (j.get('g') or {}).items()}

    def registrar_solicitacao(self, cliente_id, usina_id, tipo, detalhes):
        j = self._req('solicitar', json={'cliente_id': cliente_id, 'usina_id': usina_id, 'tipo': tipo, 'detalhes': detalhes}) or {}
        return str(j.get('id') or '')

    def situacao_solicitacoes(self, cliente_id, ids_externos):
        if not ids_externos:
            return {}
        j = self._req('situacao', params={'ids': ','.join(ids_externos)}, cliente_id=cliente_id) or {}
        return j.get('situacoes') or {}

    def anexo_relatorio(self, cliente_id, id_externo):
        b = self._req('relatorio_pdf', bruto=True, id=id_externo)
        return (b, f'relatorio-{id_externo}.pdf') if b else None

    def excluir_conta(self, cliente_id):
        self._req('excluir', json={}, cliente_id=cliente_id)


# Campos que o app aceita. Qualquer outro (ex.: portal, login do fabricante, endereço completo) é descartado aqui.
CAMPOS = ('id', 'nome', 'bairro', 'kwp', 'estado', 'potencia_kw', 'hoje_kwh', 'mes_kwh', 'total_kwh', 'atualizado',
          'ultimo_online', 'esperado_meses', 'pvgis', 'distribuidora', 'tarifa', 'investido', 'g', 'geo_aprox')


def _limpar(u):
    u = {k: u.get(k) for k in CAMPOS if k in u}
    u['id'] = str(u.get('id'))
    u['g'] = u.get('g') or {}
    return u
