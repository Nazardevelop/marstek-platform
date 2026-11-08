import Typography from '@mui/material/Typography';

export function PageTitle({ children }: { children: string }) {
  return (
    <Typography variant="h5" component="h1" sx={{ mb: 2 }}>
      {children}
    </Typography>
  );
}
