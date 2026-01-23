#include "canfd_utils.h"

#include "main.h"

#include <string.h>

// Simple ISR/main-loop handoff flags.
static volatile uint8_t s_tick_1khz_pending = 0;
static volatile uint8_t s_rx_pending = 0;

static CanfdRxFrame_t s_last_rx;

#ifndef V1_TXPDO_BASE_STDID
#define V1_TXPDO_BASE_STDID 0x200U
#endif

#ifndef V2_RXPDO_BASE_STDID
#define V2_RXPDO_BASE_STDID 0x300U
#endif

volatile Robot_Output_t g_robot_output;
volatile uint32_t g_rx_frames_total = 0;
volatile uint32_t g_rx_frames_rxpdo = 0;
volatile uint32_t g_rx_frames_other = 0;

bool CANFD_Utils_Init(FDCAN_HandleTypeDef *hfdcan)
{
    // Accept-all standard IDs into RX FIFO0 (you can tighten later by changing this filter).
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

    // Non-matching frames: accept to FIFO0 for now. Reject remote frames.
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
    s_tick_1khz_pending = 1;
}

bool CANFD_Utils_Consume1kHzTick(void)
{
    if (s_tick_1khz_pending) {
        s_tick_1khz_pending = 0;
        return true;
    }
    return false;
}

bool CANFD_Utils_SendMotorTxPDO(FDCAN_HandleTypeDef *hfdcan, uint32_t std_id, const Motor_TxPDO_t *pdo)
{
    uint8_t payload[48];
    memset(payload, 0, sizeof(payload));
    memcpy(payload, pdo, sizeof(*pdo));

    FDCAN_TxHeaderTypeDef tx = {0};
    tx.Identifier = std_id & 0x7FFU;
    tx.IdType = FDCAN_STANDARD_ID;
    tx.TxFrameType = FDCAN_DATA_FRAME;
    tx.DataLength = FDCAN_DLC_BYTES_48;
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

        // v2 -> v1: RxPDO frames are StdID 0x300..0x30E
        if ((sid >= V2_RXPDO_BASE_STDID) && (sid < (V2_RXPDO_BASE_STDID + NUM_MOTORS)))
        {
            g_rx_frames_rxpdo++;
            Motor_RxPDO_t cmd;
            memset(&cmd, 0, sizeof(cmd));
            memcpy(&cmd, rx_data, sizeof(cmd)); // 24 bytes

            uint32_t idx = (uint32_t)(sid - V2_RXPDO_BASE_STDID);
            if (cmd.motor_id < NUM_MOTORS) {
                idx = cmd.motor_id;
            }
            g_robot_output.motor[idx] = cmd; // update global robot output (ISR)
            continue;
        }

        // Unknown/other frame: keep last_rx for debugging only.
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


