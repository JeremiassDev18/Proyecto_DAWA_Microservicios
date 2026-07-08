import type { Components, Theme } from '@mui/material/styles'

export const components: Components<Theme> = {
  MuiButton: {
    defaultProps: { disableElevation: true },
    styleOverrides: {
      root: {
        borderRadius: 12,
        padding: '10px 20px',
        fontWeight: 600,
        fontSize: '0.875rem',
        transition: 'all 150ms ease',
        '&:active': { transform: 'scale(0.97)' },
      },
      contained: {
        boxShadow: '0 1px 2px 0 rgba(0,0,0,0.05)',
        '&:hover': { boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' },
      },
      outlined: {
        borderWidth: 1.5,
        '&:hover': { borderWidth: 1.5 },
      },
      sizeSmall: { padding: '6px 14px', fontSize: '0.8125rem' },
      sizeLarge: { padding: '12px 28px', fontSize: '0.9375rem' },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: 16,
        boxShadow: '0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.04)',
        transition: 'box-shadow 150ms ease, transform 150ms ease',
        '&:hover': {
          boxShadow: '0 10px 15px -3px rgba(0,0,0,0.06), 0 4px 6px -4px rgba(0,0,0,0.04)',
        },
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: { borderRadius: 14 },
      elevation1: {
        boxShadow: '0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.04)',
      },
    },
  },
  MuiTextField: {
    defaultProps: { variant: 'outlined' },
    styleOverrides: {
      root: ({ theme }) => ({
        '& .MuiOutlinedInput-root': {
          borderRadius: 12,
          transition: 'all 150ms ease',
          '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: theme.palette.grey[400] },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderWidth: 2 },
        },
      }),
    },
  },
  MuiSelect: {
    defaultProps: { variant: 'outlined' },
    styleOverrides: {
      root: { borderRadius: 12 },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: { borderRadius: 8, fontWeight: 500, fontSize: '0.75rem' },
      filled: { '&:hover': { filter: 'brightness(0.95)' } },
    },
  },
  MuiDialog: {
    styleOverrides: {
      paper: { borderRadius: 16, padding: 4 },
    },
  },
  MuiDialogTitle: {
    styleOverrides: {
      root: { fontSize: '1.125rem', fontWeight: 600, paddingBottom: 8 },
    },
  },
  MuiDrawer: {
    styleOverrides: {
      paper: ({ theme }) => ({
        border: 'none',
        borderRight: `1px solid ${theme.palette.divider}`,
      }),
    },
  },
  MuiAppBar: {
    styleOverrides: {
      root: ({ theme }) => ({
        boxShadow: '0 1px 3px 0 rgba(0,0,0,0.04)',
        backdropFilter: 'blur(12px)',
        backgroundColor: theme.palette.background.paper + 'd9',
        borderBottom: `1px solid ${theme.palette.divider}`,
      }),
    },
  },
  MuiTableHead: {
    styleOverrides: {
      root: ({ theme }) => ({
        '& .MuiTableCell-head': {
          fontWeight: 600,
          fontSize: '0.75rem',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          color: theme.palette.grey[500],
          backgroundColor: theme.palette.grey[50],
        },
      }),
    },
  },
  MuiTableCell: {
    styleOverrides: {
      root: { padding: '12px 16px', fontSize: '0.875rem' },
    },
  },
  MuiTableRow: {
    styleOverrides: {
      root: ({ theme }) => ({
        transition: 'background-color 150ms ease',
        '&:hover': { backgroundColor: theme.palette.grey[50] },
      }),
    },
  },
  MuiTooltip: {
    styleOverrides: {
      tooltip: ({ theme }) => ({
        borderRadius: 8,
        padding: '6px 12px',
        fontSize: '0.75rem',
        backgroundColor: theme.palette.grey[800],
      }),
    },
  },
  MuiAvatar: {
    styleOverrides: {
      root: { borderRadius: 10 },
    },
  },
  MuiListItemButton: {
    styleOverrides: {
      root: { borderRadius: 10, margin: '2px 8px' },
    },
  },
}
