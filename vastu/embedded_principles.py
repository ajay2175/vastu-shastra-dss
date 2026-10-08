"""Embedded Vastu Shastra principles for standalone consultation."""

from typing import Optional, Dict, List
from dataclasses import dataclass
from .constants import VASTU_PRINCIPLES, ROOM_TYPE_GUIDELINES, COMMON_VASTU_DEFECTS


@dataclass
class VastuAdvice:
    """Represents a piece of Vastu advice."""

    principle: str
    direction: str
    recommendation: str
    severity: str  # Low, Medium, High, Critical
    reasoning: str


class VastuPrinciples:
    """
    Embedded Vastu Shastra principles for standalone consultation.
    Provides guidance based on fundamental principles without external dependencies.
    """

    def __init__(self):
        """Initialize with embedded Vastu principles."""
        self.principles = VASTU_PRINCIPLES
        self.room_guidelines = ROOM_TYPE_GUIDELINES
        self.defects = COMMON_VASTU_DEFECTS

    def get_direction_advice(self, direction: str) -> Optional[Dict]:
        """Get advice for a specific direction."""
        direction_key = direction.lower().replace(" ", "_")
        for key, principle in self.principles.items():
            if direction_key in key or direction.lower() in principle.get("name", "").lower():
                return principle
        return None

    def get_room_guidelines(self, room_type: str) -> Optional[Dict]:
        """Get guidelines for a specific room type."""
        room_key = room_type.lower().replace(" ", "_")
        return self.room_guidelines.get(room_key)

    def check_defect(self, defect_type: str) -> Optional[Dict]:
        """Check for a known Vastu defect and get remedies."""
        defect_key = defect_type.lower().replace(" ", "_")
        return self.defects.get(defect_key)

    def generate_advice(self, context: Dict) -> List[VastuAdvice]:
        """
        Generate Vastu advice based on provided context.

        Args:
            context: Dictionary with keys like 'room_type', 'direction', 'purpose', 'issues'

        Returns:
            List of VastuAdvice objects
        """
        advice_list = []

        room_type = context.get("room_type", "").lower()
        direction = context.get("direction", "").lower()
        issues = context.get("issues", [])

        # Get room-specific guidelines
        if room_type:
            room_guidelines = self.get_room_guidelines(room_type)
            if room_guidelines:
                advice_list.append(
                    VastuAdvice(
                        principle=f"Room Type: {room_type.title()}",
                        direction=", ".join(room_guidelines.get("best_directions", [])),
                        recommendation=f"Best placed in {', '.join(room_guidelines.get('best_directions', []))}",
                        severity="Medium",
                        reasoning="Following room-specific Vastu guidelines optimizes energy flow",
                    )
                )

        # Get direction-specific advice
        if direction:
            direction_principle = self.get_direction_advice(direction)
            if direction_principle:
                advice_list.append(
                    VastuAdvice(
                        principle=direction_principle.get("name", ""),
                        direction=direction.title(),
                        recommendation="; ".join(direction_principle.get("key_points", [])),
                        severity="High",
                        reasoning=direction_principle.get("description", ""),
                    )
                )

        # Check for defects
        for issue in issues:
            defect = self.check_defect(issue)
            if defect:
                advice_list.append(
                    VastuAdvice(
                        principle=f"Defect: {issue.replace('_', ' ').title()}",
                        direction="N/A",
                        recommendation="; ".join(defect.get("remedies", [])),
                        severity=defect.get("severity", "Medium"),
                        reasoning=f"Issue: {defect.get('problem')} - Impact: {defect.get('impact')}",
                    )
                )

        return advice_list

    def get_remedy_suggestions(self, problem_area: str) -> Dict[str, List[str]]:
        """
        Get remedy suggestions for a problem area.

        Args:
            problem_area: The area that needs remedying

        Returns:
            Dictionary with color, element, and object remedies
        """
        from .constants import REMEDIES_BY_TYPE

        return REMEDIES_BY_TYPE

    def validate_layout(self, layout_info: Dict) -> Dict:
        """
        Validate a building layout against Vastu principles.

        Args:
            layout_info: Dictionary with layout details

        Returns:
            Validation report with issues and recommendations
        """
        issues = []
        recommendations = []

        # Check for critical defects
        if layout_info.get("toilet_in_northeast"):
            issues.append("toilet_northeast")
        if layout_info.get("kitchen_in_center"):
            issues.append("kitchen_center")
        if layout_info.get("missing_northeast"):
            issues.append("missing_northeast")

        # Generate advice for each issue
        for issue in issues:
            defect = self.check_defect(issue)
            if defect:
                recommendations.extend(defect.get("remedies", []))

        return {
            "critical_issues": issues,
            "recommendations": recommendations,
            "validation_score": max(0, 100 - len(issues) * 20),
        }

    def suggest_color_for_space(self, space_info: Dict) -> str:
        """Suggest auspicious color for a space based on direction and purpose."""
        direction = space_info.get("direction", "").lower()

        direction_advice = self.get_direction_advice(direction)
        if direction_advice:
            colors = direction_advice.get("colors", [])
            return colors[0] if colors else "White"

        return "White"  # Default auspicious color

    def get_element_for_direction(self, direction: str) -> Optional[str]:
        """Get the element associated with a direction."""
        direction = direction.lower()

        for key, principle in self.principles.items():
            if direction in principle.get("name", "").lower():
                elements = principle.get("elements", [])
                return elements[0] if elements else None

        return None
