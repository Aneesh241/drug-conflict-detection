from __future__ import annotations

from typing import List, Dict, Any

from mesa import Agent

from utils import bfs_conflicts, build_rules_kb, make_condition_tokens, read_csv_records, logger


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
        """
        Naive rule-based prescriber:
        - For each patient condition, pick the first matching drug in catalog.
        - Always add an analgesic (Ibuprofen) to expose potential conflicts in the demo.
        """
        chosen: List[str] = []
        for cond in patient.conditions:
            for row in self.drugs_catalog:
                if str(row.get("condition", "")).strip().lower() == str(cond).strip().lower():
                    drug = str(row.get("drug", "")).strip()
                    if drug and drug not in chosen:
                        chosen.append(drug)
                        break
        # Deliberately add a painkiller to demonstrate conflicts (e.g., with Hypertension)
        if "Ibuprofen" not in chosen:
            chosen.append("Ibuprofen")
        logger.info(f"Doctor prescribed for {patient.name}: {chosen}")
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
        return conflicts

    def step(self):
        pass
