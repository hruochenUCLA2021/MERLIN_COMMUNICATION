#include "esc_sheet.h"
#include "esc.h"
#include "esc_coe.h" // Required for _objd and _objectlist definitions

// --- Global Data Instances ---
Robot_Output_t robot_out;
Robot_Input_t  robot_in;
Robot_Config_t robot_config;

// Define standard device type
uint32_t esc_device_type = 0x00001234;

// ============================================================================
//   1. DEFINE SUB-INDEX ARRAYS (The Data Content)
// ============================================================================

// Standard Objects
const _objd Obj_1000[] = {
    // SubIndex 0: Value (Max Subindex = 0, treated as value for simple types)
    { 0, DTYPE_INTEGER32, sizeof(uint32_t), ATYPE_RO, "DeviceType", 0, (void*)&esc_device_type }
};

const _objd Obj_1008[] = {
    { 0, DTYPE_VISIBLE_STRING, 10, ATYPE_RO, "DeviceName", 0, (void*)"RobotHand" }
};

// --- MACRO TO GENERATE RXPDO (Output) OBJECTS ---
// Generates a const array named Obj_7000, Obj_7001, etc.
#define DECLARE_RXPDO_OBJ(hex_idx, i) \
const _objd Obj_##hex_idx[] = { \
    { 5, 0, 0, 0, 0, 0, 0 }, /* Subindex 0: Max Subindex = 5 */ \
    { 1, DTYPE_INTEGER32, 4, ATYPE_RW, "Torque",   0, (void*)&robot_out.motor[i].torque_enable }, \
    { 2, DTYPE_REAL32,    4, ATYPE_RW, "Goal_ID",  0, (void*)&robot_out.motor[i].goal_id }, \
    { 3, DTYPE_REAL32,    4, ATYPE_RW, "Goal_IQ",  0, (void*)&robot_out.motor[i].goal_iq }, \
    { 4, DTYPE_REAL32,    4, ATYPE_RW, "Goal_Vel", 0, (void*)&robot_out.motor[i].goal_velocity }, \
    { 5, DTYPE_REAL32,    4, ATYPE_RW, "Goal_Pos", 0, (void*)&robot_out.motor[i].goal_position } \
}

// Generate the 15 RxPDO arrays
DECLARE_RXPDO_OBJ(7000, 0);
DECLARE_RXPDO_OBJ(7001, 1);
DECLARE_RXPDO_OBJ(7002, 2);
DECLARE_RXPDO_OBJ(7003, 3);
DECLARE_RXPDO_OBJ(7004, 4);
DECLARE_RXPDO_OBJ(7005, 5);
DECLARE_RXPDO_OBJ(7006, 6);
DECLARE_RXPDO_OBJ(7007, 7);
DECLARE_RXPDO_OBJ(7008, 8);
DECLARE_RXPDO_OBJ(7009, 9);
DECLARE_RXPDO_OBJ(7010, 10);
DECLARE_RXPDO_OBJ(7011, 11);
DECLARE_RXPDO_OBJ(7012, 12);
DECLARE_RXPDO_OBJ(7013, 13);
DECLARE_RXPDO_OBJ(7014, 14);

// --- MACRO TO GENERATE TXPDO (Input) OBJECTS ---
// Generates a const array named Obj_6000, Obj_6001, etc.
#define DECLARE_TXPDO_OBJ(hex_idx, i) \
const _objd Obj_##hex_idx[] = { \
    { 9, 0, 0, 0, 0, 0, 0 }, /* Subindex 0: Max Subindex = 9 */ \
    { 1, DTYPE_REAL32,    4, ATYPE_RO, "Pres_ID",   0, (void*)&robot_in.motor[i].present_id }, \
    { 2, DTYPE_REAL32,    4, ATYPE_RO, "Pres_IQ",   0, (void*)&robot_in.motor[i].present_iq }, \
    { 3, DTYPE_REAL32,    4, ATYPE_RO, "Pres_Vel",  0, (void*)&robot_in.motor[i].present_velocity }, \
    { 4, DTYPE_REAL32,    4, ATYPE_RO, "Pres_Pos",  0, (void*)&robot_in.motor[i].present_position }, \
    { 5, DTYPE_REAL32,    4, ATYPE_RO, "Voltage",   0, (void*)&robot_in.motor[i].input_voltage }, \
    { 6, DTYPE_REAL32,    4, ATYPE_RO, "Temp_Coil", 0, (void*)&robot_in.motor[i].temp_winding }, \
    { 7, DTYPE_REAL32,    4, ATYPE_RO, "Temp_Pwr",  0, (void*)&robot_in.motor[i].temp_powerstage }, \
    { 8, DTYPE_REAL32,    4, ATYPE_RO, "Temp_IC",   0, (void*)&robot_in.motor[i].temp_ic }, \
    { 9, DTYPE_REAL32,    4, ATYPE_RO, "Error",     0, (void*)&robot_in.motor[i].error_status } \
}

