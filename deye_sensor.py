# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from abc import abstractmethod


class Sensor():
    """
    Models solar inverter sensor.

    This is an abstract class. Method 'read_value' must be provided by the extending subclass. 
    """

    def __init__(self, name: str, mqtt_topic_suffix='', print_format='{:s}', groups=[]):
        self.name = name
        self.mqtt_topic_suffix = mqtt_topic_suffix
        self.print_format = print_format
        self.groups = groups

    @abstractmethod
    def read_value(self, registers: dict[int, int]):
        """
        Reads sensor value from Modbus registers
        """
        pass

    def format_value(self, value):
        """
        Formats sensor value using configured format string
        """
        return self.print_format.format(value)

    def in_any_group(self, active_groups: set[str]) -> bool:
        """
        Checks if this sensor is included in at least one of the given active_groups.
        Sensor matches any group when its groups set is empty (default behavior)
        """
        return not self.groups or len(active_groups.intersection(self.groups)) > 0


class SingleRegisterSensor(Sensor):
    """
    Solar inverter sensor with value stored as 32-bit integer in a single Modbus register.
    """

    def __init__(
            self, name: str, reg_address: int, factor: float, offset: float = 0,
            mqtt_topic_suffix='', print_format='{:0.1f}', groups=[]):
        super().__init__(name, mqtt_topic_suffix, print_format, groups)
        self.reg_address = reg_address
        self.factor = factor
        self.offset = offset

    def read_value(self, registers: dict[int, int]):
        if self.reg_address in registers:
            reg_value = registers[self.reg_address]
            return int.from_bytes(reg_value, 'big') * self.factor + self.offset
        else:
            return None


class DoubleRegisterSensor(Sensor):
    """
    Solar inverter sensor with value stored as 64-bit integer in two Modbus registers.
    """

    def __init__(
            self, name: str, reg_address: int, factor: float, offset: float = 0,
            mqtt_topic_suffix='', print_format='{:0.1f}'):
        super().__init__(name, mqtt_topic_suffix, print_format)
        self.reg_address = reg_address
        self.factor = factor
        self.offset = offset

    def read_value(self, registers: dict[int, int]):
        low_word_reg_address = self.reg_address
        high_word_reg_address = self.reg_address + 1
        if low_word_reg_address in registers and high_word_reg_address in registers:
            low_word = registers[low_word_reg_address]
            high_word = registers[high_word_reg_address]
            return (int.from_bytes(high_word, 'big') * 65536 + int.from_bytes(low_word, 'big')) * self.factor + self.offset
        else:
            return None


class ComputedPowerSensor(Sensor):
    """
    Electric Power sensor with value computed as multiplication of valures reag by voltage and current sensors.
    """

    def __init__(
            self, name: str, voltage_sensor: Sensor, current_sensor: Sensor, mqtt_topic_suffix='',
            print_format='{:0.1f}', groups=[]):
        super().__init__(name, mqtt_topic_suffix, print_format, groups)
        self.voltage_sensor = voltage_sensor
        self.current_sensor = current_sensor

    def read_value(self, registers: dict[int, int]):
        voltage = self.voltage_sensor.read_value(registers)
        current = self.current_sensor.read_value(registers)
        if voltage is not None and current is not None:
            return voltage * current
        else:
            return None
