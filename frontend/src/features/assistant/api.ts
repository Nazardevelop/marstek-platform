import { API_BASE, ApiError } from '@/api/http';
import type { ChatContext, ChatMessage } from '@/api/types';

type StreamHandlers = { onDelta: (text: string) => void; signal?: AbortSignal };

/**
 * POST /assistant/chat/ and read the Server-Sent Events stream.
 * EventSource only supports GET, so we parse the stream from fetch() by hand:
 * events are separated by a blank line, each has `event:` and `data:` lines.
 */
export async function streamChat(
  messages: ChatMessage[],
  context: ChatContext,
  { onDelta, signal }: StreamHandlers,
): Promise<void> {
  const res = await fetch(`${API_BASE}/assistant/chat/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ messages, context }),
    signal,
  });
  if (!res.ok || !res.body) {
    const body: unknown = await res.json().catch(() => undefined);
    throw new ApiError(res.status, `HTTP ${res.status} for /assistant/chat/`, body);
  }

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = '';
  for (;;) {
    const { value, done } = await reader.read();
    if (done) return;
    buffer += value;
    let sep: number;
    while ((sep = buffer.indexOf('\n\n')) !== -1) {
      const raw = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const event = parseEvent(raw);
      if (event.name === 'delta') {
        const data = JSON.parse(event.data) as { text?: string };
        if (data.text) onDelta(data.text);
      } else if (event.name === 'done') {
        return;
      } else if (event.name === 'error') {
        throw new Error(event.data || 'Assistant error');
      }
    }
  }
}

export function parseEvent(raw: string): { name: string; data: string } {
  let name = 'message';
  const data: string[] = [];
  for (const line of raw.split('\n')) {
    if (line.startsWith('event:')) name = line.slice(6).trim();
    else if (line.startsWith('data:')) data.push(line.slice(5).trim());
  }
  return { name, data: data.join('\n') };
}
