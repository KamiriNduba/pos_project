import React, { useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopHeader } from './components/TopHeader';
import { Dashboard } from './components/pages/Dashboard';
import { POSPage, type CompletedSale, type DayBalance, type POSProduct } from './components/pages/POSPageEnhanced';
import { InvoicesPage } from './components/pages/InvoicesPage';
import { CustomersPage } from './components/pages/CustomersPage';
import { ProductsPageEnhanced } from './components/pages/ProductsPageEnhanced';
import { ProcurementPage } from './components/pages/ProcurementPage';
import { InventoryPage } from './components/pages/InventoryPage';
import { ExpensesPage } from './components/pages/ExpensesPage';
import { ReportsPage } from './components/pages/ReportsPage';
import { UsersPage } from './components/pages/UsersPage';
import { SettingsPage } from './components/pages/SettingsPage';
import { LoginPage } from './components/auth/LoginPage';
import { UserRole } from './types/auth';
import type { QuickActionId } from './components/QuickActions';
import type { Product } from './components/pages/ProductsPageEnhanced';
import { BusinessExpense, StockMovement, SupplierOrderInvoice } from './types/supplierOrder';
import { createProduct, downloadProductImportTemplate, hasStoredSession, importProductsFromExcel, loadBackendState, login as apiLogin, logout as apiLogout, saveDayBalance, saveSale, saveSupplierInvoice, updateProductStock, verifyTwoFactor as apiVerifyTwoFactor } from './services/api';
import type { LoginResult } from './services/api';

const getTodayKey = () => new Date().toISOString().slice(0, 10);

const createInitialDayBalance = (): DayBalance => ({
  date: getTodayKey(),
  openingBalance: 0,
  closingBalance: null,
  status: 'closed'
});

