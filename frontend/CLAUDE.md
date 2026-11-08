# Marstek Platform: Frontend

React + TypeScript (Vite) web app for monitoring and controlling a Marstek power station.
Coding conventions: follow the `react-ts` skill. Project-wide rules are in `../CLAUDE.md`.

## Architecture rules
- The FE talks **only** to the Django API (`backend/`), never to the device (UDP/JSON-RPC lives in the backend).
- No login. The app is used on the home LAN.
- Single device for now, but keep the device id in API paths/state so multi-device support stays possible.

## Screens
Shared shell: top bar (device name, online status, current mode, "Ask Marstek…" prompt). Navigation is a sidebar on desktop and bottom tabs on mobile.

| Route | Purpose | Writes hardware? |
|---|---|---|
| `/` | Dashboard: live SOC, power flow, mode, CT meter, PV inputs (polled) | No |
| `/control` | Operating mode (`ES.SetMode`): Auto/AI/Manual/Passive/UPS, Manual time-slot editor | Yes |
| `/stats` | History charts from the backend `stats` app | No |
| `/assistant` | Full-page AI chat | No |
| `/settings` | Device/WiFi/BLE info, discovery, DOD/LED/BLE/power version, factory-reset section | Yes |

## Assistant UX
- The top-bar prompt (and `Cmd/Ctrl+K`) opens a **right-side chat drawer** over the current page. Don't navigate away.
- The drawer's "Expand" button goes to `/assistant`.
- The drawer and the page share **one conversation state** (a single context/store). Send the current route as context.

## UI rules
- **Capability-driven UI:** hide sections the device model or firmware doesn't support (PV only on Venus A/D; SYS settings need FW ≥150 or E mini). Never show an error for an unsupported feature.
- **Hardware writes** always go through a confirm dialog and show the `set_result` outcome. Factory reset requires typing the device name.
- **Offline:** if the device is unreachable, show a banner and the last-known values with a timestamp.
- Hide raw API quirks from the user (e.g. `Ble.Adv` uses inverted 0/1, `week_set` is a bitmask). The backend normalizes units to Wh/W.

## UI library: MUI (Material UI)
- Use **Material UI (free/MIT packages only)**: `@mui/material`, `@mui/icons-material`, and the free tiers of MUI X (e.g. `@mui/x-charts`, `@mui/x-date-pickers`). Do **not** use MUI X Pro/Premium.
- Prefer MUI components and the theme (`ThemeProvider`, `sx`) over custom CSS.
- Docs come from the **MUI MCP server** (`mui-mcp`): https://mui.com/material-ui/getting-started/mcp/

### Use the mui-mcp server to answer any MUI questions
Server is registered in `../.mcp.json` (`npx -y @mui/mcp@latest`). Checked on 2026-11-08: version 0.1.9 exposes only `fetchDocs` and `generateReactCode`. There is **no `useMuiDocs` tool**, even though the MUI docs page still mentions it.
1. Call `fetchDocs` with the package index, e.g. `https://mui.com/material-ui/llms.txt` (MUI X has its own `llms.txt` under `https://mui.com/x/...`).
2. Call `fetchDocs` again for the relevant pages, using ONLY URLs that appear in fetched content. Don't guess URLs.
3. Repeat until you have all the relevant docs, then answer from the fetched content.
- Don't use `generateReactCode`: it needs a paid `MUI_RECIPES_API_KEY`.
- If a newer server version adds `useMuiDocs`, use it as step 1 and update this section.

## Commands (run in `frontend/`)
- `npm install`: install deps (Node 22)
- `npm run dev`: Vite on :5173; `/api` is proxied to Django on :8000 (`VITE_PROXY_TARGET`)
- `npm test` / `npm run test:watch`: Vitest + RTL + MSW
- `npm run lint`, `npm run typecheck`, `npm run format`
- `npm run build`: `tsc -b && vite build` → `dist/`
- `npm run gen:api`: regenerate `openapi.yml` + `src/api/schema.d.ts` from the backend (needs `uv` in `backend/`). Run it after any backend serializer change.
- Docker: TBD.

## Structure & libraries
- React 19, React Router (`react-router`, data router in `src/app/router.tsx`), TanStack Query v5, MUI + `@mui/x-charts` (Stats page is lazy-loaded because of the charts).
- `src/app/`: providers, theme, router, `AppShell` (top bar, sidebar / bottom nav, assistant drawer).
- `src/api/`: `http.ts` (fetch wrapper, `ApiError`, `errorMessage`), `types.ts` (aliases over the generated `schema.d.ts`; never edit `schema.d.ts` by hand).
- `src/features/<feature>/`: `api.ts`, `hooks.ts`, page + `components/`. Features: `device` (current device, status/mode/network hooks, offline banner), `dashboard`, `control`, `stats`, `settings`, `assistant`.
- `src/components/`: shared presentational UI (`ConfirmDialog`, `QueryState`, `WriteResult`, `StatCard`…). No data fetching.
- `src/test/`: MSW server and handlers (`fixtures.ts`), `renderApp(url)` renders the whole app at a route.
- Env: `VITE_API_URL` (default `/api/v1`), `VITE_PROXY_TARGET` (dev only). See `.env.example`.

## Quirks
- TypeScript is pinned to `~6.0`: `typescript-eslint` doesn't support TS 7 yet.
- `openapi-typescript` runs via `npx` (not a dependency): its peer range is TS 5.
- MSW v3: the option is `onUnhandledFrame` (not `onUnhandledRequest`). Unhandled requests fail tests.
- jsdom has no media queries; `src/test/setup.ts` stubs `matchMedia` (1024 px = desktop layout).
- The assistant uses `fetch` + a manual SSE parser (`features/assistant/api.ts`), because `EventSource` can't POST.
- `useCurrentDevice()` reads capabilities from `GET /devices/{id}/` (it re-reads model/firmware). The list endpoint only has stored values.
- The backend's `/status/` can take several seconds (several UDP calls). The device sometimes times out; the UI then shows `stale` data.
- Power sign conventions (`battery_w`, `grid_w`, passive `power_w`) aren't in the spec. `PowerFlowCard` assumes positive = discharging / exporting. Verify on the device.
