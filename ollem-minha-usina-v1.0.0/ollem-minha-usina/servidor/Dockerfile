FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ollem_app ollem_app
COPY dados/demo.json dados/demo.json
COPY wsgi.py .
ENV APP_BANCO=/dados/app.db APP_ANEXOS=/dados/anexos
EXPOSE 8090
CMD ["waitress-serve", "--port=8090", "--threads=8", "wsgi:app"]
