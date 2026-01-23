# STM32H743 NUCLEO-144 CAN-FD Bring-up Notes

This document records **all configuration decisions and reasoning** made during the CAN-FD bring-up on **STM32H743 NUCLEO-144**, including clocks, FDCAN, GPIO, timer usage, and data design.  
It is intended as a **reference note** for future development and debugging.

---

## 1. Hardware Overview

- MCU: **STM32H743**
- Board: **NUCLEO-144**
- CAN transceiver: **External CAN-FD transceiver required** (e.g. MCP2542)
- Bus topology:
  - 2 nodes (STM32 ↔ STM32)
  - Cable length ≈ **5 cm**
  - Proper **120 Ω termination at both ends**

---

## 2. System Clock Configuration

### CPU / Bus clocks
Goal: **maximum CPU performance**, independent of CAN speed.

- **SYSCLK (CPU clock)**: **400 MHz**
- **AHB (HCLK)**: 200 MHz
- **APB1 / APB2 / APB3 / APB4**: 100 MHz
- **APB Timer clocks**: 200 MHz (×2 rule when prescaler ≠ 1)

This configuration is:
- Within STM32H743 limits
- Stable
- Suitable for real-time control and high-rate communication

### Key observation
CAN-FD speed **does NOT depend on CPU clock**.  
CAN-FD uses its own **kernel clock**.

---

## 3. FDCAN Kernel Clock

- **FDCAN clock source**: PLL1Q
- **FDCAN kernel clock**: **100 MHz**
- CubeMX shows **no red error** → configuration is valid

Because the bus is very short (≈5 cm), a **10 Mbps CAN-FD data phase** is acceptable and stable.

---

## 4. CAN-FD Bit Timing Configuration

### Nominal (arbitration) phase
- **Nominal bitrate**: **1 Mbps**

| Parameter | Value |
|---------|------|
| Prescaler | 5 |
| TimeSeg1 | 13 |
| TimeSeg2 | 6 |
| SJW | 2 |

Check:
```
100 MHz / 5 / (1 + 13 + 6) = 1 Mbps
```

---

### Data phase (BRS enabled)
- **Data bitrate**: **10 Mbps**

| Parameter | Value |
|----------|------|
| Prescaler | 1 |
| TimeSeg1 | 7 |
| TimeSeg2 | 2 |
| SJW | 2 |

Check:
```
100 MHz / 1 / (1 + 7 + 2) = 10 Mbps
```

> Note: Exact 8 Mbps is NOT required. CAN-FD works as long as **both nodes use identical timing**.

---

## 5. FDCAN Peripheral Configuration (CubeMX)

### Frame / mode
- Frame format: **FD mode with Bit Rate Switching**
- Mode: Normal
- Auto retransmission: Enabled

### Message RAM
- **Standard filters**: 1
- **RX FIFO0 elements**: 4
- **RX FIFO0 element size**: 48 bytes
- RX FIFO1: not used
- **TX FIFO/Queue elements**: 4
- **TX element size**: 48 bytes

Reason:
- Payload = 9 floats = 36 bytes
- CAN-FD allows only specific sizes → **48 bytes chosen**
- Remaining bytes are zero-padded

---

## 6. GPIO / Pin Configuration

### FDCAN1 pins
| Pin | Function |
|----|---------|
| PD0 | FDCAN1_RX |
| PD1 | FDCAN1_TX |

- Alternate function mode
- No pull-up / pull-down
- Output speed: Low (acceptable)

---

## 7. Interrupt Configuration

### FDCAN
- **FDCAN1 interrupt 0**: Enabled
- Used for:
  - RX FIFO0 new message interrupt

### TIM6
- **TIM6 global interrupt**: Enabled
- Used for:
  - 1 kHz periodic trigger (slave status transmission)

---

## 8. TIM6 Configuration (1 kHz periodic tick)

TIM6 is a **basic timer**, ideal for periodic interrupts.

### Clock source
- TIM6 clock = **APB1 Timer clock = 200 MHz**

### Timer parameters
| Parameter | Value |
|---------|------|
| Prescaler | 19999 |
| Auto-reload (ARR) | 9 |
| Mode | Up |

Check:
```
200 MHz / (19999 + 1) = 10 kHz
10 kHz / (9 + 1) = 1 kHz
```

Result:
- **Interrupt every 1 ms (1000 Hz)**

### Usage pattern
- TIM6 ISR sets a flag
- Main loop sends CAN-FD frame when flag is set
- Avoid heavy logic inside ISR

---

## 9. Motor → Master Data Structure

### Slave transmits motor status periodically (1 kHz)

```c
typedef struct __attribute__((packed)) {
    float present_id;
    float present_iq;
    float present_velocity;
    float present_position;
    float input_voltage;
    float winding_temp;
    float powerstage_temp;
    float ic_temperature;
    float error_status;
} Motor_TxPDO_t;
```

- Size: **36 bytes**
- Sent as **48-byte CAN-FD frame**
- Padding bytes = 0

### Suggested CAN ID scheme
- Example: `0x200 + motor_id`
- Standard ID (11-bit)

---

## 10. RX / TX Software Architecture

### RX (from master)
- FDCAN hardware writes frame into RX FIFO
- RX interrupt fires
- ISR:
  - Reads message
  - Copies to buffer
  - Sets a flag
- Main loop:
  - Processes message
  - Uses `printf()` (UART retarget)

### TX (slave status)
- TIM6 interrupt sets `send_1khz_flag`
- Main loop:
  - Packs `Motor_TxPDO_t`
  - Sends CAN-FD frame via TX FIFO

> CAN HAL calls are **not** executed inside timer ISR.

---

## 11. What We Do NOT Use (by design)

- DMA for CAN-FD RX/TX (CAN is message-based)
- TIM1 (advanced timer, unnecessary here)
- RX FIFO1 (not needed yet)
- Exact 8 Mbps requirement (10 Mbps is acceptable)

---

## 12. What To Do Next

1. **Bring-up test**
   - Connect two STM32H743 boards
   - Verify RX interrupt fires
   - Verify 1 kHz TX frames observed on other node

2. **Add master**
   - Implement command frames (8-byte or FD)
   - Add ID-based filtering

3. **Robustness**
   - Add sequence counter / timestamp to payload
   - Detect dropped frames

4. **Scaling**
   - Multiple motors (IDs or multiple frames)
   - Optional FIFO1 separation
   - Optional RTOS task instead of timer flag

---

## 13. Key Takeaways

- CPU clock and CAN-FD speed are **independent**
- CAN-FD does NOT need DMA
- Interrupt + FIFO is the correct model
- Short bus allows aggressive data rates
- Configuration is now **clean, scalable, and correct**

---

**End of note**
