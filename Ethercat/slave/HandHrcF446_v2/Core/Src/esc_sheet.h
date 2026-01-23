#ifndef ESC_SHEET_H
#define ESC_SHEET_H

#include <stdint.h>
#include "esc.h"  // Ensure this points to your SOES header

// =========================================================
// 1. DATA STRUCTURE DEFINITIONS
// =========================================================
#define NUM_MOTORS 15

// --- RX PDO (Master -> Slave) ---
typedef struct {
    uint32_t torque_enable; // 4 bytes
    float    goal_id;       // 4 bytes
    float    goal_iq;       // 4 bytes
    float    goal_velocity; // 4 bytes
    float    goal_position; // 4 bytes
} __attribute__((packed)) Motor_RxPDO_t;

typedef struct {
    Motor_RxPDO_t motor[NUM_MOTORS];
} Robot_Output_t;


// --- TX PDO (Slave -> Master) ---
typedef struct {
    float    present_id;       // 4 bytes
    float    present_iq;       // 4 bytes
    float    present_velocity; // 4 bytes
    float    present_position; // 4 bytes
    float    input_voltage;    // 4 bytes
    float    temp_winding;     // 4 bytes
    float    temp_powerstage;  // 4 bytes
    float    temp_ic;          // 4 bytes
    float    error_status;     // 4 bytes
} __attribute__((packed)) Motor_TxPDO_t;

typedef struct {
    Motor_TxPDO_t motor[NUM_MOTORS];
} Robot_Input_t;


// --- SDO CONFIG (Parameters) ---
typedef struct {
    uint32_t id;
    uint32_t mode;
    float    p_gain_pos;
    float    limit_vel_max;
} __attribute__((packed)) Motor_Config_t;

typedef struct {
    Motor_Config_t motor[NUM_MOTORS];
} Robot_Config_t;

// =========================================================
// 2. GLOBAL VARIABLE ACCESS
// =========================================================
extern Robot_Output_t robot_out;     // Commands from Master
extern Robot_Input_t  robot_in;      // Feedback to Master
extern Robot_Config_t robot_config;  // Settings

// *** CRITICAL: Expose the dictionary as "SDOobjects" ***
extern const _objectlist SDOobjects[];

void SOES_Init_Object_Dictionary(void);

#endif // ESC_SHEET_H
