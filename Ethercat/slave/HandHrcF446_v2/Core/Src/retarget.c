/*
 * retarget.c
 *
 *  Created on: Nov 10, 2025
 *      Author: hrc
 */


#include "usart.h"
#include <sys/unistd.h> // for _write()

int _write(int file, char *ptr, int len)
{
    HAL_UART_Transmit(&huart2, (uint8_t *)ptr, len, HAL_MAX_DELAY);
    return len;
}
