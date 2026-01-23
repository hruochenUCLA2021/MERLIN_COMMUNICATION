#include "main.h"
#include "spi.h"
#include "gpio.h"
#include <stdio.h>
#include <string.h>

// --- Adjust if your pins/ports differ ---
#define LAN_CS_GPIO_Port   GPIOB
#define LAN_CS_Pin         GPIO_PIN_6

#define LAN_RST_GPIO_Port  GPIOB
#define LAN_RST_Pin        GPIO_PIN_0

extern SPI_HandleTypeDef hspi1;

// CS helpers
static inline void lan_cs_low(void)  { HAL_GPIO_WritePin(LAN_CS_GPIO_Port, LAN_CS_Pin, GPIO_PIN_RESET); }
static inline void lan_cs_high(void) { HAL_GPIO_WritePin(LAN_CS_GPIO_Port, LAN_CS_Pin, GPIO_PIN_SET);   }

// Reset pulse (active low)
static void lan9252_reset_pulse(void)
{
    // Ensure CS is inactive during reset
    lan_cs_high();

    HAL_GPIO_WritePin(LAN_RST_GPIO_Port, LAN_RST_Pin, GPIO_PIN_RESET);
    HAL_Delay(5);
    HAL_GPIO_WritePin(LAN_RST_GPIO_Port, LAN_RST_Pin, GPIO_PIN_SET);
    HAL_Delay(10);
}



static HAL_StatusTypeDef lan9252_read32(uint16_t addr, uint32_t *out)
{
    uint8_t hdr[3];
    uint8_t rx[4] = {0};

    hdr[0] = 0x03;                  // READ
    hdr[1] = (uint8_t)(addr >> 8);
    hdr[2] = (uint8_t)(addr & 0xFF);

    lan_cs_low();

    HAL_StatusTypeDef st = HAL_SPI_Transmit(&hspi1, hdr, sizeof(hdr), 100);
    if (st != HAL_OK) { lan_cs_high(); return st; }

    st = HAL_SPI_Receive(&hspi1, rx, sizeof(rx), 100);

    lan_cs_high();

    if (st != HAL_OK) return st;

    // LITTLE-ENDIAN assemble (LSB first)
    *out = ((uint32_t)rx[0] <<  0) |
           ((uint32_t)rx[1] <<  8) |
           ((uint32_t)rx[2] << 16) |
           ((uint32_t)rx[3] << 24);

    printf("LAN9252 RD32 @0x%04X bytes: %02X %02X %02X %02X  val=0x%08lX\r\n",
           addr, rx[0], rx[1], rx[2], rx[3], (unsigned long)*out);

    return HAL_OK;
}


static HAL_StatusTypeDef lan9252_write32(uint16_t addr, uint32_t val)
{
    uint8_t tx[3 + 4];

    tx[0] = 0x02;                    // WRITE (SPI)
    tx[1] = (uint8_t)(addr >> 8);    // addr high
    tx[2] = (uint8_t)(addr & 0xFF);  // addr low

    // Data is LSB-first (little endian) :contentReference[oaicite:4]{index=4}
    tx[3] = (uint8_t)(val & 0xFF);
    tx[4] = (uint8_t)((val >> 8) & 0xFF);
    tx[5] = (uint8_t)((val >> 16) & 0xFF);
    tx[6] = (uint8_t)((val >> 24) & 0xFF);

    lan_cs_low();
    HAL_StatusTypeDef st = HAL_SPI_Transmit(&hspi1, tx, sizeof(tx), 100);
    lan_cs_high();

    return st;
}


// Call this from main() once after init (UART/SPI/GPIO init)
void LAN9252_SPI_ProofOfLife(void)
{
    printf("\r\n--- LAN9252 SPI Proof-of-Life ---\r\n");

    lan9252_reset_pulse();
    printf("Reset pulse done.\r\n");

    // BYTE_TEST / BYTE_ORDER register is commonly checked at 0x0064
    // Expected: 0x87654321 when SPI is correct
    const uint16_t BYTE_TEST_ADDR = 0x0064;

    for (int i = 0; i < 20; i++)
    {
        uint32_t v = 0;
        HAL_StatusTypeDef st = lan9252_read32(BYTE_TEST_ADDR, &v);

        if (st != HAL_OK)
        {
            printf("SPI read failed: %d\r\n", (int)st);
        }
        else if (v == 0x87654321UL)
        {
            printf("PASS: BYTE_TEST = 0x%08lX\r\n", (unsigned long)v);
            return;
        }

        HAL_Delay(50);
    }

    printf("FAIL: did not read expected BYTE_TEST (0x87654321). Check wiring/SPI mode/CS.\r\n");
}


void LAN9252_WriteReadback_Test(void)
{
    const uint16_t INT_EN = 0x005C; // from common LAN9252 examples :contentReference[oaicite:5]{index=5}

    uint32_t orig = 0, rd = 0;
    lan9252_read32(INT_EN, &orig);
    printf("INT_EN original = 0x%08lX\r\n", (unsigned long)orig);

    uint32_t test = orig ^ 0x00000001UL; // flip bit0
    lan9252_write32(INT_EN, test);

    lan9252_read32(INT_EN, &rd);
    printf("INT_EN after write = 0x%08lX (expected 0x%08lX)\r\n",
           (unsigned long)rd, (unsigned long)test);

    // restore
    lan9252_write32(INT_EN, orig);
    lan9252_read32(INT_EN, &rd);
    printf("INT_EN restored = 0x%08lX\r\n", (unsigned long)rd);

    if (rd == orig)
        printf("PASS: write/readback works.\r\n");
    else
        printf("FAIL: write/readback mismatch.\r\n");
}
