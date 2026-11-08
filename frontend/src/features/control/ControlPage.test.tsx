import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { API, modeStatus } from '@/test/fixtures';
import { renderApp } from '@/test/render';
import { server } from '@/test/server';

function captureSetMode(result = { set_result: true, current: null }) {
  const bodies: unknown[] = [];
  server.use(
    http.post(`${API}/devices/:id/mode/`, async ({ request }) => {
      bodies.push(await request.json());
      return HttpResponse.json(result);
    }),
  );
  return bodies;
}

describe('Control', () => {
  it('only sends the mode after the user confirms', async () => {
    const user = userEvent.setup();
    const bodies = captureSetMode();
    renderApp('/control');

    await user.click(await screen.findByRole('button', { name: 'UPS' }));
    await user.click(screen.getByRole('button', { name: 'Activate UPS' }));
    expect(bodies).toHaveLength(0);

    const dialog = screen.getByRole('dialog');
    await user.click(within(dialog).getByRole('button', { name: 'Switch mode' }));
    expect(await screen.findByText('Mode applied.')).toBeInTheDocument();
    expect(bodies).toEqual([{ mode: 'ups' }]);
  });

  it('does nothing when the user cancels', async () => {
    const user = userEvent.setup();
    const bodies = captureSetMode();
    renderApp('/control');
    await user.click(await screen.findByRole('button', { name: 'AI' }));
    await user.click(screen.getByRole('button', { name: 'Activate AI' }));
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Cancel' }));
    expect(bodies).toHaveLength(0);
  });

  it('sends passive power and countdown in seconds', async () => {
    const user = userEvent.setup();
    const bodies = captureSetMode();
    renderApp('/control');
    await user.click(await screen.findByRole('button', { name: 'Passive' }));
    const power = screen.getByLabelText('Power (W)');
    await user.clear(power);
    await user.type(power, '-800');
    const minutes = screen.getByLabelText('Countdown (minutes)');
    await user.clear(minutes);
    await user.type(minutes, '10');
    await user.click(screen.getByRole('button', { name: 'Activate Passive' }));
    await user.click(
      within(screen.getByRole('dialog')).getByRole('button', { name: 'Switch mode' }),
    );
    await screen.findByText('Mode applied.');
    expect(bodies).toEqual([{ mode: 'passive', power_w: -800, countdown_s: 600 }]);
  });

  it('blocks a manual slot with no days before anything is sent', async () => {
    const user = userEvent.setup();
    captureSetMode();
    renderApp('/control');
    await user.click(await screen.findByRole('button', { name: 'Manual' }));
    const slot = screen.getByRole('group', { name: 'Slot 1' });
    for (const day of ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']) {
      await user.click(within(slot).getByRole('button', { name: day }));
    }
    expect(within(slot).getByRole('alert')).toHaveTextContent('Pick at least one day');
    expect(screen.getByRole('button', { name: 'Activate Manual' })).toBeDisabled();
  });

  it('warns when the device rejects the change', async () => {
    const user = userEvent.setup();
    captureSetMode({ set_result: false, current: null });
    server.use(
      http.get(`${API}/devices/:id/mode/`, () => HttpResponse.json({ ...modeStatus, mode: 'ai' })),
    );
    renderApp('/control');
    await screen.findByText('AI', { selector: 'p' });
    await user.click(screen.getByRole('button', { name: 'Auto' }));
    await user.click(screen.getByRole('button', { name: 'Activate Auto' }));
    await user.click(
      within(screen.getByRole('dialog')).getByRole('button', { name: 'Switch mode' }),
    );
    expect(await screen.findByText(/device rejected the change/)).toBeInTheDocument();
  });
});
