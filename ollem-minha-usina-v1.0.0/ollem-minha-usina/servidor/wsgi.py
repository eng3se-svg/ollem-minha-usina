# -*- coding: utf-8 -*-
"""Ponto de entrada. Desenvolvimento:  python wsgi.py   ·   Produção:  waitress-serve --port=8090 wsgi:app"""
from ollem_app.api import criar_app

app = criar_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8090, debug=False)
