import struct

# --- CONFIGURATION ---
VENDOR_ID = 0x000004d8
PRODUCT_CODE = 0x00000001
REVISION = 0x00000001
SERIAL = 0x00000001

SM2_SIZE = 300 
SM3_SIZE = 540

def calculate_checksum(eeprom):
    current_sum = 0
    # Checksum is sum of first 7 words (14 bytes)
    for i in range(14):
        current_sum += eeprom[i]
    # Checksum calculation: low byte of (0xFF - sum)
    checksum = (0xFF - (current_sum & 0xFF)) & 0xFF
    return checksum

def build_eeprom():
    # Initialize 256 byte buffer with 0
    eeprom = bytearray(256)
    
    # ==========================================
    # 1. PDI HEADER (Bytes 0-15)
    # ==========================================
    eeprom[0] = 0x80 # PDI Control (SPI)
    eeprom[1] = 0x00
    eeprom[2] = 0x00 # PDI Config
    eeprom[3] = 0x00
    # Bytes 4-13 are reserved/alias, kept as 0
    
    # ==========================================
    # 2. DATA AREA
    # ==========================================
    # We start writing categories at Offset 64 (Byte 0x40).
    # This leaves Bytes 16-63 open for the "Fixed Address" Mailbox hacks 
    # if the hardware enforces them.
    
    offset = 64
    
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
    # Layout: Vendor(4), Prod(4), Rev(4), Ser(4), CoE Details(1), FoE(1), EoE(1), SoE(1), DS402(1), Sys(1)
    # Total Data Size: 16 + 6 = 22 bytes? Standard says 18 bytes min.
    # We MUST set "CoE Details" (Byte 16 of data) to 0x01 (Enable CoE)
    
    gen_data = struct.pack('<I I I I', VENDOR_ID, PRODUCT_CODE, REVISION, SERIAL)
    # Add flags: CoE=1, FoE=0, EoE=0, SoE=0, DS402=0, Sys=0
    gen_data += b'\x01\x00\x00\x00\x00\x00' 
    
    eeprom[offset:offset+2] = struct.pack('<H', 30)
    eeprom[offset+2:offset+4] = struct.pack('<H', len(gen_data) // 2)
    offset += 4
    eeprom[offset:offset+len(gen_data)] = gen_data
    offset += len(gen_data)

    # --- CATEGORY 3: SYNC MANAGERS (Type 40) ---
    sm_data = bytearray()
    sm_data += struct.pack('<H H B B B B', 0x1000, 128, 0x26, 0, 1, 0) # SM0
    sm_data += struct.pack('<H H B B B B', 0x1080, 128, 0x22, 0, 1, 0) # SM1
    sm_data += struct.pack('<H H B B B B', 0x1100, SM2_SIZE, 0x64, 0, 1, 0) # SM2
    sm_data += struct.pack('<H H B B B B', 0x1400, SM3_SIZE, 0x20, 0, 1, 0) # SM3

    eeprom[offset:offset+2] = struct.pack('<H', 40)
    eeprom[offset+2:offset+4] = struct.pack('<H', len(sm_data) // 2)
    offset += 4
    eeprom[offset:offset+len(sm_data)] = sm_data
    offset += len(sm_data)

    # --- END CATEGORY ---
    eeprom[offset:offset+2] = b'\xFF\xFF'

    # ==========================================
    # 3. BRIDGE THE GAP (Word 8 -> Offset 64)
    # ==========================================
    # At Byte 16 (Word 8), the Master expects the first Category.
    # However, Bytes 48-56 are used by the "Fixed" Mailbox config.
    # We put a "Dummy" Category at Byte 16 that is just long enough 
    # to jump over the dangerous area and land at Offset 64.
    
    # We are at Byte 16. Target is Byte 64.
    # Gap = 64 - 16 = 48 bytes.
    # Category Header = 4 bytes. Data = 44 bytes.
    # We use Type 0 (NOP)? No, standard doesn't have NOP. 
    # We use a Dummy General Category or similar? 
    # Actually, let's just use the "Fixed Mailbox" area as the first category 
    # by crafting the data carefully.
    
    # BETTER PLAN:
    # Just write the "Fixed Mailbox" values at 48-56.
    # And at Byte 16, start the list.
    # BUT we ensure the list data simply *skips* writing 0s to 48-56?
    # No, struct.pack overwrites.
    
    # OVERWRITE FIX:
    # 1. Calculate Checksum based on current buffer (zeros at 16..63).
    # 2. Write the "Jump" logic? 
    # No, keep it simple. If we use the Categories correctly, we don't need 48-56.
    # The reason V8 failed was MISSING COE FLAGS in the Category.
    # So, we will simply start the list at Byte 16.
    
    # RESET BUFFER for standard linear write
    # We do NOT jump to 64. We write sequentially from 16.
    # If this overwrites 56, so be it. The Category takes precedence 
    # if parsed correctly.
    
    offset = 16 # Start immediately after header
    
    # --- WRITE STRINGS (At 16) ---
    eeprom[offset:offset+2] = struct.pack('<H', 10)
    eeprom[offset+2:offset+4] = struct.pack('<H', len(str_data) // 2)
    offset += 4
    eeprom[offset:offset+len(str_data)] = str_data
    offset += len(str_data)
    
    # --- WRITE GENERAL (At ~36) ---
    eeprom[offset:offset+2] = struct.pack('<H', 30)
    eeprom[offset+2:offset+4] = struct.pack('<H', len(gen_data) // 2)
    offset += 4
    eeprom[offset:offset+len(gen_data)] = gen_data
    offset += len(gen_data)

    # --- WRITE SYNC MGRS ---
    eeprom[offset:offset+2] = struct.pack('<H', 40)
    eeprom[offset+2:offset+4] = struct.pack('<H', len(sm_data) // 2)
    offset += 4
    eeprom[offset:offset+len(sm_data)] = sm_data
    offset += len(sm_data)
    
    eeprom[offset:offset+2] = b'\xFF\xFF'
    
    # ==========================================
    # 4. FINAL SAFETY (Byte 56 Force)
    # ==========================================
    # If our categories overwrote Byte 56 with 0, force it to 4.
    # This might corrupt a category data byte, but likely just a string 
    # or a reserved flag. 
    # The General Category ends around byte 50-60. 
    # Let's trust the Categories first. 
    # But as a failsafe:
    # eeprom[56] |= 0x04 
    # (Uncomment above line if this V11 still says Protocol: 00)

    # 5. CHECKSUM
    eeprom[14] = calculate_checksum(eeprom)
    
    return eeprom

if __name__ == "__main__":
    with open("robot_hand_v11.bin", "wb") as f:
        f.write(build_eeprom())
    print("Generated robot_hand_v11.bin (Full Category + CoE Flags)")