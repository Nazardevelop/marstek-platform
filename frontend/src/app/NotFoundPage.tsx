import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { Link } from 'react-router';

export function NotFoundPage() {
  return (
    <>
      <Typography variant="h5" component="h1" gutterBottom>
        Page not found
      </Typography>
      <Button component={Link} to="/">
        Back to dashboard
      </Button>
    </>
  );
}
