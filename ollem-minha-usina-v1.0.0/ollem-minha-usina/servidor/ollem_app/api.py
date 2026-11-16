# -*- coding: utf-8 -*-
"""API do app  ·  prefixo /api/app/v1  ·  contrato completo em docs/API.md"""
import datetime, functools, hmac, logging, os, time, uuid
from flask import Blueprint, Flask, abort, g, jsonify, request, send_file
from io import BytesIO
from . import acesso, banco as B, config, identidade as I
from .envio import ollivia, push
from .fontes import fonte
from .fontes.fieldops import ErroFonte

log = logging.getLogger('ollem_app')
api = Blueprint('api', __name__, url_prefix='/api/app/v1')

TIPOS = {'limpeza': 'Limpeza das placas', 'visita': 'Visita técnica', 'preventiva': 'Manutenção preventiva',
         'outro': 'Outro serviço', 'relatorio': 'Relatório de geração', 'mensagem': 'Mensagem ao pós-venda'}
MAX_ANEXO = 15 * 1024 * 1024


def erro(msg, http=400, codigo='erro'):
    return jsonify({'erro': msg, 'codigo': codigo}), http


def ip():
    return (request.headers.get('X-Forwarded-For') or request.remote_addr or '').split(',')[0].strip()[:45]


def logado(f):
    @functools.wraps(f)
    def w(*a, **k):
        tk = (request.headers.get('Authorization') or '').removeprefix('Bearer ').strip()
        s = acesso.sessao(tk)
        if not s:
            return erro('Sessão expirada. Entre de novo.', 401, 'sessao')
        g.sessao, g.token, g.cliente_id = s, tk, s['cliente_id']
        return f(*a, **k)
    return w


def interno(f):
    """Rotas chamadas pelo FieldOps/Hub (não pelo app): cabeçalho X-Token = APP_TOKEN_INTERNO."""
    @functools.wraps(f)
    def w(*a, **k):
        tk = request.headers.get('X-Token', '')
        if not config.TOKEN_INTERNO or not hmac.compare_digest(tk, config.TOKEN_INTERNO):
            abort(401)
        return f(*a, **k)
    return w


def _minhas_ids():
    c = fonte().cliente(g.cliente_id)
    return set(c['usinas']) if c else set()


def _tarifas():
    return {t['usina_id']: t for t in B.q('SELECT * FROM tarifas WHERE cliente_id=?', g.cliente_id)}


# ------------------------------------------------------------------ saúde
@api.get('/saude')
def saude():
    return jsonify({'ok': True, 'fonte': config.FONTE, 'canais': config.CANAIS, 'versao': '1.0.0'})


# ------------------------------------------------------------------ login
@api.post('/login/codigo')
def login_codigo():
    j = request.get_json(silent=True) or {}
    try:
        return jsonify(acesso.pedir_codigo(j.get('doc'), j.get('telefone'), j.get('canal') or 'sms', ip()))
    except acesso.Recusa as r:
        return erro(r.msg, r.http, r.codigo)
    except ErroFonte as e:
        log.error('login: %s', e)
        return erro('Não conseguimos conferir agora. Tente de novo em instantes.', 503, 'fonte')


@api.post('/login/entrar')
def login_entrar():
    j = request.get_json(silent=True) or {}
    try:
        return jsonify(acesso.entrar(j.get('doc'), j.get('telefone'), j.get('codigo'), j.get('aparelho')))
    except acesso.Recusa as r:
        return erro(r.msg, r.http, r.codigo)


@api.post('/sair')
@logado
def sair():
    acesso.sair(g.token)
    return jsonify({'ok': True})


@api.post('/sair-outros')
@logado
def sair_outros():
    acesso.sair_outros(g.cliente_id, g.token)
    return jsonify({'ok': True})


@api.get('/eu')
@logado
def eu():
    s = g.sessao
    aparelhos = B.q('SELECT aparelho, criado, visto FROM sessoes WHERE cliente_id=? AND revogada=0 AND expira>?', g.cliente_id, time.time())
    return jsonify({'cliente': {'id': s['cliente_id'], 'nome': s['nome'], 'doc': s['doc_masc'], 'telefone': s['tel_masc']},
                    'aparelhos': aparelhos})


