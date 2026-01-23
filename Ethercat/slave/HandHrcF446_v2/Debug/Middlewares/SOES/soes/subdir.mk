################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (13.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/SOES/soes/ecat_slv.c \
../Middlewares/SOES/soes/esc.c \
../Middlewares/SOES/soes/esc_coe.c \
../Middlewares/SOES/soes/esc_eep.c \
../Middlewares/SOES/soes/esc_eoe.c \
../Middlewares/SOES/soes/esc_foe.c 

OBJS += \
./Middlewares/SOES/soes/ecat_slv.o \
./Middlewares/SOES/soes/esc.o \
./Middlewares/SOES/soes/esc_coe.o \
./Middlewares/SOES/soes/esc_eep.o \
./Middlewares/SOES/soes/esc_eoe.o \
./Middlewares/SOES/soes/esc_foe.o 

C_DEPS += \
./Middlewares/SOES/soes/ecat_slv.d \
./Middlewares/SOES/soes/esc.d \
./Middlewares/SOES/soes/esc_coe.d \
./Middlewares/SOES/soes/esc_eep.d \
./Middlewares/SOES/soes/esc_eoe.d \
./Middlewares/SOES/soes/esc_foe.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/SOES/soes/%.o Middlewares/SOES/soes/%.su Middlewares/SOES/soes/%.cyclo: ../Middlewares/SOES/soes/%.c Middlewares/SOES/soes/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Core/Inc -I"/home/hrc/STM32CubeIDE/workspace_1.19.0/HandHrcF446_v2/Middlewares/SOES/soes" -I"/home/hrc/STM32CubeIDE/workspace_1.19.0/HandHrcF446_v2/Middlewares/SOES/soes/hal/stm32_lan9252" -I"/home/hrc/STM32CubeIDE/workspace_1.19.0/HandHrcF446_v2/Middlewares/SOES/soes/include/sys/gcc" -I"/home/hrc/STM32CubeIDE/workspace_1.19.0/HandHrcF446_v2/Middlewares" -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -O2 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-SOES-2f-soes

clean-Middlewares-2f-SOES-2f-soes:
	-$(RM) ./Middlewares/SOES/soes/ecat_slv.cyclo ./Middlewares/SOES/soes/ecat_slv.d ./Middlewares/SOES/soes/ecat_slv.o ./Middlewares/SOES/soes/ecat_slv.su ./Middlewares/SOES/soes/esc.cyclo ./Middlewares/SOES/soes/esc.d ./Middlewares/SOES/soes/esc.o ./Middlewares/SOES/soes/esc.su ./Middlewares/SOES/soes/esc_coe.cyclo ./Middlewares/SOES/soes/esc_coe.d ./Middlewares/SOES/soes/esc_coe.o ./Middlewares/SOES/soes/esc_coe.su ./Middlewares/SOES/soes/esc_eep.cyclo ./Middlewares/SOES/soes/esc_eep.d ./Middlewares/SOES/soes/esc_eep.o ./Middlewares/SOES/soes/esc_eep.su ./Middlewares/SOES/soes/esc_eoe.cyclo ./Middlewares/SOES/soes/esc_eoe.d ./Middlewares/SOES/soes/esc_eoe.o ./Middlewares/SOES/soes/esc_eoe.su ./Middlewares/SOES/soes/esc_foe.cyclo ./Middlewares/SOES/soes/esc_foe.d ./Middlewares/SOES/soes/esc_foe.o ./Middlewares/SOES/soes/esc_foe.su

.PHONY: clean-Middlewares-2f-SOES-2f-soes

