import struct

# --- CONFIGURATION ---
VENDOR_ID = 0x000004d8      # Microchip
PRODUCT_CODE = 0x00000001
REVISION = 0x00000001
SERIAL = 0x00000001
SM2_SIZE = 300
SM3_SIZE = 540

def calculate_checksum(eeprom):
    # Sum of first 14 bytes + Checksum (Byte 14) = 0xFF (mod 256)
    current_sum = 0
    for i in range(14):
        current_sum += eeprom[i]
    checksum = (0xFF - (current_sum & 0xFF)) & 0xFF
    return checksum

def build_eeprom():
    # 1. INIT BUFFER (256 Bytes)
    eeprom = bytearray(256)
    
    # 2. PDI HEADER (Word 0) - Byte 0-1
    # 0x0080 = SPI Mode.
    eeprom[0] = 0x80
    eeprom[1] = 0x00
    
    # 3. MOVE DATA START TO WORD 64 (Byte 128) 
    # We leave Bytes 16-127 as ZEROS. This is the safe "Reserved" area.
    offset = 128 
    
    # --- CATEGORY 1: GENERAL (Type 30) ---
    gen_data = struct.pack('<I I I I', VENDOR_ID, PRODUCT_CODE, REVISION, SERIAL)
    
    eeprom[offset:offset+2] = struct.pack('<H', 30) # Type
    eeprom[offset+2:offset+4] = struct.pack('<H', len(gen_data) // 2) # Len
    offset += 4
    eeprom[offset:offset+len(gen_data)] = gen_data
    offset += len(gen_data)

    # --- CATEGORY 2: STRINGS (Type 10) ---
    strings = [b"RobotHand", b"Main"]
    str_data = bytearray([len(strings)]) 
    for s in strings:
        str_data += bytearray([len(s)]) + s
    if len(str_data) % 2 != 0: str_data += b'\x00' # Pad
    
    eeprom[offset:offset+2] = struct.pack('<H', 10)
    eeprom[offset+2:offset+4] = struct.pack('<H', len(str_data) // 2)
    offset += 4
    eeprom[offset:offset+len(str_data)] = str_data
    offset += len(str_data)

    # --- CATEGORY 3: SYNC MANAGERS (Type 40) ---
    sm_data = bytearray()
    # SM0 (MbxOut)
    sm_data += struct.pack('<H H B B B B', 0x1000, 128, 0x26, 0, 1, 0)
    # SM1 (MbxIn)
    sm_data += struct.pack('<H H B B B B', 0x1080, 128, 0x22, 0, 1, 0)
    # SM2 (Outputs)
    sm_data += struct.pack('<H H B B B B', 0x1100, SM2_SIZE, 0x64, 0, 1, 0)
    # SM3 (Inputs)
    sm_data += struct.pack('<H H B B B B', 0x1400, SM3_SIZE, 0x20, 0, 1, 0)

    eeprom[offset:offset+2] = struct.pack('<H', 40)
    eeprom[offset+2:offset+4] = struct.pack('<H', len(sm_data) // 2)
    offset += 4
    eeprom[offset:offset+len(sm_data)] = sm_data
    offset += len(sm_data)

    # --- END (Type 0xFFFF) ---
    eeprom[offset:offset+2] = b'\xFF\xFF'

    # 4. CHECKSUM (At Byte 14)
    # This validates the entire layout (even though data is far away)
    eeprom[14] = calculate_checksum(eeprom)
    
    return eeprom

if __name__ == "__main__":
    bin_data = build_eeprom()
    with open("robot_hand_v7.bin", "wb") as f:
        f.write(bin_data)
    print("Generated robot_hand_v7.bin (Offset 128)")