# Testing (Vitest + React Testing Library)

## Setup
- `vitest` with `environment: 'jsdom'`, `setupFiles: ['src/test/setup.ts']`, `globals: true`.
- `setup.ts`: `import '@testing-library/jest-dom/vitest'`.
- Mock the network with **MSW** (`msw/node` `setupServer`) at the HTTP level — tests exercise the
  real hook + API client. Never hit the real backend or the device from tests.

## Render helper
```tsx
export function renderWithProviders(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}
```
A fresh `QueryClient` per test avoids cache leaking between tests; `retry: false` makes error tests fast.

## Writing tests
- Test behaviour the user sees, not implementation (no checking state or hook internals).
- Query priority: `getByRole` (with `name`) > `getByLabelText` > `getByText` > `getByTestId` (last resort).
- Interactions via `userEvent.setup()` and `await user.click(...)`, not `fireEvent`.
- Async UI: `await screen.findByText(...)`; for disappearance `waitForElementToBeRemoved`.
- Cover: loading → success, error state, empty state, and for write commands: confirm required,
  button disabled while pending, correct request body sent.
- Name tests by behaviour: `it('shows an error when the battery status request fails')`.

## Example
```tsx
it('shows battery percentage', async () => {
  server.use(http.get('/api/devices/d1/battery/', () => HttpResponse.json({ soc: 82 })));
  renderWithProviders(<BatteryCard deviceId="d1" />);
  expect(await screen.findByText('82%')).toBeInTheDocument();
});
```
