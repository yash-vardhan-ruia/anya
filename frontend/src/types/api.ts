// ============================================================
// CareVoice AI Hospital Platform - TypeScript Interfaces
// ============================================================

// ── Auth ──────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'doctor' | 'nurse' | 'receptionist';
  avatar?: string;
  hospitalId: string;
  createdAt: string;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

// ── Dashboard ─────────────────────────────────────────────────
export interface DashboardStats {
  totalCalls: number;
  totalCallsDelta: number;
  activeCalls: number;
  activeCallsDelta: number;
  appointmentsToday: number;
  appointmentsTodayDelta: number;
  avgHandleTime: string;
  avgHandleTimeDelta: number;
  satisfactionScore: number;
  satisfactionScoreDelta: number;
  totalPatients: number;
  totalPatientsDelta: number;
}

export interface CallVolumeData {
  time: string;
  inbound: number;
  outbound: number;
  missed: number;
}

export interface SystemHealthItem {
  name: string;
  status: 'operational' | 'degraded' | 'down';
  uptime: number;
  responseTime: number;
}

export interface RecentInteraction {
  id: string;
  patientName: string;
  type: 'appointment' | 'inquiry' | 'prescription' | 'follow-up' | 'emergency';
  channel: 'voice' | 'chat' | 'sms';
  status: 'completed' | 'in-progress' | 'pending' | 'failed';
  duration: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  timestamp: string;
  aiConfidence: number;
}

export interface DoctorUtilization {
  id: string;
  name: string;
  specialty: string;
  avatar?: string;
  utilization: number;
  appointmentsToday: number;
  totalAppointments: number;
  status: 'available' | 'busy' | 'break' | 'offline';
}

// ── Appointments ──────────────────────────────────────────────
export interface Appointment {
  id: string;
  patientId: string;
  patientName: string;
  patientPhone: string;
  doctorId: string;
  doctorName: string;
  department: string;
  date: string;
  time: string;
  duration: number;
  status: 'scheduled' | 'confirmed' | 'checked-in' | 'in-progress' | 'completed' | 'cancelled' | 'no-show';
  type: 'new-visit' | 'follow-up' | 'consultation' | 'procedure' | 'emergency';
  bookedVia: 'ai-voice' | 'ai-chat' | 'web' | 'phone' | 'walk-in';
  notes?: string;
  createdAt: string;
}

// ── Patients ──────────────────────────────────────────────────
export interface Patient {
  id: string;
  name: string;
  email: string;
  phone: string;
  dateOfBirth: string;
  gender: 'male' | 'female' | 'other';
  bloodGroup: string;
  address: string;
  emergencyContact: string;
  insuranceProvider?: string;
  insuranceId?: string;
  lastVisit: string;
  totalVisits: number;
  status: 'active' | 'inactive';
  avatar?: string;
  createdAt: string;
}

// ── Doctors ───────────────────────────────────────────────────
export interface Doctor {
  id: string;
  name: string;
  email: string;
  phone: string;
  specialty: string;
  department: string;
  qualification: string;
  experience: number;
  rating: number;
  totalReviews: number;
  consultationFee: number;
  avatar?: string;
  availability: DoctorAvailability[];
  status: 'available' | 'busy' | 'break' | 'offline';
  createdAt: string;
}

export interface DoctorAvailability {
  day: string;
  slots: TimeSlot[];
}

export interface TimeSlot {
  start: string;
  end: string;
  isBooked: boolean;
}

// ── Calls / Voice Sessions ────────────────────────────────────
export interface VoiceSession {
  id: string;
  callerId: string;
  callerName: string;
  callerPhone: string;
  agentId: string;
  agentName: string;
  type: 'inbound' | 'outbound';
  status: 'ringing' | 'active' | 'on-hold' | 'transferring' | 'completed' | 'failed';
  intent: string;
  duration: number;
  startedAt: string;
  endedAt?: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  aiConfidence: number;
  transcript?: string;
  recordingUrl?: string;
  department?: string;
  resolution?: string;
}

// ── Billing ───────────────────────────────────────────────────
export interface Invoice {
  id: string;
  invoiceNumber: string;
  patientId: string;
  patientName: string;
  doctorName: string;
  department: string;
  items: InvoiceItem[];
  subtotal: number;
  tax: number;
  discount: number;
  total: number;
  status: 'draft' | 'pending' | 'paid' | 'overdue' | 'cancelled' | 'refunded';
  paymentMethod?: 'cash' | 'card' | 'insurance' | 'upi' | 'bank-transfer';
  dueDate: string;
  paidAt?: string;
  createdAt: string;
}

export interface InvoiceItem {
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
}

// ── Analytics ─────────────────────────────────────────────────
export interface AnalyticsData {
  callMetrics: CallMetrics;
  appointmentMetrics: AppointmentMetrics;
  revenueMetrics: RevenueMetrics;
  aiMetrics: AIMetrics;
}

export interface CallMetrics {
  totalCalls: number;
  avgDuration: number;
  peakHour: string;
  resolutionRate: number;
  callsByHour: { hour: string; count: number }[];
  callsByDay: { day: string; count: number }[];
  callsByType: { type: string; count: number }[];
}

export interface AppointmentMetrics {
  totalScheduled: number;
  completed: number;
  cancelled: number;
  noShow: number;
  byDepartment: { department: string; count: number }[];
  byType: { type: string; count: number }[];
  trend: { date: string; count: number }[];
}

export interface RevenueMetrics {
  totalRevenue: number;
  avgPerPatient: number;
  outstandingAmount: number;
  collectionRate: number;
  byDepartment: { department: string; amount: number }[];
  trend: { date: string; amount: number }[];
  byPaymentMethod: { method: string; amount: number }[];
}

export interface AIMetrics {
  totalInteractions: number;
  avgConfidence: number;
  escalationRate: number;
  satisfactionScore: number;
  intentDistribution: { intent: string; count: number }[];
  sentimentTrend: { date: string; positive: number; neutral: number; negative: number }[];
}

// ── Navigation ────────────────────────────────────────────────
export interface NavItem {
  title: string;
  href: string;
  icon: string;
  badge?: string | number;
  children?: NavItem[];
}

// ── API Response Wrapper ──────────────────────────────────────
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

// ── Notification ──────────────────────────────────────────────
export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  read: boolean;
  createdAt: string;
}
