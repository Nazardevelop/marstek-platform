import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { Link } from 'react-router';
import type { Mode } from '@/api/types';
import { StatCard } from '@/components/StatCard';
import { modeLabel } from '@/lib/format';

export function ModeCard({ mode }: { mode: Mode | null }) {
  return (
    <StatCard title="Operating mode">
      <Typography variant="h4" component="div" sx={{ fontWeight: 600, mb: 2 }}>
        {modeLabel(mode)}
      </Typography>
      <Button component={Link} to="/control" variant="outlined">
        Change mode
      </Button>
    </StatCard>
  );
}