// Generate the 15 TxPDO arrays
DECLARE_TXPDO_OBJ(6000, 0);
DECLARE_TXPDO_OBJ(6001, 1);
DECLARE_TXPDO_OBJ(6002, 2);
DECLARE_TXPDO_OBJ(6003, 3);
DECLARE_TXPDO_OBJ(6004, 4);
DECLARE_TXPDO_OBJ(6005, 5);
DECLARE_TXPDO_OBJ(6006, 6);
DECLARE_TXPDO_OBJ(6007, 7);
DECLARE_TXPDO_OBJ(6008, 8);
DECLARE_TXPDO_OBJ(6009, 9);
DECLARE_TXPDO_OBJ(6010, 10);
DECLARE_TXPDO_OBJ(6011, 11);
DECLARE_TXPDO_OBJ(6012, 12);
DECLARE_TXPDO_OBJ(6013, 13);
DECLARE_TXPDO_OBJ(6014, 14);



// ============================================================================
//   1.5 DEFINE SYNC MANAGER ASSIGNMENTS (The Routing)
// ============================================================================

// --- 0x1C12: RxPDO Assignment (Master -> Slave) ---
// We list all 15 Output Objects (0x7000 to 0x700E) here.
uint16_t RxPDO_Map[] = {
    0x7000, 0x7001, 0x7002, 0x7003, 0x7004,
    0x7005, 0x7006, 0x7007, 0x7008, 0x7009,
    0x7010, 0x7011, 0x7012, 0x7013, 0x7014
};

