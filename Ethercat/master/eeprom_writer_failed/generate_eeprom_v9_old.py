import struct

# --- CONFIGURATION ---
VENDOR_ID = 0x000004d8
PRODUCT_CODE = 0x00000001
REVISION = 0x00000001
SERIAL = 0x00000001

# These sizes are for the EEPROM's "Fixed" records. 
# Your C code (CoE) will override them, but we need defaults.
SM2_SIZE = 300 
SM3_SIZE = 540

def calculate_checksum(eeprom):
    current_sum = 0
    for i in range(14):
        current_sum += eeprom[i]
    checksum = (0xFF - (current_sum & 0xFF)) & 0xFF
    return checksum

def build_eeprom():
    # 1. INIT BUFFER (256 Bytes)
    eeprom = bytearray(256)
    
    # 2. HEADER
    # PDI Control (Byte 0-1): 0x0080 (SPI)
    eeprom[0] = 0x80
    eeprom[1] = 0x00

    # 3. CRITICAL FIX: MAILBOX PROTOCOL (Byte 56 / Word 0x1C)
    # 0x0004 = CoE (CANopen over EtherCAT)
    # If this is 0, Master disables Mailbox and cannot read sizes!
    eeprom[56] = 0x04
    eeprom[57] = 0x00

    # 4. DATA AREA (Offset 128)
    offset = 128
    
    # --- CATEGORY 1: STRINGS (Type 10) ---
    strings = [b"RobotHand", b"Main"]
    str_data = bytearray([len(strings)]) 
    for s in strings:
        str_data += bytearray([len(s)]) + s
    if len(str_data) % 2 != 0: str_data += b'\x00'
    
    eeprom[offset:offset+2] = struct.pack('<H', 10)
    eeprom[offset+2:offset+4] = struct.pack('<H', len(str_data) // 2)
    offset += 4
    eeprom[offset:offset+len(str_data)] = str_data
    offset += len(str_data)

    # --- CATEGORY 2: GENERAL (Type 30) ---
    gen_data = struct.pack('<I I I I', VENDOR_ID, PRODUCT_CODE, REVISION, SERIAL)
    eeprom[offset:offset+2] = struct.pack('<H', 30)
    eeprom[offset+2:offset+4] = struct.pack('<H', len(gen_data) // 2)
    offset += 4
    eeprom[offset:offset+len(gen_data)] = gen_data
    offset += len(gen_data)

    # --- CATEGORY 3: SYNC MANAGERS (Type 40) ---
    sm_data = bytearray()
    # SM0 (MbxOut): 0x1000, Len 128, Control 0x26, Enable 1
    sm_data += struct.pack('<H H B B B B', 0x1000, 128, 0x26, 0, 1, 0)
    # SM1 (MbxIn):  0x1080, Len 128, Control 0x22, Enable 1
    sm_data += struct.pack('<H H B B B B', 0x1080, 128, 0x22, 0, 1, 0)
    # SM2 (Output): 0x1100, Len 300, Control 0x64, Enable 1
    sm_data += struct.pack('<H H B B B B', 0x1100, SM2_SIZE, 0x64, 0, 1, 0)
    # SM3 (Input):  0x1400, Len 540, Control 0x20, Enable 1
    sm_data += struct.pack('<H H B B B B', 0x1400, SM3_SIZE, 0x20, 0, 1, 0)

    eeprom[offset:offset+2] = struct.pack('<H', 40)
    eeprom[offset+2:offset+4] = struct.pack('<H', len(sm_data) // 2)
    offset += 4
    eeprom[offset:offset+len(sm_data)] = sm_data
    offset += len(sm_data)

    # --- END ---
    eeprom[offset:offset+2] = b'\xFF\xFF'

    # 5. CHECKSUM
    eeprom[14] = calculate_checksum(eeprom)
    
    return eeprom

if __name__ == "__main__":
    with open("robot_hand_v9.bin", "wb") as f:
        f.write(build_eeprom())
    print("Generated robot_hand_v9.bin (CoE Enabled)")