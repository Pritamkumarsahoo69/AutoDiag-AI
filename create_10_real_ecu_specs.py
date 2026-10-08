"""Generate 10 diverse real-world automotive ECU diagnostic specifications for empirical benchmarking.

Covers 10 major automotive vehicle domains:
1. Engine Control Module (ECM / Powertrain)
2. Transmission Control Unit (TCU)
3. Battery Management System (BMS - EV High Voltage)
4. Motor Inverter Controller (MCU - EV Traction)
5. Electronic Stability Program (ESP / ABS Braking)
6. Electric Power Steering (EPS)
7. Body Control Module (BCM)
8. Airbag Supplemental Restraint System (SRS)
9. Telematics & Central Gateway (T-Box / CGW)
10. ADAS Forward Camera & Radar Unit
"""

import json
import os

SPECS_DIR = os.path.join(os.path.dirname(__file__), "sample_specs")
os.makedirs(SPECS_DIR, exist_ok=True)

ECU_SPECS = [
    # 1. Engine Control Module (Powertrain)
    {
        "filename": "01_engine_ecu_pcm.json",
        "data": {
            "ecu_name": "Engine_Control_Module_PCM",
            "can_request_id": "0x7E0", "can_response_id": "0x7E8", "can_functional_id": "0x7DF",
            "p2_server_max_ms": 50, "p2_star_server_max_ms": 5000, "s3_server_timeout_ms": 5000,
            "security_seed_key_mask": 0xAA,
            "services": [
                {"service_id": 16, "name": "DiagnosticSessionControl", "supported_subfunctions": [1, 2, 3], "allowed_sessions": ["DEFAULT", "EXTENDED", "PROGRAMMING"]},
                {"service_id": 17, "name": "ECUReset", "supported_subfunctions": [1, 2, 3], "allowed_sessions": ["DEFAULT", "EXTENDED", "PROGRAMMING"]},
                {"service_id": 34, "name": "ReadDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 39, "name": "SecurityAccess", "supported_subfunctions": [1, 2, 3, 4], "allowed_sessions": ["EXTENDED", "PROGRAMMING"]},
                {"service_id": 46, "name": "WriteDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 49, "name": "RoutineControl", "supported_subfunctions": [1, 2, 3], "allowed_sessions": ["EXTENDED", "PROGRAMMING"], "requires_security": True, "security_level": 1},
                {"service_id": 20, "name": "ClearDiagnosticInformation", "supported_subfunctions": [], "allowed_sessions": ["EXTENDED"]},
                {"service_id": 25, "name": "ReadDTCInformation", "supported_subfunctions": [1, 2, 10], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 62, "name": "TesterPresent", "supported_subfunctions": [0, 128], "allowed_sessions": ["DEFAULT", "EXTENDED", "PROGRAMMING"]}
            ],
            "dids": [
                {"did_hex": "0xF190", "name": "VIN", "length_bytes": 17, "data_type": "ASCII", "access": "READ_ONLY", "default_value": "WAUZZZ4G1EN012345", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0xF187", "name": "PartNumber", "length_bytes": 11, "data_type": "ASCII", "access": "READ_ONLY", "default_value": "06L907115AB", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0100", "name": "EngineRPM", "length_bytes": 2, "data_type": "UINT16", "access": "READ_ONLY", "default_value": "0BB8", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0101", "name": "CoolantTemp", "length_bytes": 1, "data_type": "UINT8", "access": "READ_ONLY", "default_value": "5A", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0200", "name": "IdleSpeedCalib", "length_bytes": 2, "data_type": "UINT16", "access": "READ_WRITE", "default_value": "0320", "security_level": 1, "allowed_sessions": ["EXTENDED"]}
            ],
            "routines": [
                {"routine_id": "0x0201", "name": "EraseFlashSector", "supported_subfunctions": [1, 3], "start_payload_length": 4, "allowed_sessions": ["PROGRAMMING"], "requires_security": True, "security_level": 1}
            ]
        }
    },
    # 2. Transmission Control Unit (TCU)
    {
        "filename": "02_transmission_tcu.json",
        "data": {
            "ecu_name": "Transmission_Control_Unit_TCU",
            "can_request_id": "0x7E1", "can_response_id": "0x7E9", "can_functional_id": "0x7DF",
            "p2_server_max_ms": 50, "p2_star_server_max_ms": 5000, "s3_server_timeout_ms": 5000,
            "security_seed_key_mask": 0xBB,
            "services": [
                {"service_id": 16, "name": "DiagnosticSessionControl", "supported_subfunctions": [1, 2, 3], "allowed_sessions": ["DEFAULT", "EXTENDED", "PROGRAMMING"]},
                {"service_id": 34, "name": "ReadDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 39, "name": "SecurityAccess", "supported_subfunctions": [1, 2], "allowed_sessions": ["EXTENDED"]},
                {"service_id": 46, "name": "WriteDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 49, "name": "RoutineControl", "supported_subfunctions": [1, 3], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 62, "name": "TesterPresent", "supported_subfunctions": [0, 128], "allowed_sessions": ["DEFAULT", "EXTENDED"]}
            ],
            "dids": [
                {"did_hex": "0xF190", "name": "VIN", "length_bytes": 17, "data_type": "ASCII", "access": "READ_ONLY", "default_value": "WAUZZZ4G1EN012345", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0300", "name": "GearPosition", "length_bytes": 1, "data_type": "UINT8", "access": "READ_ONLY", "default_value": "04", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0301", "name": "ClutchTemp", "length_bytes": 1, "data_type": "UINT8", "access": "READ_ONLY", "default_value": "50", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0305", "name": "ClutchKissPointCalib", "length_bytes": 4, "data_type": "HEX", "access": "READ_WRITE", "default_value": "00120034", "security_level": 1, "allowed_sessions": ["EXTENDED"]}
            ],
            "routines": [
                {"routine_id": "0x0310", "name": "ClutchAdaptationRoutine", "supported_subfunctions": [1, 3], "start_payload_length": 2, "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1}
            ]
        }
    },
    # 3. Battery Management System (BMS - EV High Voltage)
    {
        "filename": "03_battery_management_bms.json",
        "data": {
            "ecu_name": "Battery_Management_System_BMS",
            "can_request_id": "0x7E2", "can_response_id": "0x7EA", "can_functional_id": "0x7DF",
            "p2_server_max_ms": 50, "p2_star_server_max_ms": 5000, "s3_server_timeout_ms": 5000,
            "security_seed_key_mask": 0xCC,
            "services": [
                {"service_id": 16, "name": "DiagnosticSessionControl", "supported_subfunctions": [1, 3], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 34, "name": "ReadDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 39, "name": "SecurityAccess", "supported_subfunctions": [1, 2], "allowed_sessions": ["EXTENDED"]},
                {"service_id": 46, "name": "WriteDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 49, "name": "RoutineControl", "supported_subfunctions": [1, 2, 3], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 20, "name": "ClearDiagnosticInformation", "supported_subfunctions": [], "allowed_sessions": ["EXTENDED"]},
                {"service_id": 25, "name": "ReadDTCInformation", "supported_subfunctions": [1, 2], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 62, "name": "TesterPresent", "supported_subfunctions": [0, 128], "allowed_sessions": ["DEFAULT", "EXTENDED"]}
            ],
            "dids": [
                {"did_hex": "0xF190", "name": "VIN", "length_bytes": 17, "data_type": "ASCII", "access": "READ_ONLY", "default_value": "5YJSA1E28MF012345", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0400", "name": "StateOfCharge_SOC", "length_bytes": 2, "data_type": "UINT16", "access": "READ_ONLY", "default_value": "1F40", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0401", "name": "PackVoltage", "length_bytes": 2, "data_type": "UINT16", "access": "READ_ONLY", "default_value": "0FA0", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0402", "name": "MaxCellTemp", "length_bytes": 1, "data_type": "UINT8", "access": "READ_ONLY", "default_value": "23", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0410", "name": "CellBalancingThreshold", "length_bytes": 2, "data_type": "UINT16", "access": "READ_WRITE", "default_value": "0E10", "security_level": 1, "allowed_sessions": ["EXTENDED"]}
            ],
            "routines": [
                {"routine_id": "0x0450", "name": "HighVoltageContactorOpenRoutine", "supported_subfunctions": [1, 3], "start_payload_length": 2, "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1}
            ]
        }
    },
    # 4. Motor Inverter Controller (MCU - EV Traction)
    {
        "filename": "04_inverter_motor_mcu.json",
        "data": {
            "ecu_name": "Inverter_Motor_Controller_MCU",
            "can_request_id": "0x7E3", "can_response_id": "0x7EB", "can_functional_id": "0x7DF",
            "p2_server_max_ms": 50, "p2_star_server_max_ms": 5000, "s3_server_timeout_ms": 5000,
            "security_seed_key_mask": 0xDD,
            "services": [
                {"service_id": 16, "name": "DiagnosticSessionControl", "supported_subfunctions": [1, 3], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 34, "name": "ReadDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 39, "name": "SecurityAccess", "supported_subfunctions": [1, 2], "allowed_sessions": ["EXTENDED"]},
                {"service_id": 46, "name": "WriteDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 49, "name": "RoutineControl", "supported_subfunctions": [1, 3], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 62, "name": "TesterPresent", "supported_subfunctions": [0, 128], "allowed_sessions": ["DEFAULT", "EXTENDED"]}
            ],
            "dids": [
                {"did_hex": "0xF190", "name": "VIN", "length_bytes": 17, "data_type": "ASCII", "access": "READ_ONLY", "default_value": "5YJSA1E28MF012345", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0500", "name": "MotorSpeed_RPM", "length_bytes": 2, "data_type": "UINT16", "access": "READ_ONLY", "default_value": "1770", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0501", "name": "InverterIGBTTemp", "length_bytes": 1, "data_type": "UINT8", "access": "READ_ONLY", "default_value": "3C", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0510", "name": "MaxTorqueLimit", "length_bytes": 2, "data_type": "UINT16", "access": "READ_WRITE", "default_value": "01C2", "security_level": 1, "allowed_sessions": ["EXTENDED"]}
            ],
            "routines": [
                {"routine_id": "0x0520", "name": "RotorPositionResolverCalibration", "supported_subfunctions": [1, 3], "start_payload_length": 2, "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1}
            ]
        }
    },
    # 5. Electronic Stability Program (ESP / ABS Braking)
    {
        "filename": "05_electronic_brake_esp_abs.json",
        "data": {
            "ecu_name": "Electronic_Stability_Program_ESP",
            "can_request_id": "0x7E4", "can_response_id": "0x7EC", "can_functional_id": "0x7DF",
            "p2_server_max_ms": 50, "p2_star_server_max_ms": 5000, "s3_server_timeout_ms": 5000,
            "security_seed_key_mask": 0xEE,
            "services": [
                {"service_id": 16, "name": "DiagnosticSessionControl", "supported_subfunctions": [1, 3], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 34, "name": "ReadDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 39, "name": "SecurityAccess", "supported_subfunctions": [1, 2], "allowed_sessions": ["EXTENDED"]},
                {"service_id": 46, "name": "WriteDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 49, "name": "RoutineControl", "supported_subfunctions": [1, 3], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 20, "name": "ClearDiagnosticInformation", "supported_subfunctions": [], "allowed_sessions": ["EXTENDED"]},
                {"service_id": 25, "name": "ReadDTCInformation", "supported_subfunctions": [1, 2], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 62, "name": "TesterPresent", "supported_subfunctions": [0, 128], "allowed_sessions": ["DEFAULT", "EXTENDED"]}
            ],
            "dids": [
                {"did_hex": "0xF190", "name": "VIN", "length_bytes": 17, "data_type": "ASCII", "access": "READ_ONLY", "default_value": "WBA3A5C50DF012345", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0600", "name": "WheelSpeed_FL", "length_bytes": 2, "data_type": "UINT16", "access": "READ_ONLY", "default_value": "03E8", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0601", "name": "MasterCylinderBrakePressure", "length_bytes": 2, "data_type": "UINT16", "access": "READ_ONLY", "default_value": "0028", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0610", "name": "BrakeBleedModeConfig", "length_bytes": 1, "data_type": "HEX", "access": "READ_WRITE", "default_value": "01", "security_level": 1, "allowed_sessions": ["EXTENDED"]}
            ],
            "routines": [
                {"routine_id": "0x0620", "name": "AutomatedHydraulicBrakeBleed", "supported_subfunctions": [1, 3], "start_payload_length": 2, "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1}
            ]
        }
    },
    # 6. Electric Power Steering (EPS)
    {
        "filename": "06_electric_power_steering_eps.json",
        "data": {
            "ecu_name": "Electric_Power_Steering_EPS",
            "can_request_id": "0x7E5", "can_response_id": "0x7ED", "can_functional_id": "0x7DF",
            "p2_server_max_ms": 50, "p2_star_server_max_ms": 5000, "s3_server_timeout_ms": 5000,
            "security_seed_key_mask": 0x12,
            "services": [
                {"service_id": 16, "name": "DiagnosticSessionControl", "supported_subfunctions": [1, 3], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 34, "name": "ReadDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 39, "name": "SecurityAccess", "supported_subfunctions": [1, 2], "allowed_sessions": ["EXTENDED"]},
                {"service_id": 46, "name": "WriteDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 49, "name": "RoutineControl", "supported_subfunctions": [1, 3], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 62, "name": "TesterPresent", "supported_subfunctions": [0, 128], "allowed_sessions": ["DEFAULT", "EXTENDED"]}
            ],
            "dids": [
                {"did_hex": "0xF190", "name": "VIN", "length_bytes": 17, "data_type": "ASCII", "access": "READ_ONLY", "default_value": "WBA3A5C50DF012345", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0700", "name": "SteeringAngle", "length_bytes": 2, "data_type": "UINT16", "access": "READ_ONLY", "default_value": "0000", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0701", "name": "SteeringTorqueSensor", "length_bytes": 2, "data_type": "UINT16", "access": "READ_ONLY", "default_value": "001A", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0710", "name": "AssistMapCurveIndex", "length_bytes": 1, "data_type": "UINT8", "access": "READ_WRITE", "default_value": "02", "security_level": 1, "allowed_sessions": ["EXTENDED"]}
            ],
            "routines": [
                {"routine_id": "0x0720", "name": "SteeringAngleSensorZeroCalibration", "supported_subfunctions": [1, 3], "start_payload_length": 2, "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1}
            ]
        }
    },
    # 7. Body Control Module (BCM)
    {
        "filename": "07_body_control_module_bcm.json",
        "data": {
            "ecu_name": "Body_Control_Module_BCM",
            "can_request_id": "0x7E6", "can_response_id": "0x7EE", "can_functional_id": "0x7DF",
            "p2_server_max_ms": 50, "p2_star_server_max_ms": 5000, "s3_server_timeout_ms": 5000,
            "security_seed_key_mask": 0x34,
            "services": [
                {"service_id": 16, "name": "DiagnosticSessionControl", "supported_subfunctions": [1, 3], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 34, "name": "ReadDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 39, "name": "SecurityAccess", "supported_subfunctions": [1, 2], "allowed_sessions": ["EXTENDED"]},
                {"service_id": 46, "name": "WriteDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 62, "name": "TesterPresent", "supported_subfunctions": [0, 128], "allowed_sessions": ["DEFAULT", "EXTENDED"]}
            ],
            "dids": [
                {"did_hex": "0xF190", "name": "VIN", "length_bytes": 17, "data_type": "ASCII", "access": "READ_ONLY", "default_value": "1FATP8FF1M5012345", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0800", "name": "DoorAjarStatus", "length_bytes": 1, "data_type": "HEX", "access": "READ_ONLY", "default_value": "00", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0801", "name": "HeadlampSwitchPosition", "length_bytes": 1, "data_type": "UINT8", "access": "READ_ONLY", "default_value": "02", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0810", "name": "AutoLockSpeedThreshold", "length_bytes": 1, "data_type": "UINT8", "access": "READ_WRITE", "default_value": "0F", "security_level": 1, "allowed_sessions": ["EXTENDED"]}
            ],
            "routines": [
                {"routine_id": "0x0820", "name": "WiperParkPositionReset", "supported_subfunctions": [1, 3], "start_payload_length": 2, "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1}
            ]
        }
    },
    # 8. Airbag Supplemental Restraint System (SRS)
    {
        "filename": "08_airbag_restraint_srs.json",
        "data": {
            "ecu_name": "Airbag_Restraint_System_SRS",
            "can_request_id": "0x7E7", "can_response_id": "0x7EF", "can_functional_id": "0x7DF",
            "p2_server_max_ms": 50, "p2_star_server_max_ms": 5000, "s3_server_timeout_ms": 5000,
            "security_seed_key_mask": 0x56,
            "services": [
                {"service_id": 16, "name": "DiagnosticSessionControl", "supported_subfunctions": [1, 3, 4], "allowed_sessions": ["DEFAULT", "EXTENDED", "SAFETY_SYSTEM"]},
                {"service_id": 34, "name": "ReadDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["DEFAULT", "EXTENDED", "SAFETY_SYSTEM"]},
                {"service_id": 39, "name": "SecurityAccess", "supported_subfunctions": [1, 2], "allowed_sessions": ["EXTENDED", "SAFETY_SYSTEM"]},
                {"service_id": 20, "name": "ClearDiagnosticInformation", "supported_subfunctions": [], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 25, "name": "ReadDTCInformation", "supported_subfunctions": [1, 2], "allowed_sessions": ["DEFAULT", "EXTENDED", "SAFETY_SYSTEM"]},
                {"service_id": 62, "name": "TesterPresent", "supported_subfunctions": [0, 128], "allowed_sessions": ["DEFAULT", "EXTENDED", "SAFETY_SYSTEM"]}
            ],
            "dids": [
                {"did_hex": "0xF190", "name": "VIN", "length_bytes": 17, "data_type": "ASCII", "access": "READ_ONLY", "default_value": "1FATP8FF1M5012345", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED", "SAFETY_SYSTEM"]},
                {"did_hex": "0x0900", "name": "CrashEventLogCounter", "length_bytes": 1, "data_type": "UINT8", "access": "READ_ONLY", "default_value": "00", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED", "SAFETY_SYSTEM"]},
                {"did_hex": "0x0901", "name": "DriverBeltBuckleStatus", "length_bytes": 1, "data_type": "UINT8", "access": "READ_ONLY", "default_value": "01", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED", "SAFETY_SYSTEM"]}
            ],
            "routines": [
                {"routine_id": "0x0910", "name": "SquibLoopResistanceSelfTest", "supported_subfunctions": [1, 3], "start_payload_length": 2, "allowed_sessions": ["SAFETY_SYSTEM"], "requires_security": True, "security_level": 1}
            ]
        }
    },
    # 9. Telematics & Central Gateway (T-Box / CGW)
    {
        "filename": "09_telematics_gateway_tbox.json",
        "data": {
            "ecu_name": "Telematics_Gateway_TBox",
            "can_request_id": "0x710", "can_response_id": "0x718", "can_functional_id": "0x7DF",
            "p2_server_max_ms": 50, "p2_star_server_max_ms": 5000, "s3_server_timeout_ms": 5000,
            "security_seed_key_mask": 0x78,
            "services": [
                {"service_id": 16, "name": "DiagnosticSessionControl", "supported_subfunctions": [1, 2, 3], "allowed_sessions": ["DEFAULT", "EXTENDED", "PROGRAMMING"]},
                {"service_id": 34, "name": "ReadDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 39, "name": "SecurityAccess", "supported_subfunctions": [1, 2], "allowed_sessions": ["EXTENDED", "PROGRAMMING"]},
                {"service_id": 46, "name": "WriteDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 49, "name": "RoutineControl", "supported_subfunctions": [1, 3], "allowed_sessions": ["EXTENDED", "PROGRAMMING"], "requires_security": True, "security_level": 1},
                {"service_id": 62, "name": "TesterPresent", "supported_subfunctions": [0, 128], "allowed_sessions": ["DEFAULT", "EXTENDED", "PROGRAMMING"]}
            ],
            "dids": [
                {"did_hex": "0xF190", "name": "VIN", "length_bytes": 17, "data_type": "ASCII", "access": "READ_ONLY", "default_value": "KMHE341CBLA012345", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0A00", "name": "CellularSignalStrength", "length_bytes": 1, "data_type": "UINT8", "access": "READ_ONLY", "default_value": "1C", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0A01", "name": "GPSLocation", "length_bytes": 8, "data_type": "HEX", "access": "READ_ONLY", "default_value": "02540B2005080E40", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0A10", "name": "OTAServerBackendURLConfig", "length_bytes": 16, "data_type": "ASCII", "access": "READ_WRITE", "default_value": "ota.oemcloud.com", "security_level": 1, "allowed_sessions": ["EXTENDED"]}
            ],
            "routines": [
                {"routine_id": "0x0A20", "name": "TriggerOTAImageVerification", "supported_subfunctions": [1, 3], "start_payload_length": 4, "allowed_sessions": ["PROGRAMMING"], "requires_security": True, "security_level": 1}
            ]
        }
    },
    # 10. ADAS Forward Camera & Radar Unit
    {
        "filename": "10_adas_camera_radar.json",
        "data": {
            "ecu_name": "ADAS_Forward_Camera_Radar",
            "can_request_id": "0x720", "can_response_id": "0x728", "can_functional_id": "0x7DF",
            "p2_server_max_ms": 50, "p2_star_server_max_ms": 5000, "s3_server_timeout_ms": 5000,
            "security_seed_key_mask": 0x99,
            "services": [
                {"service_id": 16, "name": "DiagnosticSessionControl", "supported_subfunctions": [1, 3], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 34, "name": "ReadDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"service_id": 39, "name": "SecurityAccess", "supported_subfunctions": [1, 2], "allowed_sessions": ["EXTENDED"]},
                {"service_id": 46, "name": "WriteDataByIdentifier", "supported_subfunctions": [], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 49, "name": "RoutineControl", "supported_subfunctions": [1, 3], "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1},
                {"service_id": 62, "name": "TesterPresent", "supported_subfunctions": [0, 128], "allowed_sessions": ["DEFAULT", "EXTENDED"]}
            ],
            "dids": [
                {"did_hex": "0xF190", "name": "VIN", "length_bytes": 17, "data_type": "ASCII", "access": "READ_ONLY", "default_value": "KMHE341CBLA012345", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0B00", "name": "LaneDepartureStatus", "length_bytes": 1, "data_type": "UINT8", "access": "READ_ONLY", "default_value": "00", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0B01", "name": "ForwardObstacleDistance", "length_bytes": 2, "data_type": "UINT16", "access": "READ_ONLY", "default_value": "01F4", "security_level": 0, "allowed_sessions": ["DEFAULT", "EXTENDED"]},
                {"did_hex": "0x0B10", "name": "CameraOpticalPitchYawRollOffset", "length_bytes": 6, "data_type": "HEX", "access": "READ_WRITE", "default_value": "000000000000", "security_level": 1, "allowed_sessions": ["EXTENDED"]}
            ],
            "routines": [
                {"routine_id": "0x0B20", "name": "DynamicServiceCameraAlignmentCalibration", "supported_subfunctions": [1, 3], "start_payload_length": 4, "allowed_sessions": ["EXTENDED"], "requires_security": True, "security_level": 1}
            ]
        }
    }
]

for item in ECU_SPECS:
    filepath = os.path.join(SPECS_DIR, item["filename"])
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(item["data"], f, indent=2)
    print(f"Created real-world ECU spec: {filepath}")

print(f"\n[+] Successfully generated all {len(ECU_SPECS)} real-world automotive ECU specifications!")
