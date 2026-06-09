import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Badge } from '../ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Textarea } from '../ui/textarea';
import { Plus, Search, Trash2, Receipt, TrendingDown, Loader2, RefreshCw } from 'lucide-react';
import type { BusinessExpense } from '../../types/supplierOrder';
import {
  loadExpenses,
  loadExpenseCategories,
  createExpense,
  deleteExpense,
  type BackendExpense,
  type BackendExpenseCategory
} from '../../services/api';

const today = () => new Date().toISOString().slice(0, 10);

interface ExpensesPageProps {
  expenses?: BusinessExpense[];
  onExpenseCreated?: (expense: Omit<BusinessExpense, 'id'>) => void;
}

const statusBadge = (status: string) => {
  const colors: Record<string, string> = {
    draft: 'bg-gray-500/20 text-gray-500',
    submitted: 'bg-blue-500/20 text-blue-600',
    approved: 'bg-green-500/20 text-green-600',
    paid: 'bg-purple-500/20 text-purple-600',
    rejected: 'bg-red-500/20 text-red-600'
  };
  return <Badge className={colors[status] || 'bg-gray-500/20 text-gray-500'}>{status}</Badge>;
};

export function ExpensesPage({ onExpenseCreated }: ExpensesPageProps) {
  const [expenses, setExpenses] = useState<BackendExpense[]>([]);
  const [categories, setCategories] = useState<BackendExpenseCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  const [form, setForm] = useState({
    category: '',
    amount: '',
    date: today(),
    description: '',
    notes: ''
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      setError('');
      const [expData, catData] = await Promise.all([loadExpenses(), loadExpenseCategories()]);
      setExpenses(expData);
      setCategories(catData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load expenses');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateExpense = async () => {
    const amount = Number(form.amount);
    if (!amount || amount <= 0) { setFormError('Please enter a valid amount'); return; }
    if (!form.description.trim()) { setFormError('Description is required'); return; }
    setFormError('');
    setSaving(true);
    try {
      const created = await createExpense({
        category: form.category ? Number(form.category) : undefined,
        amount,
        description: form.description.trim(),
        expense_date: form.date || today(),
        notes: form.notes.trim() || undefined
      });
      setExpenses(prev => [created, ...prev]);

      if (onExpenseCreated) {
        const cat = categories.find(c => String(c.id) === form.category);
        onExpenseCreated({
          category: cat?.name || 'Other',
          description: form.description.trim(),
          amount,
          date: form.date || today(),
          paymentMethod: 'Cash',
          receipt: true
        });
      }

      setForm({ category: '', amount: '', date: today(), description: '', notes: '' });
      setIsAddDialogOpen(false);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Could not create expense');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this expense?')) return;
    try {
      await deleteExpense(id);
      setExpenses(prev => prev.filter(e => e.id !== id));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Could not delete expense');
    }
  };

  const filteredExpenses = expenses.filter(e => {
    const matchesSearch =
      (e.description || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (e.expense_number || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (e.category_name || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || String(e.category) === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const totalAmount = expenses.reduce((sum, e) => sum + Number(e.total_amount || e.amount || 0), 0);
  const thisMonth = expenses
    .filter(e => new Date(e.expense_date).getMonth() === new Date().getMonth())
    .reduce((sum, e) => sum + Number(e.total_amount || e.amount || 0), 0);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Expense Management</h1>
          <p className="text-gray-500">Track and manage business expenses</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData} className="border-gray-200">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                <Plus className="w-4 h-4 mr-2" />
                Add Expense
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-white border-gray-200 max-w-md">
              <DialogHeader>
                <DialogTitle className="text-gray-900">Add New Expense</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                {categories.length > 0 && (
                  <Select value={form.category} onValueChange={v => setForm(f => ({ ...f, category: v }))}>
                    <SelectTrigger className="bg-gray-100 border-gray-200 text-gray-900">
                      <SelectValue placeholder="Select Category (Optional)" />
                    </SelectTrigger>
                    <SelectContent className="bg-white border-gray-200">
                      <SelectItem value="">No Category</SelectItem>
                      {categories.map(cat => (
                        <SelectItem key={cat.id} value={String(cat.id)}>{cat.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                <Input
                  placeholder="Amount (KSh) *"
                  type="number"
                  step="0.01"
                  value={form.amount}
                  onChange={e => setForm(f => ({ ...f, amount: e.target.value }))}
                  className="bg-gray-100 border-gray-200 text-gray-900"
                />
                <Input
                  type="date"
                  value={form.date}
                  onChange={e => setForm(f => ({ ...f, date: e.target.value }))}
                  className="bg-gray-100 border-gray-200 text-gray-900"
                />
                <Textarea
                  placeholder="Description *"
                  value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  className="bg-gray-100 border-gray-200 text-gray-900"
                />
                <Textarea
                  placeholder="Notes (Optional)"
                  value={form.notes}
                  onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
                  className="bg-gray-100 border-gray-200 text-gray-900"
                />
                {formError && <p className="text-red-500 text-sm">{formError}</p>}
                <div className="flex gap-2">
                  <Button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white" onClick={handleCreateExpense} disabled={saving}>
                    {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                    Add Expense
                  </Button>
                  <Button variant="outline" onClick={() => { setIsAddDialogOpen(false); setFormError(''); }}>Cancel</Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card className="bg-white border-gray-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Total Expenses</p>
                <p className="text-2xl font-semibold text-gray-900">KSh {totalAmount.toFixed(0)}</p>
              </div>
              <div className="p-2 bg-red-500/20 rounded-lg">
                <TrendingDown className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-gray-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">This Month</p>
                <p className="text-2xl font-semibold text-gray-900">KSh {thisMonth.toFixed(0)}</p>
              </div>
              <div className="p-2 bg-orange-500/20 rounded-lg">
                <Receipt className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-gray-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Total Records</p>
                <p className="text-2xl font-semibold text-gray-900">{expenses.length}</p>
              </div>
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Plus className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-gray-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Approved</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {expenses.filter(e => e.status === 'approved' || e.status === 'paid').length}
                </p>
              </div>
              <div className="p-2 bg-green-500/20 rounded-lg">
                <Search className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-white border-gray-200 mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 w-4 h-4" />
              <Input
                placeholder="Search expenses..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="pl-10 bg-gray-100 border-gray-200 text-gray-900"
              />
            </div>
            {categories.length > 0 && (
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-44 bg-gray-100 border-gray-200 text-gray-900">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white border-gray-200">
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map(cat => (
                    <SelectItem key={cat.id} value={String(cat.id)}>{cat.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Expenses Table */}
      <Card className="bg-white border-gray-200">
        <CardHeader>
          <CardTitle className="text-gray-900">Expenses ({filteredExpenses.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center items-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              <span className="ml-2 text-gray-500">Loading expenses...</span>
            </div>
          ) : error ? (
            <div className="text-red-500 text-center py-8">
              <p>{error}</p>
              <Button variant="outline" onClick={fetchData} className="mt-4">Retry</Button>
            </div>
          ) : filteredExpenses.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              {searchTerm || categoryFilter !== 'all' ? 'No expenses match your filters.' : 'No expenses yet. Add your first expense above.'}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-gray-200">
                  <TableHead className="text-gray-600">Number</TableHead>
                  <TableHead className="text-gray-600">Category</TableHead>
                  <TableHead className="text-gray-600">Description</TableHead>
                  <TableHead className="text-gray-600">Amount</TableHead>
                  <TableHead className="text-gray-600">Date</TableHead>
                  <TableHead className="text-gray-600">Status</TableHead>
                  <TableHead className="text-gray-600">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredExpenses.map(expense => (
                  <TableRow key={expense.id} className="border-gray-200">
                    <TableCell className="text-gray-500 text-xs">{expense.expense_number}</TableCell>
                    <TableCell>
                      {expense.category_name ? (
                        <Badge className="bg-purple-500/20 text-purple-600">{expense.category_name}</Badge>
                      ) : (
                        <span className="text-gray-400 text-sm">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-gray-900">{expense.description}</TableCell>
                    <TableCell className="text-red-600">
                      KSh {Number(expense.total_amount || expense.amount || 0).toFixed(2)}
                    </TableCell>
                    <TableCell className="text-gray-600">{expense.expense_date}</TableCell>
                    <TableCell>{statusBadge(expense.status)}</TableCell>
                    <TableCell>
                      {expense.status === 'draft' && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-red-500 hover:text-red-300"
                          onClick={() => handleDelete(expense.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
