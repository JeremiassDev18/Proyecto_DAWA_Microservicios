'use client'

import { createTheme } from '@mui/material/styles'
import { palette } from './palette'
import { typography } from './typography'
import { components } from './components'
import shadows from './shadows'

export const theme = createTheme({
  palette,
  typography,
  components,
  shadows,
  shape: { borderRadius: 12 },
  spacing: (factor: number) => `${0.25 * factor}rem`,
})

export { palette } from './palette'
export { typography } from './typography'
