'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Doctor } from '@/types/api';
import api from '@/lib/api';

export function useDoctors() {
  const queryClient = useQueryClient();

  const { data: doctors = [], isLoading, error } = useQuery<Doctor[]>({
    queryKey: ['doctors'],
    queryFn: async () => {
      try {
        const res = await api.get('/doctors');
        const rawItems = Array.isArray(res.data) ? res.data : (res.data.items || []);
        
        return rawItems.map((doc: any) => {
          // Map availability schedules
          const availability = (doc.schedules || []).map((sch: any) => {
            const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
            const dayName = days[sch.day_of_week] || "Monday";
            return {
              day: dayName,
              slots: [
                { start: sch.start_time.substring(0, 5), end: sch.end_time.substring(0, 5), isBooked: false }
              ]
            };
          });

          return {
            id: doc.id,
            name: doc.full_name || 'Attending Physician',
            email: doc.email || '',
            phone: doc.phone || '',
            specialty: doc.specialization || 'General Medicine',
            department: doc.department_name || doc.department?.name || 'General Medicine',
            qualification: doc.qualification || 'MD',
            experience: doc.experience_years || 0,
            consultationFee: doc.consultation_fee ? (doc.consultation_fee / 100) : 0,
            avatar: doc.avatar || undefined,
            status: doc.is_active ? 'available' : 'offline',
            availability: availability,
            createdAt: doc.created_at || new Date().toISOString()
          };
        });
      } catch (err) {
        console.warn('API error fetching doctors:', err);
        return [];
      }
    },
  });

  // Mutate: Update doctor status
  const updateStatusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: Doctor['status'] }) => {
      const is_active = status === 'available';
      const res = await api.put(`/doctors/${id}`, { is_active });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctors'] });
    },
  });

  // Mutate: Add new doctor
  const createDoctorMutation = useMutation({
    mutationFn: async (newDoc: any) => {
      const payload = {
        full_name: newDoc.name,
        email: newDoc.email || null,
        phone: newDoc.phone,
        specialization: newDoc.specialty || 'General Medicine',
        department_id: newDoc.departmentId,
        qualification: newDoc.qualification || 'MD',
        experience_years: Number(newDoc.experience) || 0,
        consultation_fee: Number(newDoc.consultationFee) * 100, // INR to paise
        is_active: true,
      };
      const res = await api.post('/doctors', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctors'] });
    },
  });

  // Mutate: Delete doctor
  const deleteDoctorMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await api.delete(`/doctors/${id}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctors'] });
      queryClient.invalidateQueries({ queryKey: ['departments'] });
    },
  });

  return {
    doctors,
    isLoading,
    error,
    updateStatus: updateStatusMutation.mutateAsync,
    isUpdating: updateStatusMutation.isPending,
    createDoctor: createDoctorMutation.mutateAsync,
    isCreating: createDoctorMutation.isPending,
    deleteDoctor: deleteDoctorMutation.mutateAsync,
    isDeleting: deleteDoctorMutation.isPending,
  };
}
