import { Outlet } from 'react-router';
import { AssistantProvider } from '@/features/assistant/AssistantProvider';

/** Providers that need the router (useLocation) live inside it. */
export function Root() {
  return (
    <AssistantProvider>
      <Outlet />
    </AssistantProvider>
  );
}
