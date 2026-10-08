"""Diagnostic Knowledge Base with semantic chunking and grounded citation generation."""

import re
from typing import List, Optional
from autodiag.api.schemas import (
    CitationResult,
    DiagnosticDatabase,
    QueryResponse,
)


class DiagnosticKnowledgeBase:
    """Knowledge store for ISO 14229 standards and ECU specifications."""

    def __init__(self):
        self.chunks: List[dict] = []
        self.active_db: Optional[DiagnosticDatabase] = None
        self._load_standard_iso14229_knowledge()

    def _load_standard_iso14229_knowledge(self):
        """Preload standard ISO 14229 reference rules."""
        standard_docs = [
            {
                "section": "ISO 14229-1: Section 9.2 (DiagnosticSessionControl)",
                "source": "ISO_14229_Standard.pdf",
                "content": "Service $10 DiagnosticSessionControl enables different diagnostic sessions (0x01 Default, 0x02 Programming, 0x03 Extended). Transition to Programming typically requires prior Extended session and stops periodic transmissions. S3 timer (typically 5000ms) resets to default session unless TesterPresent ($3E) is sent."
            },
            {
                "section": "ISO 14229-1: Section 9.4 (SecurityAccess)",
                "source": "ISO_14229_Standard.pdf",
                "content": "Service $27 SecurityAccess provides a seed/key exchange mechanism. Odd subfunctions (0x01, 0x03) request a seed; even subfunctions (0x02, 0x04) send the computed key. 3 failed attempts results in NRC 0x36 (exceedNumberOfAttempts) and mandatory time delay penalty (NRC 0x37)."
            },
            {
                "section": "ISO 14229-1: Section 10.2 (ReadDataByIdentifier)",
                "source": "ISO_14229_Standard.pdf",
                "content": "Service $22 ReadDataByIdentifier retrieves one or more 2-byte Data Identifiers (DIDs). Request format: 22 <DID_High> <DID_Low>. Positive response: 62 <DID_High> <DID_Low> <DataRecord>. If DID is unknown, returns NRC 0x31 (requestOutOfRange)."
            },
            {
                "section": "ISO 14229-1: Section 10.5 (WriteDataByIdentifier)",
                "source": "ISO_14229_Standard.pdf",
                "content": "Service $2E WriteDataByIdentifier writes data into specified 2-byte DID. Requires Extended session and appropriate Security Access Level. Payload length must exactly match defined DID length or returns NRC 0x13 (incorrectMessageLengthOrInvalidFormat)."
            },
            {
                "section": "ISO 14229-1: Section 12.2 (RoutineControl)",
                "source": "ISO_14229_Standard.pdf",
                "content": "Service $31 RoutineControl controls ECU internal test sequences and routines (e.g. Flash Erase, Memory Checksum, Calibration). Subfunctions: 0x01 StartRoutine, 0x02 StopRoutine, 0x03 RequestRoutineResults."
            }
        ]
        self.chunks.extend(standard_docs)

    def load_database(self, db: DiagnosticDatabase, source_file: str = "engine_ecu_uds_spec.json"):
        """Index ECU specification objects into searchable chunks."""
        self.active_db = db

        # Index ECU General Metadata
        self.chunks.append({
            "section": f"{db.ecu_name} Overview",
            "source": source_file,
            "content": f"ECU: {db.ecu_name}, CAN Request ID: {db.can_request_id}, Response ID: {db.can_response_id}, P2 Max: {db.p2_server_max_ms}ms, S3 Timeout: {db.s3_server_timeout_ms}ms."
        })

        # Index Services
        for srv in db.services:
            self.chunks.append({
                "section": f"Service 0x{srv.service_id:02X} - {srv.name}",
                "source": source_file,
                "content": f"Service 0x{srv.service_id:02X} ({srv.name}): Allowed in sessions {srv.allowed_sessions}. Subfunctions: {srv.supported_subfunctions}. Security required: {srv.requires_security} (Level {srv.security_level}). {srv.description}"
            })

        # Index DIDs
        for did in db.dids:
            self.chunks.append({
                "section": f"DID {did.did_hex} - {did.name}",
                "source": source_file,
                "content": f"DID {did.did_hex} ({did.name}): Length {did.length_bytes} bytes, Type {did.data_type}, Access {did.access}, Allowed in {did.allowed_sessions}, Security Level: {did.security_level}. Description: {did.description}. Default Value: {did.default_value}"
            })

        # Index Routines
        for r in db.routines:
            self.chunks.append({
                "section": f"Routine {r.routine_id} - {r.name}",
                "source": source_file,
                "content": f"Routine {r.routine_id} ({r.name}): Allowed in {r.allowed_sessions}, Requires Security: {r.requires_security} (Level {r.security_level}). Description: {r.description}"
            })

    def search(self, query: str, top_k: int = 4) -> List[CitationResult]:
        """Keyword and token similarity semantic search."""
        query_terms = re.findall(r"[A-Za-z0-9_]+", query.lower())
        if not query_terms:
            return []

        scored = []
        for chunk in self.chunks:
            text = (chunk["section"] + " " + chunk["content"]).lower()
            score = sum(text.count(term) * (3 if term in chunk["section"].lower() else 1) for term in query_terms)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, chunk in scored[:top_k]:
            results.append(CitationResult(
                source_file=chunk["source"],
                section=chunk["section"],
                content=chunk["content"],
                confidence=min(1.0, score / 5.0)
            ))

        return results

    def answer_query(self, query: str) -> QueryResponse:
        """Generate comprehensive cited answer for natural language queries."""
        q_lower = query.lower()

        # 1. Specialized Intent: Explain All Routines in the document
        if any(term in q_lower for term in ["all routine", "explain routine", "list routine", "what routine", "routines present", "every routine"]):
            if self.active_db and self.active_db.routines:
                lines = [f"### ⚙️ Diagnostic Routines Defined for **{self.active_db.ecu_name}** (Service $31):\n"]
                citations = []
                for idx, r in enumerate(self.active_db.routines, 1):
                    subfn_desc = []
                    if 1 in r.supported_subfunctions: subfn_desc.append("0x01 (StartRoutine)")
                    if 2 in r.supported_subfunctions: subfn_desc.append("0x02 (StopRoutine)")
                    if 3 in r.supported_subfunctions: subfn_desc.append("0x03 (RequestResults)")

                    lines.append(f"**{idx}. Routine {r.routine_id} — {r.name}**")
                    lines.append(f"- **Description:** {r.description or 'Diagnostic routine sequence'}")
                    lines.append(f"- **Sub-functions Supported:** {', '.join(subfn_desc)}")
                    lines.append(f"- **Allowed Sessions:** {', '.join(r.allowed_sessions)}")
                    lines.append(f"- **Security Requirement:** {'Level ' + str(r.security_level) + ' (Locked)' if r.requires_security else 'None (Open)'}")
                    lines.append(f"- **Start Payload Length:** {r.start_payload_length} bytes\n")

                    citations.append(CitationResult(
                        source_file="diagnostic_specification.pdf",
                        section=f"Routine {r.routine_id} ({r.name})",
                        content=f"Routine {r.routine_id} ({r.name}) in sessions {r.allowed_sessions} with security {r.security_level}. {r.description}",
                        confidence=1.0
                    ))

                # Add ISO 14229 Standard Reference citation
                citations.append(CitationResult(
                    source_file="ISO_14229_Standard.pdf",
                    section="ISO 14229-1 Section 12.2 (RoutineControl)",
                    content="Service $31 RoutineControl starts, stops, and requests routine execution results.",
                    confidence=0.95
                ))

                return QueryResponse(query=query, answer="\n".join(lines), citations=citations)

        # 2. Specialized Intent: Explain All DIDs (Data Identifiers)
        if any(term in q_lower for term in ["all did", "list did", "what did", "all data identifier", "parameters present"]):
            if self.active_db and self.active_db.dids:
                lines = [f"### 📋 Configured Data Identifiers (DIDs) for **{self.active_db.ecu_name}** (Service $22 / $2E):\n"]
                citations = []
                for idx, d in enumerate(self.active_db.dids, 1):
                    lines.append(f"**{idx}. DID {d.did_hex} — {d.name}**")
                    lines.append(f"- **Length:** {d.length_bytes} bytes | **Type:** {d.data_type} | **Access:** {d.access}")
                    lines.append(f"- **Allowed Sessions:** {', '.join(d.allowed_sessions)} | **Security Level:** L{d.security_level}")
                    lines.append(f"- **Default Value:** `{d.default_value}`\n")

                    citations.append(CitationResult(
                        source_file="diagnostic_specification.pdf",
                        section=f"DID {d.did_hex} ({d.name})",
                        content=f"DID {d.did_hex} ({d.name}) size {d.length_bytes}B in {d.allowed_sessions}.",
                        confidence=1.0
                    ))
                return QueryResponse(query=query, answer="\n".join(lines), citations=citations)

        # 3. Standard Semantic Search with Citations
        citations = self.search(query, top_k=3)
        if not citations:
            return QueryResponse(
                query=query,
                answer="No directly matching diagnostic specification or ISO 14229 rule found in loaded knowledge base.",
                citations=[]
            )

        summary_lines = [f"Based on **{c.section}** ({c.source_file}):\n> {c.content}" for c in citations]
        answer_text = "\n\n".join(summary_lines)

        return QueryResponse(
            query=query,
            answer=answer_text,
            citations=citations
        )
