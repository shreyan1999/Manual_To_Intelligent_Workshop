// Plain business logic for ChaiCart. No AI here, so it's easy to unit-test.

export interface Order {
  orderId: string;
  status: "delivered" | "in_transit";
  totalInr: number;
  items: string[];
  daysSinceDelivery?: number;
}

const ORDERS: Record<string, Omit<Order, "orderId">> = {
  A1029: { status: "delivered", totalInr: 640, items: ["Glass teapot"], daysSinceDelivery: 2 },
  A1030: { status: "in_transit", totalInr: 1250, items: ["Assam 500g"] },
  A1031: { status: "delivered", totalInr: 4800, items: ["Tea gift hamper"], daysSinceDelivery: 1 },
};

export interface RefundRequest {
  orderId: string;
  amountInr: number;
  reason: string;
  status: "pending_approval" | "approved" | "rejected";
}

export const refundQueue: RefundRequest[] = [];

export function findOrder(orderId: string): Order | { error: string } {
  const id = orderId.trim().toUpperCase();
  const order = ORDERS[id];
  return order ? { orderId: id, ...order } : { error: `No order found with ID ${orderId}` };
}

export function queueRefund(orderId: string, amountInr: number, reason: string): RefundRequest | { error: string } {
  const order = findOrder(orderId);
  if ("error" in order) return order;
  if (amountInr <= 0 || amountInr > order.totalInr) {
    return { error: `Refund must be between Rs 1 and the order total, Rs ${order.totalInr}.` };
  }
  const request: RefundRequest = { orderId: order.orderId, amountInr, reason, status: "pending_approval" };
  refundQueue.push(request);
  return request;
}

export function pendingRefunds(): RefundRequest[] {
  return refundQueue.filter((r) => r.status === "pending_approval");
}
