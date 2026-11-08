import AppBar from '@mui/material/AppBar';
import BottomNavigation from '@mui/material/BottomNavigation';
import BottomNavigationAction from '@mui/material/BottomNavigationAction';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Paper from '@mui/material/Paper';
import Toolbar from '@mui/material/Toolbar';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { NavLink, Outlet, useLocation } from 'react-router';
import { AskBar } from '@/features/assistant/components/AskBar';
import { AssistantDrawer } from '@/features/assistant/components/AssistantDrawer';
import { DeviceHeader } from '@/features/device/components/DeviceHeader';
import { OfflineBanner } from '@/features/device/components/OfflineBanner';
import { NAV_ITEMS } from './nav';

const SIDEBAR_W = 220;

function activeNav(pathname: string) {
  return (
    NAV_ITEMS.find((i) => (i.to === '/' ? pathname === '/' : pathname.startsWith(i.to)))?.to ?? '/'
  );
}

export function AppShell() {
  const theme = useTheme();
  const desktop = useMediaQuery(theme.breakpoints.up('md'));
  const { pathname } = useLocation();
  const current = activeNav(pathname);

  return (
    <Box sx={{ display: 'flex', minHeight: '100dvh' }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar sx={{ gap: 2 }}>
          <DeviceHeader />
          <Box sx={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
            <AskBar compact={!desktop} />
          </Box>
        </Toolbar>
      </AppBar>

      {desktop && (
        <Drawer
          variant="permanent"
          sx={{ width: SIDEBAR_W, flexShrink: 0, '& .MuiDrawer-paper': { width: SIDEBAR_W } }}
        >
          <Toolbar />
          <nav aria-label="Main">
            <List>
              {NAV_ITEMS.map(({ to, label, Icon }) => (
                <ListItemButton key={to} component={NavLink} to={to} selected={current === to}>
                  <ListItemIcon>
                    <Icon />
                  </ListItemIcon>
                  <ListItemText primary={label} />
                </ListItemButton>
              ))}
            </List>
          </nav>
        </Drawer>
      )}

      <Box
        component="main"
        sx={{ flex: 1, minWidth: 0, p: { xs: 2, md: 3 }, pb: { xs: 10, md: 3 } }}
      >
        <Toolbar />
        <OfflineBanner />
        <Outlet />
      </Box>

      {!desktop && (
        <Paper
          component="nav"
          aria-label="Main"
          elevation={3}
          sx={{ position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: (t) => t.zIndex.appBar }}
        >
          <BottomNavigation value={current} showLabels>
            {NAV_ITEMS.map(({ to, label, Icon }) => (
              <BottomNavigationAction
                key={to}
                component={NavLink}
                to={to}
                value={to}
                label={label}
                icon={<Icon />}
              />
            ))}
          </BottomNavigation>
        </Paper>
      )}

      <AssistantDrawer />
    </Box>
  );
}
