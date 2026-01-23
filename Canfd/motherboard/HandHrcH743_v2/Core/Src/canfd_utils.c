#include "../Inc/canfd_utils.h"
#ifndef __clang__
#include <string.h>
#endif

// Simple ISR/main-loop handoff.
static volatile uint32_t s_tick_1khz_count = 0;
static volatile uint8_t s_rx_pending = 0;
static CanfdRxFrame_t s_last_rx;

#ifndef V1_TXPDO_BASE_STDID
#define V1_TXPDO_BASE_STDID 0x200U
#endif

#ifndef V2_RXPDO_BASE_STDID
#define V2_RXPDO_BASE_STDID 0x300U
#endif

volatile Robot_Input_t g_robot_input;
volatile uint32_t g_rx_frames_total = 0;
volatile uint32_t g_rx_frames_txpdo = 0;
volatile uint32_t g_rx_frames_other = 0;

#ifdef __clang__
// Cursor/clangd linting environment: provide minimal stubs so the project indexes cleanly.
// Real firmware builds (STM32CubeIDE/GCC) compile the full implementations below.

bool CANFD_Utils_Init(FDCAN_HandleTypeDef *hfdcan) { (void)hfdcan; return true; }
void CANFD_Utils_On1kHzTickISR(void) { s_tick_1khz_count++; }
uint32_t CANFD_Utils_Consume1kHzTicks(void) { uint32_t n = s_tick_1khz_count; s_tick_1khz_count = 0; return n; }
bool CANFD_Utils_SendEmpty32(FDCAN_HandleTypeDef *hfdcan, uint32_t std_id) { (void)hfdcan; (void)std_id; return true; }
bool CANFD_Utils_RxPending(void) { return s_rx_pending != 0; }
bool CANFD_Utils_GetLastRx(CanfdRxFrame_t *out) { if (!out) return false; *out = s_last_rx; s_rx_pending = 0; return true; }

#else

bool CANFD_Utils_Init(FDCAN_HandleTypeDef *hfdcan)
{
    // Accept-all standard IDs into RX FIFO0 (tighten later by ID scheme).
    FDCAN_FilterTypeDef filter = {0};
    filter.IdType = FDCAN_STANDARD_ID;
    filter.FilterIndex = 0;
    filter.FilterType = FDCAN_FILTER_RANGE;
    filter.FilterConfig = FDCAN_FILTER_TO_RXFIFO0;
    filter.FilterID1 = 0x000;
    filter.FilterID2 = 0x7FF;
    if (HAL_FDCAN_ConfigFilter(hfdcan, &filter) != HAL_OK) {
        return false;
    }

    // Non-matching frames: accept to FIFO0 for bring-up. Reject remote frames.
    if (HAL_FDCAN_ConfigGlobalFilter(hfdcan,
                                    FDCAN_ACCEPT_IN_RX_FIFO0, /* NonMatchingStd */
                                    FDCAN_ACCEPT_IN_RX_FIFO0, /* NonMatchingExt */
                                    FDCAN_REJECT_REMOTE,       /* RejectRemoteStd */
                                    FDCAN_REJECT_REMOTE)       /* RejectRemoteExt */
        != HAL_OK) {
        return false;
    }

    if (HAL_FDCAN_Start(hfdcan) != HAL_OK) {
        return false;
    }

    // Enable RX FIFO0 new message interrupt.
    if (HAL_FDCAN_ActivateNotification(hfdcan, FDCAN_IT_RX_FIFO0_NEW_MESSAGE, 0) != HAL_OK) {
        return false;
    }

    return true;
}

void CANFD_Utils_On1kHzTickISR(void)
{
    s_tick_1khz_count++;
}

uint32_t CANFD_Utils_Consume1kHzTicks(void)
{
    uint32_t n = s_tick_1khz_count;
    if (n) {
        s_tick_1khz_count = 0;
    }
    return n;
}

bool CANFD_Utils_SendEmpty32(FDCAN_HandleTypeDef *hfdcan, uint32_t std_id)
{
    uint8_t payload[32];
    memset(payload, 0, sizeof(payload));

    FDCAN_TxHeaderTypeDef tx = {0};
    tx.Identifier = std_id & 0x7FFU;
    tx.IdType = FDCAN_STANDARD_ID;
    tx.TxFrameType = FDCAN_DATA_FRAME;
    tx.DataLength = FDCAN_DLC_BYTES_32;
    tx.ErrorStateIndicator = FDCAN_ESI_ACTIVE;
    tx.BitRateSwitch = FDCAN_BRS_ON;
    tx.FDFormat = FDCAN_FD_CAN;
    tx.TxEventFifoControl = FDCAN_NO_TX_EVENTS;
    tx.MessageMarker = 0;

    return (HAL_FDCAN_AddMessageToTxFifoQ(hfdcan, &tx, payload) == HAL_OK);
}

