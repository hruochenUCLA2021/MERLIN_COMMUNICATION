#include "esc_hw.h"
#include "spi.h"
#include "gpio.h"
#include <stdio.h>

/* ---------------------------------------------------------------------------
 * Hardware Definitions (From your lan9252_test.c)
 * --------------------------------------------------------------------------- */
#define LAN_CS_GPIO_Port   GPIOB
#define LAN_CS_Pin         GPIO_PIN_6

#define LAN_RST_GPIO_Port  GPIOB
#define LAN_RST_Pin        GPIO_PIN_0

extern SPI_HandleTypeDef hspi1;

/* ---------------------------------------------------------------------------
 * Private Helpers (Directly from lan9252_test.c)
 * --------------------------------------------------------------------------- */

static inline void lan_cs_low(void)
{
    HAL_GPIO_WritePin(LAN_CS_GPIO_Port, LAN_CS_Pin, GPIO_PIN_RESET);
}

static inline void lan_cs_high(void)
{
    HAL_GPIO_WritePin(LAN_CS_GPIO_Port, LAN_CS_Pin, GPIO_PIN_SET);
}

static void lan9252_reset_pulse(void)
{
    // Ensure CS is inactive during reset
    lan_cs_high();

    HAL_GPIO_WritePin(LAN_RST_GPIO_Port, LAN_RST_Pin, GPIO_PIN_RESET);
    HAL_Delay(5);   // Matches your 5ms delay
    HAL_GPIO_WritePin(LAN_RST_GPIO_Port, LAN_RST_Pin, GPIO_PIN_SET);
    HAL_Delay(10);  // Matches your 10ms delay
}

/* ---------------------------------------------------------------------------
 * SOES HAL Implementation
 * --------------------------------------------------------------------------- */

void ESC_init(const esc_cfg_t *cfg)
{
    // 1. Hardware Reset (using your exact timing)
    lan9252_reset_pulse();

    // 2. Proof of Life (Logic from LAN9252_SPI_ProofOfLife)
    // We try to read 0x0064 and expect 0x87654321
    uint32_t byte_test = 0;

    // Retry loop similar to your test code (20 attempts)
    for (int i = 0; i < 20; i++)
    {
        ESC_read(0x0064, &byte_test, 4);

        if (byte_test == 0x87654321UL)
        {
            // Success
            return;
        }

        HAL_Delay(50);
    }

    // If we reach here, the check failed.
    printf("ESC_init FAIL: Byte test read 0x%08lX, expected 0x87654321\r\n", (unsigned long)byte_test);
}

void ESC_reset(void)
{
    lan9252_reset_pulse();
}

/** * @brief Reads data from the LAN9252.
 * Adapted from lan9252_read32 to support variable 'len' for SOES.
 */
void ESC_read(uint16_t address, void *buf, uint16_t len)
{
    uint8_t cmd[3];

    // CMD 0x03 (READ) + Address (MSB first)
    cmd[0] = 0x03;
    cmd[1] = (uint8_t)(address >> 8);
    cmd[2] = (uint8_t)(address & 0xFF);

    lan_cs_low();

    // Send Command
    HAL_SPI_Transmit(&hspi1, cmd, 3, 100);

    // Receive Data
    HAL_SPI_Receive(&hspi1, (uint8_t *)buf, len, 100);

    lan_cs_high();
}

/** * @brief Writes data to the LAN9252.
 * Adapted from lan9252_write32 to support variable 'len' for SOES.
 */
void ESC_write(uint16_t address, void *buf, uint16_t len)
{
    uint8_t cmd[3];

    // CMD 0x02 (WRITE) + Address (MSB first)
    cmd[0] = 0x02;
    cmd[1] = (uint8_t)(address >> 8);
    cmd[2] = (uint8_t)(address & 0xFF);

    lan_cs_low();

    // Send Command
    HAL_SPI_Transmit(&hspi1, cmd, 3, 100);

    // Write Data
    HAL_SPI_Transmit(&hspi1, (uint8_t *)buf, len, 100);

    lan_cs_high();
}

uint32_t ESC_gettime(void)
{
    return HAL_GetTick();
}

void ESC_interrupt_enable(uint32_t mask)
{
    // Placeholder for future interrupt support
}

void ESC_interrupt_disable(void)
{
    // Placeholder for future interrupt support
}

void ESC_stop(void)
{
    // Optional shutdown logic
}
