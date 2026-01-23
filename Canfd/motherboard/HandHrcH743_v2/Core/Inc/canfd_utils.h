#ifndef CANFD_UTILS_H
#define CANFD_UTILS_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>
#include <stdint.h>

// IMPORTANT: For STM32 HAL, do NOT include a module header (like stm32h7xx_hal_fdcan.h)
// before the umbrella header (stm32h7xx_hal.h), or you'll hit an include-cycle where
// HAL_StatusTypeDef isn't defined yet. main.h pulls in stm32h7xx_hal.h in the correct order.
#ifndef __clang__
#include "main.h"
#else
// Cursor/clangd linting environment: avoid pulling in STM32 headers (needs CubeIDE include paths).
typedef struct __FDCAN_HandleTypeDef FDCAN_HandleTypeDef;
#endif

// ---- Robot PDO definitions (15 motors) ----
#ifndef NUM_MOTORS
#define NUM_MOTORS 15U
#endif

/**
 * @brief Motor status payload (40 bytes). Sent by v1 as a 48-byte CAN-FD frame (zero padded).
 */
typedef struct __attribute__((packed)) {
    uint32_t motor_id;           // 0..14
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

/**
 * @brief Master->Slave command payload (24 bytes).
 */
typedef struct __attribute__((packed)) {
    uint32_t motor_id;           // 0..14
    uint32_t torque_enable;
    float    goal_id;
    float    goal_iq;
    float    goal_velocity;
    float    goal_position;
} Motor_RxPDO_t;

// Complete Robot Structures (same idea as reference_good/soes_test.c)
typedef struct {
    Motor_RxPDO_t motor[NUM_MOTORS]; // 15 * 24 = 360 bytes
} Robot_Output_t;

typedef struct {
    Motor_TxPDO_t motor[NUM_MOTORS]; // 15 * 40 = 600 bytes
} Robot_Input_t;

// v2 (master) receives TxPDO from v1 (motor side) into this global buffer (updated in ISR).
extern volatile Robot_Input_t g_robot_input;

// RX counters (updated in ISR). Use for 1 Hz telemetry in main loop.
extern volatile uint32_t g_rx_frames_total;
extern volatile uint32_t g_rx_frames_txpdo;   // StdID 0x200..0x20E
extern volatile uint32_t g_rx_frames_other;

typedef struct {
    uint32_t std_id;      // 11-bit ID (0..0x7FF)
    uint32_t dlc_raw;     // HAL raw DLC encoding (e.g. FDCAN_DLC_BYTES_48)
    uint8_t brs;          // 0/1
    uint8_t fd;           // 0/1
    uint8_t data[64];     // raw bytes (up to 64)
} CanfdRxFrame_t;

/**
 * @brief Initialize FDCAN runtime (filters, global filter, start, RX notifications).
 */
bool CANFD_Utils_Init(FDCAN_HandleTypeDef *hfdcan);

/**
 * @brief Called from TIM6 ISR context: records a 1kHz "tick" (counted).
 */
void CANFD_Utils_On1kHzTickISR(void);

/**
 * @brief Consume pending 1kHz ticks (main loop).
 * @return number of ticks consumed since last call.
 */
uint32_t CANFD_Utils_Consume1kHzTicks(void);

/**
 * @brief Send an empty 32-byte CAN-FD frame (all zeros) to a standard ID.
 */
bool CANFD_Utils_SendEmpty32(FDCAN_HandleTypeDef *hfdcan, uint32_t std_id);

/**
 * @brief Send a Motor_RxPDO_t (24 bytes) as a CAN-FD frame.
 */
bool CANFD_Utils_SendMotorRxPDO(FDCAN_HandleTypeDef *hfdcan, uint32_t motor_id, const Motor_RxPDO_t *pdo);

/**
 * @brief RX handling: whether a frame was received and is pending for processing in main loop.
 */
bool CANFD_Utils_RxPending(void);

/**
 * @brief Copy out last received frame (clears pending flag).
 * @return true if a frame was pending and copied.
 */
bool CANFD_Utils_GetLastRx(CanfdRxFrame_t *out);

#ifdef __cplusplus
}
#endif

#endif /* CANFD_UTILS_H */


