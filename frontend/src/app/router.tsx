import { lazy, Suspense } from 'react';
import { createBrowserRouter } from 'react-router';
import { QueryState } from '@/components/QueryState';
import { AssistantPage } from '@/features/assistant/AssistantPage';
import { ControlPage } from '@/features/control/ControlPage';
import { DashboardPage } from '@/features/dashboard/DashboardPage';
import { SettingsPage } from '@/features/settings/SettingsPage';
import { AppShell } from './AppShell';
import { NotFoundPage } from './NotFoundPage';
import { Root } from './Root';

// Charts (MUI X) are the heaviest dependency: load the Stats page on demand.
const StatsPage = lazy(() =>
  import('@/features/stats/StatsPage').then((m) => ({ default: m.StatsPage })),
);

export const routes = [
  {
    element: <Root />,
    children: [
      {
        element: <AppShell />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: 'control', element: <ControlPage /> },
          {
            path: 'stats',
            element: (
              <Suspense fallback={<QueryState isPending error={null} label="statistics" />}>
                <StatsPage />
              </Suspense>
            ),
          },
          { path: 'assistant', element: <AssistantPage /> },
          { path: 'settings', element: <SettingsPage /> },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
];

export const router = createBrowserRouter(routes);