const _objd Obj_1C12[] = {
    { 15, 0, 0, 0, 0, 0, 0 }, // Subindex 0: Count = 15
    { 1, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub1", 0, (void*)&RxPDO_Map[0] },
    { 2, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub2", 0, (void*)&RxPDO_Map[1] },
    { 3, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub3", 0, (void*)&RxPDO_Map[2] },
    { 4, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub4", 0, (void*)&RxPDO_Map[3] },
    { 5, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub5", 0, (void*)&RxPDO_Map[4] },
    { 6, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub6", 0, (void*)&RxPDO_Map[5] },
    { 7, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub7", 0, (void*)&RxPDO_Map[6] },
    { 8, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub8", 0, (void*)&RxPDO_Map[7] },
    { 9, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub9", 0, (void*)&RxPDO_Map[8] },
    { 10, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub10", 0, (void*)&RxPDO_Map[9] },
    { 11, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub11", 0, (void*)&RxPDO_Map[10] },
    { 12, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub12", 0, (void*)&RxPDO_Map[11] },
    { 13, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub13", 0, (void*)&RxPDO_Map[12] },
    { 14, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub14", 0, (void*)&RxPDO_Map[13] },
    { 15, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub15", 0, (void*)&RxPDO_Map[14] },
};

// --- 0x1C13: TxPDO Assignment (Slave -> Master) ---
// We list all 15 Input Objects (0x6000 to 0x600E) here.
uint16_t TxPDO_Map[] = {
    0x6000, 0x6001, 0x6002, 0x6003, 0x6004,
    0x6005, 0x6006, 0x6007, 0x6008, 0x6009,
    0x6010, 0x6011, 0x6012, 0x6013, 0x6014
};

const _objd Obj_1C13[] = {
    { 15, 0, 0, 0, 0, 0, 0 }, // Subindex 0: Count = 15
    { 1, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub1", 0, (void*)&TxPDO_Map[0] },
    { 2, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub2", 0, (void*)&TxPDO_Map[1] },
    { 3, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub3", 0, (void*)&TxPDO_Map[2] },
    { 4, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub4", 0, (void*)&TxPDO_Map[3] },
    { 5, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub5", 0, (void*)&TxPDO_Map[4] },
    { 6, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub6", 0, (void*)&TxPDO_Map[5] },
    { 7, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub7", 0, (void*)&TxPDO_Map[6] },
    { 8, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub8", 0, (void*)&TxPDO_Map[7] },
    { 9, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub9", 0, (void*)&TxPDO_Map[8] },
    { 10, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub10", 0, (void*)&TxPDO_Map[9] },
    { 11, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub11", 0, (void*)&TxPDO_Map[10] },
    { 12, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub12", 0, (void*)&TxPDO_Map[11] },
    { 13, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub13", 0, (void*)&TxPDO_Map[12] },
    { 14, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub14", 0, (void*)&TxPDO_Map[13] },
    { 15, DTYPE_INTEGER16, 2, ATYPE_RW, "Sub15", 0, (void*)&TxPDO_Map[14] },
};

// ============================================================================
//   2. DEFINE THE MAIN OBJECT LIST (The Index Map)
// ============================================================================

// Macro to create the list entry
#define LINK_OBJ(hex_idx, name, obj_array) \
    { hex_idx, 0, 0, 0, name, obj_array }

// *** CRITICAL: NAME MUST BE SDOobjects ***
const _objectlist SDOobjects[] = {
    // Standard Objects
    LINK_OBJ(0x1000, "DeviceType", Obj_1000),
    LINK_OBJ(0x1008, "DeviceName", Obj_1008),

	// *** ADD THESE TWO LINES ***
	LINK_OBJ(0x1C12, "RxPDOAssign", Obj_1C12),
	LINK_OBJ(0x1C13, "TxPDOAssign", Obj_1C13),

    // TXPDOs (Inputs 0x6000-0x600E)
    LINK_OBJ(0x6000, "M0_In", Obj_6000),
    LINK_OBJ(0x6001, "M1_In", Obj_6001),
    LINK_OBJ(0x6002, "M2_In", Obj_6002),
    LINK_OBJ(0x6003, "M3_In", Obj_6003),
    LINK_OBJ(0x6004, "M4_In", Obj_6004),
    LINK_OBJ(0x6005, "M5_In", Obj_6005),
    LINK_OBJ(0x6006, "M6_In", Obj_6006),
    LINK_OBJ(0x6007, "M7_In", Obj_6007),
    LINK_OBJ(0x6008, "M8_In", Obj_6008),
    LINK_OBJ(0x6009, "M9_In", Obj_6009),
    LINK_OBJ(0x6010, "M10_In", Obj_6010),
    LINK_OBJ(0x6011, "M11_In", Obj_6011),
    LINK_OBJ(0x6012, "M12_In", Obj_6012),
    LINK_OBJ(0x6013, "M13_In", Obj_6013),
    LINK_OBJ(0x6014, "M14_In", Obj_6014),

    // RXPDOs (Outputs 0x7000-0x700E)
    LINK_OBJ(0x7000, "M0_Out", Obj_7000),
    LINK_OBJ(0x7001, "M1_Out", Obj_7001),
    LINK_OBJ(0x7002, "M2_Out", Obj_7002),
    LINK_OBJ(0x7003, "M3_Out", Obj_7003),
    LINK_OBJ(0x7004, "M4_Out", Obj_7004),
    LINK_OBJ(0x7005, "M5_Out", Obj_7005),
    LINK_OBJ(0x7006, "M6_Out", Obj_7006),
    LINK_OBJ(0x7007, "M7_Out", Obj_7007),
    LINK_OBJ(0x7008, "M8_Out", Obj_7008),
    LINK_OBJ(0x7009, "M9_Out", Obj_7009),
    LINK_OBJ(0x7010, "M10_Out", Obj_7010),
    LINK_OBJ(0x7011, "M11_Out", Obj_7011),
    LINK_OBJ(0x7012, "M12_Out", Obj_7012),
    LINK_OBJ(0x7013, "M13_Out", Obj_7013),
    LINK_OBJ(0x7014, "M14_Out", Obj_7014),

    // Terminator
    { 0,0,0,0,0,0 }
};

// Function not needed by library, but keeps compatibility with some examples
void SOES_Init_Object_Dictionary(void) {}
