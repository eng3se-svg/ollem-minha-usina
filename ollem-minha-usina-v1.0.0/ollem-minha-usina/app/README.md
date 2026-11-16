# App (Vue 3 + Vite + Capacitor)

```bash
npm install
npm run dev                 # modo demonstração (sem VITE_API_URL): dados fictícios
npm run build               # gera dist/ (um index.html só)
npm run cap:sync            # build + copia para os projetos nativos (depois de npx cap add android/ios)
```
- `VITE_API_URL` em `.env.local` / `.env.production` liga o app ao servidor (ver `.env.exemplo`).
- Telas em `src/views/`, componentes em `src/components/`, cálculos (esperado, alertas, economia) em `src/lib/calc.js`.
- `src/api.js` = chamadas ao servidor · `src/nativo.js` = recursos do celular (sessão, notificações).
- Identidade: Inter, verde `#11c90a` → lima `#8ef705`, fundo escuro `#0c100e`/`#111714`, símbolo da Ollem em `src/assets/simbolo.png`.
- Textos em pt-BR simples; usar "Solicitar"; nunca mostrar nome de portal de fabricante.
