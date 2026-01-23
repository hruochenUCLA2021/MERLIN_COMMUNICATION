/**
 * @brief Used by syscalls.c (_write) to output characters (printf).
 * @note  This implementation outputs over USART3 (polling).
 *        Ensure MX_USART3_UART_Init() is called before the first printf().
 */
#include <stdint.h>

#include "../../Drivers/STM32H7xx_HAL_Driver/Inc/stm32h7xx_hal.h"

int __io_putchar(int ch)
{
  extern UART_HandleTypeDef huart3;
  uint8_t c = (uint8_t)ch;
  (void)HAL_UART_Transmit(&huart3, &c, 1, HAL_MAX_DELAY);
  return ch;
}


