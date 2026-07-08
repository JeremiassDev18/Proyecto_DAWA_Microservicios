'use client'

import { CrudPageTemplate, type FormField } from '@/components/ui/CrudPageTemplate'
import { useEstudiantes } from '@/hooks/useEstudiantes'
import type { Estudiante } from '@/types/admin.types'

const formFields: FormField[] = [
  { name: 'nombres', label: 'Nombres', required: true },
  { name: 'apellidos', label: 'Apellidos', required: true },
  { name: 'email', label: 'Correo', type: 'email', required: true },
  { name: 'matricula', label: 'Matrícula', required: true },
  { name: 'carrera_id', label: 'Carrera ID', type: 'number', required: true },
  { name: 'periodo_id', label: 'Periodo ID', type: 'number', required: true },
  { name: 'activo', label: 'Estado', type: 'boolean' },
]

export default function EstudiantesPage() {
  const hook = useEstudiantes()

  return (
    <CrudPageTemplate<Estudiante>
      title="Estudiantes"
      subtitle="Gestión de estudiantes y su estado académico"
      items={hook.estudiantes}
      isLoading={hook.isLoading}
      isError={hook.isError}
      isCreating={hook.isCreating}
      isUpdating={hook.isUpdating}
      isDeleting={hook.isDeleting}
      refetch={hook.refetch}
      onCreate={hook.createEstudiante}
      onUpdate={hook.updateEstudiante}
      onDelete={hook.deleteEstudiante}
      columns={[
        { id: 'nombres', label: 'Nombres' },
        { id: 'apellidos', label: 'Apellidos' },
        { id: 'matricula', label: 'Matrícula' },
        { id: 'email', label: 'Correo' },
      ]}
      formFields={formFields}
      searchFields={['nombres', 'apellidos', 'matricula', 'email']}
      searchPlaceholder="Buscar estudiante"
      entityName="estudiante"
      createLabel="Nuevo estudiante"
      statusField="activo"
      getInitialForm={() => ({ nombres: '', apellidos: '', email: '', matricula: '', carrera_id: '', periodo_id: '', activo: true })}
    />
  )
}
