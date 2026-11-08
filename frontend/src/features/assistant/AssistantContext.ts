import { createContext, useContext } from 'react';
import type { ChatMessage } from '@/api/types';

export type UiMessage = ChatMessage & { id: string };

export type AssistantState = {
  messages: UiMessage[];
  isStreaming: boolean;
  error: string | null;
  drawerOpen: boolean;
  openDrawer: () => void;
  closeDrawer: () => void;
  ask: (prompt: string) => void;
  stop: () => void;
  clear: () => void;
};

export const AssistantContext = createContext<AssistantState | null>(null);

/** Like injecting a singleton Angular service: the drawer and /assistant share this one thread. */
export function useAssistant(): AssistantState {
  const ctx = useContext(AssistantContext);
  if (!ctx) throw new Error('useAssistant must be used inside <AssistantProvider>');
  return ctx;
}
