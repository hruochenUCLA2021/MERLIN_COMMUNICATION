from merlin_hand_master.MerlinEthercatMaster import MerlinMaster_v1
import time 

master = MerlinMaster_v1(ifname="enp63s0", slave_pos=0, num_motors=18)
# master = MerlinMaster_v1(ifname="enx000ec676fcd0", slave_pos=0, num_motors=18)

# Enable torque and set a position goal for motor 0
master.set_motor_goals(
    0,
    torque_enable=1,
    goal_position=1.57,  # rad
)

time.sleep(0.1)  # let a few PDO cycles run

state0 = master.get_motor_state(0)
print(state0)

# Example SDO config access (indices must match your firmware / ESI file!)
# master.sdo_write_f32(0x8000, value=0.001, subindex=1)  # e.g. p_gain_id
# gain = master.sdo_read_f32(0x8000, subindex=1)

master.close()