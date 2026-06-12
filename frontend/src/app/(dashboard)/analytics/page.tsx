'use client';

import { useAnalytics } from '@/hooks/use-analytics';
import { cn, formatCurrency, formatPercentage } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

export default function AnalyticsPage() {
  const { analytics, isLoading } = useAnalytics();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-48 bg-slate-200 dark:bg-zinc-800 animate-pulse rounded"></div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-96 bg-slate-200 dark:bg-zinc-800 animate-pulse rounded-xl"></div>
          <div className="h-96 bg-slate-200 dark:bg-zinc-800 animate-pulse rounded-xl"></div>
        </div>
      </div>
    );
  }

  const { callMetrics, appointmentMetrics, revenueMetrics, aiMetrics } = analytics;

  // Aggregate clinical counters
  const analyticsSummary = [
    { title: 'AI Call Resolution Rate', value: `${aiMetrics.escalationRate}% Transferred`, icon: 'escalator_warning', color: 'text-amber-600', bg: 'bg-amber-50', desc: 'Required human operator assistance' },
    { title: 'Average Speech Match Accuracy', value: `${aiMetrics.avgConfidence}%`, icon: 'neurology', color: 'text-blue-600', bg: 'bg-blue-50', desc: 'Clinical NLP intent verification confidence' },
    { title: 'Gross Hospital CSAT', value: `${aiMetrics.satisfactionScore} / 5.0`, icon: 'reviews', color: 'text-emerald-600', bg: 'bg-emerald-50', desc: 'Attending post-call feedback ratings' },
    { title: 'Outstanding Receivables', value: formatCurrency(revenueMetrics.outstandingAmount), icon: 'toll', color: 'text-rose-600', bg: 'bg-rose-50', desc: 'Pending collection claims' },
  ];

  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">Speech & Financial Analytics</h1>
        <p className="text-xs text-muted-foreground mt-1">
          Deep visual modeling of hospital financial collections, patient sentiment trends, and neural NLP accuracy.
        </p>
      </div>

      {/* ── KPI METRICS BANNER ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {analyticsSummary.map((sum, idx) => (
          <Card key={idx} className="border shadow-sm bg-white">
            <CardContent className="p-4 flex items-center justify-between">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  {sum.title}
                </span>
                <h3 className="text-lg font-black text-slate-800">{sum.value}</h3>
                <span className="text-[9px] text-muted-foreground block font-light leading-none">
                  {sum.desc}
                </span>
              </div>
              <div className={cn('h-10 w-10 rounded-xl flex items-center justify-center shrink-0 ml-2', sum.bg)}>
                <span className={cn('material-symbols-outlined text-lg', sum.color)}>{sum.icon}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* ── CHARTS PLOT GRID ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Revenue trend (7 days) */}
        <Card className="border shadow-sm bg-white">
          <CardHeader className="p-5 pb-0">
            <CardTitle className="text-base font-bold">Revenue Intake Trend</CardTitle>
            <CardDescription className="text-xs">
              Daily collections tracking over the last 7 clinical shift cycles
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5 pt-4">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={revenueMetrics.trend} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#006b24" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#006b24" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="date" tickLine={false} tick={{ fontSize: 10 }} />
                  <YAxis tickLine={false} tick={{ fontSize: 10 }} />
                  <ChartTooltip
                    formatter={(value) => [formatCurrency(Number(value)), 'Revenues']}
                    contentStyle={{
                      background: 'rgba(255,255,255,0.95)',
                      border: '1px solid #e2e5ee',
                      borderRadius: '8px',
                      fontSize: '11px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="amount"
                    stroke="#006b24"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorRevenue)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Chart 2: Revenue distribution by Department */}
        <Card className="border shadow-sm bg-white">
          <CardHeader className="p-5 pb-0">
            <CardTitle className="text-base font-bold">Billing Scope by Specialty</CardTitle>
            <CardDescription className="text-xs">
              Attending fees and treatment revenue shares split by clinic department
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5 pt-4">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={revenueMetrics.byDepartment}
                  layout="vertical"
                  margin={{ top: 10, right: 10, left: 20, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                  <XAxis type="number" tickLine={false} tick={{ fontSize: 10 }} />
                  <YAxis dataKey="department" type="category" tickLine={false} tick={{ fontSize: 10 }} width={80} />
                  <ChartTooltip
                    formatter={(value) => [formatCurrency(Number(value)), 'Intake']}
                    contentStyle={{
                      background: 'rgba(255,255,255,0.95)',
                      border: '1px solid #e2e5ee',
                      borderRadius: '8px',
                      fontSize: '11px',
                    }}
                  />
                  <Bar dataKey="amount" fill="#0058bc" radius={[0, 4, 4, 0]} maxBarSize={16} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Chart 3: AI intent distribution */}
        <Card className="border shadow-sm bg-white">
          <CardHeader className="p-5 pb-0">
            <CardTitle className="text-base font-bold">NLP Identified Intents</CardTitle>
            <CardDescription className="text-xs">
              Volumetric distribution of patient call objectives categorized by speech core
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5 pt-4">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={aiMetrics.intentDistribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="intent" tickLine={false} tick={{ fontSize: 9 }} />
                  <YAxis tickLine={false} tick={{ fontSize: 10 }} />
                  <ChartTooltip
                    contentStyle={{
                      background: 'rgba(255,255,255,0.95)',
                      border: '1px solid #e2e5ee',
                      borderRadius: '8px',
                      fontSize: '11px',
                    }}
                  />
                  <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} maxBarSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Chart 4: Stacked Sentiment Trends */}
        <Card className="border shadow-sm bg-white">
          <CardHeader className="p-5 pb-0">
            <CardTitle className="text-base font-bold">Patient Evaluation Sentiment Trend</CardTitle>
            <CardDescription className="text-xs">
              Daily aggregates of positive, neutral, and negative clinical speech evaluations
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5 pt-4">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={aiMetrics.sentimentTrend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="date" tickLine={false} tick={{ fontSize: 10 }} />
                  <YAxis tickLine={false} tick={{ fontSize: 10 }} />
                  <ChartTooltip
                    contentStyle={{
                      background: 'rgba(255,255,255,0.95)',
                      border: '1px solid #e2e5ee',
                      borderRadius: '8px',
                      fontSize: '11px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="positive"
                    stackId="1"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.15}
                  />
                  <Area
                    type="monotone"
                    dataKey="neutral"
                    stackId="1"
                    stroke="#94a3b8"
                    fill="#94a3b8"
                    fillOpacity={0.15}
                  />
                  <Area
                    type="monotone"
                    dataKey="negative"
                    stackId="1"
                    stroke="#ef4444"
                    fill="#ef4444"
                    fillOpacity={0.15}
                  />
                  <Legend iconSize={8} wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
