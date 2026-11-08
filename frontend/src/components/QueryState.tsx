import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import { errorMessage } from '@/api/http';

type Props = { isPending: boolean; error: unknown; label?: string };

/** Loading / error placeholder for a query. Render it when `data` is not available yet. */
export function QueryState({ isPending, error, label = 'data' }: Props) {
  if (isPending) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress aria-label={`Loading ${label}`} />
      </Box>
    );
  }
  if (error)
    return (
      <Alert severity="error">
        Couldn't load {label}: {errorMessage(error)}
      </Alert>
    );
  return null;
}
