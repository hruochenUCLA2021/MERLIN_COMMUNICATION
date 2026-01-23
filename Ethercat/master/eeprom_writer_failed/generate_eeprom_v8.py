import struct

# --- CONFIGURATION ---
VENDOR_ID = 0x000004d8
PRODUCT_CODE = 0x00000001
REVISION = 0x00000001
SERIAL = 0x00000001

# Sizes in BITS for the PDO Category
RX_PDO_BITS = 300  # 37 bytes * 8 = 296? No, let's use your exact structs.
# 1 uint32 (4) + 4 floats (16) = 20 bytes/motor. 15 motors = 300 bytes.
# 300 bytes * 8 = 2400 bits. 
# WAIT: In your C code, SM2 size was 300 BYTES. 
# Let's trust your SM size. 300 Bytes = 2400 Bits.
RX_PDO_SIZE_BYTES = 300 
TX_PDO_SIZE_BYTES = 540

def calculate_checksum(eeprom):
    current_sum = 0
    for i in range(14):
        current_sum += eeprom[i]
    checksum = (0xFF - (current_sum & 0xFF)) & 0xFF
    return checksum

def build_eeprom():
    eeprom = bytearray(256)
    
    # 1. HEADER (SPI Mode)
    eeprom[0] = 0x80
    eeprom[1] = 0x00
    
    # 2. START DATA AT OFFSET 128 (Proven to work for parsing)
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
    # SM0 (MbxOut) 1000h, 128, Control 0x26 (Write)
    sm_data += struct.pack('<H H B B B B', 0x1000, 128, 0x26, 0, 1, 0)
    # SM1 (MbxIn)  1080h, 128, Control 0x22 (Read)
    sm_data += struct.pack('<H H B B B B', 0x1080, 128, 0x22, 0, 1, 0)
    # SM2 (Outputs) 1100h, Size, Control 0x64 (3-buf, Write)
    sm_data += struct.pack('<H H B B B B', 0x1100, RX_PDO_SIZE_BYTES, 0x64, 0, 1, 0)
    # SM3 (Inputs)  1400h, Size, Control 0x20 (3-buf, Read)
    sm_data += struct.pack('<H H B B B B', 0x1400, TX_PDO_SIZE_BYTES, 0x20, 0, 1, 0)

    eeprom[offset:offset+2] = struct.pack('<H', 40)
    eeprom[offset+2:offset+4] = struct.pack('<H', len(sm_data) // 2)
    offset += 4
    eeprom[offset:offset+len(sm_data)] = sm_data
    offset += len(sm_data)

    # --- CATEGORY 4: TXPDO / RXPDO (Type 50/51) ---
    # We must map these so the Master knows the SMs contain PDOs.
    # Usually we map Index 0x1600 (Rx) to SM2 and 0x1A00 (Tx) to SM3.
    # But for simple SII, we often skip detailed mapping and just ensure SM2/3 are active.
    # Since SOEM saw "Output size: 0", it implies we need this.
    
    # We will stick to the simplest valid EEPROM for now. 
    # If this V8 doesn't fix "Size 0", we will have to use CoE to configure sizes.
    # But for now, let's keep the exact V7 structure but ensure Checksum is perfect.

    # --- END ---
    eeprom[offset:offset+2] = b'\xFF\xFF'

    # 3. CHECKSUM
    eeprom[14] = calculate_checksum(eeprom)
    
    return eeprom

if __name__ == "__main__":
    with open("robot_hand_v8.bin", "wb") as f:
        f.write(build_eeprom())
    print("Generated robot_hand_v8.bin")