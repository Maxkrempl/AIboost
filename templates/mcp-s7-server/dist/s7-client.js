/**
 * S7 Client — Siemens S7-1500 communication via nodes7.
 *
 * Data Block layout (matching TIA Portal project):
 *
 *   DB1 — Sensor Data:
 *     REAL0   Temperature (°C)
 *     REAL4   Pressure (bar)
 *     INT8    Motor speed (RPM)
 *     INT10   Production counter
 *     WORD12  Alarm flags (bitmask)
 *     WORD14  System status (0=stop, 1=running, 2=fault)
 *
 *   DB10 — Setpoints:
 *     REAL0   Temperature setpoint (°C)
 *     REAL4   Pressure setpoint (bar)
 *     INT8    Speed setpoint (RPM)
 *
 *   DB20 — Digital Outputs:
 *     X0.0    Green light
 *     X0.1    Yellow light
 *     X0.2    Red light
 */
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const nodes7 = require("nodes7");
export class S7Client {
    conn;
    options;
    connected = false;
    // Tag → S7 address mapping
    variables = {
        temperature: "DB1,REAL0",
        pressure: "DB1,REAL4",
        motorSpeed: "DB1,INT8",
        production: "DB1,INT10",
        alarmFlags: "DB1,WORD12",
        status: "DB1,WORD14",
        setpointTemp: "DB10,REAL0",
        setpointPress: "DB10,REAL4",
        setpointSpeed: "DB10,INT8",
        outputGreen: "DB20,X0.0",
        outputYellow: "DB20,X0.1",
        outputRed: "DB20,X0.2",
    };
    constructor(options) {
        this.options = options;
        this.conn = new nodes7();
    }
    async connect() {
        return new Promise((resolve, reject) => {
            this.conn.initiateConnection({
                port: this.options.port,
                host: this.options.host,
                rack: this.options.rack,
                slot: this.options.slot,
                debug: this.options.debug || false,
            }, (err) => {
                if (err) {
                    reject(new Error(`S7 connection failed: ${err}`));
                }
                else {
                    this.connected = true;
                    this.conn.setTranslationCB((tag) => this.variables[tag]);
                    this.conn.addItems(Object.keys(this.variables));
                    resolve();
                }
            });
        });
    }
    async disconnect() {
        return new Promise((resolve) => {
            if (!this.connected) {
                resolve();
                return;
            }
            this.conn.dropConnection(() => {
                this.connected = false;
                resolve();
            });
        });
    }
    async readAll() {
        if (!this.connected) {
            throw new Error("Not connected to S7 PLC");
        }
        return new Promise((resolve, reject) => {
            this.conn.readAllItems((anythingBad, values) => {
                if (anythingBad) {
                    reject(new Error("S7 read error — check connection and PLC settings"));
                }
                else {
                    resolve(values);
                }
            });
        });
    }
    async writeItem(name, value) {
        if (!this.connected) {
            throw new Error("Not connected to S7 PLC");
        }
        return new Promise((resolve, reject) => {
            this.conn.writeItems(name, value, (anythingBad) => {
                if (anythingBad) {
                    reject(new Error(`S7 write error for ${name}`));
                }
                else {
                    resolve();
                }
            });
        });
    }
    async getState() {
        const v = await this.readAll();
        const alarmFlags = v.alarmFlags || 0;
        const activeAlarms = [];
        if (alarmFlags & 1)
            activeAlarms.push("TEMPERATURE_HIGH");
        if (alarmFlags & 2)
            activeAlarms.push("PRESSURE_LOW");
        if (alarmFlags & 4)
            activeAlarms.push("MOTOR_FAULT");
        let status = "stopped";
        const statusCode = v.status || 0;
        if (statusCode === 1)
            status = "running";
        if (statusCode === 2)
            status = "fault";
        return {
            temperature: v.temperature || 0,
            pressure: v.pressure || 0,
            motorSpeed: v.motorSpeed || 0,
            production: v.production || 0,
            alarms: {
                temperatureHigh: !!(alarmFlags & 1),
                pressureLow: !!(alarmFlags & 2),
                motorFault: !!(alarmFlags & 4),
                active: activeAlarms,
                count: activeAlarms.length,
            },
            status,
            setpoints: {
                temperature: v.setpointTemp || 0,
                pressure: v.setpointPress || 0,
                speed: v.setpointSpeed || 0,
            },
            outputs: {
                green: !!v.outputGreen,
                yellow: !!v.outputYellow,
                red: !!v.outputRed,
            },
        };
    }
    isConnected() {
        return this.connected;
    }
}
//# sourceMappingURL=s7-client.js.map