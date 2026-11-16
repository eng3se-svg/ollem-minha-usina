# -*- coding: utf-8 -*-
"""CPF/CNPJ e celular: validar, mascarar e embaralhar (HMAC) para guardar sem expor."""
import hashlib, hmac, re
from . import config


def digitos(v):
    return re.sub(r'\D', '', str(v or ''))


def cpf_valido(c):
    if len(c) != 11 or c == c[0] * 11:
        return False
    def dv(n):
        t = sum(int(c[i]) * (n + 1 - i) for i in range(n))
        r = (t * 10) % 11
        return 0 if r == 10 else r
    return dv(9) == int(c[9]) and dv(10) == int(c[10])


def cnpj_valido(c):
    if len(c) != 14 or c == c[0] * 14:
        return False
    p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    p2 = [6] + p1
    def dv(p, n):
        r = sum(int(c[i]) * p[i] for i in range(n)) % 11
        return 0 if r < 2 else 11 - r
    return dv(p1, 12) == int(c[12]) and dv(p2, 13) == int(c[13])


def doc_valido(d):
    return cpf_valido(d) or cnpj_valido(d)


def tel_normal(t):
    """Celular brasileiro só com dígitos, com DDD e sem o 55 (ex.: 22981234567)."""
    d = digitos(t)
    if d.startswith('55') and len(d) in (12, 13):
        d = d[2:]
    return d if len(d) in (10, 11) else ''


def tel_e164(t):
    return '+55' + tel_normal(t)


def masc_doc(d):
    d = digitos(d)
    if len(d) == 11:
        return f'{d[:3]}.•••.•••-{d[9:]}'
    if len(d) == 14:
        return f'{d[:2]}.•••.•••/••••-{d[12:]}'
    return '•••'


def masc_tel(t):
    d = tel_normal(t)
    return f'({d[:2]}) {"9" if len(d) == 11 else ""}••••-{d[-4:]}' if d else '•••'


def chave(*partes):
    """Resumo embaralhado e estável (HMAC-SHA256 com APP_SEGREDO). Não dá para voltar ao CPF/telefone."""
    seg = (config.SEGREDO or 'segredo-de-desenvolvimento').encode()
    return hmac.new(seg, '|'.join(partes).encode(), hashlib.sha256).hexdigest()


def resumo(v):
    return hashlib.sha256(v.encode()).hexdigest()
