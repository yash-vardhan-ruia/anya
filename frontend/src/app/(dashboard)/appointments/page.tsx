'use client';

import { useState } from 'react';
import { useAppointments } from '@/hooks/use-appointments';
import { useDashboardStore } from '@/stores/use-dashboard-store';
import { APPOINTMENT_STATUS_COLORS } from '@/lib/constants';
import { cn, formatDate, statusLabel } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import type { Appointment } from '@/types/api';
import api from '@/lib/api';

export default function AppointmentsPage() {
  const { appointments, isLoading, updateStatus, createAppointment } = useAppointments();
  const { searchQuery, setSearchQuery, selectedDepartment } = useDashboardStore();

  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedApt, setSelectedApt] = useState<Appointment | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  // Booking dependencies states
  const [isBookOpen, setIsBookOpen] = useState(false);
  const [patientsList, setPatientsList] = useState<any[]>([]);
  const [doctorsList, setDoctorsList] = useState<any[]>([]);
  const [availableSlots, setAvailableSlots] = useState<any[]>([]);

  // Booking form state
  const [bookingPatientId, setBookingPatientId] = useState('');
  const [bookingDoctorId, setBookingDoctorId] = useState('');
  const [bookingDate, setBookingDate] = useState('');
  const [bookingSlotId, setBookingSlotId] = useState('');
  const [bookingSymptoms, setBookingSymptoms] = useState('');
  const [bookingNotes, setBookingNotes] = useState('');

  const handleOpenBookModal = async () => {
    setIsBookOpen(true);
    setBookingPatientId('');
    setBookingDoctorId('');
    setBookingDate('');
    setBookingSlotId('');
    setBookingSymptoms('');
    setBookingNotes('');
    setAvailableSlots([]);

    try {
      const patRes = await api.get('/patients');
      const docRes = await api.get('/doctors');
      const pats = patRes.data?.items || [];
      const docs = docRes.data?.items || [];
      setPatientsList(pats);
      setDoctorsList(docs);
      if (pats.length > 0) setBookingPatientId(pats[0].id);
      if (docs.length > 0) setBookingDoctorId(docs[0].id);
    } catch (err) {
      console.error('Error fetching booking dependencies:', err);
    }
  };

  const handleDoctorOrDateChange = async (doctorId: string, dateStr: string) => {
    if (!doctorId || !dateStr) return;
    try {
      // First, trigger slot generation just in case they aren't generated yet
      try {
        await api.post(`/doctors/${doctorId}/slots/generate`, null, {
          params: { date: dateStr },
        });
      } catch (genErr) {
        console.warn('Slot generation skipped or failed:', genErr);
      }

      const res = await api.get(`/doctors/${doctorId}/slots`, {
        params: { date: dateStr },
      });
      const slots = res.data?.items || [];
      // Filter out already booked/locked slots
      const freeSlots = slots.filter((s: any) => s.status === 'available');
      setAvailableSlots(freeSlots);
      if (freeSlots.length > 0) {
        setBookingSlotId(freeSlots[0].id);
      } else {
        setBookingSlotId('');
      }
    } catch (err) {
      console.error('Error fetching slots:', err);
      setAvailableSlots([]);
      setBookingSlotId('');
    }
  };

  const handleBookSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bookingPatientId || !bookingDoctorId || !bookingDate || !bookingSlotId) return;
    
    const selectedSlot = availableSlots.find(s => s.id === bookingSlotId);
    if (!selectedSlot) return;

    try {
      const selectedDoc = doctorsList.find(d => d.id === bookingDoctorId);
      const departmentId = selectedDoc?.departmentId || selectedDoc?.department_id; // handle mapped department ID if present

      await createAppointment({
        patientId: bookingPatientId,
        doctorId: bookingDoctorId,
        slotId: bookingSlotId,
        departmentId: departmentId,
        date: bookingDate,
        time: selectedSlot.start_time,
        symptoms: bookingSymptoms,
        notes: bookingNotes,
      });
      
      setIsBookOpen(false);
    } catch (err) {
      console.error('Booking failed:', err);
    }
  };


  // Filter appointments based on inputs
  const filteredAppointments = appointments.filter((apt) => {
    const matchesSearch =
      apt.patientName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      apt.doctorName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      apt.id.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesDepartment = selectedDepartment === 'all' || apt.department === selectedDepartment;
    const matchesStatus = statusFilter === 'all' || apt.status === statusFilter;

    return matchesSearch && matchesDepartment && matchesStatus;
  });

  const handleOpenDetails = (apt: Appointment) => {
    setSelectedApt(apt);
    setIsDetailsOpen(true);
  };

  const handleStatusChangeInModal = (status: Appointment['status']) => {
    if (selectedApt) {
      updateStatus({ id: selectedApt.id, status });
      setSelectedApt((prev) => (prev ? { ...prev, status } : null));
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-48 bg-slate-200 dark:bg-zinc-800 animate-pulse rounded"></div>
        <div className="h-14 bg-slate-200 dark:bg-zinc-800 animate-pulse rounded-lg"></div>
        <div className="h-96 bg-slate-200 dark:bg-zinc-800 animate-pulse rounded-xl"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">Clinical Appointments Calendar</h1>
          
        </div>
        <Button onClick={handleOpenBookModal} className="bg-voxmed-primary text-white text-xs font-bold px-4 py-2 hover:bg-voxmed-primary/95 flex items-center gap-2">
          <span className="material-symbols-outlined text-sm">calendar_month</span>
          Book Appointment
        </Button>
      </div>

      {/* ── FILTER UTILITY BAR ── */}
      <Card className="border shadow-sm">
        <CardContent className="p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="flex flex-1 flex-col sm:flex-row gap-3 w-full md:w-auto">
            {/* Inline search filter override if needed */}
            <div className="relative flex-1 max-w-xs">
              <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-sm">
                search
              </span>
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search patient or physician..."
                className="pl-9 h-9 text-xs"
              />
            </div>

            {/* Status scope selector */}
            <div className="relative">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="flex h-9 w-40 rounded-md border border-input bg-transparent px-3 py-1 text-xs ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 appearance-none cursor-pointer font-medium pr-8"
              >
                <option value="all">All Booking Statuses</option>
                <option value="scheduled">Scheduled</option>
                <option value="confirmed">Confirmed</option>
                <option value="checked-in">Checked In</option>
                <option value="in-progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
                <option value="no-show">No Show</option>
              </select>
              <span className="material-symbols-outlined absolute right-2.5 top-2.5 text-muted-foreground text-sm pointer-events-none">
                arrow_drop_down
              </span>
            </div>
          </div>

          <div className="text-xs text-muted-foreground font-semibold">
            {filteredAppointments.length} matching schedule records
          </div>
        </CardContent>
      </Card>

      {/* ── APPOINTMENTS DIRECTORY TABLE ── */}
      <Card className="border shadow-sm overflow-hidden bg-white">
        <CardContent className="p-0">
          <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border text-[10px] font-bold text-muted-foreground uppercase bg-slate-50/50 dark:bg-zinc-800/20 select-none">
                  <th className="px-5 py-3 font-semibold">ID</th>
                  <th className="px-5 py-3 font-semibold">Patient Profile</th>
                  <th className="px-5 py-3 font-semibold">Attending Doctor</th>
                  <th className="px-5 py-3 font-semibold">Department</th>
                  <th className="px-5 py-3 font-semibold">Booking Date / Time</th>
                  <th className="px-5 py-3 font-semibold">Intake Channel</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs">
                {filteredAppointments.map((apt) => {
                  const stat = APPOINTMENT_STATUS_COLORS[apt.status] || {
                    bg: 'bg-gray-100',
                    text: 'text-gray-700',
                    dot: 'bg-gray-500',
                  };

                  return (
                    <tr
                      key={apt.id}
                      className="hover:bg-slate-50/40 dark:hover:bg-zinc-800/10 transition-colors"
                    >
                      <td className="px-5 py-3.5 font-bold text-slate-500">#{apt.id}</td>
                      <td className="px-5 py-3.5">
                        <div className="flex flex-col">
                          <span className="font-bold text-slate-800 dark:text-zinc-200">
                            {apt.patientName}
                          </span>
                          <span className="text-[10px] text-muted-foreground mt-0.5">
                            {apt.patientPhone}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 font-medium text-slate-800 dark:text-zinc-200">
                        {apt.doctorName}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="text-muted-foreground font-semibold">{apt.department}</span>
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex flex-col">
                          <span className="font-semibold text-slate-800">
                            {formatDate(apt.date)}
                          </span>
                          <span className="text-[10px] text-muted-foreground font-medium mt-0.5">
                            {apt.time} ({apt.duration} min duration)
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-muted-foreground font-medium">
                        <div className="flex items-center gap-1">
                          <span className="material-symbols-outlined text-base">
                            {apt.bookedVia === 'ai-voice'
                              ? 'call'
                              : apt.bookedVia === 'ai-chat'
                              ? 'forum'
                              : 'web'}
                          </span>
                          <span className="capitalize">{apt.bookedVia.replace('-', ' ')}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          className={cn(
                            'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold capitalize select-none',
                            stat.bg,
                            stat.text
                          )}
                        >
                          <span className={cn('h-1.5 w-1.5 rounded-full shrink-0', stat.dot)}></span>
                          {apt.status.replace('-', ' ')}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 text-[10px] font-semibold border-slate-200 hover:bg-slate-50"
                          onClick={() => handleOpenDetails(apt)}
                        >
                          Triage File
                        </Button>
                      </td>
                    </tr>
                  );
                })}
                {filteredAppointments.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-xs text-muted-foreground">
                      No matching patient appointments found on calendar.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* ── APPOINTMENT DETAILS TRIAGE DIALOG MODAL ── */}
      {selectedApt && (
        <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
          <DialogContent className="sm:max-w-lg z-50 bg-white shadow-2xl p-6">
            <DialogHeader className="border-b pb-4">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-voxmed-primary text-2xl">
                  medical_information
                </span>
                <div>
                  <DialogTitle className="text-base font-bold">
                    Clinical Appointment Details
                  </DialogTitle>
                  <DialogDescription className="text-xs">
                    Review scheduling source notes, booking status modifiers and clinical summaries.
                  </DialogDescription>
                </div>
              </div>
            </DialogHeader>

            {/* Modal Body */}
            <div className="py-4 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                    Patient Profile
                  </span>
                  <p className="font-bold text-slate-800">{selectedApt.patientName}</p>
                  <p className="text-[10px] text-muted-foreground">{selectedApt.patientPhone}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                    Attending Clinician
                  </span>
                  <p className="font-bold text-slate-800">{selectedApt.doctorName}</p>
                  <p className="text-[10px] text-muted-foreground">
                    {selectedApt.department} department
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 border-t pt-3">
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                    Booking Date
                  </span>
                  <p className="font-bold text-slate-800">
                    {formatDate(selectedApt.date, 'EEEE, MMM dd, yyyy')}
                  </p>
                  <p className="text-[10px] text-muted-foreground">
                    Scheduled at {selectedApt.time} ({selectedApt.duration} mins)
                  </p>
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                    EHR Sync Source
                  </span>
                  <p className="font-bold text-slate-800 flex items-center gap-1.5 capitalize">
                    <span className="material-symbols-outlined text-base">
                      {selectedApt.bookedVia === 'ai-voice' ? 'call' : 'forum'}
                    </span>
                    {selectedApt.bookedVia.replace('-', ' ')}
                  </p>
                  <p className="text-[10px] text-muted-foreground">
                    Created on {formatDate(selectedApt.createdAt, 'MMM dd, h:mm a')}
                  </p>
                </div>
              </div>

              {/* Status Modifier Selector */}
              <div className="space-y-1.5 border-t pt-3">
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                  Update Scheduling Status
                </span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {(
                    ['scheduled', 'confirmed', 'checked-in', 'in-progress', 'completed', 'cancelled', 'no-show'] as const
                  ).map((st) => {
                    const isSelected = selectedApt.status === st;
                    const c = APPOINTMENT_STATUS_COLORS[st];
                    return (
                      <button
                        key={st}
                        onClick={() => handleStatusChangeInModal(st)}
                        className={cn(
                          'px-2.5 py-1 rounded-full text-[10px] font-bold border cursor-pointer transition-all',
                          isSelected
                            ? cn(c.bg, c.text, 'border-transparent ring-2 ring-voxmed-primary/30')
                            : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-600'
                        )}
                      >
                        {statusLabel(st)}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Clinical Intake Notes */}
              <div className="space-y-1.5 border-t pt-3 bg-slate-50 dark:bg-zinc-800/30 p-3 rounded-lg border border-dashed">
                <div className="flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-base text-voxmed-primary">
                    clinical_notes
                  </span>
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                    CareVoice Clinical Intake Notes
                  </span>
                </div>
                <p className="text-slate-700 leading-relaxed font-normal mt-1 italic">
                  &quot;{selectedApt.notes || 'No intake comments documented by active voice session.'}&quot;
                </p>
              </div>
            </div>

            <DialogFooter className="border-t pt-4">
              <Button
                variant="outline"
                size="sm"
                className="h-9 font-semibold text-xs"
                onClick={() => setIsDetailsOpen(false)}
              >
                Close File
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* ── BOOK APPOINTMENT DIALOG ── */}
      <Dialog open={isBookOpen} onOpenChange={setIsBookOpen}>
        <DialogContent className="sm:max-w-md bg-white shadow-2xl p-6">
          <DialogHeader className="border-b pb-4">
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <span className="material-symbols-outlined text-voxmed-primary">calendar_month</span>
              Book Clinical Slot
            </DialogTitle>
            <DialogDescription className="text-xs">
              Manually schedule an appointment slot for a registered patient.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleBookSubmit} className="space-y-4 py-4 text-xs">
            <div className="space-y-1">
              <label className="font-bold text-slate-700">Select Patient *</label>
              <select
                value={bookingPatientId}
                onChange={(e) => setBookingPatientId(e.target.value)}
                className="w-full h-9 px-3 rounded-md border border-input bg-transparent text-xs"
                required
              >
                {patientsList.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.phone})
                  </option>
                ))}
                {patientsList.length === 0 && (
                  <option value="">No patients found. Register a patient first.</option>
                )}
              </select>
            </div>
            
            <div className="space-y-1">
              <label className="font-bold text-slate-700">Select Attending Doctor *</label>
              <select
                value={bookingDoctorId}
                onChange={(e) => {
                  setBookingDoctorId(e.target.value);
                  handleDoctorOrDateChange(e.target.value, bookingDate);
                }}
                className="w-full h-9 px-3 rounded-md border border-input bg-transparent text-xs"
                required
              >
                {doctorsList.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.specialty})
                  </option>
                ))}
                {doctorsList.length === 0 && (
                  <option value="">No doctors available.</option>
                )}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="font-bold text-slate-700">Appointment Date *</label>
                <Input
                  type="date"
                  value={bookingDate}
                  onChange={(e) => {
                    setBookingDate(e.target.value);
                    handleDoctorOrDateChange(bookingDoctorId, e.target.value);
                  }}
                  required
                  className="h-9 text-xs"
                />
              </div>
              
              <div className="space-y-1">
                <label className="font-bold text-slate-700">Available Slot *</label>
                <select
                  value={bookingSlotId}
                  onChange={(e) => setBookingSlotId(e.target.value)}
                  className="w-full h-9 px-3 rounded-md border border-input bg-transparent text-xs"
                  required
                >
                  {availableSlots.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.start_time.substring(0, 5)} - {s.end_time.substring(0, 5)}
                    </option>
                  ))}
                  {availableSlots.length === 0 && (
                    <option value="">No slots. Choose another date/doctor</option>
                  )}
                </select>
              </div>
            </div>

            <div className="space-y-1">
              <label className="font-bold text-slate-700">Symptoms</label>
              <Input
                value={bookingSymptoms}
                onChange={(e) => setBookingSymptoms(e.target.value)}
                placeholder="Fever, cough, body ache, etc."
                className="h-9 text-xs"
              />
            </div>

            <div className="space-y-1">
              <label className="font-bold text-slate-700">Additional Notes</label>
              <Input
                value={bookingNotes}
                onChange={(e) => setBookingNotes(e.target.value)}
                placeholder="Physician instructions or special requests"
                className="h-9 text-xs"
              />
            </div>

            <DialogFooter className="border-t pt-4">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIsBookOpen(false)}
                className="h-9 font-semibold text-xs"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                className="h-9 font-semibold text-xs bg-voxmed-primary text-white"
                disabled={!bookingSlotId}
              >
                Book Slot
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
