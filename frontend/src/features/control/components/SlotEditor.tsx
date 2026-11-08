import DeleteIcon from '@mui/icons-material/Delete';
import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from '@mui/material/IconButton';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Typography from '@mui/material/Typography';
import type { ManualSlot, SlotAction, Weekday } from '@/api/types';
import { slotError, WEEKDAYS } from '../slots';

type Props = {
  slot: ManualSlot;
  withAction: boolean;
  onChange: (slot: ManualSlot) => void;
  onRemove?: () => void;
};

const ACTIONS: SlotAction[] = ['charge', 'discharge', 'auto', 'disable'];

export function SlotEditor({ slot, withAction, onChange, onRemove }: Props) {
  const error = slotError(slot);
  const n = slot.index + 1;
  const set = <K extends keyof ManualSlot>(key: K, value: ManualSlot[K]) =>
    onChange({ ...slot, [key]: value });

  return (
    <Paper variant="outlined" sx={{ p: 2 }} role="group" aria-label={`Slot ${n}`}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
        <Typography variant="subtitle2" sx={{ flex: 1 }}>
          Slot {n}
        </Typography>
        <FormControlLabel
          control={
            <Switch checked={slot.enabled} onChange={(e) => set('enabled', e.target.checked)} />
          }
          label="Enabled"
        />
        {onRemove && (
          <IconButton aria-label={`Remove slot ${n}`} onClick={onRemove}>
            <DeleteIcon />
          </IconButton>
        )}
      </Box>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 1.5 }}>
        <TextField
          label="Start"
          type="time"
          size="small"
          value={slot.start}
          onChange={(e) => set('start', e.target.value)}
        />
        <TextField
          label="End"
          type="time"
          size="small"
          value={slot.end}
          onChange={(e) => set('end', e.target.value)}
        />
        <TextField
          label="Power (W)"
          type="number"
          size="small"
          value={slot.power_w}
          onChange={(e) => set('power_w', Number(e.target.value))}
          sx={{ width: 130 }}
        />
        {withAction && (
          <TextField
            select
            label="Action"
            size="small"
            value={slot.action ?? 'charge'}
            onChange={(e) => set('action', e.target.value as SlotAction)}
            sx={{ width: 150 }}
          >
            {ACTIONS.map((a) => (
              <MenuItem key={a} value={a}>
                {a[0]?.toUpperCase() + a.slice(1)}
              </MenuItem>
            ))}
          </TextField>
        )}
      </Box>
      <ToggleButtonGroup
        size="small"
        value={slot.weekdays}
        onChange={(_, days: Weekday[]) => set('weekdays', days)}
        aria-label={`Slot ${n} days`}
        sx={{ flexWrap: 'wrap' }}
      >
        {WEEKDAYS.map((d) => (
          <ToggleButton key={d.value} value={d.value}>
            {d.label}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>
      {error && (
        <Typography color="error" variant="body2" sx={{ mt: 1 }} role="alert">
          {error}
        </Typography>
      )}
    </Paper>
  );
}
