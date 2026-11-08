import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import type { ReactNode } from 'react';

type Props = { title: string; action?: ReactNode; children: ReactNode };

export function StatCard({ title, action, children }: Props) {
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Typography
          component="h2"
          variant="subtitle2"
          color="text.secondary"
          sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}
        >
          {title}
          {action}
        </Typography>
        {children}
      </CardContent>
    </Card>
  );
}
