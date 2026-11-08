import { screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { API, device, status } from '@/test/fixtures';
import { renderApp } from '@/test/render';
import { server } from '@/test/server';

describe('Dashboard', () => {
  it('shows live battery and mode data', async () => {
    renderApp('/');
    expect(await screen.findByText('82%')).toBeInTheDocument();
    expect(screen.getByText('4.20 kWh')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Change mode' })).toHaveAttribute('href', '/control');
    expect(screen.getByText('CT not connected.')).toBeInTheDocument();
  });

  it('shows PV inputs only when the model has PV', async () => {
    const limited = { ...device, capabilities: { ...device.capabilities, pv: false } };
    server.use(
      http.get(`${API}/devices/`, () => HttpResponse.json([limited])),
      http.get(`${API}/devices/:id/`, () => HttpResponse.json(limited)),
    );
    renderApp('/');
    await screen.findByText('82%');
    expect(screen.queryByText('Solar inputs')).not.toBeInTheDocument();
  });

  it('shows the offline banner with last-known values when the device is stale', async () => {
    server.use(
      http.get(`${API}/devices/:id/status/`, () => HttpResponse.json({ ...status, stale: true })),
    );
    renderApp('/');
    expect(await screen.findByText(/Device unreachable/)).toBeInTheDocument();
    expect(screen.getByText('82%')).toBeInTheDocument();
  });

  it('shows an error when the status request fails', async () => {
    server.use(
      http.get(`${API}/devices/:id/status/`, () =>
        HttpResponse.json(
          { code: 'device_unreachable', message: 'Device did not respond' },
          { status: 504 },
        ),
      ),
    );
    renderApp('/');
    expect(await screen.findByText(/Device did not respond/)).toBeInTheDocument();
  });

  it('asks to run discovery when no device is registered', async () => {
    server.use(http.get(`${API}/devices/`, () => HttpResponse.json([])));
    renderApp('/');
    expect(await screen.findByText(/No device registered yet/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Find devices' })).toHaveAttribute('href', '/settings');
  });
});
