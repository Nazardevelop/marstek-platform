import { http, HttpResponse } from 'msw';
import { API, daily, device, history, modeStatus, network, status } from './fixtures';

/** Default happy-path API. Tests override single endpoints with server.use(...). */
export const handlers = [
  http.get(`${API}/devices/`, () => HttpResponse.json([device])),
  http.get(`${API}/devices/:id/`, () => HttpResponse.json(device)),
  http.get(`${API}/devices/:id/status/`, () => HttpResponse.json(status)),
  http.get(`${API}/devices/:id/mode/`, () => HttpResponse.json(modeStatus)),
  http.get(`${API}/devices/:id/network/`, () => HttpResponse.json(network)),
  http.get(`${API}/devices/:id/energy/daily/`, () => HttpResponse.json(daily)),
  http.get(`${API}/devices/:id/history/`, () => HttpResponse.json(history)),
];

/** SSE body the way the backend sends it: `event:` + `data:` lines, blank line between events. */
export function sseBody(chunks: string[]): ReadableStream<Uint8Array> {
  const enc = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const text of chunks) {
        controller.enqueue(enc.encode(`event: delta\ndata: ${JSON.stringify({ text })}\n\n`));
      }
      controller.enqueue(enc.encode('event: done\ndata: {}\n\n'));
      controller.close();
    },
  });
}
