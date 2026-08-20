#!/usr/bin/env node
/**
 * MCP Server za Siemens S7-1500
 *
 * Poveže AI sisteme (Claude, GPT, OpenClaw) s Siemens S7-1500 PLC
 * preko S7 protokola (RFC1006 / ISO-on-TCP).
 *
 * Tools:
 *   - read_sensor    → bere senzorske podatke iz PLC
 *   - get_alarms     → vrača aktivne alarme
 *   - get_status     → vrača status sistema
 *   - write_setpoint → piše nastavitve v PLC (varno!)
 *   - get_all        → vrača vse podatke naenkrat
 *   - read_db        → bere celotni Data Block
 *   - write_db       → piše v Data Block
 *
 * Resources:
 *   - s7://tags      → seznam vseh razpoložljivih tags
 *   - s7://alarms    → definicije alarmov
 *   - s7://status    → trenutni status
 *   - s7://plc-info  → informacije o PLC-ju
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { S7Client } from "./s7-client.js";
// Config
const PLC_HOST = process.env.PLC_HOST || "127.0.0.1";
const PLC_PORT = parseInt(process.env.PLC_PORT || "102");
const PLC_RACK = parseInt(process.env.PLC_RACK || "0");
const PLC_SLOT = parseInt(process.env.PLC_SLOT || "1");
// Initialize S7 client
const plc = new S7Client({
    host: PLC_HOST,
    port: PLC_PORT,
    rack: PLC_RACK,
    slot: PLC_SLOT,
    debug: process.env.S7_DEBUG === "true",
});
// Create MCP server
const server = new McpServer({
    name: "mcp-s7-server",
    version: "1.0.0",
});
// ============================================================
// TOOLS
// ============================================================
// READ SENSOR — read specific sensor value
server.tool("read_sensor", "Read a sensor value from the Siemens S7-1500 PLC. Returns current value with unit.", {
    sensor: z.enum(["temperature", "pressure", "motor_speed", "production"])
        .describe("Sensor to read"),
}, async ({ sensor }) => {
    try {
        const state = await plc.getState();
        const sensors = {
            temperature: { value: state.temperature, unit: "°C", name: "Temperatura" },
            pressure: { value: state.pressure, unit: "bar", name: "Tlak" },
            motor_speed: { value: state.motorSpeed, unit: "RPM", name: "Hitrost motorja" },
            production: { value: state.production, unit: "enot", name: "Proizvodnja" },
        };
        const s = sensors[sensor];
        return {
            content: [{
                    type: "text",
                    text: JSON.stringify({
                        sensor,
                        name: s.name,
                        value: s.value,
                        unit: s.unit,
                        plc: `${PLC_HOST}:${PLC_PORT}`,
                        timestamp: new Date().toISOString(),
                    }, null, 2),
                }],
        };
    }
    catch (err) {
        return {
            content: [{
                    type: "text",
                    text: `Napaka pri branju senzorja: ${err}`,
                }],
            isError: true,
        };
    }
});
// GET ALARMS — get active alarms
server.tool("get_alarms", "Get all active alarms from the Siemens S7-1500 PLC. Returns list with priority and recommended action.", {}, async () => {
    try {
        const state = await plc.getState();
        const alarmDefs = {
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
                    type: "text",
                    text: JSON.stringify({
                        activeCount: state.alarms.count,
                        alarms: activeAlarms,
                        systemStatus: state.status,
                        plc: `${PLC_HOST}:${PLC_PORT}`,
                        timestamp: new Date().toISOString(),
                    }, null, 2),
                }],
        };
    }
    catch (err) {
        return {
            content: [{
                    type: "text",
                    text: `Napaka pri branju alarmov: ${err}`,
                }],
            isError: true,
        };
    }
});
// GET STATUS — get overall system status
server.tool("get_status", "Get overall Siemens S7-1500 PLC status including all sensors, alarms, setpoints, and outputs.", {}, async () => {
    try {
        const state = await plc.getState();
        const statusText = state.status === "running"
            ? "🟢 Deluje"
            : state.status === "fault"
                ? "🔴 Napaka"
                : "⚫ Ustavljeno";
        return {
            content: [{
                    type: "text",
                    text: JSON.stringify({
                        status: state.status,
                        statusText,
                        plc: {
                            host: PLC_HOST,
                            port: PLC_PORT,
                            rack: PLC_RACK,
                            slot: PLC_SLOT,
                            protocol: "S7 (RFC1006)",
                        },
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
    }
    catch (err) {
        return {
            content: [{
                    type: "text",
                    text: `Napaka pri branju statusa: ${err}`,
                }],
            isError: true,
        };
    }
});
// WRITE SETPOINT — write a setpoint value to PLC
server.tool("write_setpoint", "Write a setpoint value to the Siemens S7-1500 PLC. Use with caution! Values are validated against safety limits.", {
    parameter: z.enum(["temperature", "pressure", "speed"])
        .describe("Parameter to set"),
    value: z.number().describe("New setpoint value"),
}, async ({ parameter, value }) => {
    try {
        // Safety limits — match TIA Portal configuration
        const limits = {
            temperature: { min: 0, max: 50, db: "DB10", tag: "setpointTemp" },
            pressure: { min: 0, max: 10, db: "DB10", tag: "setpointPress" },
            speed: { min: 0, max: 3000, db: "DB10", tag: "setpointSpeed" },
        };
        const limit = limits[parameter];
        if (value < limit.min || value > limit.max) {
            return {
                content: [{
                        type: "text",
                        text: `⚠️ Varnostna omejitev: ${parameter} mora biti med ${limit.min} in ${limit.max}. Vrednost ${value} ni dovoljena.`,
                    }],
                isError: true,
            };
        }
        // Write to PLC
        await plc.writeItem(limit.tag, value);
        return {
            content: [{
                    type: "text",
                    text: JSON.stringify({
                        success: true,
                        parameter,
                        newValue: value,
                        location: `${limit.db}.${limit.tag}`,
                        plc: `${PLC_HOST}:${PLC_PORT}`,
                        timestamp: new Date().toISOString(),
                    }, null, 2),
                }],
        };
    }
    catch (err) {
        return {
            content: [{
                    type: "text",
                    text: `Napaka pri pisanju: ${err}`,
                }],
            isError: true,
        };
    }
});
// GET ALL — get everything at once
server.tool("get_all", "Get all Siemens S7-1500 PLC data at once: sensors, alarms, status, setpoints, outputs.", {}, async () => {
    try {
        const state = await plc.getState();
        return {
            content: [{
                    type: "text",
                    text: JSON.stringify(state, null, 2),
                }],
        };
    }
    catch (err) {
        return {
            content: [{
                    type: "text",
                    text: `Napaka: ${err}`,
                }],
            isError: true,
        };
    }
});
// READ DB — read entire Data Block
server.tool("read_db", "Read a Siemens S7 Data Block. Returns raw register values.", {
    dbNumber: z.number().describe("Data Block number (e.g. 1, 10, 20)"),
    startByte: z.number().default(0).describe("Start byte offset (default: 0)"),
    byteCount: z.number().default(64).describe("Number of bytes to read (default: 64)"),
}, async ({ dbNumber, startByte, byteCount }) => {
    try {
        // Read raw bytes from DB using nodes7 address syntax
        const address = `DB${dbNumber},BYTE${startByte}.${byteCount}`;
        const tag = `_raw_db_${dbNumber}_${startByte}`;
        // Temporarily add item and read
        const conn = plc.conn;
        const vars = plc.variables;
        vars[tag] = address;
        conn.setTranslationCB((t) => vars[t]);
        conn.addItems([tag]);
        const values = await new Promise((resolve, reject) => {
            conn.readAllItems((bad, vals) => {
                if (bad)
                    reject(new Error("S7 read error"));
                else
                    resolve(vals);
            });
        });
        // Cleanup
        conn.removeItems([tag]);
        delete vars[tag];
        return {
            content: [{
                    type: "text",
                    text: JSON.stringify({
                        db: dbNumber,
                        startByte,
                        byteCount,
                        raw: values[tag],
                        timestamp: new Date().toISOString(),
                    }, null, 2),
                }],
        };
    }
    catch (err) {
        return {
            content: [{
                    type: "text",
                    text: `Napaka pri branju DB${dbNumber}: ${err}`,
                }],
            isError: true,
        };
    }
});
// ============================================================
// RESOURCES
// ============================================================
// Tags — list of available PLC tags
server.resource("tags", "s7://tags", async () => ({
    contents: [{
            uri: "s7://tags",
            mimeType: "application/json",
            text: JSON.stringify({
                plc: { host: PLC_HOST, port: PLC_PORT, rack: PLC_RACK, slot: PLC_SLOT },
                dataBlocks: {
                    "DB1 — Senzorji": {
                        REAL0: { name: "temperature", unit: "°C", range: [0, 100] },
                        REAL4: { name: "pressure", unit: "bar", range: [0, 10] },
                        INT8: { name: "motorSpeed", unit: "RPM", range: [0, 3000] },
                        INT10: { name: "production", unit: "enot", range: [0, 99999] },
                        WORD12: { name: "alarmFlags", unit: "bitmask" },
                        WORD14: { name: "status", unit: "enum", values: { 0: "stopped", 1: "running", 2: "fault" } },
                    },
                    "DB10 — Nastavitve": {
                        REAL0: { name: "setpointTemp", unit: "°C", range: [0, 50] },
                        REAL4: { name: "setpointPress", unit: "bar", range: [0, 10] },
                        INT8: { name: "setpointSpeed", unit: "RPM", range: [0, 3000] },
                    },
                    "DB20 — Digitalni izhodi": {
                        "X0.0": { name: "outputGreen", unit: "bool" },
                        "X0.1": { name: "outputYellow", unit: "bool" },
                        "X0.2": { name: "outputRed", unit: "bool" },
                    },
                },
            }, null, 2),
        }],
}));
// Alarms — alarm definitions
server.resource("alarms", "s7://alarms", async () => ({
    contents: [{
            uri: "s7://alarms",
            mimeType: "application/json",
            text: JSON.stringify({
                alarms: [
                    { code: "TEMPERATURE_HIGH", description: "Visoka temperatura", threshold: "> 80°C", priority: "CRITICAL", db: "DB1", address: "WORD12.0" },
                    { code: "PRESSURE_LOW", description: "Nizek tlak", threshold: "< 3 bar", priority: "CRITICAL", db: "DB1", address: "WORD12.1" },
                    { code: "MOTOR_FAULT", description: "Motor previsoka hitrost", threshold: "> 2800 RPM", priority: "WARNING", db: "DB1", address: "WORD12.2" },
                ],
            }, null, 2),
        }],
}));
// PLC Info — Siemens S7-1500 information
server.resource("plc-info", "s7://plc-info", async () => ({
    contents: [{
            uri: "s7://plc-info",
            mimeType: "application/json",
            text: JSON.stringify({
                manufacturer: "Siemens",
                series: "S7-1500",
                protocol: "S7 (RFC1006 / ISO-on-TCP)",
                port: PLC_PORT,
                rack: PLC_RACK,
                slot: PLC_SLOT,
                host: PLC_HOST,
                requirements: [
                    "Enable GET/PUT Access in TIA Portal (Properties > Protection)",
                    "Disable Optimized Block Access for DBs used",
                    "Use Slot 1 for S7-1200/1500",
                ],
                tiaPortalConfig: {
                    path: "Device properties > Protection > Permitted access with PUT/GET",
                    note: "S7-1200/1500 require explicit GET/PUT enable for external access",
                },
            }, null, 2),
        }],
}));
// ============================================================
// MAIN
// ============================================================
async function main() {
    console.error("🔌 MCP S7 Server starting...");
    console.error(`   Siemens S7-1500 @ ${PLC_HOST}:${PLC_PORT}`);
    console.error(`   Rack: ${PLC_RACK}, Slot: ${PLC_SLOT}`);
    // Connect to PLC
    try {
        await plc.connect();
        console.error("✅ Connected to S7-1500 via S7 protocol (RFC1006)");
    }
    catch (err) {
        console.error("⚠️  Could not connect to PLC:", err);
        console.error("   Make sure GET/PUT access is enabled in TIA Portal");
        console.error("   Server will start anyway (will fail on tool calls)");
    }
    // Start MCP server
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("🚀 MCP S7 Server ready");
}
main().catch((err) => {
    console.error("Fatal error:", err);
    process.exit(1);
});
//# sourceMappingURL=index.js.map