import { render } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { Providers } from '@/app/Providers';
import { routes } from '@/app/router';
import { createQueryClient } from '@/app/queryClient';

/** Render the whole app (shell + routes) at a URL, with a fresh QueryClient per test. */
export function renderApp(url = '/') {
  const client = createQueryClient();
  client.setDefaultOptions({ queries: { retry: false, refetchInterval: false } });
  const router = createMemoryRouter(routes, { initialEntries: [url] });
  const utils = render(
    <Providers client={client}>
      <RouterProvider router={router} />
    </Providers>,
  );
  return { ...utils, router, client };
}
