// Unit tests for the tools. They call the handlers directly, so no Copilot sign-in is needed.
import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { refundQueue } from "../src/orders.js";
import { allTools, getOrder, listPendingRefunds, queueRefundTool } from "../src/tools.js";

const invocation = { sessionId: "test", toolCallId: "t1", toolName: "x", arguments: {} };

beforeEach(() => {
  refundQueue.length = 0;
});

test("tools are registered with names and descriptions the model can read", () => {
  assert.deepEqual(allTools.map((t) => t.name), ["get_order", "queue_refund", "list_pending_refunds"]);
  for (const t of allTools) assert.ok(t.description && t.description.length > 10);
});

test("get_order finds an order case-insensitively", async () => {
  const result = (await getOrder.handler!({ orderId: "a1029" }, invocation)) as { totalInr: number };
  assert.equal(result.totalInr, 640);
});

test("get_order explains unknown IDs", async () => {
  const result = (await getOrder.handler!({ orderId: "Z1" }, invocation)) as { error: string };
  assert.match(result.error, /No order found/);
});

test("queue_refund only queues, and rejects amounts above the order total", async () => {
  const ok = (await queueRefundTool.handler!({ orderId: "A1031", amountInr: 4800, reason: "crushed" }, invocation)) as {
    status: string;
  };
  assert.equal(ok.status, "pending_approval");
  const tooMuch = (await queueRefundTool.handler!({ orderId: "A1029", amountInr: 9999, reason: "x" }, invocation)) as {
    error: string;
  };
  assert.match(tooMuch.error, /order total/);
  const pending = (await listPendingRefunds.handler!({}, invocation)) as unknown[];
  assert.equal(pending.length, 1);
});
