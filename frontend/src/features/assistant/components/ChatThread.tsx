import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { useEffect, useRef } from 'react';
import { useAssistant } from '../AssistantContext';

const SUGGESTIONS = [
  'How much did I export to the grid this week?',
  'What is my battery doing right now?',
  'When was solar production highest today?',
];

type Props = { showSuggestions?: boolean };

export function ChatThread({ showSuggestions = false }: Props) {
  const { messages, isStreaming, error, ask } = useAssistant();
  const endRef = useRef<HTMLDivElement>(null);

  // Syncing with the DOM (an external system): keep the newest message in view.
  useEffect(() => {
    endRef.current?.scrollIntoView?.({ block: 'end' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography color="text.secondary" gutterBottom>
          Ask anything about your power station.
        </Typography>
        {showSuggestions && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 2 }}>
            {SUGGESTIONS.map((s) => (
              <Paper
                key={s}
                component="button"
                type="button"
                variant="outlined"
                onClick={() => ask(s)}
                sx={{
                  p: 1.5,
                  textAlign: 'left',
                  cursor: 'pointer',
                  font: 'inherit',
                  bgcolor: 'transparent',
                }}
              >
                {s}
              </Paper>
            ))}
          </Box>
        )}
      </Box>
    );
  }

  return (
    <Box
      role="log"
      aria-live="polite"
      aria-busy={isStreaming}
      sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, p: 2 }}
    >
      {messages.map((m) => (
        <Paper
          key={m.id}
          elevation={0}
          sx={{
            p: 1.5,
            maxWidth: '85%',
            alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
            bgcolor: m.role === 'user' ? 'primary.main' : 'action.hover',
            color: m.role === 'user' ? 'primary.contrastText' : 'text.primary',
            whiteSpace: 'pre-wrap',
          }}
        >
          {m.content || (isStreaming ? '…' : '')}
        </Paper>
      ))}
      {error && <Alert severity="error">{error}</Alert>}
      <div ref={endRef} />
    </Box>
  );
}
