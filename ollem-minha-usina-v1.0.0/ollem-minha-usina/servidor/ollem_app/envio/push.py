# -*- coding: utf-8 -*-
"""Notificações no celular pelo Firebase Cloud Messaging (FCM HTTP v1), que entrega no Android e no iPhone (via APNs).
>>> PARA O TI: criar o projeto no Firebase, ligar a chave APNs da Apple nele, baixar o JSON da conta de serviço
>>> (fora do repositório) e preencher FCM_PROJETO e FCM_CREDENCIAIS. Sem isso, os avisos ficam só na central do app."""
import logging, requests
from .. import banco as B, config

log = logging.getLogger('ollem_app')
_cred = None


def _token_acesso():
    global _cred
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
    except ImportError:
        return None
    if _cred is None:
        _cred = service_account.Credentials.from_service_account_file(
            config.FCM_CREDENCIAIS, scopes=['https://www.googleapis.com/auth/firebase.messaging'])
    if not _cred.valid:
        _cred.refresh(Request())
    return _cred.token


def enviar(cliente_id, titulo, texto, dados=None):
    """Manda para todos os aparelhos do cliente. Tokens inválidos são apagados."""
    if not (config.FCM_PROJETO and config.FCM_CREDENCIAIS):
        return 0
    tk = _token_acesso()
    if not tk:
        log.warning('push: instale google-auth para enviar notificações')
        return 0
    url = f'https://fcm.googleapis.com/v1/projects/{config.FCM_PROJETO}/messages:send'
    n = 0
    for t in B.q('SELECT token FROM push_tokens WHERE cliente_id=?', cliente_id):
        r = requests.post(url, timeout=10, headers={'Authorization': f'Bearer {tk}'}, json={'message': {
            'token': t['token'], 'notification': {'title': titulo, 'body': texto},
            'data': {k: str(v) for k, v in (dados or {}).items()}}})
        if r.status_code in (400, 404):
            B.x('DELETE FROM push_tokens WHERE token=?', t['token'])
        elif r.status_code < 300:
            n += 1
    return n
