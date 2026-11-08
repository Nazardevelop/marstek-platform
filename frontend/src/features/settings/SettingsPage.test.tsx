import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { API, device } from '@/test/fixtures';
import { renderApp } from '@/test/render';
import { server } from '@/test/server';

describe('Settings', () => {
  it('shows device and network info', async () => {
    renderApp('/settings');
    expect(await screen.findByText('VenusD')).toBeInTheDocument();
    expect(await screen.findByText('Good (-59 dBm)')).toBeInTheDocument();
  });

  it('hides system settings and factory reset when the model lacks them', async () => {
    const limited = {
      ...device,
      capabilities: { ...device.capabilities, system_settings: false, factory_reset: false },
    };
    server.use(
      http.get(`${API}/devices/`, () => HttpResponse.json([limited])),
      http.get(`${API}/devices/:id/`, () => HttpResponse.json(limited)),
    );
    renderApp('/settings');
    await screen.findByText('VenusD');
    expect(screen.queryByText('System settings')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Factory reset…' })).not.toBeInTheDocument();
  });

  it('requires typing the exact device name before a factory reset', async () => {
    const user = userEvent.setup();
    const bodies: unknown[] = [];
    server.use(
      http.post(`${API}/devices/:id/factory-reset/`, async ({ request }) => {
        bodies.push(await request.json());
        return HttpResponse.json({ set_result: true });
      }),
    );
    renderApp('/settings');
    await user.click(await screen.findByRole('button', { name: 'Factory reset…' }));
    const dialog = screen.getByRole('dialog');
    const confirm = within(dialog).getByRole('button', { name: 'Reset device' });
    expect(confirm).toBeDisabled();

    await user.type(within(dialog).getByLabelText(/Type "Venus" to confirm/), 'venus');
    expect(confirm).toBeDisabled();
    await user.clear(within(dialog).getByLabelText(/Type "Venus" to confirm/));
    await user.type(within(dialog).getByLabelText(/Type "Venus" to confirm/), 'Venus');
    await user.click(confirm);

    expect(await screen.findByText('Reset command accepted.')).toBeInTheDocument();
    expect(bodies).toEqual([{ type: 2, confirm_name: 'Venus' }]);
  });

  it('sends LED off only after confirmation', async () => {
    const user = userEvent.setup();
    const bodies: unknown[] = [];
    server.use(
      http.post(`${API}/devices/:id/settings/led/`, async ({ request }) => {
        bodies.push(await request.json());
        return HttpResponse.json({ set_result: true });
      }),
    );
    renderApp('/settings');
    const row = (await screen.findByRole('heading', { name: 'Panel LEDs' })).closest(
      'div',
    )!.parentElement!;
    await user.click(within(row.parentElement!).getByRole('button', { name: 'Turn off' }));
    expect(bodies).toHaveLength(0);
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Confirm' }));
    expect(await screen.findByText('Applied.')).toBeInTheDocument();
    expect(bodies).toEqual([{ on: false }]);
  });
});
