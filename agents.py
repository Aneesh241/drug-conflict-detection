from __future__ import annotations

from typing import List, Dict, Any, Tuple

from mesa import Agent

from utils import bfs_conflicts, build_rules_kb, make_condition_tokens, severity_to_score, logger
try:
    from audit_log import get_audit_logger, EventType, Severity
    AUDIT_ENABLED = True
except ImportError:
    AUDIT_ENABLED = False


class PatientAgent(Agent):
    def __init__(self, model, patient_id: str, name: str, conditions: List[str], allergies: List[str]):
        super().__init__(patient_id, model)
        self.patient_id = patient_id
        self.name = name
        self.conditions = conditions
        self.allergies = allergies
        self.prescription: List[str] = []

    def step(self):
        # Patients do not act independently in this simple simulation.
        pass


class DoctorAgent(Agent):
    def __init__(self, model, drugs_catalog: List[Dict[str, Any]]):
        super().__init__("doctor", model)
        self.drugs_catalog = drugs_catalog

    def prescribe(self, patient: PatientAgent) -> List[str]:
        chosen: List[str] = []
        condition_tokens = make_condition_tokens(patient.conditions, patient.allergies)

        def predicted_risk(drug: str, current_rx: List[str]) -> int:
            risk = 0
            dl = drug.lower()
            kb = self.model.rule_engine.kb
            for existing in current_rx:
                a, b = sorted([existing.lower(), dl])
                key = ("drug-drug", a, b)
                rule = kb.get(key)
                if rule:
                    risk += severity_to_score(rule.severity)
            for ct in condition_tokens:
                key = ("drug-condition", ct.lower(), dl)
                rule = kb.get(key)
                if rule:
                    risk += severity_to_score(rule.severity)
            return risk

        # Choose one drug per condition minimizing predicted risk
        for cond in patient.conditions:
            candidates = [r for r in self.drugs_catalog if str(r.get("condition", "")).strip().lower() == str(cond).strip().lower()]
            scored: List[Tuple[int, str, Dict[str, Any]]] = []
            for row in candidates:
                drug = str(row.get("drug", "")).strip()
                if not drug or drug in chosen:
                    continue
                risk = predicted_risk(drug, chosen)
                scored.append((risk, drug, row))
            if not scored:
                continue
            scored.sort(key=lambda t: (t[0], t[1].lower()))
            best_risk, best_drug, best_row = scored[0]
            # Consider replacements if risk is high (>=3 i.e. at least one Major)
            replacements = best_row.get("replacements", []) or []
            if best_risk >= 3 and replacements:
                rep_scored: List[Tuple[int, str]] = []
                for rep in replacements:
                    rep_name = str(rep).strip()
                    if not rep_name or rep_name in chosen:
                        continue
                    rep_risk = predicted_risk(rep_name, chosen)
                    rep_scored.append((rep_risk, rep_name))
                if rep_scored:
                    rep_scored.sort(key=lambda t: (t[0], t[1].lower()))
                    if rep_scored[0][0] < best_risk:
                        best_drug = rep_scored[0][1]
                        best_risk = rep_scored[0][0]
            chosen.append(best_drug)

        # Add analgesic only if patient has Pain and none chosen yet
        if any(c.strip().lower() == "pain" for c in patient.conditions):
            analgesics = ["Paracetamol", "Ibuprofen", "Naproxen", "Aspirin"]
            if not any(d in chosen for d in analgesics):
                a_scored: List[Tuple[int, str]] = []
                for a in analgesics:
                    # Skip if patient is allergic (check both raw name and allergy token forms)
                    if a in patient.allergies or f"{a}Allergy" in condition_tokens:
                        continue
                    a_scored.append((predicted_risk(a, chosen), a))
                if a_scored:
                    a_scored.sort(key=lambda t: (t[0], t[1].lower()))
                    chosen.append(a_scored[0][1])

        logger.info(f"Doctor prescribed for {patient.name} (risk-aware): {chosen}")
        
        # Audit logging
        if AUDIT_ENABLED:
            try:
                audit_logger = get_audit_logger()
                audit_logger.log_event(
                    event_type=EventType.DOCTOR_PRESCRIBE,
                    actor="doctor_agent",
                    patient_id=patient.patient_id,
                    patient_name=patient.name,
                    prescription=chosen,
                    metadata={"conditions": patient.conditions, "allergies": patient.allergies}
                )
            except Exception:
                pass  # Don't fail prescription if audit logging fails
        
        return chosen

    def step(self):
        pass


class RuleEngineAgent(Agent):
    def __init__(self, model, rules_rows: List[Dict[str, Any]]):
        super().__init__("rule_engine", model)
        self.kb = build_rules_kb(rules_rows)

    def check_conflicts(self, prescription: List[str], conditions: List[str], allergies: List[str]) -> List[Dict[str, Any]]:
        condition_tokens = make_condition_tokens(conditions, allergies)
        conflicts = bfs_conflicts(prescription, condition_tokens, self.kb)
        return [
            {
                "type": c.rtype,
                "item_a": c.item_a,
                "item_b": c.item_b,
                "severity": c.severity,
                "score": c.score,
                "recommendation": c.recommendation,
            }
            for c in conflicts
        ]

    def step(self):
        pass


class PharmacistAgent(Agent):
    def __init__(self, model, rule_engine: RuleEngineAgent):
        super().__init__("pharmacist", model)
        self.rule_engine = rule_engine

    def validate(self, patient: PatientAgent, prescription: List[str]) -> List[Dict[str, Any]]:
        conflicts = self.rule_engine.check_conflicts(prescription, patient.conditions, patient.allergies)
        logger.info(
            f"Pharmacist validated {patient.name}: {len(conflicts)} conflict(s) detected"
        )
        
        # Audit logging
        if AUDIT_ENABLED:
            try:
                audit_logger = get_audit_logger()
                severity = Severity.WARNING if conflicts else Severity.INFO
                audit_logger.log_event(
                    event_type=EventType.PHARMACIST_REVIEW,
                    actor="pharmacist_agent",
                    severity=severity,
                    patient_id=patient.patient_id,
                    patient_name=patient.name,
                    prescription=prescription,
                    conflicts=conflicts
                )
            except Exception:
                pass  # Don't fail validation if audit logging fails
        
        return conflicts

    def step(self):
        pass
