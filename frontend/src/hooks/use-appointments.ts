'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Appointment } from '@/types/api';
import api from '@/lib/api';

export function useAppointments() {
  const queryClient = useQueryClient();

  // Fetch appointments
  const { data: appointments = [], isLoading, error } = useQuery<Appointment[]>({
    queryKey: ['appointments'],
    queryFn: async () => {
      try {
        const res = await api.get('/appointments');
        const rawItems = Array.isArray(res.data) ? res.data : (res.data.items || []);
        
        return rawItems.map((apt: any) => ({
          id: apt.id,
          patientId: apt.patient_id,
          patientName: apt.patient?.full_name || 'Guest Patient',
          patientPhone: apt.patient?.phone || '',
          doctorId: apt.doctor_id,
          doctorName: apt.doctor?.full_name || 'Attending Staff',
          department: apt.department?.name || 'General Medicine',
          date: apt.appointment_date || '',
          time: apt.start_time ? apt.start_time.substring(0, 5) : '00:00',
          duration: 30,
          status: apt.status || 'scheduled',
          type: apt.appointment_type || 'consultation',
          bookedVia: apt.booked_via || 'ai-voice',
          notes: apt.notes || apt.symptoms || '',
          createdAt: apt.created_at || new Date().toISOString(),
        }));
      } catch (err) {
        console.warn('API error fetching appointments:', err);
        return [];
      }
    },
  });

  // Mutate: Update Appointment Status
  const updateStatusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: Appointment['status'] }) => {
      const res = await api.patch(`/appointments/${id}/status`, { status });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
    },
  });

  // Mutate: Add new appointment
  const createAppointmentMutation = useMutation({
    mutationFn: async (newApt: Omit<Appointment, 'id' | 'createdAt'>) => {
      const res = await api.post('/appointments', newApt);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
    },
  });

  return {
    appointments,
    isLoading,
    error,
    updateStatus: updateStatusMutation.mutate,
    isUpdating: updateStatusMutation.isPending,
    createAppointment: createAppointmentMutation.mutate,
    isCreating: createAppointmentMutation.isPending,
  };
}
