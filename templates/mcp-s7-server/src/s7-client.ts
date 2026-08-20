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


export interface S7State {
  temperature: number;
  pressure: number;
  motorSpeed: number;
  production: number;
  alarms: AlarmState;
  status: "stopped" | "running" | "fault";
  setpoints: {
    temperature: number;
    pressure: number;
    speed: number;
  };
  outputs: {
    green: boolean;
    yellow: boolean;
    red: boolean;
  };
}

export interface AlarmState {
  temperatureHigh: boolean;
  pressureLow: boolean;
  motorFault: boolean;
  active: string[];
  count: number;
}

export interface S7ClientOptions {
  host: string;
  port: number;
  rack: number;
  slot: number;
  debug?: boolean;
}

export class S7Client {
  private conn: any;
  private options: S7ClientOptions;
  private connected = false;

  // Tag → S7 address mapping
  private variables: Record<string, string> = {
    temperature:    "DB1,REAL0",
    pressure:       "DB1,REAL4",
    motorSpeed:     "DB1,INT8",
    production:     "DB1,INT10",
    alarmFlags:     "DB1,WORD12",
    status:         "DB1,WORD14",
    setpointTemp:   "DB10,REAL0",
    setpointPress:  "DB10,REAL4",
    setpointSpeed:  "DB10,INT8",
    outputGreen:    "DB20,X0.0",
    outputYellow:   "DB20,X0.1",
    outputRed:      "DB20,X0.2",
  };

  constructor(options: S7ClientOptions) {
    this.options = options;
    this.conn = new nodes7();
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.conn.initiateConnection(
        {
          port: this.options.port,
          host: this.options.host,
          rack: this.options.rack,
          slot: this.options.slot,
          debug: this.options.debug || false,
        },
        (err: any) => {
          if (err) {
            reject(new Error(`S7 connection failed: ${err}`));
          } else {
            this.connected = true;
            this.conn.setTranslationCB((tag: string) => this.variables[tag]);
            this.conn.addItems(Object.keys(this.variables));
            resolve();
          }
        }
      );
    });
  }

  async disconnect(): Promise<void> {
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

  async readAll(): Promise<Record<string, any>> {
    if (!this.connected) {
      throw new Error("Not connected to S7 PLC");
    }

    return new Promise((resolve, reject) => {
      this.conn.readAllItems((anythingBad: boolean, values: Record<string, any>) => {
        if (anythingBad) {
          reject(new Error("S7 read error — check connection and PLC settings"));
        } else {
          resolve(values);
        }
      });
    });
  }

  async writeItem(name: string, value: any): Promise<void> {
    if (!this.connected) {
      throw new Error("Not connected to S7 PLC");
    }

    return new Promise((resolve, reject) => {
      this.conn.writeItems(name, value, (anythingBad: boolean) => {
        if (anythingBad) {
          reject(new Error(`S7 write error for ${name}`));
        } else {
          resolve();
        }
      });
    });
  }

  async getState(): Promise<S7State> {
    const v = await this.readAll();

    const alarmFlags = v.alarmFlags || 0;
    const activeAlarms: string[] = [];
    if (alarmFlags & 1) activeAlarms.push("TEMPERATURE_HIGH");
    if (alarmFlags & 2) activeAlarms.push("PRESSURE_LOW");
    if (alarmFlags & 4) activeAlarms.push("MOTOR_FAULT");

    let status: "stopped" | "running" | "fault" = "stopped";
    const statusCode = v.status || 0;
    if (statusCode === 1) status = "running";
    if (statusCode === 2) status = "fault";

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

  isConnected(): boolean {
    return this.connected;
  }
}
