#ifndef ESC_HW_H
#define ESC_HW_H

#ifdef __cplusplus
extern "C" {
#endif

#include "main.h"
#include "esc.h"

/**
 * @brief Initialize the ESC
 * Uses the exact logic from LAN9252_SPI_ProofOfLife (Reset + Byte Test)
 */
void ESC_init(const esc_cfg_t *cfg);

/**
 * @brief Read data from ESC via SPI
 * Generalized version of lan9252_read32 for any length
 */
void ESC_read(uint16_t address, void *buf, uint16_t len);

/**
 * @brief Write data to ESC via SPI
 * Generalized version of lan9252_write32 for any length
 */
void ESC_write(uint16_t address, void *buf, uint16_t len);

/**
 * @brief Get system time in milliseconds
 */
uint32_t ESC_gettime(void);

/**
 * @brief Reset the ESC hardware
 */
void ESC_reset(void);

/* Interrupt placeholders (not used in your test file, but required by SOES) */
void ESC_interrupt_enable(uint32_t mask);
void ESC_interrupt_disable(void);

#ifdef __cplusplus
}
#endif

#endif /* ESC_HW_H */
