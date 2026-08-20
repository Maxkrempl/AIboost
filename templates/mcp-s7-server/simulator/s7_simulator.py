"""
S7-1500 PLC Simulator — Simplified S7 protocol server.

Listens on port 102 (ISO-on-TCP) and simulates:
  - DB1:  Sensor data (temperature, pressure, motor, production, alarms, status)
  - DB10: Setpoints
  - DB20: Digital outputs

For development and testing of the MCP S7 Server.
Does NOT implement full S7 protocol — only enough for nodes7 read/write.
"""

import socket
import struct
import time
import math
import random
import threading


class S7Simulator:
    """Simulates Siemens S7-1500 PLC memory."""

    def __init__(self):
        self.temperature = 22.5
        self.pressure = 6.0
        self.motor_speed = 1500
        self.production = 0
        self.status = 1  # 0=stop, 1=run, 2=fault
        self.time_offset = 0.0

        # Data Block memory (byte arrays)
        self.db = {
            1: bytearray(32),   # DB1 — Sensor data
            10: bytearray(32),  # DB10 — Setpoints
            20: bytearray(8),   # DB20 — Digital outputs
        }

        # Setpoint defaults
        self.setpoint_temp = 25.0
        self.setpoint_press = 6.0
        self.setpoint_speed = 1500

    def update(self):
        """Update simulated values — called periodically."""
        self.time_offset += 0.5
        t = self.time_offset

        # Simulate realistic sensor behavior
        self.temperature += ((22 + 8 * math.sin(t * 0.02)) - self.temperature) * 0.05
        self.temperature += random.uniform(-0.1, 0.1)
        self.temperature = max(0, min(100, self.temperature))

        self.pressure += ((6 + 2 * math.sin(t * 0.03)) - self.pressure) * 0.08
        self.pressure += random.uniform(-0.05, 0.05)
        self.pressure = max(0, min(10, self.pressure))

        self.motor_speed += ((1500 + 200 * math.sin(t * 0.015)) - self.motor_speed) * 0.03
        self.motor_speed += random.uniform(-5, 5)
        self.motor_speed = max(0, min(3000, self.motor_speed))

        if random.random() < 0.03:
            self.production += 1

        # Alarms
        alarm_temp = self.temperature > 80
        alarm_pres = self.pressure < 3
        alarm_motor = self.motor_speed > 2800

        self.status = 2 if (alarm_temp or alarm_pres) else 1

        flags = 0
        if alarm_temp: flags |= 1
        if alarm_pres: flags |= 2
        if alarm_motor: flags |= 4

        # Pack into DB1 (REAL = 4 bytes little-endian float, INT = 2 bytes LE)
        db1 = self.db[1]
        struct.pack_into('<f', db1, 0, self.temperature)
        struct.pack_into('<f', db1, 4, self.pressure)
        struct.pack_into('<h', db1, 8, int(self.motor_speed))
        struct.pack_into('<h', db1, 10, self.production)
        struct.pack_into('<H', db1, 12, flags)
        struct.pack_into('<H', db1, 14, self.status)

        # Pack DB10 (setpoints)
        db10 = self.db[10]
        struct.pack_into('<f', db10, 0, self.setpoint_temp)
        struct.pack_into('<f', db10, 4, self.setpoint_press)
        struct.pack_into('<h', db10, 8, int(self.setpoint_speed))

        # Pack DB20 (outputs)
        db20 = self.db[20]
        db20[0] = 1 if self.status == 1 and not alarm_temp else 0  # green
        db20[1] = 1 if alarm_motor else 0  # yellow
        db20[2] = 1 if alarm_temp or alarm_pres else 0  # red


