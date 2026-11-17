// Tools the Copilot agent can call. Each one wraps a plain function from orders.ts.
import { defineTool } from "@github/copilot-sdk";
import { findOrder, pendingRefunds, queueRefund } from "./orders.js";

export const getOrder = defineTool<{ orderId: string }>("get_order", {
  description: "Look up a ChaiCart order: status, items and total in rupees.",
  parameters: {
    type: "object",
    properties: { orderId: { type: "string", description: "Order ID, for example A1029" } },
    required: ["orderId"],
  },
  handler: async ({ orderId }) => findOrder(orderId),
});

export const queueRefundTool = defineTool<{ orderId: string; amountInr: number; reason: string }>("queue_refund", {
  description: "Queue a refund for a manager to approve. It does NOT pay the customer.",
  parameters: {
    type: "object",
    properties: {
      orderId: { type: "string" },
      amountInr: { type: "number", description: "Amount in rupees" },
      reason: { type: "string" },
    },
    required: ["orderId", "amountInr", "reason"],
  },
  handler: async ({ orderId, amountInr, reason }) => queueRefund(orderId, amountInr, reason),
});

export const listPendingRefunds = defineTool("list_pending_refunds", {
  description: "List refunds waiting for a manager's approval.",
  parameters: { type: "object", properties: {} },
  handler: async () => pendingRefunds(),
});

export const allTools = [getOrder, queueRefundTool, listPendingRefunds];
