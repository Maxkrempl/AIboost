/**
 * Modbus TCP Client — reads/writes PLC registers via Modbus.
 * 
 * Register map (matching PLC simulator):
 *   0: Temperature x10 (e.g. 256 = 25.6°C)
 *   1: Pressure x10 (e.g. 85 = 8.5 bar)
 *   2: Motor speed (RPM)
 *   3: Production counter
 *   4: Alarm flags (bitmask)
 *   5: System status (0=stopped, 1=running, 2=fault)
 *   6: Temperature setpoint x10
 *   7: Pressure setpoint x10
 *   8: Speed setpoint
 *   9: Green light
 *  10: Yellow light
 *  11: Red light
 */

import net from "net";

export interface PLCState {
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

export class ModbusClient {
  private host: string;
  private port: number;
  private socket: net.Socket | null = null;
  private transactionId = 0;
  private connected = false;

  constructor(host: string = "127.0.0.1", port: number = 502) {
    this.host = host;
    this.port = port;
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.socket = new net.Socket();
      this.socket.connect(this.port, this.host, () => {
        this.connected = true;
        resolve();
      });
      this.socket.on("error", (err) => {
        this.connected = false;
        reject(err);
      });
      this.socket.on("close", () => {
        this.connected = false;
      });
    });
  }

  async disconnect(): Promise<void> {
    return new Promise((resolve) => {
      if (this.socket) {
        this.socket.end(() => resolve());
      } else {
        resolve();
      }
    });
  }

  private buildReadRequest(address: number, count: number): Buffer {
    this.transactionId++;
    const buffer = Buffer.alloc(12);
    // Transaction ID
    buffer.writeUInt16BE(this.transactionId, 0);
    // Protocol ID (0 = Modbus)
    buffer.writeUInt16BE(0, 2);
    // Length
    buffer.writeUInt16BE(6, 4);
    // Unit ID
    buffer.writeUInt8(1, 6);
    // Function code (0x03 = read holding registers)
    buffer.writeUInt8(0x03, 7);
    // Start address
    buffer.writeUInt16BE(address, 8);
    // Quantity
    buffer.writeUInt16BE(count, 10);
    return buffer;
  }

  private buildWriteRequest(address: number, value: number): Buffer {
    this.transactionId++;
    const buffer = Buffer.alloc(11);
    buffer.writeUInt16BE(this.transactionId, 0);
    buffer.writeUInt16BE(0, 2);
    buffer.writeUInt16BE(7, 4);
    buffer.writeUInt8(1, 6);
    // Function code (0x06 = write single register)
    buffer.writeUInt8(0x06, 7);
    buffer.writeUInt16BE(address, 8);
    buffer.writeUInt16BE(value, 9);
    return buffer;
  }

  async readRegisters(address: number, count: number): Promise<number[]> {
    if (!this.socket || !this.connected) {
      throw new Error("Not connected to PLC");
    }

    return new Promise((resolve, reject) => {
      const request = this.buildReadRequest(address, count);
      
      const timeout = setTimeout(() => {
        reject(new Error("Modbus read timeout"));
      }, 3000);

      const onData = (data: Buffer) => {
        clearTimeout(timeout);
        this.socket?.off("data", onData);
        
        // Parse response
        const functionCode = data[7];
        if (functionCode === 0x83) {
          reject(new Error("Modbus error: " + data[8]));
          return;
        }
        
        const byteCount = data[8];
        const registers: number[] = [];
        for (let i = 0; i < count; i++) {
          registers.push(data.readUInt16BE(9 + i * 2));
        }
        resolve(registers);
      };

      this.socket!.on("data", onData);
      this.socket!.write(request);
    });
  }

  async writeRegister(address: number, value: number): Promise<boolean> {
    if (!this.socket || !this.connected) {
      throw new Error("Not connected to PLC");
    }

    return new Promise((resolve, reject) => {
      const request = this.buildWriteRequest(address, value);
      
      const timeout = setTimeout(() => {
        reject(new Error("Modbus write timeout"));
      }, 3000);

      const onData = (data: Buffer) => {
        clearTimeout(timeout);
        this.socket?.off("data", onData);
        
        const functionCode = data[7];
        if (functionCode === 0x86) {
          reject(new Error("Modbus write error: " + data[8]));
          return;
        }
        
        resolve(true);
      };

      this.socket!.on("data", onData);
      this.socket!.write(request);
    });
  }

  async getPLCState(): Promise<PLCState> {
    const regs = await this.readRegisters(0, 12);
    
    const alarmFlags = regs[4];
    const activeAlarms: string[] = [];
    if (alarmFlags & 1) activeAlarms.push("TEMPERATURE_HIGH");
    if (alarmFlags & 2) activeAlarms.push("PRESSURE_LOW");
    if (alarmFlags & 4) activeAlarms.push("MOTOR_FAULT");

    let status: "stopped" | "running" | "fault" = "stopped";
    if (regs[5] === 1) status = "running";
    if (regs[5] === 2) status = "fault";

    return {
      temperature: regs[0] / 10,
      pressure: regs[1] / 10,
      motorSpeed: regs[2],
      production: regs[3],
      alarms: {
        temperatureHigh: !!(alarmFlags & 1),
        pressureLow: !!(alarmFlags & 2),
        motorFault: !!(alarmFlags & 4),
        active: activeAlarms,
        count: activeAlarms.length,
      },
      status,
      setpoints: {
        temperature: regs[6] / 10,
        pressure: regs[7] / 10,
        speed: regs[8],
      },
      outputs: {
        green: regs[9] === 1,
        yellow: regs[10] === 1,
        red: regs[11] === 1,
      },
    };
  }
}