export default function App() {
  const [activeItem, setActiveItem] = useState('dashboard');
  const [quickActionSignals, setQuickActionSignals] = useState({
    addProduct: 0,
    addCustomer: 0,
    newInvoice: 0
  });
  const [isAuthenticated, setIsAuthenticated] = useState(false); // Set to false for login screen
  const [userRole, setUserRole] = useState<UserRole | null>(null);
  const [userName, setUserName] = useState('');
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const [products, setProducts] = useState(() => {
    const savedProducts = window.localStorage.getItem('pos-products');
    return savedProducts ? JSON.parse(savedProducts) as POSProduct[] : [];
  });
  const [completedSales, setCompletedSales] = useState<CompletedSale[]>(() => {
    const savedSales = window.localStorage.getItem('pos-sales');
    return savedSales
      ? (JSON.parse(savedSales) as CompletedSale[]).map(sale => ({
          ...sale,
          cashAmount: sale.cashAmount ?? (sale.method.toLowerCase().startsWith('cash') ? sale.amount : 0),
          cashier: sale.cashier ?? 'John Cashier',
          timestamp: new Date(sale.timestamp)
        }))
      : [];
  });
  const [dayBalance, setDayBalance] = useState<DayBalance>(() => {
    const savedBalance = window.localStorage.getItem('pos-day-balance');
    const balance = savedBalance ? JSON.parse(savedBalance) as DayBalance : createInitialDayBalance();
    return balance.date === getTodayKey() ? balance : createInitialDayBalance();
  });
  const [supplierInvoices, setSupplierInvoices] = useState<SupplierOrderInvoice[]>(() => {
    const savedSupplierInvoices = window.localStorage.getItem('pos-supplier-invoices');
    return savedSupplierInvoices ? JSON.parse(savedSupplierInvoices) as SupplierOrderInvoice[] : [];
  });
  const [expenses, setExpenses] = useState<BusinessExpense[]>(() => {
    const savedExpenses = window.localStorage.getItem('pos-expenses');
    return savedExpenses ? JSON.parse(savedExpenses) as BusinessExpense[] : [];
  });
  const [stockMovements, setStockMovements] = useState<StockMovement[]>(() => {
    const savedStockMovements = window.localStorage.getItem('pos-stock-movements');
    return savedStockMovements ? JSON.parse(savedStockMovements) as StockMovement[] : [];
  });
  const cashSalesToday = completedSales
    .filter(sale => sale.timestamp.toISOString().slice(0, 10) === dayBalance.date)
    .reduce((sum, sale) => sum + sale.cashAmount, 0);

  useEffect(() => {
    if (!hasStoredSession()) {
      return;
    }

    let isMounted = true;

    loadBackendState(createInitialDayBalance())
      .then((backendState) => {
        if (!isMounted) return;

        setProducts(backendState.products);
        setCompletedSales(backendState.completedSales);
        setDayBalance(backendState.dayBalance.date === getTodayKey() ? backendState.dayBalance : createInitialDayBalance());
        setSupplierInvoices(backendState.supplierInvoices);
        setIsBackendConnected(true);
      })
      .catch((error) => {
        console.warn('Backend unavailable, using local browser data.', error);
        if (isMounted) {
          setIsBackendConnected(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    window.localStorage.setItem('pos-products', JSON.stringify(products));
  }, [products]);

  useEffect(() => {
    window.localStorage.setItem('pos-sales', JSON.stringify(completedSales));
  }, [completedSales]);

  useEffect(() => {
    window.localStorage.setItem('pos-day-balance', JSON.stringify(dayBalance));
  }, [dayBalance]);

  useEffect(() => {
    window.localStorage.setItem('pos-supplier-invoices', JSON.stringify(supplierInvoices));
  }, [supplierInvoices]);

  useEffect(() => {
    window.localStorage.setItem('pos-expenses', JSON.stringify(expenses));
  }, [expenses]);

  useEffect(() => {
    window.localStorage.setItem('pos-stock-movements', JSON.stringify(stockMovements));
  }, [stockMovements]);

  const handleItemClick = (itemId: string) => {
    setActiveItem(itemId);
  };

  const handleQuickAction = (action: QuickActionId) => {
    switch (action) {
      case 'new-sale':
        setActiveItem('pos');
        break;
      case 'add-product':
        setActiveItem('inventory');
        setQuickActionSignals(previousSignals => ({
          ...previousSignals,
          addProduct: previousSignals.addProduct + 1
        }));
        break;
      case 'add-customer':
        setActiveItem('customers');
        setQuickActionSignals(previousSignals => ({
          ...previousSignals,
          addCustomer: previousSignals.addCustomer + 1
        }));
        break;
      case 'quick-invoice':
        setActiveItem('invoices');
        setQuickActionSignals(previousSignals => ({
          ...previousSignals,
          newInvoice: previousSignals.newInvoice + 1
        }));
        break;
    }
  };

  const finishAuthenticatedSession = async (username: string, role: UserRole) => {
    setIsAuthenticated(true);
    setUserRole(role);
    setUserName(username);

    try {
      const backendState = await loadBackendState(dayBalance);

      setProducts(backendState.products);
      setCompletedSales(backendState.completedSales);
      setSupplierInvoices(backendState.supplierInvoices);
      setIsBackendConnected(true);
    } catch (error) {
      console.warn('Signed in, but backend data could not be loaded. Using local browser data.', error);
      setIsBackendConnected(false);
    }
  };

  const handleLogin = async (username: string, password: string, role: UserRole): Promise<LoginResult> => {
    const result = await apiLogin(username, password);
    if (!result.twoFactorRequired) {
      await finishAuthenticatedSession(username, (result.userRole as UserRole) || role);
    }
    return result;
  };

  const handleVerifyTwoFactor = async (username: string, code: string, role: UserRole): Promise<LoginResult> => {
    const result = await apiVerifyTwoFactor(username, code);
    await finishAuthenticatedSession(username, (result.userRole as UserRole) || role);
    return result;
  };

  const handleLogout = () => {
    apiLogout();
    setIsAuthenticated(false);
    setUserRole(null);
    setUserName('');
    setActiveItem('dashboard');
  };

  const handleTransactionComplete = (sale: CompletedSale) => {
    setCompletedSales(previousSales => [sale, ...previousSales]);
    setProducts(previousProducts => previousProducts.map(product => {
      const soldUnits = sale.items
        .filter(item => item.productId === product.id)
        .reduce((sum, item) => sum + (item.stockUnits * item.quantity), 0);

      if (soldUnits === 0) return product;
      return {
        ...product,
        stock: Math.max(0, product.stock - soldUnits)
      };
    }));
    setStockMovements(previousMovements => [
      ...sale.items.map(item => ({
        id: `MOV-${sale.id}-${item.productId}`,
        item: item.name,
        type: 'out' as const,
        quantity: -(item.stockUnits * item.quantity),
        date: sale.timestamp.toISOString().slice(0, 10),
        reason: `Sale ${sale.id}`
      })),
      ...previousMovements
    ]);

    if (isBackendConnected) {
      saveSale(sale).catch(error => console.warn('Unable to save sale to backend.', error));
    }
  };

  const handleProductCreated = async (product: Product) => {
    if (!isBackendConnected) {
      setProducts(previousProducts => [
        {
          id: Date.now().toString(),
          name: product.name,
          sku: product.sku,
          category: product.category,
          uom: product.uom,
          prices: product.prices,
          stock: product.stock,
          tax: product.tax,
          image: product.image || 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=100&h=100&fit=crop'
        },
        ...previousProducts
      ]);
      return;
    }

    const savedProduct = await createProduct({
      name: product.name,
      sku: product.sku,
      category_name: product.category,
      base_unit_name: product.uom,
      price: product.prices.retail || 0,
      wholesale_price: product.prices.wholesale || product.prices.retail || 0,
      cost_price: product.buyingPrice || 0,
      quantity: product.stock || 0,
      minimum_stock: product.reorderLevel || 0,
      image_data: product.image || ''
    });

    setProducts(previousProducts => [savedProduct, ...previousProducts]);
  };

  const handleSupplierOrderCreated = (invoice: Omit<SupplierOrderInvoice, 'id'>) => {
    const newInvoice: SupplierOrderInvoice = {
      ...invoice,
      id: `SUP-INV-${Date.now()}`
    };

    setSupplierInvoices(previousInvoices => [newInvoice, ...previousInvoices]);

    if (newInvoice.status === 'delivered' || newInvoice.status === 'paid') {
      setExpenses(previousExpenses => [
        {
          id: `EXP-${newInvoice.id}`,
          category: 'Supplies',
          description: `${newInvoice.supplierName} delivery${newInvoice.productName ? ` - ${newInvoice.productName}` : ''}`,
          amount: newInvoice.amount,
          date: newInvoice.date,
          paymentMethod: newInvoice.paymentMethod,
          receipt: true,
          sourceInvoiceId: newInvoice.id
        },
        ...previousExpenses
      ]);
    }

    if (newInvoice.status === 'delivered' && newInvoice.productId && newInvoice.quantityDelivered) {
      const deliveredProduct = products.find(product => product.id === newInvoice.productId);
      const nextStock = (deliveredProduct?.stock || 0) + newInvoice.quantityDelivered;
      setProducts(previousProducts => previousProducts.map(product =>
        product.id === newInvoice.productId
          ? { ...product, stock: product.stock + (newInvoice.quantityDelivered || 0) }
          : product
      ));
      setStockMovements(previousMovements => [
        {
          id: `MOV-${newInvoice.id}`,
          item: newInvoice.productName || 'Supplier delivery',
          type: 'in',
          quantity: newInvoice.quantityDelivered || 0,
          date: newInvoice.date,
          reason: `Supplier delivery ${newInvoice.id}`,
          sourceInvoiceId: newInvoice.id
        },
        ...previousMovements
      ]);

      if (isBackendConnected) {
        updateProductStock(newInvoice.productId, nextStock).catch(error => console.warn('Unable to update delivered stock in backend.', error));
      }
    }

    if (isBackendConnected) {
      saveSupplierInvoice(newInvoice)
        .then(savedInvoice => {
          setSupplierInvoices(previousInvoices => previousInvoices.map(existingInvoice =>
            existingInvoice.id === newInvoice.id
              ? {
                  ...savedInvoice,
                  status: newInvoice.status,
                  productId: newInvoice.productId,
                  productName: newInvoice.productName,
                  quantityDelivered: newInvoice.quantityDelivered
                }
              : existingInvoice
          ));
        })
        .catch(error => console.warn('Unable to save supplier invoice to backend.', error));
    }
  };

  const handleInventoryStockAdjustment = (productId: string, type: 'in' | 'out', quantity: number, reason: string) => {
    const product = products.find(item => item.id === productId);
    if (!product) return;

    if (type === 'out' && quantity > product.stock) {
      alert(`Only ${product.stock} ${product.uom} available for ${product.name}.`);
      return;
    }

    const signedQuantity = type === 'in' ? quantity : -quantity;
    const nextStock = product.stock + signedQuantity;

    setProducts(previousProducts => previousProducts.map(item =>
      item.id === productId
        ? { ...item, stock: Math.max(0, item.stock + signedQuantity) }
        : item
    ));

    setStockMovements(previousMovements => [
      {
        id: `MOV-${Date.now()}`,
        item: product.name,
        type,
        quantity: signedQuantity,
        date: getTodayKey(),
        reason
      },
      ...previousMovements
    ]);

    if (isBackendConnected) {
      updateProductStock(productId, nextStock).catch(error => console.warn('Unable to update adjusted stock in backend.', error));
    }
  };

  const handleInventoryItemCreated = async (product: Product) => {
    await handleProductCreated(product);

    if (product.stock > 0) {
      setStockMovements(previousMovements => [
        {
          id: `MOV-${Date.now()}`,
          item: product.name,
          type: 'in',
          quantity: product.stock,
          date: getTodayKey(),
          reason: 'Opening stock'
        },
        ...previousMovements
      ]);
    }
  };

  const handleDownloadProductImportTemplate = async () => {
    const template = await downloadProductImportTemplate();
    const url = window.URL.createObjectURL(template);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'product_import_template.xlsx';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const handleBulkProductImport = async (file: File) => {
    if (!isBackendConnected) {
      throw new Error('Excel import requires the backend connection.');
    }

    const result = await importProductsFromExcel(file);
    const backendState = await loadBackendState(dayBalance);

    setProducts(backendState.products);
    setCompletedSales(backendState.completedSales);
    setSupplierInvoices(backendState.supplierInvoices);

    return result;
  };

  const handleExpenseCreated = (expense: Omit<BusinessExpense, 'id'>) => {
    setExpenses(previousExpenses => [
      {
        ...expense,
        id: `EXP-${Date.now()}`
      },
      ...previousExpenses
    ]);
  };

  const handleOpenDay = (openingBalance: number) => {
    const nextDayBalance = {
      date: getTodayKey(),
      openingBalance,
      closingBalance: null,
      status: 'open'
    } as DayBalance;

    setDayBalance(nextDayBalance);

    if (isBackendConnected) {
      saveDayBalance(nextDayBalance).catch(error => console.warn('Unable to save day balance to backend.', error));
    }
  };

  const handleCloseDay = (closingBalance: number) => {
    setDayBalance(previousBalance => {
      const nextDayBalance = {
      ...previousBalance,
      closingBalance,
      status: 'closed'
      } as DayBalance;

      if (isBackendConnected) {
        saveDayBalance(nextDayBalance).catch(error => console.warn('Unable to save day balance to backend.', error));
      }

      return nextDayBalance;
    });
  };

  const renderContent = () => {
    switch (activeItem) {
      case 'dashboard':
        return (
          <Dashboard
            products={products}
            completedSales={completedSales}
            dayBalance={dayBalance}
            cashSalesToday={cashSalesToday}
            userRole={userRole!}
            onQuickAction={handleQuickAction}
          />
        );
      case 'pos':
        return (
          <POSPage
            products={products}
            dayBalance={dayBalance}
            cashSalesToday={cashSalesToday}
            onOpenDay={handleOpenDay}
            onCloseDay={handleCloseDay}
            onTransactionComplete={handleTransactionComplete}
          />
        );
      case 'invoices':
        return (
          <InvoicesPage
            supplierInvoices={supplierInvoices}
            completedSales={completedSales}
            openNewInvoiceSignal={quickActionSignals.newInvoice}
            onStartSale={() => setActiveItem('pos')}
            onRecordSupplierOrder={() => setActiveItem('procurement')}
          />
        );
      case 'customers':
        return <CustomersPage openAddCustomerSignal={quickActionSignals.addCustomer} />;
      case 'products':
        return (
          <ProductsPageEnhanced
            products={products}
            readOnly
          />
        );
      case 'purchases':
      case 'suppliers':
      case 'procurement':
        return (
          <ProcurementPage
            products={products}
            supplierInvoices={supplierInvoices}
            onSupplierOrderCreated={handleSupplierOrderCreated}
          />
        );
      case 'inventory':
        return (
          <InventoryPage
            products={products}
            stockMovements={stockMovements}
            openAddItemSignal={quickActionSignals.addProduct}
            onStockAdjustment={handleInventoryStockAdjustment}
            onAddItem={handleInventoryItemCreated}
            onBulkImportItems={handleBulkProductImport}
            onDownloadImportTemplate={handleDownloadProductImportTemplate}
          />
        );
      case 'expenses':
        return <ExpensesPage expenses={expenses} onExpenseCreated={handleExpenseCreated} />;
      case 'reports':
        return (
          <ReportsPage
            products={products}
            completedSales={completedSales}
            expenses={expenses}
            supplierInvoices={supplierInvoices}
            dayBalance={dayBalance}
          />
        );
      case 'users':
        return <UsersPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return (
          <Dashboard
            products={products}
            completedSales={completedSales}
            dayBalance={dayBalance}
            cashSalesToday={cashSalesToday}
            userRole={userRole!}
            onQuickAction={handleQuickAction}
          />
        );
    }
  };

  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} onVerifyTwoFactor={handleVerifyTwoFactor} />;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Top Header with Time and Notifications */}
      <TopHeader />
      
      {/* Main Content with Sidebar */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar 
          activeItem={activeItem} 
          onItemClick={handleItemClick}
          onLogout={handleLogout}
          userRole={userRole!}
          userName={userName}
        />
        
        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto p-8">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
}
