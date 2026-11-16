# -*- coding: utf-8 -*-
"""Confere o adaptador do FieldOps com respostas simuladas (sem rede)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ollem_app.fontes.fieldops import FonteFieldOps, ErroFonte


class Resp:
    def __init__(self, status, j=None, content=b'x'):
        self.status_code, self._j, self.content = status, j, content

    def json(self):
        return self._j


class SessaoFalsa:
    def __init__(self, respostas):
        self.headers, self.resp, self.chamadas = {}, respostas, []

    def request(self, metodo, url, **kw):
        self.chamadas.append((metodo, url, kw))
        return self.resp.pop(0)


def test_identificar_e_usinas():
    s = SessaoFalsa([Resp(200, {'id': 77, 'nome': 'Fulano', 'usinas': [1, 2]}),
                     Resp(200, {'usinas': [{'id': 1, 'kwp': 5, 'portal': 'solis', 'login': 'x', 'g': {'2026-11-01': 20}}]})])
    f = FonteFieldOps(sessao=s)
    c = f.buscar_cliente('52998224725', '22981234567')
    assert c == {'id': '77', 'nome': 'Fulano', 'usinas': ['1', '2']}
    assert s.chamadas[0][0] == 'POST' and s.chamadas[0][1].endswith('/api/app-cliente/clientes/identificar')
    u = f.usinas('77', 400)[0]
    assert u['id'] == '1' and 'portal' not in u and 'login' not in u      # nada do fabricante passa para o app


def test_nao_encontrado_e_erro():
    f = FonteFieldOps(sessao=SessaoFalsa([Resp(404), Resp(500)]))
    assert f.buscar_cliente('1', '2') is None
    try:
        f.cliente('1')
        assert False
    except ErroFonte:
        pass
