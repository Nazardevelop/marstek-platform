import SendIcon from '@mui/icons-material/Send';
import StopIcon from '@mui/icons-material/Stop';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import TextField from '@mui/material/TextField';
import { useState, type FormEvent } from 'react';
import { useAssistant } from '../AssistantContext';

export function ChatInput({ autoFocus = false }: { autoFocus?: boolean }) {
  const { ask, isStreaming, stop } = useAssistant();
  const [text, setText] = useState('');

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!text.trim() || isStreaming) return;
    ask(text);
    setText('');
  };

  return (
    <form onSubmit={submit}>
      <TextField
        fullWidth
        size="small"
        autoFocus={autoFocus}
        label="Message"
        placeholder="Ask Marstek…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        slotProps={{
          input: {
            endAdornment: (
              <InputAdornment position="end">
                {isStreaming ? (
                  <IconButton aria-label="Stop" onClick={stop} edge="end">
                    <StopIcon />
                  </IconButton>
                ) : (
                  <IconButton aria-label="Send" type="submit" edge="end" disabled={!text.trim()}>
                    <SendIcon />
                  </IconButton>
                )}
              </InputAdornment>
            ),
          },
        }}
      />
    </form>
  );
}
