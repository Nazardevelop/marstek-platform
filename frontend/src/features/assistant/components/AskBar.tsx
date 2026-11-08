import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import TextField from '@mui/material/TextField';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useAssistant } from '../AssistantContext';

/** Top-bar prompt. Submitting asks the assistant and opens the drawer; the page stays put. */
export function AskBar({ compact = false }: { compact?: boolean }) {
  const { ask, openDrawer } = useAssistant();
  const [text, setText] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Cmd/Ctrl+K focuses the prompt (a global keyboard listener is an external system).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (compact) openDrawer();
        else inputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [compact, openDrawer]);

  if (compact) {
    return (
      <IconButton color="inherit" aria-label="Ask Marstek" onClick={openDrawer}>
        <AutoAwesomeIcon />
      </IconButton>
    );
  }

  const submit = (e: FormEvent) => {
    e.preventDefault();
    openDrawer();
    if (text.trim()) ask(text);
    setText('');
  };

  return (
    <form onSubmit={submit} role="search" style={{ width: '100%', maxWidth: 420 }}>
      <TextField
        inputRef={inputRef}
        size="small"
        fullWidth
        placeholder="Ask Marstek…  (⌘K)"
        value={text}
        onChange={(e) => setText(e.target.value)}
        slotProps={{
          htmlInput: { 'aria-label': 'Ask Marstek' },
          input: {
            sx: { bgcolor: 'background.paper', borderRadius: 2 },
            startAdornment: (
              <InputAdornment position="start">
                <AutoAwesomeIcon fontSize="small" />
              </InputAdornment>
            ),
          },
        }}
      />
    </form>
  );
}
