import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import DashboardIcon from '@mui/icons-material/Dashboard';
import InsightsIcon from '@mui/icons-material/Insights';
import SettingsIcon from '@mui/icons-material/Settings';
import TuneIcon from '@mui/icons-material/Tune';

export const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', Icon: DashboardIcon },
  { to: '/control', label: 'Control', Icon: TuneIcon },
  { to: '/stats', label: 'Statistics', Icon: InsightsIcon },
  { to: '/assistant', label: 'Assistant', Icon: AutoAwesomeIcon },
  { to: '/settings', label: 'Settings', Icon: SettingsIcon },
] as const;
