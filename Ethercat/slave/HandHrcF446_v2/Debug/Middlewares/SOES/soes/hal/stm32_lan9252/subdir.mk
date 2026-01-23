################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (13.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Middlewares/SOES/soes/hal/stm32_lan9252/esc_hw.c 

OBJS += \
./Middlewares/SOES/soes/hal/stm32_lan9252/esc_hw.o 

C_DEPS += \
./Middlewares/SOES/soes/hal/stm32_lan9252/esc_hw.d 


# Each subdirectory must supply rules for building sources it contributes
Middlewares/SOES/soes/hal/stm32_lan9252/%.o Middlewares/SOES/soes/hal/stm32_lan9252/%.su Middlewares/SOES/soes/hal/stm32_lan9252/%.cyclo: ../Middlewares/SOES/soes/hal/stm32_lan9252/%.c Middlewares/SOES/soes/hal/stm32_lan9252/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m4 -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32F446xx -c -I../Core/Inc -I"/home/hrc/STM32CubeIDE/workspace_1.19.0/HandHrcF446_v2/Middlewares/SOES/soes" -I"/home/hrc/STM32CubeIDE/workspace_1.19.0/HandHrcF446_v2/Middlewares/SOES/soes/hal/stm32_lan9252" -I"/home/hrc/STM32CubeIDE/workspace_1.19.0/HandHrcF446_v2/Middlewares/SOES/soes/include/sys/gcc" -I"/home/hrc/STM32CubeIDE/workspace_1.19.0/HandHrcF446_v2/Middlewares" -I../Drivers/STM32F4xx_HAL_Driver/Inc -I../Drivers/STM32F4xx_HAL_Driver/Inc/Legacy -I../Drivers/CMSIS/Device/ST/STM32F4xx/Include -I../Drivers/CMSIS/Include -O2 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Middlewares-2f-SOES-2f-soes-2f-hal-2f-stm32_lan9252

clean-Middlewares-2f-SOES-2f-soes-2f-hal-2f-stm32_lan9252:
	-$(RM) ./Middlewares/SOES/soes/hal/stm32_lan9252/esc_hw.cyclo ./Middlewares/SOES/soes/hal/stm32_lan9252/esc_hw.d ./Middlewares/SOES/soes/hal/stm32_lan9252/esc_hw.o ./Middlewares/SOES/soes/hal/stm32_lan9252/esc_hw.su

.PHONY: clean-Middlewares-2f-SOES-2f-soes-2f-hal-2f-stm32_lan9252

