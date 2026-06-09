import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Plus, Search, Trash2, UserCheck, Shield, Users, Loader2, RefreshCw } from 'lucide-react';
import type { BackendUser } from '../../services/api';
import { loadUsers, deactivateUser, registerAccount } from '../../services/api';
import { getStatusBadge } from '../utils/helpers';

const roles = ['cashier', 'storekeeper', 'inventory_clerk', 'manager', 'accountant'];

const roleLabel = (role: string) => {
  const labels: Record<string, string> = {
    super_admin: 'Super Admin',
    admin: 'Admin',
    manager: 'Manager',
    accountant: 'Accountant',
    cashier: 'Cashier',
    inventory_clerk: 'Inventory Clerk',
    viewer: 'Viewer'
  };
  return labels[role] || role;
};

const getRoleBadge = (role: string) => {
  const colors: Record<string, string> = {
    admin: 'bg-red-500/20 text-red-600',
    super_admin: 'bg-red-500/20 text-red-600',
    manager: 'bg-blue-500/20 text-blue-600',
    cashier: 'bg-green-500/20 text-green-600',
    storekeeper: 'bg-purple-500/20 text-purple-600'
  };
  return (
    <span className={`px-2 py-1 rounded text-xs ${colors[role] || 'bg-gray-500/20 text-gray-500'}`}>
      {roleLabel(role)}
    </span>
  );
};

export function UsersPage() {
  const [users, setUsers] = useState<BackendUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    role: 'cashier' as 'cashier' | 'inventory_clerk' | 'manager' | 'accountant'
  });

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await loadUsers();
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleAddUser = async () => {
    if (!form.username.trim()) { setFormError('Username is required'); return; }
    if (!form.password.trim() || form.password.length < 6) { setFormError('Password must be at least 6 characters'); return; }
    setFormError('');
    setSaving(true);
    try {
      await registerAccount({
        username: form.username.trim(),
        email: form.email.trim(),
        password: form.password,
        role: form.role
      });
      setForm({ username: '', email: '', password: '', role: 'cashier' });
      setIsAddDialogOpen(false);
      await fetchUsers();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Could not create user');
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (id: number) => {
    if (!confirm('Deactivate this user account?')) return;
    try {
      await deactivateUser(id);
      setUsers(prev => prev.map(u => u.id === id ? { ...u, is_active: false } : u));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Could not deactivate user');
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (user.email || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">User Management</h1>
          <p className="text-gray-500">Manage staff accounts, roles, and permissions</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchUsers} className="border-gray-200">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                <Plus className="w-4 h-4 mr-2" />
                Add User
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-white border-gray-200 max-w-md">
              <DialogHeader>
                <DialogTitle className="text-gray-900">Add New User</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <Input
                  placeholder="Username *"
                  value={form.username}
                  onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                  className="bg-gray-100 border-gray-200 text-gray-900"
                />
                <Input
                  placeholder="Email Address"
                  type="email"
                  value={form.email}
                  onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                  className="bg-gray-100 border-gray-200 text-gray-900"
                />
                <Input
                  placeholder="Password * (min 6 characters)"
                  type="password"
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  className="bg-gray-100 border-gray-200 text-gray-900"
                />
                <Select
                  value={form.role}
                  onValueChange={v => setForm(f => ({ ...f, role: v as typeof form.role }))}
                >
                  <SelectTrigger className="bg-gray-100 border-gray-200 text-gray-900">
                    <SelectValue placeholder="Select Role" />
                  </SelectTrigger>
                  <SelectContent className="bg-white border-gray-200">
                    {roles.map(role => (
                      <SelectItem key={role} value={role}>{roleLabel(role)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {formError && <p className="text-red-500 text-sm">{formError}</p>}
                <div className="flex gap-2">
                  <Button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white" onClick={handleAddUser} disabled={saving}>
                    {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                    Add User
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
                <p className="text-gray-500 text-sm">Total Users</p>
                <p className="text-2xl font-semibold text-gray-900">{users.length}</p>
              </div>
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-gray-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Active Users</p>
                <p className="text-2xl font-semibold text-gray-900">{users.filter(u => u.is_active).length}</p>
              </div>
              <div className="p-2 bg-green-500/20 rounded-lg">
                <UserCheck className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-gray-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Managers</p>
                <p className="text-2xl font-semibold text-gray-900">{users.filter(u => u.role === 'manager').length}</p>
              </div>
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Shield className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white border-gray-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Cashiers</p>
                <p className="text-2xl font-semibold text-gray-900">{users.filter(u => u.role === 'cashier').length}</p>
              </div>
              <div className="p-2 bg-green-500/20 rounded-lg">
                <UserCheck className="w-6 h-6 text-green-600" />
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
                placeholder="Search by username or email..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="pl-10 bg-gray-100 border-gray-200 text-gray-900"
              />
            </div>
            <Select value={roleFilter} onValueChange={setRoleFilter}>
              <SelectTrigger className="w-44 bg-gray-100 border-gray-200 text-gray-900">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-white border-gray-200">
                <SelectItem value="all">All Roles</SelectItem>
                {['cashier', 'inventory_clerk', 'manager', 'accountant', 'admin', 'super_admin', 'viewer'].map(role => (
                  <SelectItem key={role} value={role}>{roleLabel(role)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card className="bg-white border-gray-200">
        <CardHeader>
          <CardTitle className="text-gray-900">Staff Members ({filteredUsers.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center items-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              <span className="ml-2 text-gray-500">Loading users...</span>
            </div>
          ) : error ? (
            <div className="text-red-500 text-center py-8">
              <p>{error}</p>
              <Button variant="outline" onClick={fetchUsers} className="mt-4">Retry</Button>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              {searchTerm || roleFilter !== 'all' ? 'No users match your filters.' : 'No users found.'}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-gray-200">
                  <TableHead className="text-gray-600">Username</TableHead>
                  <TableHead className="text-gray-600">Email</TableHead>
                  <TableHead className="text-gray-600">Role</TableHead>
                  <TableHead className="text-gray-600">Last Login</TableHead>
                  <TableHead className="text-gray-600">Status</TableHead>
                  <TableHead className="text-gray-600">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.map(user => (
                  <TableRow key={user.id} className="border-gray-200">
                    <TableCell className="text-gray-900 font-medium">{user.username}</TableCell>
                    <TableCell className="text-gray-600">{user.email || '—'}</TableCell>
                    <TableCell>{getRoleBadge(user.role)}</TableCell>
                    <TableCell className="text-gray-600">
                      {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}
                    </TableCell>
                    <TableCell>{getStatusBadge(user.is_active ? 'active' : 'inactive')}</TableCell>
                    <TableCell>
                      {user.is_active && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-red-500 hover:text-red-300"
                          onClick={() => handleDeactivate(user.id)}
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
