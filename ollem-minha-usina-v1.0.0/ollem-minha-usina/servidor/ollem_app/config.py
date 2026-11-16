# -*- coding: utf-8 -*-
"""Configuração por variáveis de ambiente (ou arquivo .env ao lado do servidor).
Nenhum segredo fica no código. Veja .env.exemplo e docs/PARA-O-TI.md."""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _carregar_env():
    caminho = os.environ.get('APP_ENV') or os.path.join(RAIZ, '.env')
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith('#') or '=' not in linha:
                continue
            k, v = linha.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_carregar_env()


def e(nome, padrao=''):
    return (os.environ.get(nome) or padrao).strip()


def lista(nome):
    return [x.strip() for x in e(nome).split(',') if x.strip()]


# ---------------------------------------------------------------- geral
PRODUCAO = e('APP_PRODUCAO', '0') == '1'          # 1 = bloqueia recursos de teste (código no console, fonte demo)
SEGREDO = e('APP_SEGREDO')                       # chave longa e aleatória (assina/embaralha CPF e telefone no banco)
BANCO = e('APP_BANCO', os.path.join(RAIZ, 'dados', 'app.db'))
ANEXOS = e('APP_ANEXOS', os.path.join(RAIZ, 'dados', 'anexos'))
ORIGENS = lista('APP_ORIGENS') or ['capacitor://localhost', 'http://localhost', 'https://localhost', 'http://localhost:5173']
TOKEN_INTERNO = e('APP_TOKEN_INTERNO')           # FieldOps/Hub usam para mandar avisos aos clientes (X-Token)
TARIFA_PADRAO = float(e('TARIFA_PADRAO', '1.06'))
HISTORICO_DIAS = int(e('HISTORICO_DIAS', '400'))  # quantos dias de geração vão junto com cada usina

# ---------------------------------------------------------------- login
CODIGO_VALIDADE_MIN = int(e('CODIGO_VALIDADE_MIN', '10'))
CODIGO_TENTATIVAS = int(e('CODIGO_TENTATIVAS', '5'))
ENVIOS_POR_HORA = int(e('ENVIOS_POR_HORA', '5'))      # por CPF+celular
ENVIOS_POR_HORA_IP = int(e('ENVIOS_POR_HORA_IP', '20'))
SESSAO_DIAS = int(e('SESSAO_DIAS', '180'))
# conta de demonstração para o revisor da Apple/Google (não envia SMS; código fixo)
REVISOR_DOC = e('REVISOR_DOC')
REVISOR_TEL = e('REVISOR_TEL')
REVISOR_CODIGO = e('REVISOR_CODIGO')

# ---------------------------------------------------------------- de onde vêm os dados
FONTE = e('APP_FONTE', 'demo').lower()            # demo | fieldops
FIELDOPS_URL = e('FIELDOPS_URL', 'https://fieldops.ollem.com.br').rstrip('/')
FIELDOPS_TOKEN = e('FIELDOPS_TOKEN')
FIELDOPS_TIMEOUT = float(e('FIELDOPS_TIMEOUT', '20'))

# ---------------------------------------------------------------- envio do código (SMS / WhatsApp)
VERIFICACAO = e('VERIFICACAO', 'console').lower()  # console | twilio | zenvia
TWILIO_SID = e('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN = e('TWILIO_AUTH_TOKEN')
TWILIO_VERIFY_SID = e('TWILIO_VERIFY_SERVICE_SID')
ZENVIA_TOKEN = e('ZENVIA_TOKEN')
ZENVIA_REMETENTE = e('ZENVIA_REMETENTE')          # nome/remetente cadastrado na Zenvia
CANAIS = lista('CANAIS_CODIGO') or ['sms']         # liberar 'whatsapp' só depois da migração do número da Ollivia

# ---------------------------------------------------------------- Ollivia (chat, leitura de fatura)
OLLIVIA_URL = e('OLLIVIA_URL').rstrip('/')
OLLIVIA_TOKEN = e('OLLIVIA_TOKEN')                # o mesmo HUB_TOKEN da Ollivia
OLLIVIA_WHATSAPP = e('OLLIVIA_WHATSAPP', '552231990081')

# ---------------------------------------------------------------- notificações (Firebase Cloud Messaging)
FCM_PROJETO = e('FCM_PROJETO')                    # ID do projeto no Firebase
FCM_CREDENCIAIS = e('FCM_CREDENCIAIS')            # caminho do JSON da conta de serviço (fora do repositório)


def problemas():
    """Lista o que impede rodar em produção. O servidor recusa iniciar com APP_PRODUCAO=1 se houver algum."""
    p = []
    if not SEGREDO or len(SEGREDO) < 32:
        p.append('APP_SEGREDO ausente ou curto (use 32+ caracteres aleatórios).')
    if PRODUCAO:
        if FONTE == 'demo':
            p.append('APP_FONTE=demo não pode ser usado em produção.')
        if VERIFICACAO == 'console':
            p.append('VERIFICACAO=console não pode ser usado em produção.')
        if FONTE == 'fieldops' and not FIELDOPS_TOKEN:
            p.append('FIELDOPS_TOKEN ausente.')
        if not TOKEN_INTERNO:
            p.append('APP_TOKEN_INTERNO ausente.')
    return p
