# -*- coding: utf-8 -*-
"""Testes da API com a fonte de demonstração e o envio de código no console.  Rodar:  pytest -q"""
import io, os, sys
os.environ.update({'APP_BANCO': ':memory:', 'APP_FONTE': 'demo', 'VERIFICACAO': 'console', 'APP_SEGREDO': 'x' * 40,
                   'APP_TOKEN_INTERNO': 'interno-teste', 'APP_ENV': '/nao/existe', 'CANAIS_CODIGO': 'sms,whatsapp'})
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from ollem_app import banco
from ollem_app.api import criar_app
from ollem_app.envio.codigo import Console

CPF, TEL = '529.982.247-25', '(22) 98123-4567'


@pytest.fixture()
def c():
    banco.reiniciar()
    return criar_app().test_client()


def entrar(c, canal='sms'):
    r = c.post('/api/app/v1/login/codigo', json={'doc': CPF, 'telefone': TEL, 'canal': canal})
    assert r.status_code == 200, r.json
    cod = Console.ultimo['22981234567']
    r = c.post('/api/app/v1/login/entrar', json={'doc': CPF, 'telefone': TEL, 'codigo': cod, 'aparelho': 'teste'})
    assert r.status_code == 200, r.json
    return {'Authorization': 'Bearer ' + r.json['token']}


def test_saude(c):
    assert c.get('/api/app/v1/saude').json['ok']


def test_cpf_invalido(c):
    r = c.post('/api/app/v1/login/codigo', json={'doc': '529.982.247-00', 'telefone': TEL})
    assert r.status_code == 400 and r.json['codigo'] == 'doc_invalido'


def test_dados_nao_conferem_e_generico(c):
    r = c.post('/api/app/v1/login/codigo', json={'doc': CPF, 'telefone': '(22) 98123-0000'})
    assert r.status_code == 404 and r.json['codigo'] == 'dados_nao_conferem'
    r2 = c.post('/api/app/v1/login/codigo', json={'doc': '111.444.777-35', 'telefone': TEL})   # CPF válido, não é cliente
    assert r2.status_code == 404 and r2.json == r.json                                      # mesma resposta: não revela nada


def test_login_e_mascaras(c):
    h = entrar(c)
    eu = c.get('/api/app/v1/eu', headers=h).json['cliente']
    assert eu['doc'] == '529.•••.•••-25' and eu['telefone'] == '(22) 9••••-4567'
    assert '52998224725' not in str(banco.q('SELECT * FROM sessoes')) and '22981234567' not in str(banco.q('SELECT * FROM codigos'))


def test_codigo_errado_e_limite(c):
    c.post('/api/app/v1/login/codigo', json={'doc': CPF, 'telefone': TEL})
    for _ in range(5):
        r = c.post('/api/app/v1/login/entrar', json={'doc': CPF, 'telefone': TEL, 'codigo': '000000'})
        assert r.status_code == 401
    r = c.post('/api/app/v1/login/entrar', json={'doc': CPF, 'telefone': TEL, 'codigo': Console.ultimo['22981234567']})
    assert r.status_code == 429


def test_limite_de_envios(c):
    for _ in range(5):
        assert c.post('/api/app/v1/login/codigo', json={'doc': CPF, 'telefone': TEL}).status_code == 200
    assert c.post('/api/app/v1/login/codigo', json={'doc': CPF, 'telefone': TEL}).status_code == 429


def test_sem_sessao(c):
    assert c.get('/api/app/v1/usinas').status_code == 401


def test_usinas_e_geracao(c):
    h = entrar(c)
    us = c.get('/api/app/v1/usinas', headers=h).json['usinas']
    assert len(us) == 3 and us[0]['g'] and us[0]['tarifa'] == 1.06
    assert 'portal' not in us[0]
    r = c.get(f"/api/app/v1/usinas/{us[0]['id']}/geracao?de=2026-11-01&ate=2026-11-10", headers=h)
    assert r.status_code == 200 and len(r.json['g']) == 10
    assert c.get('/api/app/v1/usinas/outra-usina/geracao?de=2026-11-01&ate=2026-11-10', headers=h).status_code == 404


def test_solicitacoes_e_relatorio(c):
    h = entrar(c)
    r = c.post('/api/app/v1/solicitacoes', headers=h, json={'tipo': 'limpeza', 'usina_id': 'demo-1', 'periodo': 'Manhã'})
    assert r.status_code == 200
    dados = {'usina_id': 'demo-1', 'de': '2026-08-01', 'ate': '2026-10-31', 'entrega': 'app,whatsapp',
             'contas': [(io.BytesIO(b'%PDF-1.4 conta'), 'conta-outubro.pdf', 'application/pdf')]}
    r = c.post('/api/app/v1/relatorios', headers=h, data=dados, content_type='multipart/form-data')
    assert r.status_code == 200 and r.json['contas'] == 1
    lst = c.get('/api/app/v1/solicitacoes', headers=h).json['solicitacoes']
    assert [s['tipo'] for s in lst] == ['relatorio', 'limpeza'] and lst[0]['contas'] == 1
    assert c.post('/api/app/v1/solicitacoes', headers=h, json={'tipo': 'limpeza', 'usina_id': 'de-outro'}).status_code == 404


def test_tarifa_digitada(c):
    h = entrar(c)
    assert c.put('/api/app/v1/tarifa', headers=h, json={'usina_id': 'demo-1', 'valor': '0,98'}).json['tarifa'] == 0.98
    us = c.get('/api/app/v1/usinas', headers=h).json['usinas']
    assert us[0]['tarifa'] == 0.98 and us[0]['tarifa_origem'] == 'digitada'
    assert c.put('/api/app/v1/tarifa', headers=h, json={'usina_id': 'demo-1', 'valor': '9'}).status_code == 400


def test_aviso_interno_e_exclusao(c):
    h = entrar(c)
    assert c.post('/api/app/v1/interno/avisos', json={'cliente_id': 'cli-demo', 'titulo': 'x'}).status_code == 401
    r = c.post('/api/app/v1/interno/avisos', headers={'X-Token': 'interno-teste'},
               json={'cliente_id': 'cli-demo', 'usina_id': 'demo-3', 'tipo': 'parada', 'titulo': 'Sua usina parou', 'texto': 'Já avisamos a equipe.'})
    assert r.status_code == 200
    assert c.get('/api/app/v1/avisos', headers=h).json['avisos'][0]['titulo'] == 'Sua usina parou'
    assert c.delete('/api/app/v1/conta', headers=h).json['ok']
    assert c.get('/api/app/v1/usinas', headers=h).status_code == 401


def test_chat_sem_ollivia(c):
    h = entrar(c)
    r = c.post('/api/app/v1/chat', headers=h, json={'texto': 'Quanto gerei hoje?'})
    assert r.status_code == 200 and 'WhatsApp' in r.json['resposta']
