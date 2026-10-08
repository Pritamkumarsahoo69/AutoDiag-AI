"""Diagnostic Specification Parser supporting JSON, ODX-D XML, and PDF documents."""

import json
import os
import re
from typing import Optional
from autodiag.api.schemas import (
    DIDSpec,
    DiagnosticDatabase,
    DiagnosticServiceSpec,
    RoutineSpec,
)


class SpecParser:
    """Multi-format diagnostic specification parser."""

    @staticmethod
    def parse_file(file_path: str) -> DiagnosticDatabase:
        """Parse file according to its extension (.json, .xml, .odx, .pdf, .txt)."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Specification file not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return DiagnosticDatabase(**data)

        elif ext in (".xml", ".odx"):
            return SpecParser._parse_odx_xml(file_path)

        elif ext == ".pdf":
            return SpecParser._parse_pdf(file_path)

        elif ext in (".txt", ".md"):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return SpecParser.parse_raw_text(content, os.path.basename(file_path))

        else:
            # Fallback: try parsing as JSON
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return DiagnosticDatabase(**data)

    @staticmethod
    def _parse_pdf(file_path: str) -> DiagnosticDatabase:
        """Extract text from PDF using pypdf and build DiagnosticDatabase."""
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            full_text = "\n".join([page.extract_text() or "" for page in reader.pages])
            return SpecParser.parse_raw_text(full_text, os.path.basename(file_path))
        except Exception:
            # Fallback to default schema if empty or unparseable
            return DiagnosticDatabase(ecu_name=os.path.splitext(os.path.basename(file_path))[0])

    @staticmethod
    def _parse_odx_xml(file_path: str) -> DiagnosticDatabase:
        """Extract services and DIDs from ODX-D XML structures."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return SpecParser.parse_raw_text(content, os.path.basename(file_path))

    @staticmethod
    def parse_raw_text(text: str, source_name: str = "Imported_Spec") -> DiagnosticDatabase:
        """Heuristic regex-based extraction from unstructured text/ODX/PDF."""
        ecu_name = re.sub(r"[^a-zA-Z0-9_]", "_", os.path.splitext(source_name)[0])
        db = DiagnosticDatabase(ecu_name=ecu_name)

        # 1. Extract Services (e.g. Service 0x22 or SID $22)
        service_matches = re.findall(r"(?:Service|SID)\s*[:=]?\s*(?:0x|\$)?([0-9A-Fa-f]{2})\b", text, re.IGNORECASE)
        found_sids = set()
        for sid_hex in service_matches:
            sid_int = int(sid_hex, 16)
            if sid_int not in found_sids:
                found_sids.add(sid_int)
                db.services.append(DiagnosticServiceSpec(
                    service_id=sid_int,
                    name=f"Service_0x{sid_int:02X}",
                    allowed_sessions=["DEFAULT", "EXTENDED", "PROGRAMMING"]
                ))

        # Always ensure core services exist if not found
        if not db.services:
            db.services = [
                DiagnosticServiceSpec(service_id=0x10, name="DiagnosticSessionControl", supported_subfunctions=[1, 2, 3]),
                DiagnosticServiceSpec(service_id=0x22, name="ReadDataByIdentifier"),
                DiagnosticServiceSpec(service_id=0x27, name="SecurityAccess", supported_subfunctions=[1, 2]),
                DiagnosticServiceSpec(service_id=0x2E, name="WriteDataByIdentifier", requires_security=True, security_level=1),
                DiagnosticServiceSpec(service_id=0x3E, name="TesterPresent", supported_subfunctions=[0, 128])
            ]

        # 2. Extract DIDs (e.g. DID 0xF190 VIN 17 bytes)
        did_matches = re.findall(r"(?:DID|Identifier)\s*[:=]?\s*(?:0x|\$)?([0-9A-Fa-f]{4})\s+([A-Za-z0-9_]+)", text, re.IGNORECASE)
        found_dids = set()
        for did_hex, did_name in did_matches:
            did_key = f"0x{did_hex.upper()}"
            if did_key not in found_dids:
                found_dids.add(did_key)
                db.dids.append(DIDSpec(
                    did_hex=did_key,
                    name=did_name,
                    length_bytes=4,
                    data_type="ASCII",
                    access="READ_ONLY",
                    default_value="00000000"
                ))

        # 3. Extract Routines (e.g. Routine 0x0201 EraseFlashMemory or RID 0x0310)
        routine_matches = re.findall(r"(?:Routine|RID|RoutineControl)\s*[:=]?\s*(?:0x|\$)?([0-9A-Fa-f]{4})\s+([A-Za-z0-9_]+)", text, re.IGNORECASE)
        found_rids = set()
        for rid_hex, rid_name in routine_matches:
            rid_key = f"0x{rid_hex.upper()}"
            if rid_key not in found_rids:
                found_rids.add(rid_key)
                db.routines.append(RoutineSpec(
                    routine_id=rid_key,
                    name=rid_name,
                    supported_subfunctions=[1, 3],
                    start_payload_length=4,
                    allowed_sessions=["EXTENDED", "PROGRAMMING"],
                    requires_security=True,
                    security_level=1,
                    description=f"Diagnostic routine {rid_name} ({rid_key}) extracted from specification"
                ))

        # If no DIDs extracted, provide default base set
        if not db.dids:
            db.dids = [
                DIDSpec(did_hex="0xF190", name="VIN", length_bytes=17, data_type="ASCII", default_value="WVWZZZ3CZWE123456"),
                DIDSpec(did_hex="0xF187", name="PartNumber", length_bytes=11, data_type="ASCII", default_value="ECU-990-2026"),
                DIDSpec(did_hex="0x0100", name="EngineRPM", length_bytes=2, data_type="UINT16", default_value="0DAC")
            ]

        # If no Routines extracted, provide standard base routine
        if not db.routines:
            db.routines = [
                RoutineSpec(
                    routine_id="0x0201",
                    name="EraseFlashMemory",
                    supported_subfunctions=[1, 3],
                    start_payload_length=4,
                    allowed_sessions=["PROGRAMMING"],
                    requires_security=True,
                    security_level=1,
                    description="Erases application flash sector before reprogramming"
                )
            ]

        return db
