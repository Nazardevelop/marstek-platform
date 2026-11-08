# Components & hooks

## Props
```tsx
type Props = {
  label: string;
  value: number;
  unit?: 'W' | 'Wh' | '%';           // literal unions over plain string
  onSelect?: (id: string) => void;
  children?: React.ReactNode;
};

export function StatCard({ label, value, unit = 'W', onSelect, children }: Props) { ... }
```
- Named exports for components (better refactoring, grep, auto-imports). Default export only where a
  tool requires it (e.g. lazy routes).
- Extend native elements with `React.ComponentProps<'button'>` instead of re-declaring attributes.
- Model mutually exclusive states with discriminated unions, not several optional booleans:
  `type State = { status: 'idle' } | { status: 'error'; message: string } | { status: 'ok'; data: T }`.

## State
- Keep state minimal; derive the rest during render. Don't store `fullName` next to `first`/`last`.
- Lift state only as high as the nearest common parent. Reach for Context for truly app-wide values
  (theme, current device id), not to avoid passing two props.
- Updating from previous state: `setCount(c => c + 1)`.
- Objects/arrays in state are immutable: spread to update.
- `useReducer` when several state fields change together.

## Effects
Ask "is this syncing with something outside React?" If not, you probably don't need an effect.
- Fetching → TanStack Query. Derived values → compute in render (or `useMemo` if measured slow).
- Reset state on prop change → pass a `key` to the component.
- Always return a cleanup for intervals, listeners, subscriptions.
- Keep the deps array honest (eslint `react-hooks/exhaustive-deps`). If it fights you, restructure.

## Memoization
React 19 + the React Compiler make most manual `useMemo`/`useCallback`/`memo` unnecessary. Add them
only for a measured problem or a referential-identity requirement (e.g. a dep of another hook).

## Custom hooks
- Name `useXxx`, put reusable logic there (data access, subscriptions, form logic).
- Return an object for >2 values (`{ data, isLoading, refresh }`); a tuple only for useState-like pairs.
- Hooks must not be called conditionally or in loops.

## Events & forms
- Type handlers via the element: `(e: React.ChangeEvent<HTMLInputElement>) => ...`.
- Controlled inputs for validated forms; keep numeric input as string in state and parse on submit.
- Validate before calling a mutation; show field errors next to the field.
