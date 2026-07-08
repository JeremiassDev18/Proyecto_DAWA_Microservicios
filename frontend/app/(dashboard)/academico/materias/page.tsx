'use client'

import { Box, Card, CardContent, Typography, Stack, Chip, Grid } from '@mui/material'
import { School, Book, TrendingUp, Person } from '@mui/icons-material'
import { useStudent } from '@/hooks/useStudent'
import { useAuth } from '@/hooks/useAuth'
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton'
import { ErrorState } from '@/components/ui/ErrorState'

export default function MateriasPage() {
  const { user } = useAuth()
  const { materias, carrera, isLoading, isError, refetch } = useStudent()

  if (isError) {
    return <ErrorState title="Error al cargar materias" message="No se pudieron cargar tus materias." onRetry={() => refetch()} />
  }

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>Mis Materias</Typography>
        {carrera && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Carrera: {carrera.nombre}
          </Typography>
        )}
      </Box>

      {isLoading ? (
        <LoadingSkeleton type="card" count={4} />
      ) : materias.length === 0 ? (
        <Card variant="outlined" sx={{ p: 4, textAlign: 'center', borderRadius: 3 }}>
          <Book sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
          <Typography variant="h6" color="text.secondary">Sin materias asignadas</Typography>
          <Typography variant="body2" color="text.disabled">
            No hay materias registradas para tu carrera y período actual.
          </Typography>
        </Card>
      ) : (
        <Grid container spacing={2}>
          {materias.map((materia: any) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={materia.id}>
              <Card variant="outlined" sx={{ borderRadius: 3, height: '100%' }}>
                <CardContent>
                  <Stack spacing={1}>
                    <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {materia.nombre}
                      </Typography>
                      <Chip label={materia.codigo} size="small" variant="outlined" />
                    </Stack>
                    {materia.nivel && (
                      <Typography variant="caption" color="text.secondary">
                        Nivel: {materia.nivel}
                      </Typography>
                    )}
                    {materia.creditos && (
                      <Typography variant="caption" color="text.secondary">
                        Créditos: {materia.creditos}
                      </Typography>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  )
}
