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
          phone: pat.phone || '',
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
          avatar: pat.avatar || 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&q=80&w=150',
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
      const res = await api.post('/patients', newPatient);
      return res.data;
    },
    onSuccess: (newPatient) => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
    },
  });

  return {
    patients,
    isLoading,
    error,
    createPatient: createPatientMutation.mutate,
    isCreating: createPatientMutation.isPending,
  };
}
