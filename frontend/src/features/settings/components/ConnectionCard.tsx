import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import { useState, type FormEvent } from 'react';
import type { Device } from '@/api/types';
import { StatCard } from '@/components/StatCard';
import { WriteResult } from '@/components/WriteResult';
import { usePatchDevice } from '@/features/device/hooks';

/** Name and address the backend uses. Doesn't touch the device itself. */
export function ConnectionCard({ device }: { device: Device }) {
  const patch = usePatchDevice(device.id);
  const [name, setName] = useState(device.name ?? '');
  const [host, setHost] = useState(device.host ?? '');
  const [port, setPort] = useState(String(device.port ?? 30000));

  const portNum = Number(port);
  const portError = !Number.isInteger(portNum) || portNum < 1 || portNum > 65535;
  const dirty = name !== device.name || host !== device.host || portNum !== device.port;

  const submit = (e: FormEvent) => {
    e.preventDefault();
    patch.mutate({ name: name.trim(), host: host.trim(), port: portNum });
  };

  return (
    <StatCard title="Connection">
      <Box
        component="form"
        onSubmit={submit}
        sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'flex-start' }}
      >
        <TextField
          size="small"
          label="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <TextField
          size="small"
          label="IP / host"
          value={host}
          onChange={(e) => setHost(e.target.value)}
          required
        />
        <TextField
          size="small"
          label="UDP port"
          type="number"
          value={port}
          onChange={(e) => setPort(e.target.value)}
          error={portError}
          helperText={portError ? '1–65535' : ' '}
          sx={{ width: 120 }}
        />
        <Button type="submit" variant="contained" disabled={!dirty || portError || patch.isPending}>
          Save
        </Button>
      </Box>
      <WriteResult
        isSuccess={patch.isSuccess}
        isError={patch.isError}
        error={patch.error}
        setResult={patch.isSuccess}
        successText="Saved."
      />
    </StatCard>
  );
}
