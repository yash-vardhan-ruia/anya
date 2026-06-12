'use client';

import { useState } from 'react';
import { useDoctors } from '@/hooks/use-doctors';
import { useDashboardStore } from '@/stores/use-dashboard-store';
import { DOCTOR_STATUS_COLORS } from '@/lib/constants';
import { cn, formatCurrency, getInitials } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';

export default function DoctorsPage() {
  const { doctors, isLoading, updateStatus } = useDoctors();
  const { searchQuery, setSearchQuery, selectedDepartment } = useDashboardStore();

  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);
  const [isScheduleOpen, setIsScheduleOpen] = useState(false);

  // Filter doctors
  const filteredDoctors = doctors.filter((doc) => {
    const matchesSearch =
      doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.specialty.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesDepartment = selectedDepartment === 'all' || doc.department === selectedDepartment;

    return matchesSearch && matchesDepartment;
  });

  const handleOpenSchedule = (doc: any) => {
    setSelectedDoc(doc);
    setIsScheduleOpen(true);
  };

  const handleStatusToggle = (id: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'available' ? 'offline' : 'available';
    updateStatus({ id, status: nextStatus });
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-48 bg-slate-200 dark:bg-zinc-800 animate-pulse rounded"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array(6).fill(0).map((_, i) => (
            <div key={i} className="h-64 bg-slate-200 dark:bg-zinc-800 animate-pulse rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">On-Duty Clinical Staff</h1>
        <p className="text-xs text-muted-foreground mt-1">
          Monitor attending physician availability, consult fees, and active clinical appointment calendars.
        </p>
      </div>

      {/* Search Header */}
      <Card className="border shadow-sm">
        <CardContent className="p-4 flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="relative flex-1 max-w-xs w-full">
            <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-sm">
              search
            </span>
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by physician name or specialty..."
              className="pl-9 h-9 text-xs"
            />
          </div>
          <span className="text-xs font-semibold text-muted-foreground">
            {filteredDoctors.length} Attending Staff Found
          </span>
        </CardContent>
      </Card>

      {/* Attending Doctors Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredDoctors.map((doc) => {
          const stat = DOCTOR_STATUS_COLORS[doc.status] || {
            bg: 'bg-gray-100',
            text: 'text-gray-700',
            dot: 'bg-gray-400',
          };

          return (
            <Card
              key={doc.id}
              className="border border-border bg-white dark:bg-zinc-900 shadow-sm relative overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:shadow-md"
            >
              {/* Colored top band based on status */}
              <div
                className={cn(
                  'h-1.5 w-full absolute top-0 left-0',
                  doc.status === 'available' ? 'bg-emerald-500' : 'bg-slate-400'
                )}
              ></div>

              <CardContent className="p-5 pt-7 space-y-4 text-xs">
                {/* Doctor Bio Header */}
                <div className="flex items-start gap-4">
                  <Avatar className="h-14 w-14 shadow-sm border border-slate-100 shrink-0">
                    <AvatarImage src={doc.avatar} alt={doc.name} />
                    <AvatarFallback className="bg-voxmed-primary text-white font-bold text-base">
                      {getInitials(doc.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 flex-1">
                    <h3 className="text-sm font-black text-slate-800 dark:text-zinc-200 leading-snug truncate">
                      {doc.name}
                    </h3>
                    <p className="text-[11px] font-bold text-voxmed-primary mt-0.5 uppercase tracking-wide truncate">
                      {doc.specialty}
                    </p>
                    <p className="text-[10px] text-muted-foreground truncate font-light mt-0.5">
                      {doc.qualification}
                    </p>
                  </div>
                </div>

                {/* Attending stats */}
                <div className="grid grid-cols-2 gap-3 py-3 border-y border-dashed text-[10px] font-semibold text-slate-600 dark:text-zinc-400">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-slate-400 text-[9px] uppercase tracking-wider font-bold">
                      Experience
                    </span>
                    <span className="text-slate-800 dark:text-zinc-200">
                      {doc.experience} Years
                    </span>
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-slate-400 text-[9px] uppercase tracking-wider font-bold">
                      Attending Fee
                    </span>
                    <span className="text-slate-800 dark:text-zinc-200">
                      {formatCurrency(doc.consultationFee)} consultation
                    </span>
                  </div>
                </div>

                {/* Status selector & Actions */}
                <div className="flex items-center justify-between mt-4">
                  {/* Status clicker */}
                  <button
                    onClick={() => handleStatusToggle(doc.id, doc.status)}
                    className={cn(
                      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold border transition-all cursor-pointer select-none',
                      stat.bg,
                      stat.text
                    )}
                  >
                    <span className={cn('h-1.5 w-1.5 rounded-full shrink-0', stat.dot)}></span>
                    {doc.status}
                    <span className="material-symbols-outlined text-[10px] leading-none">autorenew</span>
                  </button>

                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 text-[10px] font-semibold border-slate-200 hover:bg-slate-50"
                    onClick={() => handleOpenSchedule(doc)}
                  >
                    Weekly Schedule
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
        {filteredDoctors.length === 0 && (
          <div className="col-span-full py-12 text-center text-xs text-muted-foreground">
            No matching medical staff listed for this scope.
          </div>
        )}
      </div>

      {/* ── DOCTOR SCHEDULE DETAIL DIALOG MODAL ── */}
      {selectedDoc && (
        <Dialog open={isScheduleOpen} onOpenChange={setIsScheduleOpen}>
          <DialogContent className="sm:max-w-lg z-50 bg-white shadow-2xl p-6">
            <DialogHeader className="border-b pb-4">
              <div className="flex items-center gap-3">
                <Avatar className="h-10 w-10">
                  <AvatarImage src={selectedDoc.avatar} />
                  <AvatarFallback className="bg-voxmed-primary text-white font-bold">
                    {getInitials(selectedDoc.name)}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <DialogTitle className="text-base font-bold">
                    {selectedDoc.name} Availability
                  </DialogTitle>
                  <DialogDescription className="text-xs">
                    Weekly clinical shift slots registered in VoxMed EHR.
                  </DialogDescription>
                </div>
              </div>
            </DialogHeader>

            {/* Schedule Body */}
            <div className="py-4 space-y-4 text-xs">
              <div className="space-y-3">
                {selectedDoc.availability && selectedDoc.availability.length > 0 ? (
                  selectedDoc.availability.map((avail: any, index: number) => (
                    <div
                      key={index}
                      className="p-3 bg-slate-50 dark:bg-zinc-800/30 rounded-lg border flex flex-col gap-2"
                    >
                      <span className="font-bold text-slate-800 dark:text-zinc-200 border-b pb-1 flex items-center justify-between">
                        <span>{avail.day}</span>
                        <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50 text-[9px] font-bold py-0.5 px-2">
                          Active Shift
                        </Badge>
                      </span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {avail.slots.map((slot: any, sIdx: number) => (
                          <div
                            key={sIdx}
                            className={cn(
                              'px-2.5 py-1 rounded text-[10px] font-medium border flex items-center gap-1 select-none',
                              slot.isBooked
                                ? 'bg-rose-50 border-rose-100 text-rose-700'
                                : 'bg-blue-50 border-blue-100 text-blue-700'
                            )}
                          >
                            <span className="material-symbols-outlined text-xs">
                              {slot.isBooked ? 'event_busy' : 'check_circle'}
                            </span>
                            {slot.start} - {slot.end} {slot.isBooked ? '(Booked)' : '(Available)'}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="py-8 text-center text-xs text-muted-foreground">
                    No active shift schedules registered in VoxMed EHR for this physician.
                  </div>
                )}
              </div>
            </div>

            <div className="border-t pt-4 flex justify-end">
              <Button
                variant="outline"
                size="sm"
                className="h-9 font-semibold text-xs"
                onClick={() => setIsScheduleOpen(false)}
              >
                Close Schedule
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
