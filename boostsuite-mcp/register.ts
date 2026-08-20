#!/usr/bin/env node
import { config } from "dotenv";
import { Payments } from "@nevermined-io/payments";

config();

async function main() {
  console.log("🚀 Registering BoostSuite MCP with Nevermined...");

  const payments = Payments.getInstance({
    nvmApiKey: process.env.NVM_API_KEY!,
    environment: (process.env.NVM_ENVIRONMENT as any) || "sandbox",
  });

  // USDC on Base Sepolia (sandbox)
  const USDC_ADDRESS = "0x036CbD53842c5426634e7929541eC2318f3dCF7e";

  // Register agent + payment plan
  // 0.01 USDC per tool call, 1000 credits
  const { agentId, planId } = await payments.agents.registerAgentAndPlan(
    // Service metadata
    {
      name: "BoostSuite MCP — SEO/GEO Tools for AI Agents",
      description:
        "SEO audit, GEO check, schema generation, ad copy, NAP consistency — the first MCP server for AI-visible web presence. Pay per call.",
      tags: ["seo", "geo", "schema", "mcp", "ai-agents", "boostsuite"],
      dateCreated: new Date(),
    },
    // Service endpoint
    {
      endpoints: [
        { POST: "https://hd-webdesign.si/api/mcp/" },
      ],
    },
    // Plan metadata
    {
      name: "Pay-Per-Call",
      description: "0.01 USDC per tool call — SEO, GEO, Schema, Ad Copy, NAP",
      dateCreated: new Date(),
    },
    // Price: 0.01 USDC per call
    payments.plans.getERC20PriceConfig(
      10_000n, // 0.01 USDC (6 decimals)
      USDC_ADDRESS,
      process.env.NVM_WALLET! // Builder wallet
    ),
    // Credits: 1000 calls, 1 credit each
    payments.plans.getFixedCreditsConfig(1000n, 1n)
  );

  console.log("✅ Registered!");
  console.log(`   Agent ID: ${agentId}`);
  console.log(`   Plan ID: ${planId}`);
  console.log(`   Wallet: ${process.env.NVM_WALLET}`);
  console.log("");
  console.log("Next steps:");
  console.log("1. Start the MCP server: npx ts-node server.ts");
  console.log("2. Test with Nevermined sandbox");
  console.log("3. Deploy to hd-webdesign.si/api/mcp/");
}

main().catch(console.error);
