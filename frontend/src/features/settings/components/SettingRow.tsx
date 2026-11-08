import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import type { ReactNode } from 'react';

type Props = { title: string; description: string; children: ReactNode; result?: ReactNode };

export function SettingRow({ title, description, children, result }: Props) {
  return (
    <Box sx={{ py: 1.5, '&:not(:last-of-type)': { borderBottom: 1, borderColor: 'divider' } }}>
      <Box
        sx={{
          display: 'flex',
          gap: 2,
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Box sx={{ minWidth: 200, flex: 1 }}>
          <Typography component="h3" variant="subtitle1">
            {title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {description}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
          {children}
        </Box>
      </Box>
      {result && <Box sx={{ mt: 1 }}>{result}</Box>}
    </Box>
  );
}
