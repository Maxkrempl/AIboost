"""
PLC Simulator — Simple Modbus TCP server.

Runs on localhost:502
"""

import socket
import struct
import time
import math
import random
import threading

class PLCSimulator:
    def __init__(self):
        self.temperature = 22.5
        self.pressure = 6.0
        self.motor_speed = 1500
        self.production = 0
        self.status = 1
        self.time_offset = 0
        self.registers = [0] * 20  # holding registers
        
    def update(self):
        self.time_offset += 0.1
        
        t = self.time_offset
        self.temperature += ((22 + 8 * math.sin(t * 0.02)) - self.temperature) * 0.05
        self.temperature += random.uniform(-0.1, 0.1)
        self.temperature = max(0, min(100, self.temperature))
        
        self.pressure += ((6 + 2 * math.sin(t * 0.03)) - self.pressure) * 0.08
        self.pressure += random.uniform(-0.05, 0.05)
        self.pressure = max(0, min(10, self.pressure))
        
        self.motor_speed += ((1500 + 200 * math.sin(t * 0.015)) - self.motor_speed) * 0.03
        self.motor_speed += random.uniform(-5, 5)
        self.motor_speed = max(0, min(3000, self.motor_speed))
        
        if random.random() < 0.05:
            self.production += 1
        
        alarm_temp = self.temperature > 80
        alarm_pres = self.pressure < 3
        alarm_motor = self.motor_speed > 2800
        
        if alarm_temp or alarm_pres:
            self.status = 2
        else:
            self.status = 1
        
        flags = 0
        if alarm_temp: flags |= 1
        if alarm_pres: flags |= 2
        if alarm_motor: flags |= 4
        
        self.registers[0] = int(self.temperature * 10)
        self.registers[1] = int(self.pressure * 10)
        self.registers[2] = int(self.motor_speed)
        self.registers[3] = self.production
        self.registers[4] = flags
        self.registers[5] = self.status
        self.registers[6] = 250   # setpoint temp
        self.registers[7] = 60    # setpoint pressure
        self.registers[8] = 1500  # setpoint speed
        self.registers[9] = 1 if self.status == 1 and not alarm_temp else 0
        self.registers[10] = 1 if alarm_motor else 0
        self.registers[11] = 1 if alarm_temp or alarm_pres else 0


def handle_modbus(data, sim):
    """Handle Modbus TCP request."""
    if len(data) < 8:
        return None
    
    # Parse MBAP header
    txn_id = struct.unpack('>H', data[0:2])[0]
    proto_id = struct.unpack('>H', data[2:4])[0]
    length = struct.unpack('>H', data[4:6])[0]
    unit_id = data[6]
    func_code = data[7]
    
    # Read Holding Registers (FC 0x03)
    if func_code == 0x03:
        start = struct.unpack('>H', data[8:10])[0]
        count = struct.unpack('>H', data[10:12])[0]
        
        response = struct.pack('>HHHB', txn_id, proto_id, 3 + count * 2, unit_id)
        response += bytes([0x03, count * 2])
        
        for i in range(count):
            idx = (start + i) % len(sim.registers)
            response += struct.pack('>H', sim.registers[idx])
        
        return response
    
    # Write Single Register (FC 0x06)
    elif func_code == 0x06:
        addr = struct.unpack('>H', data[8:10])[0]
        value = struct.unpack('>H', data[10:12])[0]
        
        if 0 <= addr < len(sim.registers):
            sim.registers[addr] = value
        
        return data  # echo back
    
    # Error response
    else:
        return struct.pack('>HHHBB', txn_id, proto_id, 3, unit_id, func_code | 0x80, 0x01)


def run_server():
    sim = PLCSimulator()
    
    # Initial register values
    for i in range(20):
        sim.registers[i] = 0
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 502))
    server.listen(5)
    server.settimeout(1.0)
    
    print("🏭 PLC Simulator starting...")
    print("   Modbus TCP on localhost:502")
    print("   Simulating: Temperature, Pressure, Motor, Production")
    print("   Press Ctrl+C to stop")
    print()
    
    running = True
    last_print = 0
    
    def update_loop():
        nonlocal last_print
        while running:
            time.sleep(0.5)
            sim.update()
            now = int(time.time())
            if now != last_print and now % 5 == 0:
                last_print = now
                print(f"  T={sim.temperature:.1f}°C  "
                      f"P={sim.pressure:.1f}bar  "
                      f"RPM={sim.motor_speed:.0f}  "
                      f"PROD={sim.production}  "
                      f"STATUS={'RUN' if sim.status==1 else 'FAULT'}")
    
    updater = threading.Thread(target=update_loop, daemon=True)
    updater.start()
    
    try:
        while running:
            try:
                client, addr = server.accept()
                data = client.recv(1024)
                if data:
                    response = handle_modbus(data, sim)
                    if response:
                        client.sendall(response)
                client.close()
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        running = False
        print("\n⏹ Simulator stopped.")
    finally:
        server.close()


if __name__ == "__main__":
    run_server()
