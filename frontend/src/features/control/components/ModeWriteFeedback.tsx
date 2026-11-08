import Alert from '@mui/material/Alert';
import { errorMessage } from '@/api/http';
import type { ModeWriteResult } from '@/api/types';

type Props = { data: ModeWriteResult | undefined; error: unknown; isError: boolean };

export function ModeWriteFeedback({ data, error, isError }: Props) {
  if (isError)
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {errorMessage(error)}
      </Alert>
    );
  if (!data) return null;
  if (data.set_result)
    return (
      <Alert severity="success" sx={{ mt: 2 }}>
        Mode applied.
      </Alert>
    );
  const failed = data.slots?.filter((s) => !s.set_result).map((s) => s.index + 1) ?? [];
  return (
    <Alert severity="warning" sx={{ mt: 2 }}>
      The device rejected the change{failed.length ? ` for slot(s) ${failed.join(', ')}` : ''}.
    </Alert>
  );
}
