# -*- coding: utf-8 -*-
"""Banco próprio do app (SQLite). Guarda só o que é do app: códigos, sessões, solicitações,
preferências, tarifas informadas e tokens de notificação. Os dados das usinas vêm da fonte (FieldOps).
CPF e telefone NUNCA são gravados em texto: só um resumo embaralhado (HMAC) e a versão mascarada."""
import json, os, sqlite3, threading, time
from . import config

_lk = threading.RLock()
_con = None

ESQUEMA = """
CREATE TABLE IF NOT EXISTS codigos (
  id INTEGER PRIMARY KEY AUTOINCREMENT, chave TEXT, codigo_hash TEXT, canal TEXT, externo INTEGER DEFAULT 0,
  criado REAL, expira REAL, tentativas INTEGER DEFAULT 0, usado INTEGER DEFAULT 0, ip TEXT);
CREATE INDEX IF NOT EXISTS i_codigos ON codigos(chave, criado);
CREATE TABLE IF NOT EXISTS sessoes (
  token_hash TEXT PRIMARY KEY, cliente_id TEXT, nome TEXT, doc_masc TEXT, tel_masc TEXT, aparelho TEXT,
  criado REAL, visto REAL, expira REAL, revogada INTEGER DEFAULT 0);
CREATE INDEX IF NOT EXISTS i_sessoes ON sessoes(cliente_id);
CREATE TABLE IF NOT EXISTS solicitacoes (
  id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id TEXT, usina_id TEXT, tipo TEXT, detalhes TEXT, estado TEXT DEFAULT 'recebido',
  externo_id TEXT DEFAULT '', erro TEXT DEFAULT '', criado REAL, atualizado REAL);
CREATE INDEX IF NOT EXISTS i_solic ON solicitacoes(cliente_id);
CREATE TABLE IF NOT EXISTS push_tokens (token TEXT PRIMARY KEY, cliente_id TEXT, plataforma TEXT, criado REAL);
CREATE TABLE IF NOT EXISTS preferencias (cliente_id TEXT PRIMARY KEY, dados TEXT, atualizado REAL);
CREATE TABLE IF NOT EXISTS tarifas (cliente_id TEXT, usina_id TEXT, valor REAL, origem TEXT, referencia TEXT, criado REAL,
  PRIMARY KEY (cliente_id, usina_id));
CREATE TABLE IF NOT EXISTS familiares (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id TEXT, nome TEXT, tel_chave TEXT,
  tel_masc TEXT, estado TEXT DEFAULT 'convidado', criado REAL);
CREATE TABLE IF NOT EXISTS avisos (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id TEXT, usina_id TEXT, tipo TEXT,
  titulo TEXT, texto TEXT, lido INTEGER DEFAULT 0, criado REAL);
CREATE INDEX IF NOT EXISTS i_avisos ON avisos(cliente_id, criado);
CREATE TABLE IF NOT EXISTS exclusoes (cliente_id TEXT, criado REAL);
"""


def con():
    global _con
    with _lk:
        if _con is None:
            if config.BANCO != ':memory:':
                os.makedirs(os.path.dirname(config.BANCO), exist_ok=True)
            _con = sqlite3.connect(config.BANCO, check_same_thread=False)
            _con.row_factory = sqlite3.Row
            _con.execute('PRAGMA journal_mode=WAL')
            _con.executescript(ESQUEMA)
        return _con


def reiniciar():                     # usado nos testes
    global _con
    with _lk:
        if _con is not None:
            _con.close()
        _con = None


def x(sql, *a):
    with _lk:
        c = con().execute(sql, a)
        con().commit()
        return c.lastrowid


def q(sql, *a):
    with _lk:
        return [dict(r) for r in con().execute(sql, a).fetchall()]


def um(sql, *a):
    r = q(sql, *a)
    return r[0] if r else None


def agora():
    return time.time()


def jdump(v):
    return json.dumps(v, ensure_ascii=False)


def jload(s, padrao=None):
    try:
        return json.loads(s) if s else padrao
    except ValueError:
        return padrao
