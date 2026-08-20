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
export declare class S7Client {
    private conn;
    private options;
    private connected;
    private variables;
    constructor(options: S7ClientOptions);
    connect(): Promise<void>;
    disconnect(): Promise<void>;
    readAll(): Promise<Record<string, any>>;
    writeItem(name: string, value: any): Promise<void>;
    getState(): Promise<S7State>;
    isConnected(): boolean;
}
//# sourceMappingURL=s7-client.d.ts.map