'use client';

import { useState } from 'react';
import { useAnalytics } from '@/hooks/use-analytics';
import { useDashboardStore } from '@/stores/use-dashboard-store';
import { INVOICE_STATUS_COLORS } from '@/lib/constants';
import { cn, formatDate, formatCurrency } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import type { Invoice } from '@/types/api';

export default function BillingPage() {
  const { invoices, isLoading } = useAnalytics();
  const { searchQuery, setSearchQuery } = useDashboardStore();

  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [isInvoiceOpen, setIsInvoiceOpen] = useState(false);

  // Filter invoices list
  const filteredInvoices = invoices.filter((inv) => {
    const matchesSearch =
      inv.patientName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inv.invoiceNumber.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'all' || inv.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const handleOpenInvoice = (inv: Invoice) => {
    setSelectedInvoice(inv);
    setIsInvoiceOpen(true);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-48 bg-slate-200 dark:bg-zinc-800 animate-pulse rounded"></div>
        <div className="h-96 bg-slate-200 dark:bg-zinc-800 animate-pulse rounded-xl"></div>
      </div>
    );
  }

  // Aggregate totals
  const totalInvoiced = invoices.reduce((acc, curr) => acc + curr.total, 0);
  const totalPaid = invoices.filter((i) => i.status === 'paid').reduce((acc, curr) => acc + curr.total, 0);
  const totalOutstanding = invoices.filter((i) => i.status === 'pending' || i.status === 'overdue').reduce((acc, curr) => acc + curr.total, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">Clinical Billing & Invoices</h1>
        <p className="text-xs text-muted-foreground mt-1">
          Track billing cycles, process insurance claims, and review invoice records synced by CareVoice AI.
        </p>
      </div>

      {/* ── BILLING COUNTERS BANNER ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { title: 'Total Invoiced Scope', value: totalInvoiced, icon: 'receipt_long', color: 'text-blue-600', bg: 'bg-blue-50' },
          { title: 'Collected Revenues', value: totalPaid, icon: 'payments', color: 'text-emerald-600', bg: 'bg-emerald-50' },
          { title: 'Outstanding Receivables', value: totalOutstanding, icon: 'pending_actions', color: 'text-rose-600', bg: 'bg-rose-50' },
        ].map((ctr, idx) => (
          <Card key={idx} className="border shadow-sm bg-white">
            <CardContent className="p-4 flex items-center justify-between">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                  {ctr.title}
                </span>
                <h3 className="text-xl font-black text-slate-800">{formatCurrency(ctr.value)}</h3>
              </div>
              <div className={cn('h-10 w-10 rounded-xl flex items-center justify-center', ctr.bg)}>
                <span className={cn('material-symbols-outlined text-lg', ctr.color)}>{ctr.icon}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* ── FILTER & TAB BAR ── */}
      <Card className="border shadow-sm bg-white">
        <CardContent className="p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="flex flex-1 flex-col sm:flex-row gap-3 w-full md:w-auto">
            {/* Search */}
            <div className="relative flex-1 max-w-xs">
              <span className="material-symbols-outlined absolute left-3 top-2.5 text-muted-foreground text-sm">
                search
              </span>
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search patient or invoice ID..."
                className="pl-9 h-9 text-xs"
              />
            </div>

            {/* Filter Tabs */}
            <div className="flex border rounded-lg overflow-hidden bg-slate-50 border-slate-200">
              {['all', 'paid', 'pending', 'overdue'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setStatusFilter(tab)}
                  className={cn(
                    'px-3.5 py-1 text-xs font-bold capitalize cursor-pointer transition-all',
                    statusFilter === tab
                      ? 'bg-voxmed-primary text-white font-semibold'
                      : 'hover:bg-slate-100 text-slate-600'
                  )}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>
          <span className="text-xs font-semibold text-muted-foreground">
            {filteredInvoices.length} matching billing receipts
          </span>
        </CardContent>
      </Card>

      {/* ── INVOICES ARCHIVE TABLE ── */}
      <Card className="border shadow-sm overflow-hidden bg-white">
        <CardContent className="p-0">
          <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border text-[10px] font-bold text-muted-foreground uppercase bg-slate-50/50 dark:bg-zinc-800/20 select-none">
                  <th className="px-5 py-3 font-semibold">Invoice ID</th>
                  <th className="px-5 py-3 font-semibold">Patient Name</th>
                  <th className="px-5 py-3 font-semibold">Attending Physician</th>
                  <th className="px-5 py-3 font-semibold">Consulting Dept</th>
                  <th className="px-5 py-3 font-semibold">Created / Due</th>
                  <th className="px-5 py-3 font-semibold">Gross Sum</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold text-right">Invoice details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs">
                {filteredInvoices.map((inv) => {
                  const stat = INVOICE_STATUS_COLORS[inv.status] || {
                    bg: 'bg-gray-100',
                    text: 'text-gray-700',
                    dot: 'bg-gray-400',
                  };

                  return (
                    <tr
                      key={inv.id}
                      className="hover:bg-slate-50/40 dark:hover:bg-zinc-800/10 transition-colors"
                    >
                      <td className="px-5 py-3.5 font-bold text-slate-800">{inv.invoiceNumber}</td>
                      <td className="px-5 py-3.5 font-semibold text-slate-800">{inv.patientName}</td>
                      <td className="px-5 py-3.5 font-medium text-slate-700">{inv.doctorName}</td>
                      <td className="px-5 py-3.5 font-medium text-slate-700">{inv.department}</td>
                      <td className="px-5 py-3.5">
                        <div className="flex flex-col text-[10px]">
                          <span>Created: {formatDate(inv.createdAt)}</span>
                          <span className="text-rose-600 mt-0.5">Due: {formatDate(inv.dueDate)}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 font-black text-slate-800">
                        {formatCurrency(inv.total)}
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          className={cn(
                            'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold capitalize select-none',
                            stat.bg,
                            stat.text
                          )}
                        >
                          <span className={cn('h-1.5 w-1.5 rounded-full shrink-0', stat.dot)}></span>
                          {inv.status}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 text-[10px] font-semibold border-slate-200 hover:bg-slate-50"
                          onClick={() => handleOpenInvoice(inv)}
                        >
                          Detailed Bill
                        </Button>
                      </td>
                    </tr>
                  );
                })}
                {filteredInvoices.length === 0 && (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-xs text-muted-foreground">
                      No matching clinical invoices recorded.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* ── ITEMIZED BILLING DETAILS DIALOG MODAL ── */}
      {selectedInvoice && (
        <Dialog open={isInvoiceOpen} onOpenChange={setIsInvoiceOpen}>
          <DialogContent className="sm:max-w-lg z-50 bg-white shadow-2xl p-6">
            <DialogHeader className="border-b pb-4">
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-voxmed-primary text-2xl">
                    receipt_long
                  </span>
                  <div>
                    <DialogTitle className="text-base font-bold">
                      Itemized Clinical Invoice
                    </DialogTitle>
                    <DialogDescription className="text-xs">
                      Sync ID: {selectedInvoice.id} • Issued {formatDate(selectedInvoice.createdAt)}
                    </DialogDescription>
                  </div>
                </div>
                <span className="text-xs font-bold text-slate-800 dark:text-zinc-200">
                  {selectedInvoice.invoiceNumber}
                </span>
              </div>
            </DialogHeader>

            {/* Invoice Body */}
            <div className="py-4 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Patient Payee
                  </span>
                  <p className="font-bold text-slate-800">{selectedInvoice.patientName}</p>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Attending Clinic
                  </span>
                  <p className="font-semibold text-slate-800">
                    {selectedInvoice.doctorName} ({selectedInvoice.department})
                  </p>
                </div>
              </div>

              {/* Itemized list */}
              <div className="border rounded-lg overflow-hidden mt-3">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b text-[9px] font-bold text-muted-foreground uppercase">
                      <th className="px-3 py-2">Service Description</th>
                      <th className="px-3 py-2 text-center">Qty</th>
                      <th className="px-3 py-2 text-right">Unit Rate</th>
                      <th className="px-3 py-2 text-right">Total Price</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border text-[11px]">
                    {selectedInvoice.items.map((item, idx) => (
                      <tr key={idx}>
                        <td className="px-3 py-2 text-slate-800 font-semibold">{item.description}</td>
                        <td className="px-3 py-2 text-center font-bold text-slate-600">
                          {item.quantity}
                        </td>
                        <td className="px-3 py-2 text-right text-muted-foreground">
                          {formatCurrency(item.unitPrice)}
                        </td>
                        <td className="px-3 py-2 text-right font-black text-slate-800">
                          {formatCurrency(item.total)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Totals panel */}
              <div className="flex flex-col gap-1.5 items-end border-t pt-3 font-semibold text-slate-600">
                <div className="flex justify-between w-48 text-[11px]">
                  <span>Subtotal:</span>
                  <span className="text-slate-800">{formatCurrency(selectedInvoice.subtotal)}</span>
                </div>
                <div className="flex justify-between w-48 text-[11px]">
                  <span>GST Tax (18%):</span>
                  <span className="text-slate-800">{formatCurrency(selectedInvoice.tax)}</span>
                </div>
                {selectedInvoice.discount > 0 && (
                  <div className="flex justify-between w-48 text-[11px] text-emerald-600 font-bold">
                    <span>Loyalty Discount:</span>
                    <span>-{formatCurrency(selectedInvoice.discount)}</span>
                  </div>
                )}
                <div className="flex justify-between w-48 text-xs font-black text-slate-800 border-t pt-2 mt-1">
                  <span>Gross Total:</span>
                  <span className="text-voxmed-primary">{formatCurrency(selectedInvoice.total)}</span>
                </div>
              </div>
            </div>

            <DialogFooter className="border-t pt-4">
              <Button
                variant="outline"
                size="sm"
                className="h-9 font-semibold text-xs"
                onClick={() => setIsInvoiceOpen(false)}
              >
                Close Receipt
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
