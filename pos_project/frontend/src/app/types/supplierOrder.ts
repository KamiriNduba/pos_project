export type SupplierOrderStatus = 'paid' | 'pending' | 'overdue' | 'delivered';

export interface SupplierOrderInvoice {
  id: string;
  supplierId: number;
  supplierName: string;
  contact: string;
  date: string;
  amount: number;
  status: SupplierOrderStatus;
  items: number;
  paymentMethod: string;
  productId?: string;
  productName?: string;
  quantityDelivered?: number;
}

export interface BusinessExpense {
  id: string;
  category: string;
  description: string;
  amount: number;
  date: string;
  paymentMethod: string;
  receipt: boolean;
  sourceInvoiceId?: string;
}

export interface StockMovement {
  id: string;
  item: string;
  type: 'in' | 'out';
  quantity: number;
  date: string;
  reason: string;
  sourceInvoiceId?: string;
}
