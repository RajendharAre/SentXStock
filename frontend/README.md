# Frontend (React + Vite)

This folder contains the React + Vite frontend for SentXStock. Below are the common npm commands and a suggested `package.json` scripts block.

Quick start

```bash
cd frontend
npm install
npm run dev      # start Vite dev server (http://localhost:5173)
npm run build    # build production assets to dist/
npm run preview  # locally preview the production build
```

Suggested `package.json` scripts

```json
"scripts": {
  "dev": "vite",
  "build": "vite build",
  "preview": "vite preview --port 5174",
  "lint": "eslint src --ext .js,.jsx,.ts,.tsx",
  "format": "prettier --write \"src/**/*.{js,jsx,ts,tsx,json,css,md}\""
}
```

Notes
- During development the React app calls the Flask API at `http://localhost:5000`. CORS is enabled in `server.py` by default.
- If you prefer to proxy API requests from Vite dev server instead of relying on CORS, add a `vite.config.js` proxy entry or set `server.proxy` in Vite config.
- Keep environment variables for the frontend in `.env` files inside `frontend/` (e.g. `VITE_API_URL=http://localhost:5000`). Vite exposes variables prefixed with `VITE_`.

Example `.env` (frontend):

```
VITE_API_URL=http://localhost:5000
```

Adding concurrency helper (optional)

To run backend and frontend together during development you can use `concurrently` in the repo root, or add a top-level `Makefile` with a `dev` target that launches both processes in separate terminals.
# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
