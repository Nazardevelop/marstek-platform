import Box from '@mui/material/Box';
import type { ReactNode } from 'react';

/** Responsive card grid: 1 column on phones, more as space allows. */
export function CardGrid({ children, min = 280 }: { children: ReactNode; min?: number }) {
  return (
    <Box
      sx={{
        display: 'grid',
        gap: 2,
        gridTemplateColumns: { xs: '1fr', sm: `repeat(auto-fill, minmax(${min}px, 1fr))` },
      }}
    >
      {children}
    </Box>
  );
}
