import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react';
import { useLocation } from 'react-router';
import { errorMessage } from '@/api/http';
import { useCurrentDevice } from '@/features/device/hooks';
import { streamChat } from './api';
import { AssistantContext, type AssistantState, type UiMessage } from './AssistantContext';

let nextId = 0;
const newId = () => `m${++nextId}`;

export function AssistantProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const location = useLocation();
  const { device } = useCurrentDevice();

  const ask = useCallback(
    (prompt: string) => {
      const text = prompt.trim();
      if (!text || abortRef.current) return;
      const user: UiMessage = { id: newId(), role: 'user', content: text };
      const reply: UiMessage = { id: newId(), role: 'assistant', content: '' };
      const history = [...messages, user];
      setMessages([...history, reply]);
      setError(null);
      setIsStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;
      const context = {
        route: location.pathname + location.search,
        ...(device ? { device_id: device.id } : {}),
      };
      streamChat(
        history.map(({ role, content }) => ({ role, content })),
        context,
        {
          signal: controller.signal,
          onDelta: (chunk) =>
            setMessages((ms) =>
              ms.map((m) => (m.id === reply.id ? { ...m, content: m.content + chunk } : m)),
            ),
        },
      )
        .catch((e: unknown) => {
          if (!controller.signal.aborted) setError(errorMessage(e));
        })
        .finally(() => {
          abortRef.current = null;
          setIsStreaming(false);
        });
    },
    [messages, location.pathname, location.search, device],
  );

  const value = useMemo<AssistantState>(
    () => ({
      messages,
      isStreaming,
      error,
      drawerOpen,
      openDrawer: () => setDrawerOpen(true),
      closeDrawer: () => setDrawerOpen(false),
      ask,
      stop: () => abortRef.current?.abort(),
      clear: () => {
        abortRef.current?.abort();
        setMessages([]);
        setError(null);
      },
    }),
    [messages, isStreaming, error, drawerOpen, ask],
  );

  return <AssistantContext value={value}>{children}</AssistantContext>;
}