# ------------------------------------------------------------------ usinas
@api.get('/usinas')
@logado
def usinas():
    try:
        us = fonte().usinas(g.cliente_id, config.HISTORICO_DIAS)
    except ErroFonte as e:
        log.error('usinas: %s', e)
        return erro('Não conseguimos buscar a sua usina agora.', 503, 'fonte')
    tar = _tarifas()
    for u in us:
        t = tar.get(u['id'])
        if t:
            u['tarifa'], u['tarifa_origem'], u['tarifa_referencia'] = t['valor'], t['origem'], t['referencia']
        elif not u.get('tarifa'):
            u['tarifa'], u['tarifa_origem'] = config.TARIFA_PADRAO, 'media'
    return jsonify({'usinas': us, 'gerado_em': time.time()})


@api.get('/usinas/<usina_id>/geracao')
@logado
def geracao(usina_id):
    try:
        de = datetime.date.fromisoformat(request.args['de'])
        ate = datetime.date.fromisoformat(request.args['ate'])
    except (KeyError, ValueError):
        return erro('Informe de e ate (AAAA-MM-DD).')
    if ate < de or (ate - de).days > 800:
        return erro('Período inválido (máximo de 2 anos).')
    gg = fonte().geracao(g.cliente_id, usina_id, de.isoformat(), ate.isoformat())
    if gg is None:
        return erro('Usina não encontrada.', 404, 'usina')
    return jsonify({'g': gg})


# ------------------------------------------------------------------ solicitações (serviços, relatório, mensagem)
def _registrar(usina_id, tipo, detalhes):
    if usina_id and usina_id not in _minhas_ids():
        return None, erro('Usina não encontrada.', 404, 'usina')
    agora = time.time()
    i = B.x('INSERT INTO solicitacoes(cliente_id, usina_id, tipo, detalhes, criado, atualizado) VALUES(?,?,?,?,?,?)',
            g.cliente_id, usina_id or '', tipo, B.jdump(detalhes), agora, agora)
    try:
        ext = fonte().registrar_solicitacao(g.cliente_id, usina_id, tipo, detalhes)
        B.x('UPDATE solicitacoes SET externo_id=? WHERE id=?', ext, i)
    except Exception as e:                       # fica registrada aqui e o TI reenvia (ver /interno/pendentes)
        log.error('solicitação %s não chegou à fonte: %s', i, e)
        B.x('UPDATE solicitacoes SET erro=? WHERE id=?', str(e)[:300], i)
    return i, None


@api.post('/solicitacoes')
@logado
def solicitar():
    j = request.get_json(silent=True) or {}
    tipo = j.get('tipo')
    if tipo not in ('limpeza', 'visita', 'preventiva', 'outro', 'mensagem'):
        return erro('Tipo de solicitação inválido.')
    det = {'periodo': (j.get('periodo') or '')[:20], 'texto': (j.get('texto') or '')[:2000], 'assunto': (j.get('assunto') or '')[:60]}
    i, e = _registrar(j.get('usina_id'), tipo, det)
    return e or jsonify({'ok': True, 'id': i})


@api.post('/relatorios')
@logado
def pedir_relatorio():
    """multipart/form-data: usina_id, de, ate, entrega (app,whatsapp) e arquivos 'contas' (PDF/foto, opcionais)."""
    f = request.form
    try:
        de, ate = datetime.date.fromisoformat(f['de']), datetime.date.fromisoformat(f['ate'])
    except (KeyError, ValueError):
        return erro('Informe o período (de e ate).')
    anexos = []
    for arq in request.files.getlist('contas')[:12]:
        dados = arq.read(MAX_ANEXO + 1)
        if len(dados) > MAX_ANEXO:
            return erro('Cada conta pode ter até 15 MB.')
        if not (arq.mimetype or '').startswith(('image/', 'application/pdf')):
            return erro('Envie as contas em PDF ou foto.')
        os.makedirs(config.ANEXOS, exist_ok=True)
        nome = f'{uuid.uuid4().hex}{os.path.splitext(arq.filename or "")[1][:6]}'
        with open(os.path.join(config.ANEXOS, nome), 'wb') as h:
            h.write(dados)
        anexos.append({'arquivo': nome, 'nome_original': (arq.filename or '')[:80], 'tipo': arq.mimetype})
    det = {'de': de.isoformat(), 'ate': ate.isoformat(), 'entrega': [x for x in (f.get('entrega') or 'app').split(',') if x in ('app', 'whatsapp')],
           'contas': anexos}
    i, e = _registrar(f.get('usina_id'), 'relatorio', det)
    return e or jsonify({'ok': True, 'id': i, 'contas': len(anexos)})


