'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Patient } from '@/types/api';
import api from '@/lib/api';

export function usePatients() {
  const queryClient = useQueryClient();

  const { data: patients = [], isLoading, error } = useQuery<Patient[]>({
    queryKey: ['patients'],
    queryFn: async () => {
      try {
        const res = await api.get('/patients');
        const rawItems = Array.isArray(res.data) ? res.data : (res.data.items || []);
        
        return rawItems.map((pat: any) => ({
          id: pat.id,
          name: pat.full_name || 'Anonymous Patient',
          email: pat.email || '',
          
          dateOfBirth: pat.date_of_birth || '',
          gender: pat.gender || 'other',
          bloodGroup: pat.blood_group || 'O+',
          address: pat.address || '',
          emergencyContact: pat.emergency_contact || 'None',
          insuranceProvider: pat.insurance_provider || 'Self Pay',
          insuranceId: pat.insurance_id || '',
          lastVisit: pat.last_visit || pat.created_at || new Date().toISOString(),
          totalVisits: pat.total_visits || 1,
          status: pat.status || 'active',
          avatar: pat.avatar || undefined,
          createdAt: pat.created_at || new Date().toISOString(),
        }));
      } catch (err) {
        console.warn('API error fetching patients:', err);
        return [];
      }
    },
  });

  // Create new patient
  const createPatientMutation = useMutation({
    mutationFn: async (newPatient: Omit<Patient, 'id' | 'createdAt' | 'totalVisits' | 'lastVisit'>) => {
      const payload = {
        full_name: newPatient.name,
        email: newPatient.email || null,
        date_of_birth: newPatient.dateOfBirth || null,
        gender: newPatient.gender || null,
        address: newPatient.address || null,
      };
      const res = await api.post('/patients', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
    },
  });

  // Update patient
  const updatePatientMutation = useMutation({
    mutationFn: async ({ id, ...updatedFields }: Partial<Patient> & { id: string }) => {
      const payload: any = {};
      if (updatedFields.name !== undefined) payload.full_name = updatedFields.name;
      if (updatedFields.email !== undefined) payload.email = updatedFields.email || null;
      if (updatedFields.dateOfBirth !== undefined) payload.date_of_birth = updatedFields.dateOfBirth || null;
      if (updatedFields.gender !== undefined) payload.gender = updatedFields.gender || null;
      if (updatedFields.address !== undefined) payload.address = updatedFields.address || null;

      const res = await api.put(`/patients/${id}`, payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
    },
  });

  // Delete patient
  const deletePatientMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await api.delete(`/patients/${id}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
    },
  });

  return {
    patients,
    isLoading,
    error,
    createPatient: createPatientMutation.mutateAsync,
    isCreating: createPatientMutation.isPending,
    updatePatient: updatePatientMutation.mutateAsync,
    isUpdating: updatePatientMutation.isPending,
    deletePatient: deletePatientMutation.mutateAsync,
    isDeleting: deletePatientMutation.isPending,
  };
}
