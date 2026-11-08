import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  // Follows the OS light/dark setting.
  colorSchemes: { light: true, dark: true },
  palette: { primary: { main: '#1e88e5' }, secondary: { main: '#43a047' } },
  shape: { borderRadius: 10 },
});