@api.get('/solicitacoes')
@logado
def minhas_solicitacoes():
    rs = B.q('SELECT * FROM solicitacoes WHERE cliente_id=? ORDER BY id DESC LIMIT 50', g.cliente_id)
    ext = [r['externo_id'] for r in rs if r['externo_id']]
    try:
        sit = fonte().situacao_solicitacoes(g.cliente_id, ext) if ext else {}
    except Exception as e:
        log.warning('situação: %s', e)
        sit = {}
    out = []
    for r in rs:
        est = sit.get(r['externo_id']) or r['estado']
        if est != r['estado']:
            B.x('UPDATE solicitacoes SET estado=?, atualizado=? WHERE id=?', est, time.time(), r['id'])
        out.append({'id': r['id'], 'tipo': r['tipo'], 'titulo': TIPOS.get(r['tipo'], r['tipo']), 'usina_id': r['usina_id'],
                    'estado': est, 'criado': r['criado'], 'detalhes': {k: v for k, v in B.jload(r['detalhes'], {}).items() if k != 'contas'},
                    'contas': len(B.jload(r['detalhes'], {}).get('contas') or []), 'pdf': r['tipo'] == 'relatorio' and est == 'pronto'})
    return jsonify({'solicitacoes': out})


@api.get('/solicitacoes/<int:i>/pdf')
@logado
def relatorio_pdf(i):
    r = B.um('SELECT * FROM solicitacoes WHERE id=? AND cliente_id=?', i, g.cliente_id)
    if not r or r['tipo'] != 'relatorio' or not r['externo_id']:
        return erro('Relatório não encontrado.', 404)
    a = fonte().anexo_relatorio(g.cliente_id, r['externo_id'])
    if not a:
        return erro('O relatório ainda não está pronto.', 404)
    return send_file(BytesIO(a[0]), mimetype='application/pdf', download_name=a[1])


# ------------------------------------------------------------------ Ollivia (chat) e conta de luz
@api.post('/chat')
@logado
def chat():
    j = request.get_json(silent=True) or {}
    texto = (j.get('texto') or '').strip()[:2000]
    if not texto:
        return erro('Escreva a mensagem.')
    if not ollivia.configurada():
        return jsonify({'resposta': 'A Ollivia ainda não está disponível no app. Fale com ela pelo WhatsApp.',
                        'whatsapp': config.OLLIVIA_WHATSAPP})
    try:
        us = [{'id': u['id'], 'bairro': u.get('bairro'), 'kwp': u.get('kwp'), 'estado': u.get('estado'), 'hoje_kwh': u.get('hoje_kwh'),
               'mes_kwh': u.get('mes_kwh')} for u in fonte().usinas(g.cliente_id, 7)]
        resp = ollivia.conversar({'id': g.cliente_id, 'nome': g.sessao['nome']}, us, j.get('historico') or [], texto)
        return jsonify({'resposta': resp})
    except Exception as e:
        log.error('chat: %s', e)
        return erro('A Ollivia não respondeu agora. Tente de novo ou fale pelo WhatsApp.', 503, 'ollivia')


