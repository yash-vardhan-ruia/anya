'use client';

import { useQuery } from '@tanstack/react-query';
import type { AnalyticsData, DashboardStats, SystemHealthItem, RecentInteraction, DoctorUtilization, VoiceSession, Invoice } from '@/types/api';
import api from '@/lib/api';

const EMPTY_STATS: DashboardStats = {
  totalCalls: 0,
  totalCallsDelta: 0,
  activeCalls: 0,
  activeCallsDelta: 0,
  appointmentsToday: 0,
  appointmentsTodayDelta: 0,
  avgHandleTime: '0:00',
  avgHandleTimeDelta: 0,
  satisfactionScore: 0,
  satisfactionScoreDelta: 0,
  totalPatients: 0,
  totalPatientsDelta: 0,
};

const EMPTY_ANALYTICS: AnalyticsData = {
  callMetrics: {
    totalCalls: 0,
    avgDuration: 0,
    peakHour: 'N/A',
    resolutionRate: 0,
    callsByHour: [],
    callsByDay: [],
    callsByType: [],
  },
  appointmentMetrics: {
    totalScheduled: 0,
    completed: 0,
    cancelled: 0,
    noShow: 0,
    byDepartment: [],
    byType: [],
    trend: [],
  },
  revenueMetrics: {
    totalRevenue: 0,
    avgPerPatient: 0,
    outstandingAmount: 0,
    collectionRate: 100,
    byDepartment: [],
    trend: [],
    byPaymentMethod: [],
  },
  aiMetrics: {
    totalInteractions: 0,
    avgConfidence: 0,
    escalationRate: 0,
    satisfactionScore: 0,
    intentDistribution: [],
    sentimentTrend: [],
  },
};

export function useAnalytics() {
  // 1. Fetch Aggregated Statistics
  const { data: stats = EMPTY_STATS, isLoading: statsLoading } = useQuery<DashboardStats>({
    queryKey: ['analytics', 'stats'],
    queryFn: async () => {
      try {
        const res = await api.get('/analytics/stats');
        return res.data;
      } catch (err) {
        console.warn('API error fetching stats:', err);
        return EMPTY_STATS;
      }
    },
  });

  // 2. Fetch Full Analytics
  const { data: analytics = EMPTY_ANALYTICS, isLoading: analyticsLoading } = useQuery<AnalyticsData>({
    queryKey: ['analytics', 'full'],
    queryFn: async () => {
      try {
        const res = await api.get('/analytics');
        return res.data;
      } catch (err) {
        console.warn('API error fetching full analytics:', err);
        return EMPTY_ANALYTICS;
      }
    },
  });

  // 3. Fetch System Health
  const { data: systemHealth = [], isLoading: healthLoading } = useQuery<SystemHealthItem[]>({
    queryKey: ['analytics', 'system-health'],
    queryFn: async () => {
      try {
        const res = await api.get('/analytics/system-health');
        return res.data;
      } catch (err) {
        console.warn('API error fetching system health:', err);
        return [];
      }
    },
  });

  // 4. Fetch Recent Interactions
  const { data: recentInteractions = [], isLoading: interactionsLoading } = useQuery<RecentInteraction[]>({
    queryKey: ['analytics', 'recent-interactions'],
    queryFn: async () => {
      try {
        const res = await api.get('/analytics/recent-interactions');
        return res.data;
      } catch (err) {
        console.warn('API error fetching interactions:', err);
        return [];
      }
    },
  });

  // 5. Fetch Doctor Utilization
  const { data: doctorUtilization = [], isLoading: utilizationLoading } = useQuery<DoctorUtilization[]>({
    queryKey: ['analytics', 'doctor-utilization'],
    queryFn: async () => {
      try {
        const res = await api.get('/analytics/doctor-utilization');
        return res.data;
      } catch (err) {
        console.warn('API error fetching doctor utilization:', err);
        return [];
      }
    },
  });

  // 6. Fetch Call Sessions
  const { data: calls = [], isLoading: callsLoading } = useQuery<VoiceSession[]>({
    queryKey: ['calls'],
    queryFn: async () => {
      try {
        const res = await api.get('/calls');
        return Array.isArray(res.data) ? res.data : (res.data.items || []);
      } catch (err) {
        console.warn('API error fetching call sessions:', err);
        return [];
      }
    },
  });

  // 7. Fetch Invoices
  const { data: invoices = [], isLoading: invoicesLoading } = useQuery<Invoice[]>({
    queryKey: ['invoices'],
    queryFn: async () => {
      try {
        const res = await api.get('/billing/invoices');
        const rawItems = Array.isArray(res.data) ? res.data : (res.data.items || []);
        return rawItems.map((inv: any) => {
          const subtotal = (inv.subtotal || 0) / 100;
          const tax = (inv.gst_amount || inv.tax || 0) / 100;
          const total = (inv.total_amount || inv.total || 0) / 100;
          const discount = 0;
          
          const doctorName = inv.doctor_name || 'Attending Staff';
          const departmentName = inv.department_name || 'General Medicine';
          
          return {
            id: inv.id,
            invoiceNumber: inv.invoice_number || 'INV-UNKNOWN',
            patientId: inv.patient_id || '',
            patientName: inv.patient_name || 'Guest Patient',
            doctorName: doctorName,
            department: departmentName,
            items: [
              {
                description: `OPD Consultation Fee - ${doctorName}`,
                quantity: 1,
                unitPrice: subtotal,
                total: subtotal,
              }
            ],
            subtotal: subtotal,
            tax: tax,
            discount: discount,
            total: total,
            status: inv.status || 'pending',
            paymentMethod: inv.payment?.payment_method || 'card',
            dueDate: new Date(new Date(inv.created_at || new Date()).getTime() + 7 * 24 * 60 * 60 * 1000).toISOString(),
            createdAt: inv.created_at || new Date().toISOString(),
          };
        });
      } catch (err) {
        console.warn('API error fetching invoices:', err);
        return [];
      }
    },
  });

  return {
    stats,
    analytics,
    systemHealth,
    recentInteractions,
    doctorUtilization,
    calls,
    invoices,
    isLoading:
      statsLoading ||
      analyticsLoading ||
      healthLoading ||
      interactionsLoading ||
      utilizationLoading ||
      callsLoading ||
      invoicesLoading,
  };
}
