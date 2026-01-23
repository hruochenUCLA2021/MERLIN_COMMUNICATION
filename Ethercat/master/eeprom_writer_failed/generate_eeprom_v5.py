import struct

# --- CONFIGURATION ---
VENDOR_ID = 0x000004d8      # Microchip
PRODUCT_CODE = 0x00000001
REVISION = 0x00000001
SERIAL = 0x00000001
SM2_SIZE = 300
SM3_SIZE = 540

def build_eeprom():
    # 1. INIT BUFFER (256 Bytes)
    eeprom = bytearray(256)
    
    # 2. PDI HEADER (Word 0-7) -> ALL ZEROS
    # This ensures no SPI/Strap conflicts.
    # Checksum will be set at the end.
    
    # 3. CATEGORIES START at Word 8 (Byte 16)
    offset = 16
    
    # --- CATEGORY 1: STRINGS (Type 10) ---
    # Standard practice: Put strings first so they are indexed 1, 2, ...
    strings = [b"RobotHand", b"Main"]
    str_data = bytearray([len(strings)]) 
    for s in strings:
        str_data += bytearray([len(s)]) + s
    if len(str_data) % 2 != 0: str_data += b'\x00' # Pad
    
    # Write Header
    eeprom[offset:offset+2] = struct.pack('<H', 10) # Type 10
    eeprom[offset+2:offset+4] = struct.pack('<H', len(str_data) // 2) # Len in Words
    offset += 4
    # Write Data
    eeprom[offset:offset+len(str_data)] = str_data
    offset += len(str_data)

    # --- CATEGORY 2: GENERAL (Type 30) ---
    # Now valid Vendor ID comes after the strings.
    gen_data = struct.pack('<I I I I', VENDOR_ID, PRODUCT_CODE, REVISION, SERIAL)
    
    eeprom[offset:offset+2] = struct.pack('<H', 30) # Type 30
    eeprom[offset+2:offset+4] = struct.pack('<H', len(gen_data) // 2)
    offset += 4
    eeprom[offset:offset+len(gen_data)] = gen_data
    offset += len(gen_data)

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

    # 4. CHECKSUM (Byte 14)
    # Since Bytes 0-13 are all 0x00, Sum=0.
    # Checksum = 0xFF.
    eeprom[14] = 0xFF

    return eeprom

if __name__ == "__main__":
    bin_data = build_eeprom()
    with open("robot_hand_v5.bin", "wb") as f:
        f.write(bin_data)
    print("Generated robot_hand_v5.bin (Standard Order)")