@api.post('/conta-de-luz')
@logado
def conta_de_luz():
    """multipart: usina_id + arquivo (PDF/foto). A Ollivia lê a fatura e a tarifa passa a valer para a usina."""
    uid = request.form.get('usina_id')
    arq = request.files.get('arquivo')
    if not arq or uid not in _minhas_ids():
        return erro('Envie a conta de luz e a usina.')
    if not ollivia.configurada():
        return erro('A leitura da conta ainda não está disponível.', 503, 'ollivia')
    dados = arq.read(MAX_ANEXO + 1)
    if len(dados) > MAX_ANEXO:
        return erro('A conta pode ter até 15 MB.')
    try:
        fat = ollivia.ler_fatura(dados, arq.filename or 'conta')
    except Exception as e:
        log.error('fatura: %s', e)
        return erro('Não conseguimos ler esta conta. Tente uma foto mais nítida ou o PDF.', 502, 'leitura')
    f = next((x for x in fat if x.get('tarifa')), None)
    if not f:
        return erro('Não encontramos a tarifa nesta conta.', 422, 'sem_tarifa')
    valor = float(f['tarifa'])
    if not 0.3 < valor < 3:
        return erro('A tarifa lida parece errada. Confira ou digite o valor.', 422, 'tarifa_estranha')
    ref = f.get('referencia') or f.get('mes') or ''
    B.x('INSERT OR REPLACE INTO tarifas(cliente_id, usina_id, valor, origem, referencia, criado) VALUES(?,?,?,?,?,?)',
        g.cliente_id, uid, valor, 'conta', str(ref)[:20], time.time())
    return jsonify({'ok': True, 'tarifa': valor, 'referencia': ref})


@api.put('/tarifa')
@logado
def tarifa_digitada():
    j = request.get_json(silent=True) or {}
    uid = j.get('usina_id')
    if uid not in _minhas_ids():
        return erro('Usina não encontrada.', 404)
    if j.get('valor') in (None, ''):
        B.x('DELETE FROM tarifas WHERE cliente_id=? AND usina_id=?', g.cliente_id, uid)
        return jsonify({'ok': True})
    try:
        v = float(str(j['valor']).replace(',', '.'))
    except ValueError:
        return erro('Valor inválido.')
    if not 0.3 < v < 3:
        return erro('A tarifa deve ficar entre R$ 0,30 e R$ 3,00 por kWh.')
    B.x('INSERT OR REPLACE INTO tarifas(cliente_id, usina_id, valor, origem, referencia, criado) VALUES(?,?,?,?,?,?)',
        g.cliente_id, uid, v, 'digitada', '', time.time())
    return jsonify({'ok': True, 'tarifa': v})


# ------------------------------------------------------------------ preferências, avisos, aparelhos, família, conta
@api.get('/preferencias')
@logado
def pref_get():
    r = B.um('SELECT dados FROM preferencias WHERE cliente_id=?', g.cliente_id)
    return jsonify(B.jload(r['dados'], {}) if r else {})


@api.put('/preferencias')
@logado
def pref_put():
    permitidas = ('push', 'silencio', 'canais', 'tema', 'texto_grande', 'biometria')
    j = {k: v for k, v in (request.get_json(silent=True) or {}).items() if k in permitidas}
    B.x('INSERT OR REPLACE INTO preferencias(cliente_id, dados, atualizado) VALUES(?,?,?)', g.cliente_id, B.jdump(j), time.time())
    return jsonify({'ok': True})


@api.post('/push/registrar')
@logado
def push_registrar():
    j = request.get_json(silent=True) or {}
    tk, plat = (j.get('token') or '')[:400], j.get('plataforma')
    if not tk or plat not in ('ios', 'android', 'web'):
        return erro('Token ou plataforma inválidos.')
    B.x('INSERT OR REPLACE INTO push_tokens(token, cliente_id, plataforma, criado) VALUES(?,?,?,?)', tk, g.cliente_id, plat, time.time())
    return jsonify({'ok': True})


@api.get('/avisos')
@logado
def avisos():
    return jsonify({'avisos': B.q('SELECT id, usina_id, tipo, titulo, texto, lido, criado FROM avisos WHERE cliente_id=? ORDER BY id DESC LIMIT 100', g.cliente_id)})


@api.post('/avisos/lidos')
@logado
def avisos_lidos():
    B.x('UPDATE avisos SET lido=1 WHERE cliente_id=?', g.cliente_id)
    return jsonify({'ok': True})


