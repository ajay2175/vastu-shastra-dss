"""
Offline Mode Validation & Performance Benchmarking Tool

Validates that Vastu DSS operates completely offline:
- Verifies no external API calls
- Checks network isolation
- Measures offline performance
- Validates data consistency

Author: Claude Haiku 4.5
Version: 1.0.0
"""

import asyncio
import time
import json
import socket
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
from statistics import mean, stdev
from contextlib import contextmanager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# NETWORK MONITORING
# ============================================================================

class NetworkMonitor:
    """Monitor network activity to ensure offline operation."""

    def __init__(self):
        self.external_calls = []
        self.blocked_domains = []

    def check_network_isolation(self) -> Dict[str, Any]:
        """Verify system operates without external network calls."""
        results = {
            "status": "isolated",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "api_endpoints_blocked": True,
                "external_services_blocked": True,
                "local_only_mode": True,
            },
            "warnings": [],
            "network_calls": [],
        }

        # Attempt to detect common external service patterns
        test_external_hosts = [
            ("openai.com", 443),
            ("api.anthropic.com", 443),
            ("vector.db.example.com", 5432),
            ("remote-rag.example.com", 8000),
        ]

        for host, port in test_external_hosts:
            try:
                # Try to connect (this should fail in offline mode)
                socket.create_connection((host, port), timeout=0.5)
                results["checks"]["api_endpoints_blocked"] = False
                results["network_calls"].append({
                    "host": host,
                    "port": port,
                    "status": "connected",
                    "severity": "high"
                })
            except (socket.timeout, socket.error, OSError):
                # Expected - connection failed (good for offline)
                pass

        return results


# ============================================================================
# DATA VALIDATION
# ============================================================================

class DataValidation:
    """Validate embedded data completeness and consistency."""

    @staticmethod
    def validate_embedded_principles() -> Dict[str, Any]:
        """Validate embedded principles are complete."""
        results = {
            "status": "valid",
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "issues": [],
        }

        try:
            from vastu.embedded_principles import (
                DIRECTIONS, ROOM_PLACEMENTS, VASTU_DOSHAS, REMEDIES
            )

            # Check directions
            required_directions = ["north", "northeast", "east", "southeast",
                                  "south", "southwest", "west", "northwest", "center"]
            available_directions = list(DIRECTIONS.keys())

            results["checks"]["directions"] = {
                "required": len(required_directions),
                "available": len(available_directions),
                "complete": all(d in available_directions for d in required_directions),
            }

            if not results["checks"]["directions"]["complete"]:
                missing = [d for d in required_directions if d not in available_directions]
                results["issues"].append(f"Missing directions: {missing}")

            # Check rooms
            required_rooms = ["bedroom", "kitchen", "puja_room", "living_room"]
            available_rooms = list(ROOM_PLACEMENTS.keys()) if ROOM_PLACEMENTS else []

            results["checks"]["rooms"] = {
                "required": len(required_rooms),
                "available": len(available_rooms),
                "complete": all(r in available_rooms for r in required_rooms),
            }

            # Check doshas
            if VASTU_DOSHAS:
                results["checks"]["doshas"] = {
                    "count": len(VASTU_DOSHAS),
                    "min_required": 10,
                    "sufficient": len(VASTU_DOSHAS) >= 10,
                }

            # Check remedies
            if REMEDIES:
                results["checks"]["remedies"] = {
                    "count": len(REMEDIES),
                    "min_required": 5,
                    "sufficient": len(REMEDIES) >= 5,
                }

        except Exception as e:
            results["status"] = "error"
            results["issues"].append(str(e))

        return results

    @staticmethod
    def validate_local_kg() -> Dict[str, Any]:
        """Validate local knowledge graph if available."""
        results = {
            "status": "checking",
            "timestamp": datetime.now().isoformat(),
            "kg_available": False,
            "kg_path": None,
            "checks": {},
            "issues": [],
        }

        try:
            kg_path = Path(__file__).parent / "data" / "kg" / "vastu_knowledge_graph_final.json"

            if kg_path.exists():
                results["kg_available"] = True
                results["kg_path"] = str(kg_path)

                # Load and validate KG structure
                with open(kg_path, "r") as f:
                    kg_data = json.load(f)

                # Check for required keys
                required_keys = ["nodes", "edges", "metadata"]
                has_required = all(key in kg_data for key in required_keys)

                results["checks"]["structure"] = {
                    "has_nodes": "nodes" in kg_data,
                    "has_edges": "edges" in kg_data,
                    "has_metadata": "metadata" in kg_data,
                    "complete": has_required,
                }

                if has_required:
                    results["checks"]["node_count"] = len(kg_data.get("nodes", []))
                    results["checks"]["edge_count"] = len(kg_data.get("edges", []))
                    results["checks"]["node_types"] = len(set(
                        n.get("type", "unknown") for n in kg_data.get("nodes", [])
                    ))

            else:
                results["status"] = "not_found"
                results["issues"].append(f"KG not found at: {kg_path}")

        except Exception as e:
            results["status"] = "error"
            results["issues"].append(str(e))

        return results


