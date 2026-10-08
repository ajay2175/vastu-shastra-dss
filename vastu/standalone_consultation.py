"""Standalone Vastu Shastra consultation without external dependencies."""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from .embedded_principles import VastuPrinciples


class StandaloneConsultation:
    """
    Standalone Vastu Shastra consultation system.
    Works without vector databases or external APIs.
    """

    def __init__(self):
        """Initialize the standalone consultation system."""
        self.principles = VastuPrinciples()
        self.consultation_history = []

    async def analyze_space(self, space_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a space for Vastu compliance.

        Args:
            space_details: Dictionary with space information including:
                - name: Space name
                - type: Room type (bedroom, kitchen, etc.)
                - direction: Primary direction facing
                - area: Approximate area
                - features: List of features
                - issues: List of perceived issues
                - purpose: Primary purpose

        Returns:
            Analysis report with recommendations
        """
        analysis = {
            "space_name": space_details.get("name", "Unknown Space"),
            "analysis_timestamp": datetime.now().isoformat(),
            "compliance_score": 0,
            "issues": [],
            "recommendations": [],
            "principles_applied": [],
            "remedies": [],
        }

        # Validate layout
        layout_validation = self.principles.validate_layout(space_details)
        analysis["layout_validation"] = layout_validation
        analysis["compliance_score"] = layout_validation.get("validation_score", 50)

        # Generate advice based on space details
        advice_list = self.principles.generate_advice(space_details)
        analysis["principles_applied"] = [
            {"principle": a.principle, "direction": a.direction, "reasoning": a.reasoning}
            for a in advice_list
        ]
        analysis["recommendations"] = [a.recommendation for a in advice_list]

        # Get remedies for issues
        if space_details.get("issues"):
            remedies_by_type = self.principles.get_remedy_suggestions(space_details["issues"][0])
            analysis["remedies"] = remedies_by_type

        # Suggest color
        color = self.principles.suggest_color_for_space(space_details)
        analysis["suggested_color"] = color

        # Get element for direction
        direction = space_details.get("direction", "")
        if direction:
            element = self.principles.get_element_for_direction(direction)
            analysis["element_association"] = element

        return analysis

    async def get_direction_consultation(self, direction: str) -> Dict[str, Any]:
        """Get detailed consultation for a specific direction."""
        advice = self.principles.get_direction_advice(direction)

        if not advice:
            return {"error": f"No Vastu principles found for direction: {direction}"}

        return {
            "direction": direction,
            "principle_name": advice.get("name"),
            "description": advice.get("description"),
            "key_points": advice.get("key_points", []),
            "elements": advice.get("elements", []),
            "colors": advice.get("colors", []),
            "remedies": advice.get("remedies", []),
        }

    async def get_room_consultation(self, room_type: str) -> Dict[str, Any]:
        """Get detailed consultation for a specific room type."""
        guidelines = self.principles.get_room_guidelines(room_type)

        if not guidelines:
            return {"error": f"No guidelines found for room type: {room_type}"}

        return {
            "room_type": room_type,
            "best_directions": guidelines.get("best_directions", []),
            "directions_to_avoid": guidelines.get("avoid", []),
            "ideal_shape": guidelines.get("shape", "Not specified"),
            "window_placement": guidelines.get("window_placement", "Not specified"),
            "recommended_color": guidelines.get("color", "Not specified"),
            "furniture_guidelines": guidelines.get("furniture", "Not specified"),
        }

    async def diagnose_defect(self, defect_type: str) -> Dict[str, Any]:
        """Diagnose and get remedies for a known Vastu defect."""
        defect_info = self.principles.check_defect(defect_type)

        if not defect_info:
            return {"error": f"Unknown defect type: {defect_type}"}

        return {
            "defect": defect_type,
            "problem": defect_info.get("problem"),
            "impact": defect_info.get("impact"),
            "severity": defect_info.get("severity"),
            "remedies": defect_info.get("remedies", []),
            "detailed_remedies": self._elaborate_remedies(defect_info.get("remedies", [])),
        }

    async def create_consultation_report(self, space_data: Dict) -> str:
        """Create a human-readable consultation report."""
        analysis = await self.analyze_space(space_data)

        report = f"""
VASTU SHASTRA CONSULTATION REPORT
{'=' * 50}

Space: {analysis['space_name']}
Analysis Date: {analysis['analysis_timestamp']}

COMPLIANCE ASSESSMENT
{'-' * 50}
Overall Compliance Score: {analysis['compliance_score']}/100

PRINCIPLES APPLIED
{'-' * 50}
"""

        for principle in analysis["principles_applied"]:
            report += f"\n• {principle['principle']}\n"
            report += f"  Direction: {principle['direction']}\n"
            report += f"  Rationale: {principle['reasoning']}\n"

        report += f"\nRECOMMENDATIONS\n{'-' * 50}\n"
        for i, rec in enumerate(analysis["recommendations"], 1):
            report += f"{i}. {rec}\n"

        if analysis.get("suggested_color"):
            report += f"\nRECOMMENDED COLOR: {analysis['suggested_color']}\n"

        if analysis.get("element_association"):
            report += f"ELEMENT ASSOCIATION: {analysis['element_association']}\n"

        if analysis.get("remedies"):
            report += f"\nREMEDIES\n{'-' * 50}\n"
            remedies = analysis["remedies"]
            for remedy_type, items in remedies.items():
                report += f"\n{remedy_type.title()}:\n"
                for item, description in items.items():
                    report += f"  • {item}: {description}\n"

        return report

    def _elaborate_remedies(self, remedies: List[str]) -> List[Dict[str, str]]:
        """Elaborate on remedies with detailed explanations."""
        elaborate_remedies = []
        remedies_db = self.principles.get_remedy_suggestions("")

        for remedy in remedies:
            remedy_lower = remedy.lower()

            if "color" in remedy_lower:
                elaborate_remedies.append(
                    {
                        "remedy": remedy,
                        "type": "Color",
                        "details": f"Use {remedy} in the affected area",
                    }
                )
            elif "mirror" in remedy_lower:
                elaborate_remedies.append(
                    {
                        "remedy": remedy,
                        "type": "Object",
                        "details": "Place strategically to correct energy flow",
                    }
                )
            else:
                elaborate_remedies.append(
                    {"remedy": remedy, "type": "Remedy", "details": "Follow Vastu guidelines"}
                )

        return elaborate_remedies

    async def batch_analyze_spaces(self, spaces: List[Dict]) -> List[Dict]:
        """Analyze multiple spaces concurrently."""
        tasks = [self.analyze_space(space) for space in spaces]
        return await asyncio.gather(*tasks)

    def save_consultation(self, consultation_id: str, data: Dict) -> None:
        """Save consultation for historical reference."""
        self.consultation_history.append({"id": consultation_id, "data": data, "timestamp": datetime.now()})

    def get_consultation_history(self) -> List[Dict]:
        """Get consultation history."""
        return self.consultation_history
