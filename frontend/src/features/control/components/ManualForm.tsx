import AddIcon from '@mui/icons-material/Add';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { useState } from 'react';
import type { ManualSlot } from '@/api/types';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { useSetMode } from '../hooks';
import { newSlot, slotError } from '../slots';
import { ModeWriteFeedback } from './ModeWriteFeedback';
import { SlotEditor } from './SlotEditor';

type Props = { deviceId: number; maxSlots: number; withAction: boolean };

export function ManualForm({ deviceId, maxSlots, withAction }: Props) {
  const setMode = useSetMode(deviceId);
  const [slots, setSlots] = useState<ManualSlot[]>(() => [newSlot([], withAction)]);
  const [confirming, setConfirming] = useState(false);

  const invalid = slots.length === 0 || slots.some((s) => slotError(s) !== null);
  const update = (index: number, next: ManualSlot) =>
    setSlots((ss) => ss.map((s) => (s.index === index ? next : s)));
  const remove = (index: number) => setSlots((ss) => ss.filter((s) => s.index !== index));

  return (
    <>
      <Typography gutterBottom>
        Up to {maxSlots} time slots. Each slot is sent to the device as its own command.
      </Typography>
      <Box sx={{ display: 'grid', gap: 2, my: 2 }}>
        {slots.map((s) => (
          <SlotEditor
            key={s.index}
            slot={s}
            withAction={withAction}
            onChange={(next) => update(s.index, next)}
            onRemove={slots.length > 1 ? () => remove(s.index) : undefined}
          />
        ))}
      </Box>
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Button
          startIcon={<AddIcon />}
          disabled={slots.length >= maxSlots}
          onClick={() => setSlots((ss) => [...ss, newSlot(ss, withAction)])}
        >
          Add slot
        </Button>
        <Button
          variant="contained"
          disabled={invalid || setMode.isPending}
          onClick={() => setConfirming(true)}
        >
          {setMode.isPending ? 'Applying…' : 'Activate Manual'}
        </Button>
      </Box>
      <ModeWriteFeedback data={setMode.data} error={setMode.error} isError={setMode.isError} />
      <ConfirmDialog
        open={confirming}
        title="Switch to Manual?"
        confirmLabel="Program slots"
        onClose={() => setConfirming(false)}
        onConfirm={() => {
          setConfirming(false);
          setMode.mutate({ mode: 'manual', slots });
        }}
      >
        {slots.length} slot(s) will be written to the device, one <code>ES.SetMode</code> call each.
      </ConfirmDialog>
    </>
  );
}
