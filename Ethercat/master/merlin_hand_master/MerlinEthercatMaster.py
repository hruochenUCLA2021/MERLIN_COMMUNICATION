import threading
import struct
import time
from dataclasses import dataclass
from typing import Optional, List

import pysoem


@dataclass
class MotorCommand:
    """Command values sent from PC master to a single motor (RxPDO)."""

    torque_enable: int = 0
    goal_id: float = 0.0
    goal_iq: float = 0.0
    goal_velocity: float = 0.0
    goal_position: float = 0.0


@dataclass
class MotorState:
    """State values received from a single motor (TxPDO)."""

    present_id: float = 0.0
    present_iq: float = 0.0
    present_velocity: float = 0.0
    present_position: float = 0.0
    input_voltage: float = 0.0
    winding_temperature: float = 0.0
    powerstage_temperature: float = 0.0
    ic_temperature: float = 0.0
    error_status: float = 0.0


class MerlinMaster_v1:
    """
    EtherCAT master wrapper for the Merlin hand motors using PySOEM.

    One STM32-based slave controls 18 motors; this class talks to that slave
    via CoE SDOs (configuration registers) and PDOs (status/goal registers).

    Assumptions:
    - There is exactly one relevant EtherCAT slave at position `slave_pos`.
    - RxPDO layout (per motor, from PC -> slave):
        torque_enable   : uint32
        goal_id         : float32
        goal_iq         : float32
        goal_velocity   : float32
        goal_position   : float32
    - TxPDO layout (per motor, from slave -> PC):
        present_id, present_iq, present_velocity, present_position,
        input_voltage, winding_temperature, powerstage_temperature,
        ic_temperature, error_status : all float32

    These layouts must match the STM32 / ESC firmware PDO mapping.
    """

    # EtherCAT PDO layout sizes (bytes per motor)
    _RXPDO_STRUCT = struct.Struct("<Iffff")          # 1x uint32 + 4x float32 = 20 bytes
    _TXPDO_STRUCT = struct.Struct("<fffffffff")      # 9x float32 = 36 bytes

    def __init__(
        self,
        ifname: str,
        slave_pos: int = 0,
        ifname_red: Optional[str] = None,
        num_motors: int = 18,
        cycle_time_s: float = 0.001,
    ) -> None:
        """
        Create and fully initialize the EtherCAT master.

        - Opens the adapter
        - Finds and configures slaves
        - Maps PDOs
        - Brings network into OP state
        - Starts background process-data loop

        :param ifname: Network interface name (e.g. 'enx000ec676fcd0').
        :param slave_pos: Position of the STM32/ESC slave in the EtherCAT ring.
        :param ifname_red: Optional second interface for redundant topology.
        :param num_motors: Number of motors controlled by this slave (default 18).
        :param cycle_time_s: PDO update cycle time for the background thread.
        """
        self._ifname = ifname
        self._ifname_red = ifname_red
        self._slave_pos = slave_pos
        self._num_motors = num_motors
        self._cycle_time_s = cycle_time_s

        self._master = pysoem.Master()
        self._master.in_op = False
        self._master.do_check_state = False

        self._pd_thread_stop_event = threading.Event()
        self._actual_wkc = 0

        # Command and state buffers (one entry per motor)
        self._commands: List[MotorCommand] = [
            MotorCommand() for _ in range(self._num_motors)
        ]
        self._states: List[MotorState] = [
            MotorState() for _ in range(self._num_motors)
        ]

        # Master/slave initialization
        self._open_and_configure()
        self._start_processdata_loop()

    # -------------------------------------------------------------------------
    # Public high-level API
    # -------------------------------------------------------------------------

    @property
    def num_motors(self) -> int:
        return self._num_motors

    def close(self) -> None:
        """Stop background threads and close the master."""
        self._pd_thread_stop_event.set()
        if self._master.in_op:
            self._master.state = pysoem.INIT_STATE
            self._master.write_state()
        self._master.close()

    # -------------------- Motor command / state API --------------------------

    def set_motor_goals(
        self,
        motor_idx: int,
        *,
        torque_enable: Optional[int] = None,
        goal_id: Optional[float] = None,
        goal_iq: Optional[float] = None,
        goal_velocity: Optional[float] = None,
        goal_position: Optional[float] = None,
    ) -> None:
        """
        Update command values for a single motor. Changes are sent on the next PDO cycle.

        :param motor_idx: Motor index [0 .. num_motors-1].
        """
        self._check_motor_index(motor_idx)
        cmd = self._commands[motor_idx]

        if torque_enable is not None:
            cmd.torque_enable = int(torque_enable)
        if goal_id is not None:
            cmd.goal_id = float(goal_id)
        if goal_iq is not None:
            cmd.goal_iq = float(goal_iq)
        if goal_velocity is not None:
            cmd.goal_velocity = float(goal_velocity)
        if goal_position is not None:
            cmd.goal_position = float(goal_position)

    def get_motor_state(self, motor_idx: int) -> MotorState:
        """
        Return the last received state for a single motor.
        """
        self._check_motor_index(motor_idx)
        # Return a copy to avoid accidental modification.
        state = self._states[motor_idx]
        return MotorState(**vars(state))

    def get_all_states(self) -> List[MotorState]:
        """
        Return the last received state for all motors.
        """
        return [MotorState(**vars(s)) for s in self._states]

    # -------------------- Generic SDO access (configuration) -----------------

    def sdo_read_u32(self, index: int, subindex: int = 0) -> int:
        """
        Read an unsigned 32‑bit configuration value via SDO.
        """
        slave = self._master.slaves[self._slave_pos]
        data = slave.sdo_read(index=index, subindex=subindex)
        return struct.unpack("<I", data)[0]

    def sdo_write_u32(self, index: int, value: int, subindex: int = 0, complete_access: bool = False) -> None:
        """
        Write an unsigned 32‑bit configuration value via SDO.
        """
        slave = self._master.slaves[self._slave_pos]
        data = struct.pack("<I", int(value))
        slave.sdo_write(index=index, subindex=subindex, data=data, ca=complete_access)

    def sdo_read_f32(self, index: int, subindex: int = 0) -> float:
        """
        Read a 32‑bit float configuration value via SDO.
        """
        slave = self._master.slaves[self._slave_pos]
        data = slave.sdo_read(index=index, subindex=subindex)
        return struct.unpack("<f", data)[0]

    def sdo_write_f32(self, index: int, value: float, subindex: int = 0, complete_access: bool = False) -> None:
        """
        Write a 32‑bit float configuration value via SDO.
        """
        slave = self._master.slaves[self._slave_pos]
        data = struct.pack("<f", float(value))
        slave.sdo_write(index=index, subindex=subindex, data=data, ca=complete_access)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _check_motor_index(self, idx: int) -> None:
        if not (0 <= idx < self._num_motors):
            raise IndexError(f"motor_idx {idx} out of range [0, {self._num_motors - 1}]")

    def _open_and_configure(self) -> None:
        """
        Open the adapter, discover and configure slaves, map PDOs, and go to OP state.
        """
        self._master.open(self._ifname, self._ifname_red)

        # Discover/config slaves.
        if not self._master.config_init() > 0:
            self._master.close()
            raise RuntimeError("No EtherCAT slaves found on interface "
                               f"{self._ifname}")

        if self._slave_pos >= len(self._master.slaves):
            self._master.close()
            raise RuntimeError(
                f"Requested slave_pos {self._slave_pos}, but only "
                f"{len(self._master.slaves)} slaves were found"
            )

        # Here you could add vendor/product checks for the STM32/ESC slave.
        # slave = self._master.slaves[self._slave_pos]
        # if not (slave.man == EXPECTED_VENDOR and slave.id == EXPECTED_PRODUCT):
        #     raise RuntimeError("Unexpected slave at configured position")

        # PREOP -> SAFEOP, apply any config_func hooks.
        self._master.config_map()

        if self._master.state_check(pysoem.SAFEOP_STATE, timeout=50_000) != pysoem.SAFEOP_STATE:
            self._master.close()
            raise RuntimeError("Not all slaves reached SAFEOP state")

        # Enable DC sync on the target slave (optional but recommended).
        slave = self._master.slaves[self._slave_pos]
        # sync0_cycle_time is in ns; approximate from cycle_time_s.
        sync0_cycle_time_ns = int(self._cycle_time_s * 1e9)
        slave.dc_sync(act=True, sync0_cycle_time=sync0_cycle_time_ns)

        # SAFEOP -> OP
        self._master.state = pysoem.OP_STATE
        self._master.write_state()

        if self._master.state_check(pysoem.OP_STATE, timeout=50_000) != pysoem.OP_STATE:
            self._master.close()
            raise RuntimeError("Not all slaves reached OP state")

        self._master.in_op = True

    def _start_processdata_loop(self) -> None:
        """Start background thread for continuous PDO exchange."""
        self._pd_thread = threading.Thread(
            target=self._processdata_thread, name="MerlinPDO", daemon=True
        )
        self._pd_thread.start()

    def _processdata_thread(self) -> None:
        """
        Background thread:
        - Packs current MotorCommand list into the slave RxPDO (output buffer)
        - Exchanges process data
        - Unpacks slave TxPDO (input buffer) into MotorState list
        """
        slave = self._master.slaves[self._slave_pos]

        # Pre-allocate buffers.
        rxpdo_len = self._num_motors * self._RXPDO_STRUCT.size
        txpdo_len = self._num_motors * self._TXPDO_STRUCT.size

        while not self._pd_thread_stop_event.is_set():
            # Pack commands -> output bytes
            out_buf = bytearray(rxpdo_len)
            offset = 0
            for cmd in self._commands:
                out_buf[offset: offset + self._RXPDO_STRUCT.size] = self._RXPDO_STRUCT.pack(
                    cmd.torque_enable,
                    cmd.goal_id,
                    cmd.goal_iq,
                    cmd.goal_velocity,
                    cmd.goal_position,
                )
                offset += self._RXPDO_STRUCT.size
            slave.output = bytes(out_buf)

            # Exchange process data
            self._master.send_processdata()
            self._actual_wkc = self._master.receive_processdata(timeout=100_000)
            if self._actual_wkc != self._master.expected_wkc:
                # You may want to log or handle WKC mismatch here.
                pass

            # Unpack input bytes -> states
            in_buf = slave.input
            if len(in_buf) >= txpdo_len:
                offset = 0
                for i in range(self._num_motors):
                    (
                        present_id,
                        present_iq,
                        present_velocity,
                        present_position,
                        input_voltage,
                        winding_temperature,
                        powerstage_temperature,
                        ic_temperature,
                        error_status,
                    ) = self._TXPDO_STRUCT.unpack_from(in_buf, offset)
                    self._states[i] = MotorState(
                        present_id=present_id,
                        present_iq=present_iq,
                        present_velocity=present_velocity,
                        present_position=present_position,
                        input_voltage=input_voltage,
                        winding_temperature=winding_temperature,
                        powerstage_temperature=powerstage_temperature,
                        ic_temperature=ic_temperature,
                        error_status=error_status,
                    )
                    offset += self._TXPDO_STRUCT.size

            time.sleep(self._cycle_time_s)


__all__ = ["MerlinMaster_v1", "MotorCommand", "MotorState"]


