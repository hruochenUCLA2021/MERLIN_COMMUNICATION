import struct

# --- CONFIGURATION ---
VENDOR_ID = 0x000004d8      # Microchip
PRODUCT_CODE = 0x00000001
REVISION = 0x00000001
SERIAL = 0x00000001

SM2_SIZE = 300  # RobotHand Output
SM3_SIZE = 540  # RobotHand Input

def build_eeprom():
    # 1. INIT BUFFER (256 Bytes - Standard Size)
    eeprom = bytearray(256)
    
    # 2. PDI CONTROL (Word 0) = 0x0080 (SPI Mode)
    # Word 1-6 = Reserved (0)
    eeprom[0] = 0x80
    eeprom[1] = 0x00
    
    # 3. STRINGS CATEGORY (Type 10)
    # We put strings first (after header) to ensure alignment
    strings = [b"RobotHand", b"Main"]
    str_data = bytearray([len(strings)]) 
    for s in strings:
        str_data += bytearray([len(s)]) + s
    if len(str_data) % 2 != 0: str_data += b'\x00' # Pad
    
    # Write Category Header (Type 10) at Byte 16 (Word 8)
    # Offset 16: Type (10), Offset 18: Length (Words)
    cat_offset = 16
    eeprom[cat_offset:cat_offset+2] = struct.pack('<H', 10)
    eeprom[cat_offset+2:cat_offset+4] = struct.pack('<H', len(str_data) // 2)
    cat_offset += 4
    
    # Write Data
    eeprom[cat_offset:cat_offset+len(str_data)] = str_data
    cat_offset += len(str_data)

    # 4. GENERAL CATEGORY (Type 30) - Vendor ID
    gen_data = struct.pack('<I I I I', VENDOR_ID, PRODUCT_CODE, REVISION, SERIAL)
    
    eeprom[cat_offset:cat_offset+2] = struct.pack('<H', 30)
    eeprom[cat_offset+2:cat_offset+4] = struct.pack('<H', len(gen_data) // 2)
    cat_offset += 4
    eeprom[cat_offset:cat_offset+len(gen_data)] = gen_data
    cat_offset += len(gen_data)

    # 5. SYNC MANAGER CATEGORY (Type 40)
    sm_data = bytearray()
    # SM0 (MbxOut), SM1 (MbxIn)
    sm_data += struct.pack('<H H B B B B', 0x1000, 128, 0x26, 0, 1, 0)
    sm_data += struct.pack('<H H B B B B', 0x1080, 128, 0x22, 0, 1, 0)
    # SM2 (Outputs), SM3 (Inputs) - YOUR SIZES
    sm_data += struct.pack('<H H B B B B', 0x1100, SM2_SIZE, 0x64, 0, 1, 0)
    sm_data += struct.pack('<H H B B B B', 0x1400, SM3_SIZE, 0x20, 0, 1, 0)

    eeprom[cat_offset:cat_offset+2] = struct.pack('<H', 40)
    eeprom[cat_offset+2:cat_offset+4] = struct.pack('<H', len(sm_data) // 2)
    cat_offset += 4
    eeprom[cat_offset:cat_offset+len(sm_data)] = sm_data
    cat_offset += len(sm_data)

    # 6. END CATEGORY (Type 0xFFFF)
    eeprom[cat_offset:cat_offset+2] = b'\xFF\xFF'
    
    # 7. CALCULATE CHECKSUM (Critical Step)
    # The LAN9252 expects the checksum at Byte 14 (Word 7 Low Byte).
    # Algorithm: XOR/Sum of first 14 bytes + Checksum = 0xFF (basically)
    chk = 0
    # Sum bytes 0 to 13
    for i in range(14):
        chk += eeprom[i]
        
    # The checksum is the value that satisfies: (Sum(0..13) + Checksum) & 0xFF == 0xFF
    checksum_byte = (0xFF - (chk & 0xFF)) & 0xFF
    eeprom[14] = checksum_byte
    
    return eeprom

if __name__ == "__main__":
    bin_data = build_eeprom()
    with open("robot_hand_v3.bin", "wb") as f:
        f.write(bin_data)
    print("Generated robot_hand_v3.bin")