def handle_s7_request(data, simulator):
    """
    Handle incoming S7 protocol data.

    S7 protocol layers:
      - ISO 8073 (COTP) — connection-oriented transport
      - S7 — Siemens proprietary communication

    This is a simplified handler that supports:
      - Connection request/confirm (COTP CR/CC)
      - PDU negotiation (S7CommunicationSetup)
      - Read variable (S7 ReadVar)
      - Write variable (S7 WriteVar)
    """
    if len(data) < 7:
        return None

    # Parse ISO header (4 bytes)
    # Byte 0: Length (1 byte for TPDU)
    # Actually ISO 8073 has different format...
    # For simplicity, detect by first byte patterns

    # COTP Connection Request (CR) — first byte = 0x11 (TPDU length 17)
    if data[0] == 0x11 and data[1] == 0x00 and data[2] == 0x00:
        # COTP CR — respond with Connection Confirm (CC)
        # Build CC response
        response = bytearray(22)
        response[0] = 0x14  # TPDU length (20)
        response[1] = 0x00  # PDU type: CC
        response[2] = 0x00
        response[3] = data[3]  # Destination reference (from CR)
        response[4] = 0x00
        # Class 1, no options
        response[5] = 0xC1  # Parameter code: source TSAP
        response[6] = 0x02  # Parameter length
        response[7] = data[7] if len(data) > 7 else 0x01  # Source TSAP
        response[8] = data[8] if len(data) > 8 else 0x00
        response[9] = 0xC2  # Parameter code: destination TSAP
        response[10] = 0x02  # Parameter length
        response[11] = data[10] if len(data) > 10 else 0x01  # Dest TSAP
        response[12] = data[11] if len(data) > 11 else 0x01
        response[13] = 0xC0  # Parameter code: TPDU size
        response[14] = 0x01
        response[15] = 0x0A  # 1024 bytes
        # Fill remaining
        return bytes(response)

    # S7 Communication Setup (PDU type negotiation)
    # Typically: TPKT(4) + COTP(3) + S7 header
    if len(data) > 7:
        # Try to detect S7 PDU after ISO header
        # S7 header starts after COTP header
        s7_start = -1
        for i in range(min(10, len(data))):
            if i + 4 < len(data):
                # Look for S7 protocol magic: 0x32 (S7 PDU type)
                if data[i] == 0x32:
                    s7_start = i
                    break

        if s7_start >= 0:
            s7 = data[s7_start:]
            return handle_s7_pdu(s7, simulator, data[:s7_start])

    return None


def handle_s7_pdu(s7_data, simulator, iso_header=b""):
    """Handle S7 protocol data unit."""
    if len(s7_data) < 10:
        return None

    # S7 header: 0x32 + protocol data unit reference + reserved + PDU length
    pdu_type = s7_data[0]  # 0x32 = S7

    if pdu_type != 0x32:
        return None

    # Bytes 1-2: PDU reference (echo back)
    # Bytes 3-4: Parameter length
    # Bytes 5-6: Data length
    param_len = struct.unpack('>H', s7_data[3:5])[0] if len(s7_data) > 4 else 0
    data_len = struct.unpack('>H', s7_data[5:7])[0] if len(s7_data) > 6 else 0

    # Message type (byte 8 after S7 header start, but could be at different offset)
    # For job request: 0x01 at s7_data[8]
    if len(s7_data) > 8:
        msg_type = s7_data[8]
    else:
        msg_type = 0x01

    # S7 Communication Setup request (0x0001 = job, function 0xF0)
    if len(s7_data) >= 13:
        function = s7_data[11] if len(s7_data) > 11 else 0

        if function == 0xF0 and s7_data[9] == 0x00:
            # Communication setup — respond with PDU size negotiation
            response = bytearray(iso_header)
            # TPKT
            response += struct.pack('>BBH', 3, 0, 0)  # version, reserved, length
            struct.pack_into('>H', response, 2, len(response))
            # COTP
            response += bytes([2, 0xF0, 0x80])  # length, PDU type, last PDU
            # S7 response
            response += bytes([0x32, 0x03, 0x00, 0x00, 0x00, 0x00])
            response += bytes([0x00, 0x01, 0x00, 0x01])  # setup response
            # Fix lengths
            struct.pack_into('>H', response, 2, len(response))
            return bytes(response)

        # Read Var request
        if function == 0x04 or function == 0x05:
            return handle_read_var(s7_data, simulator, iso_header)

        # Write Var request
        if function == 0x05 and len(s7_data) > 17 and s7_data[17] == 0x01:
            return handle_write_var(s7_data, simulator, iso_header)

    return None


