import { create } from 'zustand';

interface DashboardState {
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  searchQuery: string;
  dateRange: { from: Date | undefined; to: Date | undefined };
  selectedDepartment: string;
  toggleSidebar: () => void;
  toggleSidebarCollapse: () => void;
  setSearchQuery: (query: string) => void;
  setDateRange: (range: { from: Date | undefined; to: Date | undefined }) => void;
  setSelectedDepartment: (dept: string) => void;
}

export const useDashboardStore = create<DashboardState>()((set) => ({
  sidebarOpen: true,
  sidebarCollapsed: false,
  searchQuery: '',
  dateRange: { from: undefined, to: undefined },
  selectedDepartment: 'all',

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleSidebarCollapse: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setDateRange: (range) => set({ dateRange: range }),
  setSelectedDepartment: (dept) => set({ selectedDepartment: dept }),
}));
