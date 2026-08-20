#!/usr/bin/env node

/**
 * MCP Server za Industrijsko Avtomatizacijo
 * 
 * Poveže AI sisteme (Claude, GPT) s PLC krmilniki preko Modbus TCP.
 * 
 * Tools:
 *   - read_sensor    → bere senzorske podatke iz PLC
 *   - get_alarms     → vrača aktivne alarme
 *   - get_status     → vrača status sistema
 *   - write_setpoint → piše nastavitve v PLC (varno!)
 *   - get_all        → vrača vse podatke naenkrat
 * 
 * Resources:
 *   - plc://tags      → seznam vseh razpoložljivih tags
 *   - plc://alarms    → definicije alarmov
 *   - plc://status    → trenutni status
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { ModbusClient, PLCState } from "./modbus-client.js";

// Config
const PLC_HOST = process.env.PLC_HOST || "127.0.0.1";
const PLC_PORT = parseInt(process.env.PLC_PORT || "502");

// Initialize Modbus client
const plc = new ModbusClient(PLC_HOST, PLC_PORT);

// Create MCP server
const server = new McpServer({
  name: "mcp-plc-server",
  version: "1.0.0",
});

// ============================================================
// TOOLS
// ============================================================

// READ SENSOR — read specific sensor value
server.tool(
  "read_sensor",
  "Read a sensor value from the PLC. Returns current value with unit.",
  {
    sensor: z.enum(["temperature", "pressure", "motor_speed", "production"])
      .describe("Sensor to read"),
  },
  async ({ sensor }) => {
    try {
      const state = await plc.getPLCState();
      
      const sensors: Record<string, { value: number; unit: string; name: string }> = {
        temperature: { value: state.temperature, unit: "°C", name: "Temperatura" },
        pressure: { value: state.pressure, unit: "bar", name: "Tlak" },
        motor_speed: { value: state.motorSpeed, unit: "RPM", name: "Hitrost motorja" },
        production: { value: state.production, unit: "enot", name: "Proizvodnja" },
      };
      
      const s = sensors[sensor];
      return {
        content: [{
          type: "text" as const,
          text: JSON.stringify({
            sensor,
            name: s.name,
            value: s.value,
            unit: s.unit,
            timestamp: new Date().toISOString(),
          }, null, 2),
        }],
      };
    } catch (err) {
      return {
        content: [{
          type: "text" as const,
          text: `Napaka pri branju senzorja: ${err}`,
        }],
        isError: true,
      };
    }
  }
);

// GET ALARMS — get active alarms
server.tool(
  "get_alarms",
  "Get all active alarms from the PLC. Returns list of active alarms with priority.",
  {},
  async () => {
    try {
      const state = await plc.getPLCState();
      
      const alarmDefs: Record<string, { description: string; priority: string; action: string }> = {
        TEMPERATURE_HIGH: {
          description: "Visoka temperatura (> 80°C)",
          priority: "KRITIČNO",
          action: "Takoj znižaj temperaturo ali izklopi ogrevanje",
        },
        PRESSURE_LOW: {
          description: "Nizek tlak (< 3 bar)",
          priority: "KRITIČNO",
          action: "Preveri črpalke in cevi",
        },
        MOTOR_FAULT: {
          description: "Motor previsoka hitrost (> 2800 RPM)",
          priority: "OPOZORILO",
          action: "Preveri obremenitev motorja",
        },
      };
      
      const activeAlarms = state.alarms.active.map(name => ({
        name,
        ...alarmDefs[name],
      }));
      
      return {
        content: [{
          type: "text" as const,
          text: JSON.stringify({
            activeCount: state.alarms.count,
            alarms: activeAlarms,
            systemStatus: state.status,
            timestamp: new Date().toISOString(),
          }, null, 2),
        }],
      };
    } catch (err) {
      return {
        content: [{
          type: "text" as const,
          text: `Napaka pri branju alarmov: ${err}`,
        }],
        isError: true,
      };
    }
  }
);

// GET STATUS — get overall system status
server.tool(
  "get_status",
  "Get overall PLC system status including all sensors, alarms, and outputs.",
  {},
  async () => {
    try {
      const state = await plc.getPLCState();
      
      return {
        content: [{
          type: "text" as const,
          text: JSON.stringify({
            status: state.status,
            statusText: state.status === "running" ? "🟢 Deluje" : state.status === "fault" ? "🔴 Napaka" : "⚫ Ustavljeno",
            sensors: {
              temperature: `${state.temperature}°C`,
              pressure: `${state.pressure} bar`,
              motorSpeed: `${state.motorSpeed} RPM`,
              production: `${state.production} enot`,
            },
            alarms: {
              count: state.alarms.count,
              active: state.alarms.active,
            },
            setpoints: state.setpoints,
            outputs: state.outputs,
            timestamp: new Date().toISOString(),
          }, null, 2),
        }],
      };
    } catch (err) {
      return {
        content: [{
          type: "text" as const,
          text: `Napaka pri branju statusa: ${err}`,
        }],
        isError: true,
      };
    }
  }
);

// WRITE SETPOINT — write a setpoint value to PLC
server.tool(
  "write_setpoint",
  "Write a setpoint value to the PLC. Use with caution!",
  {
    parameter: z.enum(["temperature", "pressure", "speed"])
      .describe("Parameter to set"),
    value: z.number().describe("New setpoint value"),
  },
  async ({ parameter, value }) => {
    try {
      // Safety limits
      const limits: Record<string, { min: number; max: number; address: number; scale: number }> = {
        temperature: { min: 0, max: 50, address: 6, scale: 10 },
        pressure: { min: 0, max: 10, address: 7, scale: 10 },
        speed: { min: 0, max: 3000, address: 8, scale: 1 },
      };
      
      const limit = limits[parameter];
      if (value < limit.min || value > limit.max) {
        return {
          content: [{
            type: "text" as const,
            text: `⚠️ Varnostna omejitev: ${parameter} mora biti med ${limit.min} in ${limit.max}. Vrednost ${value} ni dovoljena.`,
          }],
          isError: true,
        };
      }
      
      // Write to PLC
      const regValue = Math.round(value * limit.scale);
      await plc.writeRegister(limit.address, regValue);
      
      return {
        content: [{
          type: "text" as const,
          text: JSON.stringify({
            success: true,
            parameter,
            newValue: value,
            register: limit.address,
            timestamp: new Date().toISOString(),
          }, null, 2),
        }],
      };
    } catch (err) {
      return {
        content: [{
          type: "text" as const,
          text: `Napaka pri pisanju: ${err}`,
        }],
        isError: true,
      };
    }
  }
);

// GET ALL — get everything at once
server.tool(
  "get_all",
  "Get all PLC data at once: sensors, alarms, status, setpoints.",
  {},
  async () => {
    try {
      const state = await plc.getPLCState();
      
      return {
        content: [{
          type: "text" as const,
          text: JSON.stringify(state, null, 2),
        }],
      };
    } catch (err) {
      return {
        content: [{
          type: "text" as const,
          text: `Napaka: ${err}`,
        }],
        isError: true,
      };
    }
  }
);

// ============================================================
// RESOURCES
// ============================================================

// PLC Tags — list of available tags
server.resource(
  "tags",
  "plc://tags",
  async () => ({
    contents: [{
      uri: "plc://tags",
      mimeType: "application/json",
      text: JSON.stringify({
        tags: [
          { name: "temperature", address: 0, type: "float", unit: "°C", range: [0, 100] },
          { name: "pressure", address: 1, type: "float", unit: "bar", range: [0, 10] },
          { name: "motor_speed", address: 2, type: "int", unit: "RPM", range: [0, 3000] },
          { name: "production", address: 3, type: "int", unit: "enot", range: [0, 99999] },
          { name: "alarm_flags", address: 4, type: "bitmask", unit: "", range: [0, 7] },
          { name: "status", address: 5, type: "enum", unit: "", values: { 0: "stopped", 1: "running", 2: "fault" } },
          { name: "setpoint_temp", address: 6, type: "float", unit: "°C", range: [0, 50] },
          { name: "setpoint_pressure", address: 7, type: "float", unit: "bar", range: [0, 10] },
          { name: "setpoint_speed", address: 8, type: "int", unit: "RPM", range: [0, 3000] },
          { name: "output_green", address: 9, type: "bool", unit: "" },
          { name: "output_yellow", address: 10, type: "bool", unit: "" },
          { name: "output_red", address: 11, type: "bool", unit: "" },
        ],
      }, null, 2),
    }],
  })
);

// Alarms — alarm definitions
server.resource(
  "alarms",
  "plc://alarms",
  async () => ({
    contents: [{
      uri: "plc://alarms",
      mimeType: "application/json",
      text: JSON.stringify({
        alarms: [
          { code: "TEMPERATURE_HIGH", description: "Visoka temperatura", threshold: "> 80°C", priority: "CRITICAL" },
          { code: "PRESSURE_LOW", description: "Nizek tlak", threshold: "< 3 bar", priority: "CRITICAL" },
          { code: "MOTOR_FAULT", description: "Motor previsoka hitrost", threshold: "> 2800 RPM", priority: "WARNING" },
        ],
      }, null, 2),
    }],
  })
);

// ============================================================
// MAIN
// ============================================================

async function main() {
  console.error("🔌 MCP PLC Server starting...");
  console.error(`   PLC: ${PLC_HOST}:${PLC_PORT}`);
  
  // Connect to PLC
  try {
    await plc.connect();
    console.error("✅ Connected to PLC via Modbus TCP");
  } catch (err) {
    console.error("⚠️  Could not connect to PLC:", err);
    console.error("   Server will start anyway (will fail on tool calls)");
  }
  
  // Start MCP server
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("🚀 MCP PLC Server ready");
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
