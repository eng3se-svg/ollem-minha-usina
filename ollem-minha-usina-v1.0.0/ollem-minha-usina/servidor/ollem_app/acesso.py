# -*- coding: utf-8 -*-
"""Login do cliente: CPF/CNPJ do titular + celular + código de 6 dígitos (SMS ou WhatsApp) → sessão.

Regras de segurança:
- o código só sai se CPF/CNPJ e celular forem do MESMO cadastro na fonte; a resposta para "não confere" é genérica;
- código guardado só como resumo (hash), vale CODIGO_VALIDADE_MIN minutos e aceita CODIGO_TENTATIVAS tentativas;
- limite de envios por CPF+celular e por IP (evita custo de SMS e ataques);
- a sessão é um token aleatório; no banco fica só o resumo dele. CPF e celular nunca são gravados em texto.
"""
import secrets, time
from . import banco as B, config, identidade as I
from .envio.codigo import envio
from .fontes import fonte


class Recusa(Exception):
    def __init__(self, codigo, msg, http=400):
        super().__init__(msg)
        self.codigo, self.msg, self.http = codigo, msg, http


def _revisor(doc, tel):
    return bool(config.REVISOR_DOC and config.REVISOR_TEL and config.REVISOR_CODIGO
                and doc == I.digitos(config.REVISOR_DOC) and tel == I.tel_normal(config.REVISOR_TEL))


def pedir_codigo(doc, telefone, canal, ip=''):
    doc, tel = I.digitos(doc), I.tel_normal(telefone)
    canal = 'whatsapp' if canal in ('whats', 'whatsapp') else 'sms'
    if not I.doc_valido(doc):
        raise Recusa('doc_invalido', 'Confira o CPF ou CNPJ.')
    if not tel:
        raise Recusa('telefone_invalido', 'Confira o celular, com DDD.')
    if canal not in config.CANAIS:
        canal = config.CANAIS[0]
    ch = I.chave('login', doc, tel)
    hora = time.time() - 3600
    if B.um('SELECT COUNT(*) n FROM codigos WHERE chave=? AND criado>?', ch, hora)['n'] >= config.ENVIOS_POR_HORA or \
       (ip and B.um('SELECT COUNT(*) n FROM codigos WHERE ip=? AND criado>?', ip, hora)['n'] >= config.ENVIOS_POR_HORA_IP):
        raise Recusa('muitas_tentativas', 'Muitos pedidos de código. Tente de novo em alguns minutos.', 429)

    revisor = _revisor(doc, tel)
    if not revisor and not fonte().buscar_cliente(doc, tel):
        # resposta genérica: não revela se o CPF é cliente nem de quem é o celular
        B.x('INSERT INTO codigos(chave, codigo_hash, canal, criado, expira, usado, ip) VALUES(?,?,?,?,?,1,?)',
            ch, '', canal, time.time(), time.time(), ip)
        raise Recusa('dados_nao_conferem', 'Os dados não conferem com o cadastro da Ollem.', 404)

    ev = envio()
    codigo = config.REVISOR_CODIGO if revisor else f'{secrets.randbelow(10 ** 6):06d}'
    if not revisor:
        ev.enviar(tel, canal, None if ev.proprio else codigo)
    B.x('INSERT INTO codigos(chave, codigo_hash, canal, externo, criado, expira, ip) VALUES(?,?,?,?,?,?,?)',
        ch, '' if (ev.proprio and not revisor) else I.resumo(ch + codigo), canal, int(ev.proprio and not revisor),
        time.time(), time.time() + config.CODIGO_VALIDADE_MIN * 60, ip)
    return {'ok': True, 'canal': canal, 'enviado_para': I.masc_tel(tel), 'validade_min': config.CODIGO_VALIDADE_MIN}


def entrar(doc, telefone, codigo, aparelho=''):
    doc, tel, codigo = I.digitos(doc), I.tel_normal(telefone), I.digitos(codigo)
    ch = I.chave('login', doc, tel)
    c = B.um('SELECT * FROM codigos WHERE chave=? AND usado=0 AND expira>? ORDER BY id DESC LIMIT 1', ch, time.time())
    if not c:
        raise Recusa('codigo_expirado', 'O código expirou. Peça um novo.', 401)
    if c['tentativas'] >= config.CODIGO_TENTATIVAS:
        raise Recusa('muitas_tentativas', 'Muitas tentativas. Peça um novo código.', 429)
    B.x('UPDATE codigos SET tentativas=tentativas+1 WHERE id=?', c['id'])
    ok = envio().conferir(tel, codigo) if c['externo'] else (len(codigo) == 6 and secrets.compare_digest(c['codigo_hash'], I.resumo(ch + codigo)))
    if not ok:
        raise Recusa('codigo_incorreto', 'Código incorreto.', 401)
    B.x('UPDATE codigos SET usado=1 WHERE id=?', c['id'])

    cli = fonte().buscar_cliente(doc, tel)   # o revisor das lojas também precisa existir na fonte (cliente de demonstração)
    if not cli:
        raise Recusa('dados_nao_conferem', 'Os dados não conferem com o cadastro da Ollem.', 404)
    token = secrets.token_urlsafe(32)
    agora = time.time()
    B.x('INSERT INTO sessoes(token_hash, cliente_id, nome, doc_masc, tel_masc, aparelho, criado, visto, expira) VALUES(?,?,?,?,?,?,?,?,?)',
        I.resumo(token), cli['id'], cli.get('nome') or '', I.masc_doc(doc), I.masc_tel(tel), (aparelho or '')[:80],
        agora, agora, agora + config.SESSAO_DIAS * 86400)
    return {'token': token, 'cliente': {'id': cli['id'], 'nome': cli.get('nome') or '', 'doc': I.masc_doc(doc),
                                        'telefone': I.masc_tel(tel), 'usinas': len(cli.get('usinas') or [])}}


def sessao(token):
    if not token:
        return None
    s = B.um('SELECT * FROM sessoes WHERE token_hash=? AND revogada=0 AND expira>?', I.resumo(token), time.time())
    if s and time.time() - (s['visto'] or 0) > 300:
        B.x('UPDATE sessoes SET visto=? WHERE token_hash=?', time.time(), s['token_hash'])
    return s


def sair(token):
    B.x('UPDATE sessoes SET revogada=1 WHERE token_hash=?', I.resumo(token))


def sair_outros(cliente_id, token_atual):
    B.x('UPDATE sessoes SET revogada=1 WHERE cliente_id=? AND token_hash<>?', cliente_id, I.resumo(token_atual))
