import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { errorMessage } from '@/api/http';
import { StatCard } from '@/components/StatCard';
import { useDiscoverDevices } from '@/features/device/hooks';

export function DiscoverCard() {
  const discover = useDiscoverDevices();
  return (
    <StatCard title="Discover devices">
      <Typography gutterBottom color="text.secondary">
        Broadcasts on your LAN (about 2 s) and registers every Marstek device that answers. Local
        API must be enabled in the Marstek app.
      </Typography>
      <Button variant="outlined" onClick={() => discover.mutate()} disabled={discover.isPending}>
        {discover.isPending ? 'Searching…' : 'Discover'}
      </Button>
      {discover.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {errorMessage(discover.error)}
        </Alert>
      )}
      {discover.data && (
        <Alert severity={discover.data.length ? 'success' : 'info'} sx={{ mt: 2 }}>
          {discover.data.length
            ? `Found: ${discover.data.map((d) => `${d.name} (${d.host})`).join(', ')}`
            : 'No devices answered.'}
        </Alert>
      )}
    </StatCard>
  );
}
