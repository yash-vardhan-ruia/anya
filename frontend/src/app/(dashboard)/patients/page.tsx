'use client';

import { useState } from 'react';
import { usePatients } from '@/hooks/use-patients';
import { useAnalytics } from '@/hooks/use-analytics';
import { useDashboardStore } from '@/stores/use-dashboard-store';
import { SENTIMENT_COLORS } from '@/lib/constants';
import { cn, formatDate, getInitials } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';

export default function PatientsPage() {
  const { patients, isLoading, createPatient, updatePatient, deletePatient } = usePatients();
  const { calls } = useAnalytics();
  const { searchQuery, setSearchQuery } = useDashboardStore();

  const [selectedPatient, setSelectedPatient] = useState<any | null>(null);
  const [isSheetOpen, setIsSheetOpen] = useState(false);
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editingPatient, setEditingPatient] = useState<any | null>(null);

  // Form states
  const [formName, setFormName] = useState('');
  const [formPhone, setFormPhone] = useState('');
  const [formEmail, setFormEmail] = useState('');
  const [formDob, setFormDob] = useState('');
  const [formGender, setFormGender] = useState('male');
  const [formAddress, setFormAddress] = useState('');

  const resetForm = () => {
    setFormName('');
    setFormPhone('');
    setFormEmail('');
    setFormDob('');
    setFormGender('male');
    setFormAddress('');
  };

  const handleOpenRegister = () => {
    resetForm();
    setIsRegisterOpen(true);
  };

  const handleOpenEdit = (pat: any) => {
    setEditingPatient(pat);
    setFormName(pat.name);
    setFormPhone(pat.phone);
    setFormEmail(pat.email);
    setFormDob(pat.dateOfBirth ? pat.dateOfBirth.substring(0, 10) : '');
    setFormGender(pat.gender || 'male');
    setFormAddress(pat.address || '');
    setIsEditOpen(true);
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName || !formPhone) return;
    try {
      await createPatient({
        name: formName,
        phone: formPhone,
        email: formEmail,
        dateOfBirth: formDob,
        gender: formGender as any,
        address: formAddress,
        bloodGroup: 'O+',
        emergencyContact: '',
        status: 'active',
      });
      setIsRegisterOpen(false);
      resetForm();
    } catch (err) {
      console.error(err);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingPatient || !formName || !formPhone) return;
    try {
      await updatePatient({
        id: editingPatient.id,
        name: formName,
        phone: formPhone,
        email: formEmail,
        dateOfBirth: formDob,
        gender: formGender as any,
        address: formAddress,
      });
      setIsEditOpen(false);
      setEditingPatient(null);
      resetForm();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this patient profile?')) {
      try {
        await deletePatient(id);
      } catch (err) {
        console.error(err);
      }
    }
  };


  // Filter patients list
  const filteredPatients = patients.filter((pat) => {
    return (
      pat.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      pat.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      pat.phone.toLowerCase().includes(searchQuery.toLowerCase()) ||
      pat.id.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  const handleOpenProfile = (pat: any) => {
    setSelectedPatient(pat);
    setIsSheetOpen(true);
  };

  // Find call logs for selected patient
  const patientCalls = selectedPatient
    ? calls.filter(
        (c) =>
          c.callerId === selectedPatient.id ||
          c.callerName.toLowerCase().includes(selectedPatient.name.toLowerCase())
      )
    : [];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-48 bg-slate-200 dark:bg-zinc-800 animate-pulse rounded"></div>
        <div className="h-96 bg-slate-200 dark:bg-zinc-800 animate-pulse rounded-xl"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">EHR Patient Directory</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Access complete clinical histories, electronic health records (EHR), and speech session voice logs.
          </p>
        </div>
        <Button onClick={handleOpenRegister} className="bg-voxmed-primary text-white text-xs font-bold px-4 py-2 hover:bg-voxmed-primary/95 flex items-center gap-2">
          <span className="material-symbols-outlined text-sm">person_add</span>
          Register Patient
        </Button>
      </div>

      {/* Directory Search & Count */}
      <Card className="border shadow-sm">
        <CardContent className="p-4 flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="relative flex-1 max-w-xs w-full">
            <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-sm">
              search
            </span>
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name, email, or record ID..."
              className="pl-9 h-9 text-xs"
            />
          </div>
          <span className="text-xs font-semibold text-muted-foreground">
            {filteredPatients.length} Registered Patients
          </span>
        </CardContent>
      </Card>

      {/* Directory Table */}
      <Card className="border shadow-sm overflow-hidden bg-white">
        <CardContent className="p-0">
          <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border text-[10px] font-bold text-muted-foreground uppercase bg-slate-50/50 dark:bg-zinc-800/20 select-none">
                  <th className="px-5 py-3 font-semibold">Patient Profile</th>
                  <th className="px-5 py-3 font-semibold">Contact Info</th>
                  <th className="px-5 py-3 font-semibold">Birthdate / Gender</th>
                  <th className="px-5 py-3 font-semibold">Blood Group</th>
                  <th className="px-5 py-3 font-semibold">Insurance Carrier</th>
                  <th className="px-5 py-3 font-semibold">Total Visits</th>
                  <th className="px-5 py-3 font-semibold">Last Medical Evaluation</th>
                  <th className="px-5 py-3 font-semibold text-right">Scope</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs">
                {filteredPatients.map((pat) => (
                  <tr
                    key={pat.id}
                    className="hover:bg-slate-50/40 dark:hover:bg-zinc-800/10 transition-colors"
                  >
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-3">
                        <Avatar className="h-9 w-9 shadow-sm border border-slate-100">
                          <AvatarImage src={pat.avatar} alt={pat.name} />
                          <AvatarFallback className="bg-voxmed-primary text-white text-xs font-semibold">
                            {getInitials(pat.name)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex flex-col">
                          <span className="font-bold text-slate-800 dark:text-zinc-200">
                            {pat.name}
                          </span>
                          <span className="text-[10px] text-slate-400 font-bold uppercase mt-0.5">
                            ID: #{pat.id}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex flex-col">
                        <span className="font-semibold text-slate-700">{pat.email}</span>
                        <span className="text-[10px] text-muted-foreground font-medium mt-0.5">
                          {pat.phone}
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex flex-col">
                        <span className="font-medium text-slate-800">{formatDate(pat.dateOfBirth)}</span>
                        <span className="text-[10px] text-slate-400 capitalize mt-0.5">
                          {pat.gender}
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200 text-[10px] font-bold">
                        {pat.bloodGroup}
                      </Badge>
                    </td>
                    <td className="px-5 py-3.5 text-muted-foreground font-semibold">
                      {pat.insuranceProvider || 'Self Pay'}
                    </td>
                    <td className="px-5 py-3.5 font-bold text-slate-700 text-center">{pat.totalVisits}</td>
                    <td className="px-5 py-3.5">
                      <span className="font-semibold text-slate-800">{formatDate(pat.lastVisit)}</span>
                    </td>
                    <td className="px-5 py-3.5 text-right flex items-center justify-end gap-1.5">
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-[10px] font-semibold border-slate-200 hover:bg-slate-50"
                        onClick={() => handleOpenProfile(pat)}
                      >
                        Clinical File
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 w-7 p-0 text-slate-600 border-slate-200 hover:bg-slate-50 flex items-center justify-center"
                        onClick={() => handleOpenEdit(pat)}
                      >
                        <span className="material-symbols-outlined text-[14px]">edit</span>
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 w-7 p-0 text-rose-600 border-rose-100 hover:bg-rose-50 flex items-center justify-center"
                        onClick={() => handleDelete(pat.id)}
                      >
                        <span className="material-symbols-outlined text-[14px]">delete</span>
                      </Button>
                    </td>
                  </tr>
                ))}
                {filteredPatients.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-xs text-muted-foreground">
                      No matching patient profiles found in local database.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* ── EXPANDABLE PATIENT PROFILE SHEET ── */}
      {selectedPatient && (
        <Sheet open={isSheetOpen} onOpenChange={setIsSheetOpen}>
          <SheetContent className="sm:max-w-xl overflow-y-auto custom-scrollbar bg-white z-50 p-6 flex flex-col gap-6">
            <SheetHeader className="border-b pb-4">
              <div className="flex items-center gap-4">
                <Avatar className="h-12 w-12 border border-slate-200 shadow-md">
                  <AvatarImage src={selectedPatient.avatar} />
                  <AvatarFallback className="bg-voxmed-primary text-white font-bold">
                    {getInitials(selectedPatient.name)}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <SheetTitle className="text-base font-bold">{selectedPatient.name}</SheetTitle>
                  <SheetDescription className="text-xs">
                    Clinical record file: {selectedPatient.id} • Registered {formatDate(selectedPatient.createdAt)}
                  </SheetDescription>
                </div>
              </div>
            </SheetHeader>

            {/* EHR Demographic Profile Section */}
            <div className="space-y-4 text-xs">
              <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider border-b pb-1">
                EHR Demographic Data
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-0.5">
                  <span className="text-slate-400 font-medium">Professional Email</span>
                  <p className="font-semibold text-slate-800">{selectedPatient.email}</p>
                </div>
                <div className="space-y-0.5">
                  <span className="text-slate-400 font-medium">Active Phone</span>
                  <p className="font-semibold text-slate-800">{selectedPatient.phone}</p>
                </div>
                <div className="space-y-0.5">
                  <span className="text-slate-400 font-medium">Birthdate</span>
                  <p className="font-semibold text-slate-800">
                    {formatDate(selectedPatient.dateOfBirth, 'MMMM dd, yyyy')}
                  </p>
                </div>
                <div className="space-y-0.5">
                  <span className="text-slate-400 font-medium">Gender scope</span>
                  <p className="font-semibold text-slate-800 capitalize">{selectedPatient.gender}</p>
                </div>
              </div>

              <div className="space-y-0.5 mt-2">
                <span className="text-slate-400 font-medium">Registered Address</span>
                <p className="font-semibold text-slate-800 leading-normal">{selectedPatient.address}</p>
              </div>

              <div className="space-y-0.5 mt-2 bg-slate-50 p-2.5 rounded-lg border border-dashed">
                <span className="text-slate-400 font-medium">Emergency Clinical Triage Contact</span>
                <p className="font-semibold text-slate-800 mt-0.5">{selectedPatient.emergencyContact}</p>
              </div>
            </div>

            {/* Insurance Policy Records */}
            <div className="space-y-3 text-xs">
              <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider border-b pb-1">
                Clinical Insurance Policy
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-0.5">
                  <span className="text-slate-400 font-medium">Policy Carrier</span>
                  <p className="font-semibold text-slate-800">
                    {selectedPatient.insuranceProvider || 'Self Pay Profile'}
                  </p>
                </div>
                <div className="space-y-0.5">
                  <span className="text-slate-400 font-medium">Insurance Policy ID</span>
                  <p className="font-semibold text-slate-800">
                    {selectedPatient.insuranceId || 'Not Documented'}
                  </p>
                </div>
              </div>
            </div>

            {/* Speech Interactions & Voice logs */}
            <div className="space-y-3 text-xs flex-1">
              <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider border-b pb-1">
                Speech Analytics & Live Call Records
              </h4>
              <div className="space-y-2.5 max-h-56 overflow-y-auto custom-scrollbar">
                {patientCalls.map((call) => (
                  <div
                    key={call.id}
                    className="p-3 bg-slate-50 dark:bg-zinc-800/30 rounded-lg border border-border flex flex-col gap-2"
                  >
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="font-bold text-slate-800">
                        {call.type === 'inbound' ? 'Inbound Call' : 'Outbound Call'}
                      </span>
                      <span className="text-muted-foreground">{formatDate(call.startedAt, 'MMM dd, yyyy h:mm a')}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[10px] border-y py-1.5 border-dashed">
                      <div>
                        <span className="text-slate-400 font-medium">Intent Identified:</span>
                        <p className="font-semibold text-slate-700 mt-0.5">{call.intent}</p>
                      </div>
                      <div>
                        <span className="text-slate-400 font-medium">CSAT Sentiment:</span>
                        <p className={cn('font-bold mt-0.5 capitalize', SENTIMENT_COLORS[call.sentiment])}>
                          {call.sentiment}
                        </p>
                      </div>
                    </div>

                    {call.resolution && (
                      <div className="text-[10px]">
                        <span className="text-slate-400 font-bold">Call Resolution summary:</span>
                        <p className="text-slate-600 mt-0.5 font-light leading-relaxed">
                          {call.resolution}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
                {patientCalls.length === 0 && (
                  <div className="py-6 text-center text-muted-foreground">
                    No active voice recordings indexed for this patient file.
                  </div>
                )}
              </div>
            </div>
          </SheetContent>
        </Sheet>
      )}

      {/* ── REGISTER PATIENT DIALOG ── */}
      <Dialog open={isRegisterOpen} onOpenChange={setIsRegisterOpen}>
        <DialogContent className="sm:max-w-md bg-white shadow-2xl p-6">
          <DialogHeader className="border-b pb-4">
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <span className="material-symbols-outlined text-voxmed-primary">person_add</span>
              Register New Patient
            </DialogTitle>
            <DialogDescription className="text-xs">
              Manually register a new patient in the hospital EHR directory.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleRegisterSubmit} className="space-y-4 py-4 text-xs">
            <div className="space-y-1">
              <label className="font-bold text-slate-700">Full Name *</label>
              <Input
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="Enter patient full name"
                required
                className="h-9 text-xs"
              />
            </div>
            <div className="space-y-1">
              <label className="font-bold text-slate-700">Phone Number *</label>
              <Input
                value={formPhone}
                onChange={(e) => setFormPhone(e.target.value)}
                placeholder="+91 XXXXX XXXXX"
                required
                className="h-9 text-xs"
              />
            </div>
            <div className="space-y-1">
              <label className="font-bold text-slate-700">Email Address</label>
              <Input
                type="email"
                value={formEmail}
                onChange={(e) => setFormEmail(e.target.value)}
                placeholder="patient@example.com"
                className="h-9 text-xs"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="font-bold text-slate-700">Date of Birth</label>
                <Input
                  type="date"
                  value={formDob}
                  onChange={(e) => setFormDob(e.target.value)}
                  className="h-9 text-xs"
                />
              </div>
              <div className="space-y-1">
                <label className="font-bold text-slate-700">Gender</label>
                <select
                  value={formGender}
                  onChange={(e) => setFormGender(e.target.value)}
                  className="w-full h-9 px-3 rounded-md border border-input bg-transparent text-xs"
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>
            <div className="space-y-1">
              <label className="font-bold text-slate-700">Address</label>
              <Input
                value={formAddress}
                onChange={(e) => setFormAddress(e.target.value)}
                placeholder="Residential address"
                className="h-9 text-xs"
              />
            </div>
            <DialogFooter className="border-t pt-4">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIsRegisterOpen(false)}
                className="h-9 font-semibold text-xs"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                className="h-9 font-semibold text-xs bg-voxmed-primary text-white"
              >
                Register
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* ── EDIT PATIENT DIALOG ── */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="sm:max-w-md bg-white shadow-2xl p-6">
          <DialogHeader className="border-b pb-4">
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <span className="material-symbols-outlined text-voxmed-primary">edit</span>
              Edit Patient Demographics
            </DialogTitle>
            <DialogDescription className="text-xs">
              Update existing demographics details for #{editingPatient?.id}.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEditSubmit} className="space-y-4 py-4 text-xs">
            <div className="space-y-1">
              <label className="font-bold text-slate-700">Full Name *</label>
              <Input
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="Enter patient full name"
                required
                className="h-9 text-xs"
              />
            </div>
            <div className="space-y-1">
              <label className="font-bold text-slate-700">Phone Number *</label>
              <Input
                value={formPhone}
                onChange={(e) => setFormPhone(e.target.value)}
                placeholder="+91 XXXXX XXXXX"
                required
                className="h-9 text-xs"
              />
            </div>
            <div className="space-y-1">
              <label className="font-bold text-slate-700">Email Address</label>
              <Input
                type="email"
                value={formEmail}
                onChange={(e) => setFormEmail(e.target.value)}
                placeholder="patient@example.com"
                className="h-9 text-xs"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="font-bold text-slate-700">Date of Birth</label>
                <Input
                  type="date"
                  value={formDob}
                  onChange={(e) => setFormDob(e.target.value)}
                  className="h-9 text-xs"
                />
              </div>
              <div className="space-y-1">
                <label className="font-bold text-slate-700">Gender</label>
                <select
                  value={formGender}
                  onChange={(e) => setFormGender(e.target.value)}
                  className="w-full h-9 px-3 rounded-md border border-input bg-transparent text-xs"
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>
            <div className="space-y-1">
              <label className="font-bold text-slate-700">Address</label>
              <Input
                value={formAddress}
                onChange={(e) => setFormAddress(e.target.value)}
                placeholder="Residential address"
                className="h-9 text-xs"
              />
            </div>
            <DialogFooter className="border-t pt-4">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIsEditOpen(false)}
                className="h-9 font-semibold text-xs"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                className="h-9 font-semibold text-xs bg-voxmed-primary text-white"
              >
                Save Changes
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
