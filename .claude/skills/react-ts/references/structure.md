# Project structure & tooling

## Folders (feature-first)
```
frontend/src/
  app/            App.tsx, providers (QueryClientProvider, router), routes
  api/            http.ts, shared DTO types
  features/
    battery/      api.ts, hooks.ts, types.ts, components/BatteryCard.tsx, BatteryCard.test.tsx
    mode/
    assistant/
  components/     shared presentational UI (Button, Card, Spinner) — no data fetching
  lib/            pure helpers (formatWatts, dates)
  test/           setup.ts, test utils (renderWithProviders), msw handlers
```
- Colocate tests and styles with the component. A feature folder owns its api/hooks/components.
- Shared `components/` must not import from `features/`.

## Naming
- Components & their files: `PascalCase.tsx`. Hooks: `useThing.ts`. Other modules: `camelCase.ts`.
- One exported component per file (small private helpers are fine).
- Avoid barrel `index.ts` files everywhere; they slow Vite/HMR and create cycles. Fine at a feature's
  public boundary if needed.

## tsconfig essentials
`"strict": true`, `"noUncheckedIndexedAccess": true`, `"noUnusedLocals"`, `"noUnusedParameters"`,
`"verbatimModuleSyntax": true` (use `import type` for types), path alias `"@/*": ["src/*"]`
(mirror it in `vite.config.ts` `resolve.alias`).

## Lint & format
ESLint flat config (`eslint.config.js`) with `typescript-eslint`, `eslint-plugin-react-hooks`
(rules-of-hooks + exhaustive-deps as errors), `eslint-plugin-react-refresh`. Prettier for formatting.
Scripts: `dev`, `build` (`tsc -b && vite build`), `lint`, `test`, `typecheck`.

## Env vars
Only `VITE_*` vars reach the browser and they are **public** — never put secrets
(e.g. `ANTHROPIC_API_KEY`) in the frontend. Type them in `src/vite-env.d.ts`:
```ts
interface ImportMetaEnv { readonly VITE_API_URL?: string }
```
Document them in `.env.example`.

## Styling
Pick one approach (CSS Modules is the zero-dependency default with Vite) and stick to it.
