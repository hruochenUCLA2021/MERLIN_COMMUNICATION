import struct

# --- CONFIGURATION ---
VENDOR_ID = 0x000004d8      # Microchip
PRODUCT_CODE = 0x00000001
REVISION = 0x00000001
SERIAL = 0x00000001
SM2_SIZE = 300  # Output (RxPDO)
SM3_SIZE = 540  # Input (TxPDO)

def calculate_checksum(eeprom):
    # The checksum is calculated over Words 0 to 6 (Bytes 0-13).
    # The checksum is Byte 14.
    # Algorithm: Sum of all 14 bytes (treated as unsigned 8-bit) must result in 0xFF (modulo 256).
    # i.e. (Sum_0_to_13 + Checksum) & 0xFF == 0xFF
    
    current_sum = 0
    for i in range(14):
        current_sum += eeprom[i]
    
    # Calculate required checksum
    checksum = (0xFF - (current_sum & 0xFF)) & 0xFF
    return checksum

def build_eeprom():
    # 1. INIT BUFFER (256 Bytes)
    eeprom = bytearray(256)
    
    # 2. PDI HEADER (Word 0-7)
    # Word 0: PDI Control. 0x0080 = SPI Interface. 
    # This is standard for LAN9252.
    eeprom[0] = 0x80
    eeprom[1] = 0x00
    
    # 3. CATEGORIES START at Word 8 (Byte 16)
    # We MUST put General (Type 30) FIRST because your tool reads Word 8 as VendorID.
    offset = 16
    
    # --- CATEGORY 1: GENERAL (Type 30) ---
    gen_data = struct.pack('<I I I I', VENDOR_ID, PRODUCT_CODE, REVISION, SERIAL)
    
    # Header: Type 30, Length 8 Words
    eeprom[offset:offset+2] = struct.pack('<H', 30)
    eeprom[offset+2:offset+4] = struct.pack('<H', len(gen_data) // 2)
    offset += 4
    # Data
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
    # SM2 (Outputs) - YOUR SIZES
    sm_data += struct.pack('<H H B B B B', 0x1100, SM2_SIZE, 0x64, 0, 1, 0)
    # SM3 (Inputs) - YOUR SIZES
    sm_data += struct.pack('<H H B B B B', 0x1400, SM3_SIZE, 0x20, 0, 1, 0)

    eeprom[offset:offset+2] = struct.pack('<H', 40)
    eeprom[offset+2:offset+4] = struct.pack('<H', len(sm_data) // 2)
    offset += 4
    eeprom[offset:offset+len(sm_data)] = sm_data
    offset += len(sm_data)

    # --- END (Type 0xFFFF) ---
    eeprom[offset:offset+2] = b'\xFF\xFF'

    # 4. CALCULATE CHECKSUM
    # Now that data is filled, we calculate Byte 14
    chk = calculate_checksum(eeprom)
    eeprom[14] = chk
    
    print(f"EEPROM Generated. Checksum set to: 0x{chk:02X}")
    return eeprom

if __name__ == "__main__":
    bin_data = build_eeprom()
    with open("robot_hand_v6.bin", "wb") as f:
        f.write(bin_data)