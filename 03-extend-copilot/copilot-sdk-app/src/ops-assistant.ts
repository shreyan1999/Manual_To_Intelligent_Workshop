// ChaiCart ops assistant: GitHub Copilot's agent loop inside our own terminal tool.
//
//   npm install
//   npm start                                   # interactive
//   npm start -- "Which refunds are waiting for approval?"
//
// Needs a GitHub account with Copilot (Copilot Student is free for verified students).
import * as readline from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import { approveAll, CopilotClient } from "@github/copilot-sdk";
import { allTools } from "./tools.js";

const INSTRUCTIONS = `You are the ChaiCart operations assistant for the support team.
Use the tools to answer questions about orders and refunds. Never invent order data.
Refunds are only queued for a manager; say so clearly. Keep answers short.`;

async function main(): Promise<void> {
  const client = new CopilotClient();
  await client.start();
  try {
    const session = await client.createSession({
      tools: allTools,
      availableTools: ["custom:*"], // only our ChaiCart tools: no shell, no file edits
      systemMessage: { mode: "append", content: INSTRUCTIONS },
      onPermissionRequest: approveAll, // safe here: the only tools are our own, and refunds just queue
    });

    const oneShot = process.argv.slice(2).join(" ").trim();
    if (oneShot) {
      const reply = await session.sendAndWait({ prompt: oneShot });
      console.log(reply?.data.content ?? "(no reply)");
      return;
    }

    const rl = readline.createInterface({ input, output });
    console.log("ChaiCart ops assistant. Type 'exit' to quit.");
    for (;;) {
      const text = (await rl.question("\nYou: ")).trim();
      if (!text || text.toLowerCase() === "exit") break;
      const reply = await session.sendAndWait({ prompt: text });
      console.log(`Assistant: ${reply?.data.content ?? "(no reply)"}`);
    }
    rl.close();
  } finally {
    await client.stop();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