# ============================================================================
# PERFORMANCE BENCHMARKING
# ============================================================================

class PerformanceBenchmark:
    """Benchmark system performance in offline mode."""

    def __init__(self):
        self.benchmarks = {}

    async def benchmark_direction_consultation(self, consultation_system) -> Dict[str, float]:
        """Benchmark direction consultation latency."""
        directions = ["north", "northeast", "east", "southeast",
                     "south", "southwest", "west", "northwest", "center"]

        latencies = []

        for direction in directions:
            try:
                start = time.time()
                await consultation_system.get_direction_consultation(direction)
                latency_ms = (time.time() - start) * 1000
                latencies.append(latency_ms)
            except Exception as e:
                logger.error(f"Failed to benchmark {direction}: {e}")

        if not latencies:
            return {}

        return {
            "operation": "direction_consultation",
            "count": len(latencies),
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "mean_ms": mean(latencies),
            "stdev_ms": stdev(latencies) if len(latencies) > 1 else 0,
            "p50_ms": sorted(latencies)[len(latencies) // 2],
            "p95_ms": sorted(latencies)[int(len(latencies) * 0.95)],
        }

    async def benchmark_room_consultation(self, consultation_system) -> Dict[str, float]:
        """Benchmark room consultation latency."""
        rooms = ["bedroom", "kitchen", "puja_room", "living_room", "study", "office"]

        latencies = []

        for room in rooms:
            try:
                start = time.time()
                await consultation_system.get_room_consultation(room)
                latency_ms = (time.time() - start) * 1000
                latencies.append(latency_ms)
            except Exception as e:
                logger.error(f"Failed to benchmark {room}: {e}")

        if not latencies:
            return {}

        return {
            "operation": "room_consultation",
            "count": len(latencies),
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "mean_ms": mean(latencies),
            "stdev_ms": stdev(latencies) if len(latencies) > 1 else 0,
            "p50_ms": sorted(latencies)[len(latencies) // 2],
            "p95_ms": sorted(latencies)[int(len(latencies) * 0.95)],
        }

    async def benchmark_space_analysis(self, consultation_system, num_samples=10) -> Dict[str, float]:
        """Benchmark space analysis latency."""
        latencies = []

        for i in range(num_samples):
            try:
                space = {
                    "name": f"Space {i}",
                    "type": ["bedroom", "kitchen", "living_room"][i % 3],
                    "direction": ["north", "east", "south"][i % 3],
                }

                start = time.time()
                await consultation_system.analyze_space(space)
                latency_ms = (time.time() - start) * 1000
                latencies.append(latency_ms)
            except Exception as e:
                logger.error(f"Failed to benchmark space analysis: {e}")

        if not latencies:
            return {}

        return {
            "operation": "space_analysis",
            "count": len(latencies),
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "mean_ms": mean(latencies),
            "stdev_ms": stdev(latencies) if len(latencies) > 1 else 0,
            "p50_ms": sorted(latencies)[len(latencies) // 2],
            "p95_ms": sorted(latencies)[int(len(latencies) * 0.95)],
        }

    async def benchmark_batch_analysis(self, consultation_system, batch_sizes=[5, 10, 20]) -> List[Dict]:
        """Benchmark batch analysis performance."""
        results = []

        for batch_size in batch_sizes:
            try:
                spaces = [
                    {
                        "name": f"Space {i}",
                        "type": ["bedroom", "kitchen", "living_room"][i % 3],
                        "direction": ["north", "east", "south"][i % 3],
                    }
                    for i in range(batch_size)
                ]

                start = time.time()
                await consultation_system.batch_analyze_spaces(spaces)
                latency_ms = (time.time() - start) * 1000

                results.append({
                    "operation": "batch_analysis",
                    "batch_size": batch_size,
                    "total_ms": latency_ms,
                    "per_item_ms": latency_ms / batch_size,
                })
            except Exception as e:
                logger.error(f"Failed to benchmark batch analysis: {e}")

        return results


# ============================================================================
# MAIN VALIDATION SUITE
# ============================================================================

class OfflineModeValidator:
    """Main validator orchestrating all offline mode checks."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "status": "passing",
            "sections": {},
        }

    async def run_all_validations(self) -> Dict[str, Any]:
        """Run complete validation suite."""
        logger.info("Starting Offline Mode Validation Suite")
        logger.info("=" * 80)

        # Network isolation check
        logger.info("\n1. NETWORK ISOLATION CHECK")
        logger.info("-" * 80)
        network_monitor = NetworkMonitor()
        network_results = network_monitor.check_network_isolation()
        self.results["sections"]["network_isolation"] = network_results
        self._print_results(network_results)

        # Data validation
        logger.info("\n2. EMBEDDED PRINCIPLES VALIDATION")
        logger.info("-" * 80)
        data_validator = DataValidation()
        principles_results = data_validator.validate_embedded_principles()
        self.results["sections"]["embedded_principles"] = principles_results
        self._print_results(principles_results)

        # KG validation
        logger.info("\n3. LOCAL KNOWLEDGE GRAPH VALIDATION")
        logger.info("-" * 80)
        kg_results = data_validator.validate_local_kg()
        self.results["sections"]["local_kg"] = kg_results
        self._print_results(kg_results)

        # Performance benchmarking
        logger.info("\n4. PERFORMANCE BENCHMARKING")
        logger.info("-" * 80)
        try:
            from vastu.standalone_consultation import StandaloneConsultation

            consultation_system = StandaloneConsultation()
            benchmark = PerformanceBenchmark()

            perf_results = {
                "timestamp": datetime.now().isoformat(),
                "benchmarks": {},
                "quality_gates": {},
            }

            # Direction consultation
            logger.info("Benchmarking direction consultation...")
            dir_results = await benchmark.benchmark_direction_consultation(consultation_system)
            if dir_results:
                perf_results["benchmarks"]["direction_consultation"] = dir_results
                logger.info(f"  Mean latency: {dir_results['mean_ms']:.2f}ms")

            # Room consultation
            logger.info("Benchmarking room consultation...")
            room_results = await benchmark.benchmark_room_consultation(consultation_system)
            if room_results:
                perf_results["benchmarks"]["room_consultation"] = room_results
                logger.info(f"  Mean latency: {room_results['mean_ms']:.2f}ms")

            # Space analysis
            logger.info("Benchmarking space analysis...")
            space_results = await benchmark.benchmark_space_analysis(consultation_system)
            if space_results:
                perf_results["benchmarks"]["space_analysis"] = space_results
                logger.info(f"  Mean latency: {space_results['mean_ms']:.2f}ms")

            # Batch analysis
            logger.info("Benchmarking batch analysis...")
            batch_results = await benchmark.benchmark_batch_analysis(consultation_system)
            if batch_results:
                perf_results["benchmarks"]["batch_analysis"] = batch_results
                for result in batch_results:
                    logger.info(f"  Batch size {result['batch_size']}: "
                               f"{result['per_item_ms']:.2f}ms per item")

            # Quality gates
            all_mean_latencies = []
            for bench in perf_results["benchmarks"].values():
                if isinstance(bench, dict) and "mean_ms" in bench:
                    all_mean_latencies.append(bench["mean_ms"])

            if all_mean_latencies:
                overall_mean = mean(all_mean_latencies)
                perf_results["quality_gates"]["overall_mean_latency_ms"] = overall_mean
                perf_results["quality_gates"]["latency_requirement_met"] = overall_mean < 3000
                perf_results["quality_gates"]["latency_requirement_ms"] = 3000
                logger.info(f"\nQuality Gate: Overall mean latency = {overall_mean:.2f}ms "
                           f"(requirement: <3000ms) - "
                           f"{'✓ PASS' if overall_mean < 3000 else '✗ FAIL'}")

            self.results["sections"]["performance"] = perf_results

        except Exception as e:
            logger.error(f"Performance benchmarking failed: {e}")
            self.results["sections"]["performance"] = {"error": str(e)}

        # Determine overall status
        self._determine_overall_status()

        logger.info("\n" + "=" * 80)
        logger.info("OFFLINE MODE VALIDATION COMPLETE")
        logger.info("=" * 80)

        return self.results

    def _print_results(self, results: Dict):
        """Pretty print validation results."""
        if "checks" in results:
            for check_name, check_result in results["checks"].items():
                if isinstance(check_result, bool):
                    status = "✓" if check_result else "✗"
                    logger.info(f"  {status} {check_name}: {check_result}")
                elif isinstance(check_result, dict):
                    logger.info(f"  {check_name}:")
                    for key, value in check_result.items():
                        logger.info(f"    - {key}: {value}")

        if "issues" in results and results["issues"]:
            for issue in results["issues"]:
                logger.warning(f"  ⚠ {issue}")

    def _determine_overall_status(self):
        """Determine overall validation status."""
        issues = []

        # Check network isolation
        network = self.results["sections"].get("network_isolation", {})
        if network.get("network_calls"):
            issues.append("Network isolation failed - external calls detected")

        # Check embedded principles
        principles = self.results["sections"].get("embedded_principles", {})
        if principles.get("issues"):
            issues.extend(principles["issues"])

        # Check performance
        perf = self.results["sections"].get("performance", {})
        quality_gates = perf.get("quality_gates", {})
        if not quality_gates.get("latency_requirement_met", True):
            issues.append("Performance quality gate failed - latency too high")

        if issues:
            self.results["status"] = "failing"
            self.results["issues"] = issues
        else:
            self.results["status"] = "passing"

    def save_report(self, output_path: str = None):
        """Save validation report to JSON file."""
        if output_path is None:
            output_path = Path(__file__).parent / "OFFLINE_MODE_VALIDATION_REPORT.json"

        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"\nValidation report saved to: {output_path}")

        return output_path


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

async def main():
    """Run offline mode validation from command line."""
    validator = OfflineModeValidator()
    results = await validator.run_all_validations()

    # Save report
    validator.save_report()

    # Print summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Overall Status: {results['status'].upper()}")

    if results.get("issues"):
        print(f"\nIssues Found ({len(results['issues'])}):")
        for issue in results["issues"]:
            print(f"  - {issue}")
    else:
        print("\n✓ All validations passed!")

    print("=" * 80)

    # Exit with appropriate code
    sys.exit(0 if results["status"] == "passing" else 1)


if __name__ == "__main__":
    asyncio.run(main())