@api.post('/familiares')
@logado
def convidar():
    j = request.get_json(silent=True) or {}
    tel = I.tel_normal(j.get('telefone'))
    nome = (j.get('nome') or '').strip()[:60]
    if not tel or not nome:
        return erro('Informe nome e celular.')
    i = B.x('INSERT INTO familiares(cliente_id, nome, tel_chave, tel_masc, criado) VALUES(?,?,?,?,?)',
            g.cliente_id, nome, I.chave('familiar', tel), I.masc_tel(tel), time.time())
    # >>> PARA O TI: enviar o convite (SMS/WhatsApp) e liberar o acesso só-leitura — ver docs/PARA-O-TI.md (Fase 2b)
    return jsonify({'ok': True, 'id': i})


@api.delete('/conta')
@logado
def excluir_conta():
    """Exigência da Apple: excluir a conta dentro do app. Apaga os dados do app; a usina continua monitorada pela Ollem."""
    cid = g.cliente_id
    for t in ('sessoes', 'push_tokens', 'preferencias', 'tarifas', 'familiares', 'avisos'):
        B.x(f'DELETE FROM {t} WHERE cliente_id=?', cid)
    B.x('INSERT INTO exclusoes(cliente_id, criado) VALUES(?,?)', cid, time.time())
    try:
        fonte().excluir_conta(cid)
    except Exception as e:
        log.warning('excluir na fonte: %s', e)
    return jsonify({'ok': True})


# ------------------------------------------------------------------ rotas internas (FieldOps / Hub → app)
@api.post('/interno/avisos')
@interno
def interno_aviso():
    """O FieldOps (ou o Hub) avisa um cliente: usina parada, relatório pronto, visita agendada…
    {cliente_id, usina_id?, tipo, titulo, texto}"""
    j = request.get_json(silent=True) or {}
    if not j.get('cliente_id') or not j.get('titulo'):
        return erro('Informe cliente_id e titulo.')
    B.x('INSERT INTO avisos(cliente_id, usina_id, tipo, titulo, texto, criado) VALUES(?,?,?,?,?,?)',
        j['cliente_id'], j.get('usina_id') or '', (j.get('tipo') or 'geral')[:30], j['titulo'][:120], (j.get('texto') or '')[:500], time.time())
    n = push.enviar(j['cliente_id'], j['titulo'], j.get('texto') or '', {'tipo': j.get('tipo') or 'geral', 'usina_id': j.get('usina_id') or ''})
    return jsonify({'ok': True, 'aparelhos': n})


@api.post('/interno/solicitacoes/<int:i>/estado')
@interno
def interno_estado(i):
    j = request.get_json(silent=True) or {}
    est = j.get('estado')
    if est not in ('recebido', 'agendado', 'feito', 'gerando', 'pronto', 'respondido', 'cancelado'):
        return erro('Estado inválido.')
    B.x('UPDATE solicitacoes SET estado=?, atualizado=? WHERE id=?', est, time.time(), i)
    return jsonify({'ok': True})


@api.get('/interno/pendentes')
@interno
def interno_pendentes():
    """Solicitações que não chegaram à fonte (FieldOps fora do ar na hora)."""
    return jsonify({'pendentes': B.q("SELECT id, cliente_id, usina_id, tipo, criado, erro FROM solicitacoes WHERE externo_id='' ORDER BY id")})


# ------------------------------------------------------------------ aplicativo Flask
def criar_app():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    p = config.problemas()
    if config.PRODUCAO and p:
        raise SystemExit('Configuração incompleta para produção:\n- ' + '\n- '.join(p))
    for x in p:
        log.warning('configuração: %s', x)
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 60 * 1024 * 1024
    app.register_blueprint(api)

    @app.after_request
    def cors(r):
        o = request.headers.get('Origin')
        if o and o in config.ORIGENS:
            r.headers['Access-Control-Allow-Origin'] = o
            r.headers['Vary'] = 'Origin'
            r.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
            r.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        r.headers['X-Content-Type-Options'] = 'nosniff'
        r.headers['Cache-Control'] = 'no-store'
        return r

    @app.route('/api/app/v1/<path:_>', methods=['OPTIONS'])
    def preflight(_):
        return '', 204

    return app
