# -*- coding: utf-8 -*-
"""Fonte de DEMONSTRAÇÃO: 3 usinas fictícias (dados derivados de usinas reais, alterados e sem identificação).
Cliente de teste: CPF 529.982.247-25 · celular (22) 98123-4567. Bloqueada com APP_PRODUCAO=1."""
import itertools, json, os, time
from .base import Fonte, ClienteFonte
from .. import config

_ARQ = os.path.join(config.RAIZ, 'dados', 'demo.json')
_seq = itertools.count(1)


class FonteDemo(Fonte):
    nome = 'demo'

    def __init__(self):
        with open(_ARQ, encoding='utf-8') as f:
            d = json.load(f)
        self.clientes = {c['id']: c for c in d['clientes']}
        self.usinas_ = {u['id']: u for u in d['usinas']}
        self.pedidos = {}

    def buscar_cliente(self, doc, telefone):
        for c in self.clientes.values():
            if c['doc'] == doc and c['telefone'] == telefone:
                return ClienteFonte(id=c['id'], nome=c['nome'], usinas=list(c['usinas']))
        return None

    def cliente(self, cliente_id):
        c = self.clientes.get(cliente_id)
        return ClienteFonte(id=c['id'], nome=c['nome'], usinas=list(c['usinas'])) if c else None

    def _minhas(self, cliente_id):
        c = self.clientes.get(cliente_id)
        return c['usinas'] if c else []

    def usinas(self, cliente_id, dias):
        out = []
        for uid in self._minhas(cliente_id):
            u = dict(self.usinas_[uid])
            datas = sorted(u['g'])[-dias:]
            u['g'] = {k: u['g'][k] for k in datas}
            out.append(u)
        return out

    def geracao(self, cliente_id, usina_id, de, ate):
        if usina_id not in self._minhas(cliente_id):
            return None
        return {k: v for k, v in self.usinas_[usina_id]['g'].items() if de <= k <= ate}

    def registrar_solicitacao(self, cliente_id, usina_id, tipo, detalhes):
        i = f'demo-{next(_seq)}'
        self.pedidos[i] = {'tipo': tipo, 'criado': time.time()}
        return i

    def situacao_solicitacoes(self, cliente_id, ids_externos):
        return {i: 'recebido' for i in ids_externos if i in self.pedidos}
