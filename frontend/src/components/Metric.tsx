import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

type Props = { label: string; value: string; big?: boolean };

export function Metric({ label, value, big = false }: Props) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary" component="div">
        {label}
      </Typography>
      <Typography variant={big ? 'h4' : 'body1'} component="div" sx={{ fontWeight: 600 }}>
        {value}
      </Typography>
    </Box>
  );
}
