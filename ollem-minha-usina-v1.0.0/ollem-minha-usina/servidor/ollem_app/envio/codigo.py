# -*- coding: utf-8 -*-
"""Envio do código de acesso por SMS ou WhatsApp.

- console : só para desenvolvimento; escreve o código no log (bloqueado em produção).
- twilio  : Twilio Verify. O próprio Twilio gera, envia (SMS ou WhatsApp) e confere o código.
- zenvia  : Zenvia (Brasil). Só SMS; o código é gerado e conferido por este servidor.
>>> PARA O TI: confira os endpoints na documentação atual do provedor escolhido antes de ligar em produção.
"""
import logging, requests
from .. import config, identidade

log = logging.getLogger('ollem_app')


class Envio:
    proprio = False          # True = o provedor gera e confere o código (ex.: Twilio Verify)

    def enviar(self, telefone, canal, codigo=None):
        raise NotImplementedError

    def conferir(self, telefone, codigo):
        raise NotImplementedError


class Console(Envio):
    ultimo = {}

    def enviar(self, telefone, canal, codigo=None):
        if config.PRODUCAO:
            raise RuntimeError('VERIFICACAO=console bloqueado em produção')
        Console.ultimo[identidade.tel_normal(telefone)] = codigo
        log.warning('[DESENVOLVIMENTO] código %s para %s por %s', codigo, identidade.masc_tel(telefone), canal)


class TwilioVerify(Envio):
    proprio = True
    BASE = 'https://verify.twilio.com/v2/Services/{sid}'

    def _url(self, fim):
        return self.BASE.format(sid=config.TWILIO_VERIFY_SID) + fim

    def enviar(self, telefone, canal, codigo=None):
        r = requests.post(self._url('/Verifications'), auth=(config.TWILIO_SID, config.TWILIO_TOKEN), timeout=15,
                          data={'To': identidade.tel_e164(telefone), 'Channel': 'whatsapp' if canal == 'whatsapp' else 'sms',
                                'Locale': 'pt-BR'})
        if r.status_code >= 400:
            raise RuntimeError(f'Twilio {r.status_code}')

    def conferir(self, telefone, codigo):
        r = requests.post(self._url('/VerificationCheck'), auth=(config.TWILIO_SID, config.TWILIO_TOKEN), timeout=15,
                          data={'To': identidade.tel_e164(telefone), 'Code': codigo})
        return r.status_code < 400 and (r.json() or {}).get('status') == 'approved'


class Zenvia(Envio):
    URL = 'https://api.zenvia.com/v2/channels/sms/messages'

    def enviar(self, telefone, canal, codigo=None):
        texto = f'Ollem - Minha usina: seu código é {codigo}. Ele vale por {config.CODIGO_VALIDADE_MIN} minutos. Não compartilhe.'
        r = requests.post(self.URL, timeout=15, headers={'X-API-TOKEN': config.ZENVIA_TOKEN},
                          json={'from': config.ZENVIA_REMETENTE, 'to': '55' + identidade.tel_normal(telefone),
                                'contents': [{'type': 'text', 'text': texto}]})
        if r.status_code >= 400:
            raise RuntimeError(f'Zenvia {r.status_code}')


def envio():
    return {'twilio': TwilioVerify, 'zenvia': Zenvia}.get(config.VERIFICACAO, Console)()
