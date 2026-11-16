# Segurança e proteção de dados (LGPD)

## Princípios
1. **Cada cliente vê só as próprias usinas.** Toda rota com usina confere se ela pertence ao cliente da sessão (pela fonte).
2. **Mínimo de dados no app.** O servidor do app não guarda dados de usina; busca no FieldOps a cada pedido.
3. **CPF e celular nunca em texto** no banco do app: só um resumo HMAC (com `APP_SEGREDO`) e a versão mascarada
   (`529.•••.•••-25`, `(22) 9••••-4567`). No aparelho, o app guarda só o token da sessão e as versões mascaradas.
4. **Nada de portal de fabricante.** O app não conhece logins/senhas de portais e não mostra o nome do portal.
   O adaptador do FieldOps descarta qualquer campo fora da lista permitida (`_limpar`).
5. **Sem segredos no repositório.** `.env`, chaves do Firebase, certificados e keystores estão no `.gitignore`.

## Login
- CPF/CNPJ do titular **+** celular do **mesmo** cadastro **+** código de 6 dígitos (SMS ou WhatsApp).
- Resposta **genérica** quando não confere (não revela se o CPF é cliente nem de quem é o celular).
- Código: guardado como hash, vale 10 min, 5 tentativas. Limite de 5 envios/hora por CPF+celular e 20/hora por IP.
- Sessão: token aleatório de 256 bits; no banco só o hash. Vale 180 dias; pode ser encerrada pelo cliente
  ("Sair" e "Sair dos outros aparelhos") e é apagada na exclusão da conta.
- Na volta ao app, Face ID/digital protegem a sessão guardada (a implementar no nativo, ver PARA-O-TI).

## Anexos (contas de luz)
- PDF ou imagem, até 15 MB cada, salvos com nome aleatório em `APP_ANEXOS` (fora da pasta pública).
- Contêm dados pessoais (nome, endereço, UC): definir prazo de retenção (sugestão: apagar após o relatório ficar pronto + 90 dias)
  e incluir na política de privacidade.

## Direitos do titular
- **Exclusão da conta** dentro do app (Perfil → Excluir minha conta): apaga sessões, aparelhos, preferências,
  tarifas, familiares e avisos do app; registra a exclusão e avisa a fonte. A usina continua monitorada pela Ollem
  (relação de contrato, fora do app).
- Política de privacidade e termos de uso: **textos a escrever e publicar** numa URL da Ollem (o app já tem os links).

## Operação
- HTTPS obrigatório (Caddy no `docker-compose.yml`).
- `APP_PRODUCAO=1` bloqueia fonte de demonstração e código no console.
- Backup diário do volume `dados-producao/`. Registros (logs) não contêm CPF, telefone nem código.
- Rotas `/interno/*` só com `APP_TOKEN_INTERNO` (comparação em tempo constante).
