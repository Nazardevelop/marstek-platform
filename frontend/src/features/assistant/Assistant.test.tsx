import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { sseBody } from '@/test/handlers';
import { API } from '@/test/fixtures';
import { renderApp } from '@/test/render';
import { server } from '@/test/server';
import { parseEvent } from './api';

function mockChat() {
  const bodies: unknown[] = [];
  server.use(
    http.post(`${API}/assistant/chat/`, async ({ request }) => {
      bodies.push(await request.json());
      return new HttpResponse(sseBody(['You exported ', '2.5 kWh.']), {
        headers: { 'Content-Type': 'text/event-stream' },
      });
    }),
  );
  return bodies;
}

describe('Assistant', () => {
  it('answers a top-bar prompt in the drawer without leaving the page', async () => {
    const user = userEvent.setup();
    const bodies = mockChat();
    const { router } = renderApp('/stats?range=7d');

    await user.type(
      await screen.findByRole('textbox', { name: 'Ask Marstek' }),
      'How much did I export?{Enter}',
    );

    const drawer = await screen.findByRole('presentation');
    expect(await within(drawer).findByText('You exported 2.5 kWh.')).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/stats');
    expect(bodies).toEqual([
      {
        messages: [{ role: 'user', content: 'How much did I export?' }],
        context: { route: '/stats?range=7d', device_id: 1 },
      },
    ]);
  });

  it('keeps the same conversation when expanding to the full page', async () => {
    const user = userEvent.setup();
    mockChat();
    const { router } = renderApp('/');
    await user.type(await screen.findByRole('textbox', { name: 'Ask Marstek' }), 'Hi{Enter}');
    await screen.findByText('You exported 2.5 kWh.');

    await user.click(screen.getByRole('button', { name: 'Expand' }));
    expect(router.state.location.pathname).toBe('/assistant');
    expect(await screen.findByRole('heading', { name: 'Assistant', level: 1 })).toBeInTheDocument();
    expect(screen.getByText('Hi')).toBeInTheDocument();
    expect(screen.getByText('You exported 2.5 kWh.')).toBeInTheDocument();
  });

  it('shows an error when the chat request fails', async () => {
    const user = userEvent.setup();
    server.use(
      http.post(`${API}/assistant/chat/`, () =>
        HttpResponse.json({ code: 'invalid', message: 'Invalid request' }, { status: 400 }),
      ),
    );
    renderApp('/assistant');
    await user.type(await screen.findByLabelText('Message'), 'Hi{Enter}');
    expect(await screen.findByText('Invalid request')).toBeInTheDocument();
  });

  it('parses SSE event and data lines', () => {
    expect(parseEvent('event: delta\ndata: {"text":"a"}')).toEqual({
      name: 'delta',
      data: '{"text":"a"}',
    });
  });
});
