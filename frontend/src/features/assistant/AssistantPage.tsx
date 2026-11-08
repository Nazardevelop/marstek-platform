import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { useAssistant } from './AssistantContext';
import { ChatInput } from './components/ChatInput';
import { ChatThread } from './components/ChatThread';

export function AssistantPage() {
  const { clear, messages } = useAssistant();
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: { xs: 'calc(100dvh - 180px)', md: 'calc(100dvh - 120px)' },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" component="h1" sx={{ flex: 1 }}>
          Assistant
        </Typography>
        <Button startIcon={<DeleteSweepIcon />} onClick={clear} disabled={messages.length === 0}>
          New chat
        </Button>
      </Box>
      <Paper variant="outlined" sx={{ flex: 1, overflowY: 'auto', mb: 2 }}>
        <ChatThread showSuggestions />
      </Paper>
      <ChatInput />
    </Box>
  );
}