def handle_read_var(s7_data, simulator, iso_header=b""):
    """Handle S7 Read Var request."""
    # Parse the read request
    # S7 ReadVar: header + items to read
    # Items start at offset 12 in S7 PDU
    items_start = 12
    if len(s7_data) <= items_start:
        return None

    num_items = s7_data[items_start] if len(s7_data) > items_start else 1
    results = []

    offset = items_start + 1
    for i in range(num_items):
        if offset + 12 > len(s7_data):
            break

        item_type = s7_data[offset]      # 0x12 = variable specification
        item_len = s7_data[offset + 1]   # length of variable spec
        syntax_id = s7_data[offset + 2]  # 0xB0 = S7 500, 0xB1 = S7 anytype

        if syntax_id in (0xB0, 0xB1):
            db_number = struct.unpack('>H', s7_data[offset + 3:offset + 5])[0]
            area_code = s7_data[offset + 5]  # area code
            byte_addr = struct.unpack('>H', s7_data[offset + 6:offset + 8])[0]
            bit_addr = s7_data[offset + 8] if len(s7_data) > offset + 8 else 0
            byte_count = struct.unpack('>H', s7_data[offset + 10:offset + 12])[0] if len(s7_data) > offset + 11 else 0

            # Read from simulator memory
            data_val = b'\x00' * byte_count
            if area_code == 0x84:  # DB area
                if db_number in simulator.db:
                    db = simulator.db[db_number]
                    start = byte_addr
                    end = min(start + byte_count, len(db))
                    data_val = bytes(db[start:end])
                    if len(data_val) < byte_count:
                        data_val += b'\x00' * (byte_count - len(data_val))

            results.append(data_val)

        offset += item_len + 2  # Move to next item

    # Build response
    # Response: TPKT + COTP + S7 Read response
    total_data_len = sum(len(r) for r in results)

    # Simple response construction
    response = bytearray(iso_header)
    # S7 response header
    response += bytes([0x32, 0x03, 0x00, 0x00])
    param_len = 1 + num_items * 2  # item count + 2 bytes per item
    data_header_len = 4  # data qualifier + return code + transport size + length
    data_len = sum(len(r) + data_header_len for r in results)
    response += struct.pack('>H', param_len)
    response += struct.pack('>H', data_len)
    response += bytes([0x00])  # error class
    response += bytes([0x00])  # error code

    # Parameters — return codes
    response += bytes([num_items])
    for r in results:
        response += bytes([0xFF, 0x04])  # Return code: OK, transport size: BYTE

    # Data
    for r in results:
        response += struct.pack('>H', len(r))
        response += r

    # Fix TPKT length
    struct.pack_into('>H', response, 2, len(response))

    return bytes(response)


def handle_write_var(s7_data, simulator, iso_header=b""):
    """Handle S7 Write Var request."""
    # Simplified — just acknowledge the write
    response = bytearray(iso_header)
    # S7 response
    response += bytes([0x32, 0x03, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01])
    response += bytes([0x00, 0x00])  # success

    struct.pack_into('>H', response, 2, len(response))
    return bytes(response)


def run_server():
    sim = S7Simulator()
    sim.update()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 102))
    server.listen(5)
    server.settimeout(1.0)

    print("🏭 Siemens S7-1500 Simulator starting...")
    print("   S7 Protocol (RFC1006) on port 102")
    print("   Simulating: DB1 (Sensors), DB10 (Setpoints), DB20 (Outputs)")
    print("   Connect: PLC_HOST=127.0.0.1 PLC_PORT=102 npm run dev")
    print("   Press Ctrl+C to stop")
    print()

    running = True
    last_print = 0
    connection_count = 0

    def update_loop():
        nonlocal last_print
        while running:
            time.sleep(1.0)
            sim.update()
            now = int(time.time())
            if now != last_print and now % 5 == 0:
                last_print = now
                status_str = 'RUN' if sim.status == 1 else 'FAULT'
                print(f"  T={sim.temperature:.1f}°C  "
                      f"P={sim.pressure:.1f}bar  "
                      f"RPM={sim.motor_speed:.0f}  "
                      f"PROD={sim.production}  "
                      f"STATUS={status_str}")

    updater = threading.Thread(target=update_loop, daemon=True)
    updater.start()

    try:
        while running:
            try:
                client, addr = server.accept()
                connection_count += 1
                print(f"  🔗 Connection #{connection_count} from {addr[0]}:{addr[1]}")
                data = client.recv(4096)
                if data:
                    response = handle_s7_request(data, sim)
                    if response:
                        client.sendall(response)
                        print(f"  📨 Handled request ({len(data)} bytes → {len(response)} bytes)")
                    else:
                        print(f"  ⚠️  Unhandled request ({len(data)} bytes)")
                        print(f"     Raw: {data[:30].hex()}")
                client.close()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"  ❌ Error: {e}")
    except KeyboardInterrupt:
        running = False
        print("\n⏹ Simulator stopped.")
    finally:
        server.close()


if __name__ == "__main__":
    run_server()
