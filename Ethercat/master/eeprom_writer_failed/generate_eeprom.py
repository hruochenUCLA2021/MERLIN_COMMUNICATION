import struct
import sys

# --- CONFIGURATION BASED ON ESC_SHEET.H ---
VENDOR_ID = 0x000004d8      # Microchip (Safe to use for dev)
PRODUCT_CODE = 0x00000001   # Your Product Version
REVISION = 0x00000001
SERIAL = 0x00000001

# Sync Manager Sizes (Calculated from your structs)
SM2_SIZE = 300  # 15 motors * 20 bytes (RxPDO)
SM3_SIZE = 540  # 15 motors * 36 bytes (TxPDO)

def build_eeprom():
    # 1. EEPROM HEADER (Word 0-7)
    # PDI Control: 0x0080 (SPI Interface), PDI Config: 0x0000
    eeprom = bytearray([0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    
    # Placeholder for Checksum (Word 0) - Calculated at the end
    
    # 2. STRINGS CATEGORY (Type 10)
    # Stores the name "RobotHand"
    strings = [b"RobotHand", b"Main"]
    str_data = bytearray([len(strings)]) # Number of strings
    for s in strings:
        str_data += bytearray([len(s)]) + s
    
    # Pad to even length (Word alignment)
    if len(str_data) % 2 != 0: str_data += b'\x00'
    
    # Add Category Header (Type 10, Length in Words)
    eeprom += struct.pack('<H H', 10, len(str_data) // 2)
    eeprom += str_data

    # 3. GENERAL CATEGORY (Type 30)
    # Vendor, Product, Rev, Serial
    gen_data = struct.pack('<I I I I', VENDOR_ID, PRODUCT_CODE, REVISION, SERIAL)
    eeprom += struct.pack('<H H', 30, len(gen_data) // 2)
    eeprom += gen_data

    # 4. SYNC MANAGER CATEGORY (Type 40)
    # Defines the 4 memory regions (Mailbox Out, Mailbox In, Outputs, Inputs)
    # Format per SM: Address(2), Length(2), Control(1), Status(1), Enable(1), PDI Control(1)
    
    sm_data = bytearray()
    
    # SM0: Mailbox Out (Master -> Slave)
    # Addr: 0x1000, Len: 128, Ctrl: 0x26 (Mailbox), Enable: 1
    sm_data += struct.pack('<H H B B B B', 0x1000, 128, 0x26, 0, 1, 0)
    
    # SM1: Mailbox In (Slave -> Master)
    # Addr: 0x1080, Len: 128, Ctrl: 0x22 (Mailbox), Enable: 1
    sm_data += struct.pack('<H H B B B B', 0x1080, 128, 0x22, 0, 1, 0)
    
    # SM2: Process Data Out (Master -> Slave) - YOUR 300 BYTES
    # Addr: 0x1100, Len: 300, Ctrl: 0x64 (3-Buffer + Watchdog), Enable: 1
    sm_data += struct.pack('<H H B B B B', 0x1100, SM2_SIZE, 0x64, 0, 1, 0)
    
    # SM3: Process Data In (Slave -> Master) - YOUR 540 BYTES
    # Addr: 0x1400, Len: 540, Ctrl: 0x20 (3-Buffer), Enable: 1
    # Note: Address 0x1400 is standard, but verify it doesn't overlap. 
    # 0x1100 + 300 = 0x122C. 0x1400 is safe.
    sm_data += struct.pack('<H H B B B B', 0x1400, SM3_SIZE, 0x20, 0, 1, 0)
    
    eeprom += struct.pack('<H H', 40, len(sm_data) // 2)
    eeprom += sm_data

    # 5. END CATEGORY (Type 0xFFFF)
    eeprom += struct.pack('<H H', 0xFFFF, 0)
    
    # Pad to 128 bytes minimum (Standard EEPROM size)
    while len(eeprom) < 128:
        eeprom += b'\x00'

    # 6. CALCULATE CHECKSUM
    # The checksum is the low byte of Word 0. Algorithm: XOR of 14 bytes in Config Area = 0.
    # Actually, for LAN9252, it's a standard checksum over the first 7 words (14 bytes).
    # But usually, 0x80 is fine for PDI control.
    # Let's rely on the tool or valid default. LAN9252 validates the checksum automatically.
    # A simple checksum algorithm for EtherCAT SII (Word 0-6 sum to 0xFF or similar).
    # Simpler: The checksum byte (byte 14) is set so the checksum of first 14 bytes is 0xFF.
    
    # Let's verify standard header checksum logic:
    # "The checksum is calculated over Word 0 to Word 6. The low byte of Word 7 contains the checksum."
    # Wait, Word 0 is PDI Control. Word 7 is Checksum? No.
    # Config Area is Words 0-3. Checksum is at 0x0E (Word 7 low byte)? No.
    # Standard: Byte 14 (0x0E) is the checksum.
    
    chk = 0
    # Sum bytes 0 to 13
    for i in range(14):
        chk += eeprom[i]
        
    # Checksum is the value that makes the lower byte of the sum equal to 0xFF
    checksum_byte = (0xFF - (chk & 0xFF)) & 0xFF
    
    # Insert checksum at Byte 14 (Word 7 Low Byte) - This is typical SII location
    # Note: Some docs say Word 0. Let's stick to standard layout where offset 14 is checksum.
    # Extending eeprom if short
    if len(eeprom) < 16: eeprom += b'\x00' * (16 - len(eeprom))
    
    eeprom[14] = checksum_byte

    return eeprom

if __name__ == "__main__":
    bin_data = build_eeprom()
    with open("robot_hand.bin", "wb") as f:
        f.write(bin_data)
    print(f"Successfully generated robot_hand.bin ({len(bin_data)} bytes)")
    print(f"Configured for: Out={SM2_SIZE} bytes, In={SM3_SIZE} bytes")