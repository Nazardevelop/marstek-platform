import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

type Props = { rows: [label: string, value: string | number | null | undefined][] };

export function InfoList({ rows }: Props) {
  return (
    <Box
      component="dl"
      sx={{
        m: 0,
        display: 'grid',
        gridTemplateColumns: 'minmax(110px, auto) 1fr',
        rowGap: 1,
        columnGap: 2,
      }}
    >
      {rows.map(([label, value]) => (
        <Box key={label} sx={{ display: 'contents' }}>
          <Typography component="dt" color="text.secondary">
            {label}
          </Typography>
          <Typography component="dd" sx={{ m: 0, wordBreak: 'break-all' }}>
            {value === null || value === undefined || value === '' ? '—' : value}
          </Typography>
        </Box>
      ))}
    </Box>
  );
}
