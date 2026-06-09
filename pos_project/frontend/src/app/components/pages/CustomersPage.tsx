import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Badge } from '../ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Plus, Search, Edit, Eye, Phone, Mail, Loader2, Trash2, RefreshCw } from 'lucide-react';
import { loadCustomers, createCustomer, updateCustomer, deleteCustomer, type BackendCustomer } from '../../services/api';

interface CustomersPageProps {
  openAddCustomerSignal?: number;
}

export function CustomersPage({ openAddCustomerSignal = 0 }: CustomersPageProps) {
  const [customers, setCustomers] = useState<BackendCustomer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<BackendCustomer | null>(null);
  const [editCustomer, setEditCustomer] = useState<BackendCustomer | null>(null);
  const [saving, setSaving] = useState(false);

  const [form, setForm] = useState({
    name: '',
    phone: '',
    email: '',
    pricing_tier: 'retail',
    notes: ''
  });
  const [formError, setFormError] = useState('');

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await loadCustomers();
      setCustomers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load customers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, []);

  useEffect(() => {
    if (openAddCustomerSignal > 0) {
      setIsAddDialogOpen(true);
    }
  }, [openAddCustomerSignal]);

  const handleAddCustomer = async () => {
    if (!form.name.trim()) { setFormError('Name is required'); return; }
    if (!form.phone.trim()) { setFormError('Phone is required'); return; }
    setFormError('');
    setSaving(true);
    try {
      const created = await createCustomer({
        name: form.name.trim(),
        phone: form.phone.trim(),
        email: form.email.trim() || undefined,
        pricing_tier: form.pricing_tier
      });
      setCustomers(prev => [created, ...prev]);
      setForm({ name: '', phone: '', email: '', pricing_tier: 'retail', notes: '' });
      setIsAddDialogOpen(false);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Could not create customer');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateCustomer = async () => {
    if (!editCustomer) return;
    setSaving(true);
    try {
      const updated = await updateCustomer(editCustomer.id, {
        name: editCustomer.name,
        phone: editCustomer.phone,
        email: editCustomer.email || undefined,
        pricing_tier: editCustomer.pricing_tier
      });
      setCustomers(prev => prev.map(c => c.id === updated.id ? updated : c));
      setEditCustomer(null);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Could not update customer');
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (id: number) => {
    if (!confirm('Deactivate this customer?')) return;
    try {
      await deleteCustomer(id);
      setCustomers(prev => prev.map(c => c.id === id ? { ...c, is_active: false } : c));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Could not deactivate customer');
    }
  };

  const filteredCustomers = customers.filter(c =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.phone || '').includes(searchTerm) ||
    (c.email || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getCustomerTier = (points: number) => {
    if (points >= 500) return <Badge className="bg-yellow-500/20 text-yellow-600">Gold</Badge>;
    if (points >= 200) return <Badge className="bg-gray-400/20 text-gray-600">Silver</Badge>;
    return <Badge className="bg-orange-500/20 text-orange-600">Bronze</Badge>;
  };

  const getPricingBadge = (tier: string) => {
    const colors: Record<string, string> = {
      retail: 'bg-blue-500/20 text-blue-600',
      wholesale: 'bg-green-500/20 text-green-600',
      vip: 'bg-purple-500/20 text-purple-600'
    };
    return <Badge className={colors[tier] || 'bg-gray-500/20 text-gray-600'}>{tier}</Badge>;
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Customer Management</h1>
          <p className="text-gray-500">Manage customer information and loyalty programs</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchCustomers} className="border-gray-200">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                <Plus className="w-4 h-4 mr-2" />
                Add Customer
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-white border-gray-200 max-w-md">
              <DialogHeader>
                <DialogTitle className="text-gray-900">Add New Customer</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <Input
                  placeholder="Full Name *"
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  className="bg-gray-100 border-gray-200 text-gray-900"
                />
                <Input
                  placeholder="Phone Number * (e.g. 0712345678)"
                  value={form.phone}
                  onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
                  className="bg-gray-100 border-gray-200 text-gray-900"
                />
                <Input
                  placeholder="Email Address (Optional)"
                  type="email"
                  value={form.email}
                  onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                  className="bg-gray-100 border-gray-200 text-gray-900"
                />
                <Select value={form.pricing_tier} onValueChange={v => setForm(f => ({ ...f, pricing_tier: v }))}>
                  <SelectTrigger className="bg-gray-100 border-gray-200 text-gray-900">
                    <SelectValue placeholder="Pricing Tier" />
                  </SelectTrigger>
                  <SelectContent className="bg-white border-gray-200">
                    <SelectItem value="retail">Retail</SelectItem>
                    <SelectItem value="wholesale">Wholesale</SelectItem>
                    <SelectItem value="vip">VIP</SelectItem>
                  </SelectContent>
                </Select>
                {formError && <p className="text-red-500 text-sm">{formError}</p>}
                <div className="flex gap-2">
                  <Button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white" onClick={handleAddCustomer} disabled={saving}>
                    {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                    Add Customer
                  </Button>
                  <Button variant="outline" onClick={() => { setIsAddDialogOpen(false); setFormError(''); }}>Cancel</Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card className="bg-white border-gray-200">
          <CardContent className="p-4">
            <p className="text-gray-500 text-sm">Total Customers</p>
            <p className="text-2xl font-semibold text-gray-900">{customers.length}</p>
          </CardContent>
        </Card>
        <Card className="bg-white border-gray-200">
          <CardContent className="p-4">
            <p className="text-gray-500 text-sm">Active Customers</p>
            <p className="text-2xl font-semibold text-gray-900">{customers.filter(c => c.is_active).length}</p>
          </CardContent>
        </Card>
        <Card className="bg-white border-gray-200">
          <CardContent className="p-4">
            <p className="text-gray-500 text-sm">VIP Members</p>
            <p className="text-2xl font-semibold text-gray-900">{customers.filter(c => c.pricing_tier === 'vip').length}</p>
          </CardContent>
        </Card>
        <Card className="bg-white border-gray-200">
          <CardContent className="p-4">
            <p className="text-gray-500 text-sm">Total Loyalty Points</p>
            <p className="text-2xl font-semibold text-gray-900">
              {customers.reduce((sum, c) => sum + (c.loyalty_points || 0), 0).toLocaleString()}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Card className="bg-white border-gray-200 mb-6">
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 w-4 h-4" />
            <Input
              placeholder="Search by name, phone or email..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="pl-10 bg-gray-100 border-gray-200 text-gray-900"
            />
          </div>
        </CardContent>
      </Card>

      {/* Customers Table */}
      <Card className="bg-white border-gray-200">
        <CardHeader>
          <CardTitle className="text-gray-900">Customers ({filteredCustomers.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center items-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              <span className="ml-2 text-gray-500">Loading customers...</span>
            </div>
          ) : error ? (
            <div className="text-red-500 text-center py-8">
              <p>{error}</p>
              <Button variant="outline" onClick={fetchCustomers} className="mt-4">Retry</Button>
            </div>
          ) : filteredCustomers.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              {searchTerm ? 'No customers match your search.' : 'No customers yet. Add your first customer above.'}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-gray-200">
                  <TableHead className="text-gray-600">Name</TableHead>
                  <TableHead className="text-gray-600">Contact</TableHead>
                  <TableHead className="text-gray-600">Loyalty Points</TableHead>
                  <TableHead className="text-gray-600">Total Spent</TableHead>
                  <TableHead className="text-gray-600">Tier</TableHead>
                  <TableHead className="text-gray-600">Status</TableHead>
                  <TableHead className="text-gray-600">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCustomers.map(customer => (
                  <TableRow key={customer.id} className="border-gray-200">
                    <TableCell className="text-gray-900 font-medium">
                      {customer.name}
                      {customer.account_reference && (
                        <div className="text-xs text-gray-400">{customer.account_reference}</div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="text-gray-600 text-sm">
                        <div className="flex items-center gap-1">
                          <Phone className="w-3 h-3" />
                          {customer.phone}
                        </div>
                        {customer.email && (
                          <div className="flex items-center gap-1 mt-1">
                            <Mail className="w-3 h-3" />
                            {customer.email}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-yellow-600">{customer.loyalty_points || 0}</TableCell>
                    <TableCell className="text-green-600">KSh {Number(customer.total_spent || 0).toFixed(2)}</TableCell>
                    <TableCell>{getPricingBadge(customer.pricing_tier)}</TableCell>
                    <TableCell>
                      <Badge className={customer.is_active ? 'bg-green-500/20 text-green-600' : 'bg-red-500/20 text-red-600'}>
                        {customer.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-blue-600 hover:text-blue-300"
                          onClick={() => setSelectedCustomer(customer)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-green-600 hover:text-green-300"
                          onClick={() => setEditCustomer({ ...customer })}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        {customer.is_active && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-red-500 hover:text-red-300"
                            onClick={() => handleDeactivate(customer.id)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* View Customer Dialog */}
      {selectedCustomer && (
        <Dialog open={!!selectedCustomer} onOpenChange={() => setSelectedCustomer(null)}>
          <DialogContent className="bg-white border-gray-200 max-w-md">
            <DialogHeader>
              <DialogTitle className="text-gray-900">Customer Details</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-gray-900 font-semibold">{selectedCustomer.name}</h3>
                {getPricingBadge(selectedCustomer.pricing_tier)}
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-gray-600">
                  <Phone className="w-4 h-4" />
                  {selectedCustomer.phone}
                </div>
                {selectedCustomer.email && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Mail className="w-4 h-4" />
                    {selectedCustomer.email}
                  </div>
                )}
                {selectedCustomer.account_reference && (
                  <div className="text-gray-400 text-xs">Ref: {selectedCustomer.account_reference}</div>
                )}
              </div>
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                <div>
                  <p className="text-gray-500 text-xs">Total Spent</p>
                  <p className="text-green-600 font-semibold">KSh {Number(selectedCustomer.total_spent || 0).toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Loyalty Points</p>
                  <p className="text-yellow-600 font-semibold">{selectedCustomer.loyalty_points || 0}</p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Status</p>
                  <p className="text-gray-900 font-semibold">{selectedCustomer.is_active ? 'Active' : 'Inactive'}</p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Tier</p>
                  <p className="text-gray-900 font-semibold capitalize">{selectedCustomer.pricing_tier}</p>
                </div>
              </div>
              <Button className="w-full" onClick={() => setSelectedCustomer(null)}>Close</Button>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Edit Customer Dialog */}
      {editCustomer && (
        <Dialog open={!!editCustomer} onOpenChange={() => setEditCustomer(null)}>
          <DialogContent className="bg-white border-gray-200 max-w-md">
            <DialogHeader>
              <DialogTitle className="text-gray-900">Edit Customer</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <Input
                placeholder="Full Name *"
                value={editCustomer.name}
                onChange={e => setEditCustomer(c => c ? { ...c, name: e.target.value } : c)}
                className="bg-gray-100 border-gray-200 text-gray-900"
              />
              <Input
                placeholder="Phone Number *"
                value={editCustomer.phone}
                onChange={e => setEditCustomer(c => c ? { ...c, phone: e.target.value } : c)}
                className="bg-gray-100 border-gray-200 text-gray-900"
              />
              <Input
                placeholder="Email Address"
                type="email"
                value={editCustomer.email || ''}
                onChange={e => setEditCustomer(c => c ? { ...c, email: e.target.value } : c)}
                className="bg-gray-100 border-gray-200 text-gray-900"
              />
              <Select
                value={editCustomer.pricing_tier}
                onValueChange={v => setEditCustomer(c => c ? { ...c, pricing_tier: v } : c)}
              >
                <SelectTrigger className="bg-gray-100 border-gray-200 text-gray-900">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white border-gray-200">
                  <SelectItem value="retail">Retail</SelectItem>
                  <SelectItem value="wholesale">Wholesale</SelectItem>
                  <SelectItem value="vip">VIP</SelectItem>
                </SelectContent>
              </Select>
              {formError && <p className="text-red-500 text-sm">{formError}</p>}
              <div className="flex gap-2">
                <Button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white" onClick={handleUpdateCustomer} disabled={saving}>
                  {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  Save Changes
                </Button>
                <Button variant="outline" onClick={() => { setEditCustomer(null); setFormError(''); }}>Cancel</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
