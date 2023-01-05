# Deye solar inverter MQTT bridge

Reads Deye solar inverter metrics using Modbus over TCP and publishes them over MQTT.

Tested with:
* [Deye SUN-4K-G05](https://www.deyeinverter.com/product/three-phase-string-inverter/sun4-5-6-7-8-10kg03.html) and Logger S/N 23xxxxxxxx
* [Deye SUN1300G3](https://www.deyeinverter.com/product/microinverter-1/sun13002000g3eu230.html) and Logger S/N 41xxxxxxxx

Supported metrics:

|Metric|Modbus address|MQTT topic suffix|Unit|
|---|:-:|---|:-:|
|Production today|0x3c|`day_energy`|kWh|
|Uptime|0x3e|`uptime`|minutes|
|AC Phase 1 voltage|0x49|`ac/l1/voltage`|V|
|AC Phase 2 voltage|0x4a|`ac/l2/voltage`|V|
|AC Phase 3 voltage|0x4b|`ac/l3/voltage`|V|
|AC Phase 1 current|0x4c|`ac/l1/current`|A|
|AC Phase 2 current|0x4d|`ac/l2/current`|A|
|AC Phase 3 current|0x4e|`ac/l3/current`|A|
|AC Frequency|0x4f|`ac/freq`|Hz|
|Operating power|0x50|`operating_power`|W|
|DC total power|0x52|`dc/total_power`|W|
|AC apparent power|0x54|`ac/apparent_power`|W|
|AC active power|0x56|`ac/active_power`|W|
|AC reactive power|0x58|`ac/reactive_power`|W|
|Radiator temperature|0x5a|`radiator_temp`|C|
|IGBT temperature|0x5b|`igbt_temp`|C|
|DC PV1 voltage|0x6d|`dc/pv1/voltage`|V|
|DC PV1 current|0x6e|`dc/pv1/current`|A|
|DC PV2 voltage|0x6f|`dc/pv2/voltage`|V|
|DC PV2 current|0x70|`dc/pv2/current`|A|
|DC PV3 voltage|0x71|`dc/pv3/voltage`|V|
|DC PV3 current|0x72|`dc/pv3/current`|A|
|DC PV4 voltage|0x73|`dc/pv4/voltage`|V|
|DC PV4 current|0x74|`dc/pv4/current`|A|


## Installation
1. Copy `config.env.example` as `config.env`
2. Fill in values in `config.env`
3. Run the container

    ```
    docker run --rm --env-file config.env ghcr.io/kbialek/deye-inverter-mqtt
    ```


## Configuration
All configuration options are controlled through environment variables.

* `LOG_LEVEL` - application log level, can be any of `DEBUG`, `INFO`, `WARN`, `ERROR`
* `DEYE_DATA_READ_INTERVAL` - interval between subsequent data reads, in seconds, defaults to 60
* `DEYE_LOGGER_SERIAL_NUMBER` - inverter data logger serial number
* `DEYE_LOGGER_IP_ADDRESS` - inverter data logger IP address
* `DEYE_LOGGER_PORT` - inverter data logger communication port, typically 8899
* `MQTT_HOST`
* `MQTT_PORT`
* `MQTT_USERNAME`
* `MQTT_PASSWORD`
* `MQTT_TOPIC_PREFIX` - mqtt topic prefix used for all inverter metrics

## Reading and writing raw register values
The tool allows reading and writing raw register values directly in the terminal.

**USE AT YOUR OWN RISK!** Be sure to know what you are doing. Writing invalid values may damage the inverter.
By using this tool you accept this risk and you take full responsiblity for the consequences.

* To read register value execute:
    ```
    docker run --rm --env-file config.env ghcr.io/kbialek/deye-inverter-mqtt r <reg_address>
    ```
    where `<reg_address>` is register address (decimal)

* To write register value execute:
    ```
    docker run --rm --env-file config.env ghcr.io/kbialek/deye-inverter-mqtt w <reg_address> <reg_value>
    ```
    where `<reg_address>` is register address (decimal), and <reg_value> is a value to set (decimal)

## Development
1. Install python dependencies
    ```
    pip install -r requirements.txt
    ```
1. Running the code
    1. Option 1 - Run the code locally without using Docker
        1. Fill in `config.env` file
        1. Execute `make run`
    1. Option 2 - Build a new docker image locally (for amd64 architecture)
        1. Execute `make docker-build-local`
        1. Fill in `config.env` file    
        1. Execute `make docker-run`
1. To run the tests use `make test`
    

