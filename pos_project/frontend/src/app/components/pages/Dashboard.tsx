import React from 'react';
import { KPICards } from '../KPICards';
import { Charts } from '../Charts';
import { DataTables } from '../DataTables';
import { QuickActions, type QuickActionId } from '../QuickActions';
import type { CompletedSale, DayBalance, POSProduct } from './POSPageEnhanced';
import type { UserRole } from '../../types/auth';

interface DashboardProps {
  products: POSProduct[];
  completedSales: CompletedSale[];
  dayBalance: DayBalance;
  cashSalesToday: number;
  userRole: UserRole;
  onQuickAction: (action: QuickActionId) => void;
}

export function Dashboard({ products, completedSales, dayBalance, cashSalesToday, userRole, onQuickAction }: DashboardProps) {
  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">DASHBOARD OVERVIEW</h1>
        <p className="text-gray-500">Welcome back! Here's what's happening with your store today.</p>
      </div>

      {/* KPI Cards */}
      <KPICards
        products={products}
        completedSales={completedSales}
        dayBalance={dayBalance}
        cashSalesToday={cashSalesToday}
      />

      {/* Charts Section */}
      <Charts completedSales={completedSales} />

      {/* Data Tables */}
      <DataTables products={products} completedSales={completedSales} />

      {/* Quick Actions and Staff Leaderboard */}
      <QuickActions completedSales={completedSales} userRole={userRole} onAction={onQuickAction} />
    </div>
  );
}