bool CANFD_Utils_SendMotorRxPDO(FDCAN_HandleTypeDef *hfdcan, uint32_t motor_id, const Motor_RxPDO_t *pdo)
{
    uint8_t payload[24];
    memset(payload, 0, sizeof(payload));
    Motor_RxPDO_t msg = {0};
    if (pdo) { msg = *pdo; }
    msg.motor_id = motor_id;
    memcpy(payload, &msg, sizeof(msg));

    FDCAN_TxHeaderTypeDef tx = {0};
    tx.Identifier = (V2_RXPDO_BASE_STDID + (motor_id & 0xFU)) & 0x7FFU;
    tx.IdType = FDCAN_STANDARD_ID;
    tx.TxFrameType = FDCAN_DATA_FRAME;
    tx.DataLength = FDCAN_DLC_BYTES_24;
    tx.ErrorStateIndicator = FDCAN_ESI_ACTIVE;
    tx.BitRateSwitch = FDCAN_BRS_ON;
    tx.FDFormat = FDCAN_FD_CAN;
    tx.TxEventFifoControl = FDCAN_NO_TX_EVENTS;
    tx.MessageMarker = 0;

    return (HAL_FDCAN_AddMessageToTxFifoQ(hfdcan, &tx, payload) == HAL_OK);
}

bool CANFD_Utils_RxPending(void)
{
    return s_rx_pending != 0;
}

bool CANFD_Utils_GetLastRx(CanfdRxFrame_t *out)
{
    if (!out) {
        s_rx_pending = 0;
        return false;
    }

    if (!s_rx_pending) {
        return false;
    }

    *out = s_last_rx;
    s_rx_pending = 0;
    return true;
}

void HAL_FDCAN_RxFifo0Callback(FDCAN_HandleTypeDef *hfdcan, uint32_t RxFifo0ITs)
{
    if ((RxFifo0ITs & FDCAN_IT_RX_FIFO0_NEW_MESSAGE) == 0U) {
        return;
    }

    // Drain FIFO0: at high rates we can have multiple frames queued.
    while (HAL_FDCAN_GetRxFifoFillLevel(hfdcan, FDCAN_RX_FIFO0) > 0U)
    {
        FDCAN_RxHeaderTypeDef rx_hdr;
        uint8_t rx_data[64];
        memset(&rx_hdr, 0, sizeof(rx_hdr));
        memset(rx_data, 0, sizeof(rx_data));

        if (HAL_FDCAN_GetRxMessage(hfdcan, FDCAN_RX_FIFO0, &rx_hdr, rx_data) != HAL_OK) {
            return;
        }

        g_rx_frames_total++;

        uint32_t sid = rx_hdr.Identifier & 0x7FFU;

        // v1 -> v2: TxPDO frames are StdID 0x200..0x20E
        if ((sid >= V1_TXPDO_BASE_STDID) && (sid < (V1_TXPDO_BASE_STDID + NUM_MOTORS)))
        {
            g_rx_frames_txpdo++;
            Motor_TxPDO_t pdo;
            memset(&pdo, 0, sizeof(pdo));
            memcpy(&pdo, rx_data, sizeof(pdo)); // 40 bytes

            uint32_t idx = (uint32_t)(sid - V1_TXPDO_BASE_STDID);
            if (pdo.motor_id < NUM_MOTORS) {
                idx = pdo.motor_id;
            }
            g_robot_input.motor[idx] = pdo; // update global robot input (ISR)
            continue;
        }

        // Unknown/other frame: keep last_rx for debugging only (not used for control flow).
        g_rx_frames_other++;
        memset(&s_last_rx, 0, sizeof(s_last_rx));
        s_last_rx.std_id = sid;
        s_last_rx.dlc_raw = rx_hdr.DataLength;
        s_last_rx.brs = (rx_hdr.BitRateSwitch == FDCAN_BRS_ON) ? 1U : 0U;
        s_last_rx.fd  = (rx_hdr.FDFormat      == FDCAN_FD_CAN) ? 1U : 0U;
        memcpy(s_last_rx.data, rx_data, sizeof(s_last_rx.data));
        s_rx_pending = 1;
    }
}

#endif /* __clang__ */


