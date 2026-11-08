import Alert from '@mui/material/Alert';
import { errorMessage } from '@/api/http';

type Props = {
  isSuccess: boolean;
  isError: boolean;
  error: unknown;
  setResult: boolean | undefined;
  successText?: string;
};

/** Shows the outcome of a hardware write: HTTP error, device refused (set_result=false), or OK. */
export function WriteResult({
  isSuccess,
  isError,
  error,
  setResult,
  successText = 'Applied.',
}: Props) {
  if (isError) return <Alert severity="error">{errorMessage(error)}</Alert>;
  if (!isSuccess) return null;
  return setResult ? (
    <Alert severity="success">{successText}</Alert>
  ) : (
    <Alert severity="warning">The device rejected the change (set_result = false).</Alert>
  );
}
