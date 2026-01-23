#include <stdio.h>
#include "main.h"       // For HAL headers
#include "esc_sheet.h"  // Use the OFFICIAL structs (no duplicates!)

// External references to the SPI handle (defined in main.c)
extern SPI_HandleTypeDef hspi1;

// Define the Chip Select Pin (Update these if your pin names represent differently)
#define LAN9252_CS_PORT  GPIOB
#define LAN9252_CS_PIN   GPIO_PIN_6

// --- The Benchmark Function ---
void run_spi_benchmark(void) {
    printf("\r\n=== STARTING POWER-ON SELF-TEST (SPI SPEED) ===\r\n");

    // 1. Setup Data using the GLOBAL structs (from esc_sheet.c)
    // We fill them with dummy data just for the test
    for (int i = 0; i < NUM_MOTORS; i++) {
        robot_out.motor[i].torque_enable = 1;
        robot_out.motor[i].goal_position = 123.456f + i;
    }

    // 2. Variables for Timing
    uint32_t start_time, end_time, duration;
    uint32_t total_time = 0;
    int test_cycles = 10000; // Run 10k times

    // 3. The Test Loop
    start_time = HAL_GetTick();

    for (int i = 0; i < test_cycles; i++) {
        // Chip Select LOW
        HAL_GPIO_WritePin(LAN9252_CS_PORT, LAN9252_CS_PIN, GPIO_PIN_RESET);

        // Transmit "Output" (Command) Data
        HAL_SPI_Transmit(&hspi1, (uint8_t*)&robot_out, sizeof(Robot_Output_t), HAL_MAX_DELAY);

        // Receive "Input" (Feedback) Data
        HAL_SPI_Receive(&hspi1, (uint8_t*)&robot_in, sizeof(Robot_Input_t), HAL_MAX_DELAY);

        // Chip Select HIGH
        HAL_GPIO_WritePin(LAN9252_CS_PORT, LAN9252_CS_PIN, GPIO_PIN_SET);
    }

    end_time = HAL_GetTick();
    total_time = end_time - start_time;

    // 4. Report Results
    printf("Test Complete: %d cycles in %lu ms\r\n", test_cycles, total_time);
    float time_per_cycle = (float)total_time * 1000.0f / test_cycles; // in microseconds
    printf("Speed: %.2f us per cycle\r\n", time_per_cycle);

    if (time_per_cycle < 600.0f) {
        printf("RESULT: PASS (High Speed)\r\n");
    } else {
        printf("RESULT: WARNING (Slow SPI Detected)\r\n");
    }

    printf("=== SELF-TEST COMPLETE. STARTING ETHERCAT... ===\r\n\r\n");
}
