import CloseIcon from '@mui/icons-material/Close';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import OpenInFullIcon from '@mui/icons-material/OpenInFull';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useNavigate } from 'react-router';
import { useAssistant } from '../AssistantContext';
import { ChatInput } from './ChatInput';
import { ChatThread } from './ChatThread';

export function AssistantDrawer() {
  const { drawerOpen, closeDrawer, clear } = useAssistant();
  const navigate = useNavigate();
  const theme = useTheme();
  const mobile = useMediaQuery(theme.breakpoints.down('sm'));

  const expand = () => {
    closeDrawer();
    void navigate('/assistant');
  };

  return (
    <Drawer
      anchor="right"
      open={drawerOpen}
      onClose={closeDrawer}
      // The app bar sits above the sidebar (drawer + 1); this overlay must sit above both.
      sx={{ zIndex: (t) => t.zIndex.modal }}
      slotProps={{ paper: { sx: { width: mobile ? '100%' : 420 } } }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', px: 2, py: 1, gap: 0.5 }}>
        <Typography variant="h6" component="h2" sx={{ flex: 1 }}>
          Assistant
        </Typography>
        <Tooltip title="Clear conversation">
          <IconButton aria-label="Clear conversation" onClick={clear}>
            <DeleteSweepIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Open full page">
          <IconButton aria-label="Expand" onClick={expand}>
            <OpenInFullIcon />
          </IconButton>
        </Tooltip>
        <IconButton aria-label="Close assistant" onClick={closeDrawer}>
          <CloseIcon />
        </IconButton>
      </Box>
      <Divider />
      <Box sx={{ flex: 1, overflowY: 'auto' }}>
        <ChatThread showSuggestions />
      </Box>
      <Divider />
      <Box sx={{ p: 2 }}>
        <ChatInput autoFocus />
      </Box>
    </Drawer>
  );
}
