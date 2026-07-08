'use client'

import { useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import {
  Box, Drawer, AppBar, Toolbar, Typography, IconButton,
  Avatar, Menu, MenuItem, List, ListItem, ListItemIcon,
  ListItemText, Divider,
} from '@mui/material'
import { Menu as MenuIcon, Logout, Person } from '@mui/icons-material'
import { useAuth } from '@/hooks/useAuth'
import { menuItems } from '@/config/menu'
import { DRAWER_WIDTH, APP_NAME } from '@/config/constants'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  const handleDrawerToggle = () => setMobileOpen(!mobileOpen)
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => setAnchorEl(event.currentTarget)
  const handleMenuClose = () => setAnchorEl(null)

  const handleLogout = async () => {
    handleMenuClose()
    await logout()
  }

  const currentItem = menuItems
    .filter((item) => {
      if (!item.roles) return true
      return user?.roles?.some((r) => item.roles!.includes(r))
    })
    .find((item) => {
      if (item.path === '/') return pathname === '/'
      return pathname.startsWith(item.path)
    })

  const drawer = (
    <Box>
      <Toolbar sx={{ justifyContent: 'center' }}>
        <Typography
          variant="h6"
          sx={{ fontWeight: 800, letterSpacing: '-0.03em', cursor: 'pointer' }}
          color="primary"
          onClick={() => router.push('/')}
        >
          {APP_NAME}
        </Typography>
      </Toolbar>
      <Divider />
      <List sx={{ px: 1 }}>
        {menuItems
          .filter((item) => {
            if (!item.roles) return true
            return user?.roles?.some((r) => item.roles!.includes(r))
          })
          .map((item) => {
          const isActive = item.path === '/'
            ? pathname === '/'
            : pathname.startsWith(item.path)
          return (
            <ListItem
              key={item.path}
              component="a"
              href={item.path}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                cursor: 'pointer',
                transition: 'all 150ms ease',
                bgcolor: isActive ? 'action.selected' : 'transparent',
                color: isActive ? 'primary.main' : 'text.secondary',
                '&:hover': {
                  bgcolor: isActive ? 'action.selected' : 'action.hover',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40, color: 'inherit' }}>
                <item.icon sx={{ fontSize: 20 }} />
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                slotProps={{ primary: { sx: { fontSize: '0.875rem', fontWeight: isActive ? 600 : 500 } } }}
              />
            </ListItem>
          )
        })}
      </List>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar
        position="fixed"
        color="inherit"
        sx={{
          width: { sm: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { sm: `${DRAWER_WIDTH}px` },
          bgcolor: 'background.paper',
          opacity: 0.95,
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, fontWeight: 600, fontSize: '1rem' }}>
            {currentItem?.label || 'Dashboard'}
          </Typography>
          <IconButton onClick={handleMenuOpen} color="inherit" size="small">
            <Avatar sx={{ width: 34, height: 34, bgcolor: 'primary.main', fontSize: '0.875rem', fontWeight: 700 }}>
              {user?.nombre?.[0]?.toUpperCase() || 'U'}
            </Avatar>
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            slotProps={{ paper: { sx: { mt: 1, borderRadius: 3, minWidth: 180 } } }}
          >
            <Box sx={{ px: 2, py: 1 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>{user?.nombre}</Typography>
              <Typography variant="caption" color="text.secondary">{user?.email}</Typography>
            </Box>
            <Divider />
            <MenuItem onClick={() => { handleMenuClose(); router.push('/perfil'); }} sx={{ borderRadius: 2, mx: 1 }}>
              <ListItemIcon><Person fontSize="small" /></ListItemIcon>
              <ListItemText>Mi Perfil</ListItemText>
            </MenuItem>
            <MenuItem onClick={handleLogout} sx={{ borderRadius: 2, mx: 1 }}>
              <ListItemIcon><Logout fontSize="small" /></ListItemIcon>
              <ListItemText>Cerrar Sesión</ListItemText>
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { sm: DRAWER_WIDTH }, flexShrink: { sm: 0 } }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{ display: { xs: 'block', sm: 'none' }, '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH } }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH, border: 'none', borderRight: '1px solid', borderColor: 'divider' },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, sm: 3 },
          width: { sm: `calc(100% - ${DRAWER_WIDTH}px)` },
          mt: '64px',
        }}
      >
        {children}
      </Box>
    </Box>
  )
}
