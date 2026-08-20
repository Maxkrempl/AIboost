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
export {};
//# sourceMappingURL=index.d.ts.map