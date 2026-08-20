/**
 * MCP PLC Core — VS Code Extension
 *
 * Connects any PLC to VS Code Copilot / Claude via MCP.
 * Runs an MCP server inside VS Code that exposes PLC data as tools.
 */

import * as vscode from "vscode";
import { ModbusTCPAdapter } from "../../mcp-plc-core/src/adapters/modbus";
import type { PLCAdapter, SensorData, AlarmData, StatusData } from "../../mcp-plc-core/src/adapter";

// ─── State ───────────────────────────────────────────────────
let adapter: PLCAdapter | null = null;
let statusBarItem: vscode.StatusBarItem;
let statusTreeProvider: StatusTreeProvider;
let alarmTreeProvider: AlarmTreeProvider;
let pollTimer: NodeJS.Timeout | null = null;
let lastSensors: SensorData = {};
let lastAlarms: AlarmData = { active: [], count: 0 };
let lastStatus: StatusData = { status: "stopped" };

// ─── Activate ────────────────────────────────────────────────
export async function activate(context: vscode.ExtensionContext) {
  console.log("MCP PLC Core activating...");

  // Status bar
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBarItem.command = "mcp-plc.connect";
  updateStatusBar("disconnected");
  context.subscriptions.push(statusBarItem);

  // Tree providers
  statusTreeProvider = new StatusTreeProvider();
  alarmTreeProvider = new AlarmTreeProvider();
  vscode.window.registerTreeDataProvider("mcp-plc.status", statusTreeProvider);
  vscode.window.registerTreeDataProvider("mcp-plc.alarms", alarmTreeProvider);

  // Commands
  context.subscriptions.push(
    vscode.commands.registerCommand("mcp-plc.connect", cmdConnect),
    vscode.commands.registerCommand("mcp-plc.disconnect", cmdDisconnect),
    vscode.commands.registerCommand("mcp-plc.readSensor", cmdReadSensor),
    vscode.commands.registerCommand("mcp-plc.getAlarms", cmdGetAlarms),
    vscode.commands.registerCommand("mcp-plc.getAll", cmdGetAll),
    vscode.commands.registerCommand("mcp-plc.refreshStatus", refreshStatus)
  );

  // Auto-connect if configured
  const config = vscode.workspace.getConfiguration("mcp-plc");
  if (config.get("host") !== "127.0.0.1" || config.get("adapter") !== "modbus") {
    // User has configured something — offer to connect
    const choice = await vscode.window.showInformationMessage(
      "MCP PLC: Connect to " + config.get("adapter") + " PLC at " + config.get("host") + ":" + config.get("port") + "?",
      "Connect", "Later"
    );
    if (choice === "Connect") {
      await cmdConnect();
    }
  }

  console.log("MCP PLC Core activated");
}

export function deactivate() {
  stopPolling();
  adapter?.disconnect();
}

// ─── Commands ────────────────────────────────────────────────
async function cmdConnect() {
  const config = vscode.workspace.getConfiguration("mcp-plc");

  const adapterType = await vscode.window.showQuickPick(["modbus", "s7"], {
    placeHolder: "Select PLC adapter",
  });
  if (!adapterType) return;

  const host = await vscode.window.showInputBox({
    prompt: "PLC IP address",
    value: config.get("host", "127.0.0.1"),
  });
  if (!host) return;

  const defaultPort = adapterType === "s7" ? 102 : 502;
  const portStr = await vscode.window.showInputBox({
    prompt: "PLC port",
    value: String(config.get("port", defaultPort)),
  });
  if (!portStr) return;
  const port = parseInt(portStr);

  // Create adapter
  if (adapterType === "modbus") {
    adapter = new ModbusTCPAdapter({ host, port });
  } else {
    // Dynamic import for S7 adapter (requires nodes7)
    try {
      const s7Mod = await import("../../mcp-plc-core/src/adapters/s7.js");
      const S7Adapter = s7Mod.S7Adapter;
      const rack = config.get("rack", 0);
      const slot = config.get("slot", 1);
      adapter = new S7Adapter({ host, port, rack, slot });
    } catch (err) {
      vscode.window.showErrorMessage("S7 adapter requires 'nodes7': npm install nodes7");
      return;
    }
  }

  // Connect
  vscode.window.showInformationMessage(`Connecting to ${adapterType} PLC at ${host}:${port}...`);
  updateStatusBar("connecting");

  try {
    await adapter.connect();
    updateStatusBar("connected");
    vscode.window.showInformationMessage(`✅ Connected to PLC via ${adapterType}`);
    startPolling();
    refreshStatus();
  } catch (err: any) {
    updateStatusBar("error");
    vscode.window.showErrorMessage(`Connection failed: ${err.message}`);
  }
}

async function cmdDisconnect() {
  stopPolling();
  await adapter?.disconnect();
  adapter = null;
  updateStatusBar("disconnected");
  statusTreeProvider.clear();
  alarmTreeProvider.clear();
  vscode.window.showInformationMessage("Disconnected from PLC");
}

async function cmdReadSensor() {
  if (!adapter?.isConnected()) {
    vscode.window.showWarningMessage("Not connected to PLC. Run: MCP PLC Connect");
    return;
  }

  const sensors = await adapter.readSensors();
  const names = Object.keys(sensors);
  const pick = await vscode.window.showQuickPick(names, {
    placeHolder: "Select sensor to read",
  });
  if (!pick) return;

  const value = sensors[pick];
  vscode.window.showInformationMessage(`${pick}: ${value}`);
}

