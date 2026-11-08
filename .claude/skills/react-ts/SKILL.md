---
name: react-ts
description: Best practices for writing React + TypeScript code in this project's Vite frontend (frontend/). Covers components and hooks, typing props and state, data fetching from the Django API, folder structure, strict tsconfig/ESLint, and testing with Vitest + React Testing Library. Use this whenever you create, edit, refactor or review any .tsx/.ts file under frontend/, add a page/component/hook, wire a component to an API endpoint, set up frontend tooling, or write frontend tests — even if the user doesn't say "best practices".
---

# React + TypeScript best practices

Stack: React 19, TypeScript (strict), Vite, TanStack Query v5, Vitest + React Testing Library.
The frontend only talks to the Django REST API (`/api/...`), never to the Marstek device.

Read the reference file for the area you're touching:
- `references/components-hooks.md` — components, props typing, state, effects, custom hooks
- `references/data-fetching.md` — API client, DTO types, TanStack Query, write (device) commands
- `references/structure.md` — folders, naming, tsconfig, ESLint, imports, env vars
- `references/testing.md` — Vitest + RTL conventions, mocking the API

## Core rules (apply always)

1. **Function components + hooks only.** No class components. Type props with a `type Props = {...}`
   and destructure them; don't use `React.FC` (it adds nothing and hides return-type issues).
2. **No `any`.** Use `unknown` and narrow, or a precise type. Data from the API is typed via DTOs in
   one place, not inline in components.
3. **Derive, don't sync.** If a value can be computed from props/state, compute it during render.
   `useEffect` is for synchronizing with *external* systems (timers, subscriptions, DOM APIs), not
   for copying state or fetching data by hand.
4. **Server state ≠ client state.** Anything that comes from the API goes through TanStack Query
   (`useQuery` / `useMutation`) inside a custom hook. `useState` is for UI state only.
5. **Components never call `fetch` directly.** They call a hook (`useBatteryStatus()`), the hook calls
   the typed API client. This keeps components easy to test and the API easy to mock.
6. **Every async UI has loading, error and empty states.** Don't render `data!.foo`.
7. **Keys are stable IDs**, never array indexes for lists that can change.
8. **Write commands are dangerous** (they change real hardware). Confirm before sending, disable the
   button while pending, show the result, and invalidate the related queries afterwards.
   Factory reset needs an explicit typed confirmation.
9. **Accessible by default.** Real `<button>`s and `<label>`s, so tests can query by role/label.
10. **Keep components small.** Over ~150 lines or doing fetching + layout + logic → split.

## When reviewing code
List concrete issues with the rule they break and a fixed snippet. Prioritize: correctness bugs
(stale closures, missing deps, unhandled errors) > type safety > structure > style.
