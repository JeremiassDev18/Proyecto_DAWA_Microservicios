'use client'

import { Box, Button, Card, CardContent, Typography, Stack, Chip, LinearProgress } from '@mui/material'
import { Psychology, PlayArrow } from '@mui/icons-material'
import { useTraining } from '@/hooks/useTraining'
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton'

export default function EntrenamientoPage() {
  const { models, isLoadingModels, startTraining, isTraining, taskId } = useTraining()

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Entrenamiento</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Gestiona el entrenamiento del modelo de IA
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<PlayArrow />} onClick={() => startTraining()} disabled={isTraining}>
          {isTraining ? 'Entrenando...' : 'Iniciar entrenamiento'}
        </Button>
      </Box>

      {isTraining && taskId && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
              <Psychology color="primary" />
              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Entrenamiento en progreso</Typography>
                <Typography variant="caption" color="text.secondary">Task ID: {taskId}</Typography>
                <LinearProgress sx={{ mt: 1, borderRadius: 1 }} />
              </Box>
            </Stack>
          </CardContent>
        </Card>
      )}

      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Historial de modelos</Typography>

      {isLoadingModels ? (
        <LoadingSkeleton type="list" count={3} />
      ) : models.length === 0 ? (
        <Card variant="outlined" sx={{ p: 4, textAlign: 'center', borderRadius: 3 }}>
          <Psychology sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
          <Typography variant="h6" color="text.secondary">Sin modelos entrenados</Typography>
          <Typography variant="body2" color="text.disabled">Inicia un entrenamiento para generar un modelo.</Typography>
        </Card>
      ) : (
        <Stack spacing={2}>
          {models.map((model: any, index: number) => (
            <Card key={model.id ?? index} variant="outlined" sx={{ borderRadius: 3 }}>
              <CardContent>
                <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>v{model.version}</Typography>
                      {model.activo && <Chip label="Activo" color="success" size="small" />}
                    </Stack>
                    {model.accuracy && (
                      <Typography variant="caption" color="text.secondary">
                        Accuracy: {(model.accuracy * 100).toFixed(1)}%
                      </Typography>
                    )}
                  </Box>
                  <Typography variant="caption" color="text.disabled">{model.creado_en}</Typography>
                </Stack>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}
    </Box>
  )
}
