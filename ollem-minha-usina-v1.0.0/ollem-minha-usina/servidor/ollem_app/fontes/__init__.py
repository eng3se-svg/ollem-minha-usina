# -*- coding: utf-8 -*-
from .. import config

_fonte = None


def fonte():
    """Fonte escolhida em APP_FONTE (demo | fieldops)."""
    global _fonte
    if _fonte is None:
        if config.FONTE == 'fieldops':
            from .fieldops import FonteFieldOps
            _fonte = FonteFieldOps()
        else:
            if config.PRODUCAO:
                raise RuntimeError('APP_FONTE=demo não é permitido em produção')
            from .demo import FonteDemo
            _fonte = FonteDemo()
    return _fonte


def definir(f):            # testes
    global _fonte
    _fonte = f