async function cmdGetAlarms() {
  if (!adapter?.isConnected()) {
    vscode.window.showWarningMessage("Not connected to PLC");
    return;
  }

  const alarms = await adapter.readAlarms();
  if (alarms.count === 0) {
    vscode.window.showInformationMessage("✅ No active alarms");
  } else {
    const list = alarms.active.map(a => `[${a.priority}] ${a.code}: ${a.description}`).join("\n");
    vscode.window.showWarningMessage(`${alarms.count} active alarms:\n${list}`);
  }
}

async function cmdGetAll() {
  if (!adapter?.isConnected()) {
    vscode.window.showWarningMessage("Not connected to PLC");
    return;
  }

  const [sensors, alarms, status, setpoints, outputs] = await Promise.all([
    adapter.readSensors(),
    adapter.readAlarms(),
    adapter.readStatus(),
    adapter.readSetpoints(),
    adapter.readOutputs(),
  ]);

  const output = JSON.stringify({ sensors, alarms, status, setpoints, outputs }, null, 2);
  const doc = await vscode.workspace.openTextDocument({ content: output, language: "json" });
  await vscode.window.showTextDocument(doc);
}

// ─── Polling ─────────────────────────────────────────────────
function startPolling() {
  stopPolling();
  const interval = vscode.workspace.getConfiguration("mcp-plc").get("pollInterval", 2000);
  pollTimer = setInterval(refreshStatus, interval);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function refreshStatus() {
  if (!adapter?.isConnected()) return;

  try {
    [lastSensors, lastAlarms, lastStatus] = await Promise.all([
      adapter.readSensors(),
      adapter.readAlarms(),
      adapter.readStatus(),
    ]);
    statusTreeProvider.update(lastSensors, lastStatus);
    alarmTreeProvider.update(lastAlarms);
  } catch (err) {
    // Silently handle — polling will retry
  }
}

// ─── Status Bar ──────────────────────────────────────────────
function updateStatusBar(state: "connected" | "connecting" | "disconnected" | "error") {
  const config = vscode.workspace.getConfiguration("mcp-plc");
  const adapterType = config.get("adapter", "modbus");
  const host = config.get("host", "127.0.0.1");

  switch (state) {
    case "connected":
      statusBarItem.text = `$(zap) PLC: ${adapterType} @ ${host}`;
      statusBarItem.tooltip = "MCP PLC — Connected";
      statusBarItem.backgroundColor = undefined;
      break;
    case "connecting":
      statusBarItem.text = `$(sync~spin) PLC: Connecting...`;
      statusBarItem.tooltip = "MCP PLC — Connecting";
      statusBarItem.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
      break;
    case "error":
      statusBarItem.text = `$(error) PLC: Error`;
      statusBarItem.tooltip = "MCP PLC — Connection error";
      statusBarItem.backgroundColor = new vscode.ThemeColor("statusBarItem.errorBackground");
      break;
    default:
      statusBarItem.text = `$(circle-slash) PLC: Disconnected`;
      statusBarItem.tooltip = "MCP PLC — Click to connect";
      statusBarItem.backgroundColor = undefined;
  }
  statusBarItem.show();
}

// ─── Tree Providers ──────────────────────────────────────────
class StatusTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<vscode.TreeItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private sensors: SensorData = {};
  private status: StatusData = { status: "stopped" };

  update(sensors: SensorData, status: StatusData) {
    this.sensors = sensors;
    this.status = status;
    this._onDidChangeTreeData.fire(undefined);
  }

  clear() {
    this.sensors = {};
    this.status = { status: "stopped" };
    this._onDidChangeTreeData.fire(undefined);
  }

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(): vscode.TreeItem[] {
    const items: vscode.TreeItem[] = [];

    // Status
    const statusEmoji = { running: "🟢", stopped: "⚫", fault: "🔴", maintenance: "🟡" };
    const statusItem = new vscode.TreeItem(`Status: ${statusEmoji[this.status.status] || "❓"} ${this.status.status}`);
    statusItem.iconPath = new vscode.ThemeIcon(this.status.status === "running" ? "check" : "warning");
    items.push(statusItem);

    // Sensors
    if (Object.keys(this.sensors).length > 0) {
      const sep = new vscode.TreeItem("── Sensors ──");
      sep.iconPath = new vscode.ThemeIcon("divider");
      items.push(sep);

      for (const [name, value] of Object.entries(this.sensors)) {
        if (value === undefined) continue;
        const item = new vscode.TreeItem(`${name}: ${value}`);
        item.iconPath = new vscode.ThemeIcon("graph");
        items.push(item);
      }
    }

    return items;
  }
}

class AlarmTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<vscode.TreeItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private alarms: AlarmData = { active: [], count: 0 };

  update(alarms: AlarmData) {
    this.alarms = alarms;
    this._onDidChangeTreeData.fire(undefined);
  }

  clear() {
    this.alarms = { active: [], count: 0 };
    this._onDidChangeTreeData.fire(undefined);
  }

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(): vscode.TreeItem[] {
    if (this.alarms.count === 0) {
      const ok = new vscode.TreeItem("✅ No active alarms");
      return [ok];
    }

    return this.alarms.active.map(alarm => {
      const icon = alarm.priority === "CRITICAL" ? "error" : "warning";
      const item = new vscode.TreeItem(`[${alarm.priority}] ${alarm.code}`);
      item.description = alarm.description;
      item.iconPath = new vscode.ThemeIcon(icon);
      item.tooltip = alarm.action || alarm.description;
      return item;
    });
  }
}
