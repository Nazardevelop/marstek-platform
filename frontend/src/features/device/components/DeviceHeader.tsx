import BoltIcon from '@mui/icons-material/Bolt';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import { modeLabel } from '@/lib/format';
import { useCurrentDevice, useStatus } from '../hooks';

/** Top-bar summary: device name, online state, current mode. */
export function DeviceHeader() {
  const { device, isPending } = useCurrentDevice();
  const status = useStatus(device?.id);
  const online = status.data ? !status.data.stale : device?.online;

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
      <BoltIcon />
      <Typography variant="h6" component="div" noWrap>
        {isPending ? 'Marstek' : (device?.name ?? 'No device')}
      </Typography>
      {device && (
        <>
          <Chip
            size="small"
            label={online ? 'Online' : 'Offline'}
            color={online ? 'success' : 'default'}
            sx={{ bgcolor: online ? undefined : 'grey.500', color: 'white' }}
          />
          {status.data?.mode && (
            <Chip
              size="small"
              variant="outlined"
              label={modeLabel(status.data.mode)}
              sx={{
                color: 'inherit',
                borderColor: 'currentColor',
                display: { xs: 'none', sm: 'flex' },
              }}
            />
          )}
        </>
      )}
    </Box>
  );
}
