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
      // Map frontend status values to backend AppointmentStatus
      // Frontend might use "scheduled" or "confirmed", backend uses: pending, confirmed, completed, cancelled, no_show
      let backendStatus = status.toLowerCase();
      if (backendStatus === 'scheduled') backendStatus = 'confirmed';
      const res = await api.put(`/appointments/${id}`, { status: backendStatus });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
    },
  });

  // Mutate: Add new appointment
  const createAppointmentMutation = useMutation({
    mutationFn: async (newApt: any) => {
      const startTimeStr = newApt.time || newApt.startTime; // format: "HH:MM"
      let endTimeStr = newApt.endTime;
      if (!endTimeStr && startTimeStr) {
        const [hours, minutes] = startTimeStr.split(':').map(Number);
        const endMinutes = (minutes + 30) % 60;
        const endHours = hours + Math.floor((minutes + 30) / 60);
        endTimeStr = `${String(endHours).padStart(2, '0')}:${String(endMinutes).padStart(2, '0')}:00`;
      }
      
      const payload = {
        patient_id: newApt.patientId,
        doctor_id: newApt.doctorId,
        slot_id: newApt.slotId,
        department_id: newApt.departmentId,
        appointment_date: newApt.date || newApt.appointmentDate,
        start_time: startTimeStr ? (startTimeStr.length === 5 ? `${startTimeStr}:00` : startTimeStr).substring(0, 8) : null,
        end_time: endTimeStr ? (endTimeStr.length === 5 ? `${endTimeStr}:00` : endTimeStr).substring(0, 8) : null,
        symptoms: newApt.symptoms || null,
        notes: newApt.notes || null,
      };
      const res = await api.post('/appointments', payload);
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
    updateStatus: updateStatusMutation.mutateAsync,
    isUpdating: updateStatusMutation.isPending,
    createAppointment: createAppointmentMutation.mutateAsync,
    isCreating: createAppointmentMutation.isPending,
  };
}
