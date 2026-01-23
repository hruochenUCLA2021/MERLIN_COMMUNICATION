import struct

# --- CONFIGURATION (MATCHES ESC_SHEET.H) ---
VENDOR_ID = 0x000004d8      # Microchip
PRODUCT_CODE = 0x00000001
REVISION = 0x00000001
SERIAL = 0x00000001

# Sync Manager Sizes (Your Robot Requirements)
# SM2 (Output/RxPDO): 15 Motors * 20 bytes = 300 bytes
SM2_SIZE = 300 
# SM3 (Input/TxPDO): 15 Motors * 36 bytes = 540 bytes
SM3_SIZE = 540

def build_eeprom():
    # 1. EEPROM HEADER (First 16 Bytes / 8 Words)
    # Word 0: PDI Control (0x0080 = SPI)
    # Word 1: PDI Config
    # Word 2-6: Reserved
    # Word 7: Checksum (Low byte is checksum, High byte is 0x00)
    eeprom = bytearray([0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    eeprom += bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    # --- CATEGORY 1: GENERAL (Type 30) ---
    # MUST BE FIRST! This contains Vendor ID.
    gen_data = struct.pack('<I I I I', VENDOR_ID, PRODUCT_CODE, REVISION, SERIAL)
    eeprom += struct.pack('<H H', 30, len(gen_data) // 2) # Header: Type 30, Size in Words
    eeprom += gen_data

    # --- CATEGORY 2: SYNC MANAGERS (Type 40) ---
    # Defines the memory layout. 
    sm_data = bytearray()
    
    # SM0: Mailbox Out (Addr 0x1000, Len 128)
    sm_data += struct.pack('<H H B B B B', 0x1000, 128, 0x26, 0, 1, 0)
    # SM1: Mailbox In (Addr 0x1080, Len 128)
    sm_data += struct.pack('<H H B B B B', 0x1080, 128, 0x22, 0, 1, 0)
    # SM2: Outputs (Addr 0x1100, Len 300) <--- YOUR ROBOT DATA
    sm_data += struct.pack('<H H B B B B', 0x1100, SM2_SIZE, 0x64, 0, 1, 0)
    # SM3: Inputs (Addr 0x1400, Len 540) <--- YOUR ROBOT DATA
    sm_data += struct.pack('<H H B B B B', 0x1400, SM3_SIZE, 0x20, 0, 1, 0)
    
    eeprom += struct.pack('<H H', 40, len(sm_data) // 2)
    eeprom += sm_data

    # --- CATEGORY 3: STRINGS (Type 10) ---
    strings = [b"RobotHand", b"Main"]
    str_data = bytearray([len(strings)]) 
    for s in strings:
        str_data += bytearray([len(s)]) + s
    if len(str_data) % 2 != 0: str_data += b'\x00' # Padding
    
    eeprom += struct.pack('<H H', 10, len(str_data) // 2)
    eeprom += str_data

    # --- END CATEGORY ---
    eeprom += struct.pack('<H H', 0xFFFF, 0)

    # Pad to minimum 128 bytes
    while len(eeprom) < 128:
        eeprom += b'\x00'

    # --- CHECKSUM CALCULATION ---
    # The checksum is at Byte 14 (0x0E). 
    # It makes the sum of the first 14 bytes (0-13) + Checksum = 0xFF (low byte).
    chk = 0
    for i in range(14):
        chk += eeprom[i]
    
    checksum_byte = (0xFF - (chk & 0xFF)) & 0xFF
    eeprom[14] = checksum_byte

    return eeprom

if __name__ == "__main__":
    bin_data = build_eeprom()
    with open("robot_hand_v2.bin", "wb") as f:
        f.write(bin_data)
    print(f"Generated robot_hand_v2.bin: {len(bin_data)} bytes")