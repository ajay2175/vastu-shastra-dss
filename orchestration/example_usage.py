"""Example usage of the multi-model orchestration layer."""

import asyncio
import os
from orchestration import ConsultationOrchestrator, ConsultationRequest


async def run_single_consultation():
    """Example: Single consultation through multi-model pipeline."""
    print("=" * 80)
    print("EXAMPLE 1: Single Consultation")
    print("=" * 80)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        return

    orchestrator = ConsultationOrchestrator(api_key=api_key)

    # Create consultation request
    request = ConsultationRequest(
        query="My living room feels dark and stagnant. It's located in the southwest "
        "corner of my home and faces that direction. What can I do to improve "
        "the energy flow and make it more vibrant?",
        space_type="living_room",
        location="southwest",
        issue_type="energy_flow",
        user_background="beginner",
        supplementary_data={
            "room_dimensions": "20x18 feet",
            "windows": "north side only",
            "main_furniture": "heavy wooden pieces",
        },
    )

    print(f"\nRequest ID: {request.request_id}")
    print(f"Query: {request.query[:100]}...")
    print(f"Space Type: {request.space_type}")
    print(f"Location: {request.location}")
    print()

    # Process consultation
    response = await orchestrator.process_consultation(request)

    # Display results
    print("\n--- CONSULTATION RESULTS ---")
    print(f"Status: {response.status}")
    print(f"Timestamp: {response.timestamp}")
    print()

    print("--- CONFIDENCE METRICS ---")
    for key, value in response.confidence_metrics.items():
        print(f"  {key}: {value:.2f}")
    print()

    print("--- EXECUTIVE SUMMARY ---")
    print(response.executive_summary)
    print()

    print("--- RECOMMENDATIONS ---")
    for i, rec in enumerate(response.recommendations, 1):
        if isinstance(rec, dict):
            print(f"  {i}. {rec.get('title', 'Recommendation')}: {rec.get('description', '')}")
        else:
            print(f"  {i}. {rec}")
    print()

    print("--- PERFORMANCE METRICS ---")
    for key, value in response.performance_metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.0f}ms")
        else:
            print(f"  {key}: {value}")
    print()

    print("--- MODEL ROUTING ---")
    for key, value in response.model_routing.items():
        print(f"  {key}: {value}")
    print()

    return response


async def run_batch_consultation():
    """Example: Batch consultations with concurrent processing."""
    print("=" * 80)
    print("EXAMPLE 2: Batch Consultations (Parallel Processing)")
    print("=" * 80)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        return

    orchestrator = ConsultationOrchestrator(api_key=api_key)

    # Create multiple requests
    requests = [
        ConsultationRequest(
            query="My kitchen is in the south, how should I arrange it?",
            space_type="kitchen",
            location="south",
            issue_type="arrangement",
            user_background="general",
        ),
        ConsultationRequest(
            query="Bedroom in northeast is causing sleep issues. What remedies?",
            space_type="bedroom",
            location="northeast",
            issue_type="sleep_disturbance",
            user_background="general",
        ),
        ConsultationRequest(
            query="How should I position my work desk for maximum productivity?",
            space_type="home_office",
            location="center",
            issue_type="productivity",
            user_background="professional",
        ),
    ]

    print(f"\nProcessing {len(requests)} consultations in parallel (max 3 concurrent)...")
    print()

    responses = await orchestrator.process_batch_consultations(requests, max_concurrent=3)

    print("\n--- BATCH RESULTS SUMMARY ---")
    total_time = 0
    for response in responses:
        total_time += response.performance_metrics.get("total_latency_ms", 0)
        status = "✓" if response.status == "success" else "✗"
        confidence = response.confidence_metrics.get("overall", 0)
        latency = response.performance_metrics.get("total_latency_ms", 0)
        print(
            f"  {status} {response.query[:40]:40s} | "
            f"Conf: {confidence:.2f} | Latency: {latency:.0f}ms"
        )

    print(f"\nTotal Processing Time: {total_time:.0f}ms")
    print(f"Average Time per Consultation: {total_time / len(responses):.0f}ms")
    print()

    return responses


async def run_health_check():
    """Example: Check model health and performance."""
    print("=" * 80)
    print("EXAMPLE 3: Model Health & Performance Monitoring")
    print("=" * 80)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        return

    orchestrator = ConsultationOrchestrator(api_key=api_key)

    # Get model health status
    health_status = orchestrator.get_model_health_status()

    print("\n--- MODEL HEALTH STATUS ---")
    for model_name, health_data in health_status.items():
        status = "✓ Available" if health_data["available"] else "✗ Unavailable"
        score = health_data["health_score"]
        latency = health_data["avg_latency_ms"]

        print(f"\n{model_name}")
        print(f"  Status: {status}")
        print(f"  Health Score: {score:.2f}/1.00")
        print(f"  Success Count: {health_data['success_count']}")
        print(f"  Failure Count: {health_data['failure_count']}")
        print(f"  Avg Latency: {latency:.0f}ms")

    print()

    # Get consultation history
    history = orchestrator.get_consultation_history(limit=5)

    print("\n--- RECENT CONSULTATIONS ---")
    for i, response in enumerate(history[-5:], 1):
        print(f"\n{i}. {response.query[:50]}...")
        print(f"   Status: {response.status}")
        print(f"   Confidence: {response.confidence_metrics['overall']:.2f}")
        print(f"   Latency: {response.performance_metrics['total_latency_ms']:.0f}ms")

    print()


async def demonstrate_fallback_handling():
    """Example: Demonstrate graceful fallback when models unavailable."""
    print("=" * 80)
    print("EXAMPLE 4: Fallback Handling (Graceful Degradation)")
    print("=" * 80)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        return

    orchestrator = ConsultationOrchestrator(api_key=api_key)

    # Simulate model unavailability (for demo purposes)
    print("\nSimulating primary model unavailability...")
    print("The orchestrator will automatically:")
    print("  1. Try primary model")
    print("  2. Fall back to secondary model if primary fails")
    print("  3. Fall back to fallback response if all models fail")
    print("  4. Track health and recovery")
    print()

    # Run a consultation
    request = ConsultationRequest(
        query="What are the best colors for a north-facing bedroom?",
        space_type="bedroom",
        location="north",
        issue_type="color_selection",
    )

    print(f"Processing request: {request.request_id}")
    response = await orchestrator.process_consultation(request)

    print(f"\nResult Status: {response.status}")
    print(f"Models Used: {response.model_routing}")

    # Show that consultation completes even with failures
    if response.status == "success":
        print("✓ Consultation completed successfully despite potential model issues")
    elif response.status == "fallback":
        print("◐ Consultation completed with fallback models")
        print("  Quality reduced but consultation still provides value")

    print()


async def demonstrate_caching_benefit():
    """Example: Show prompt caching benefit with repeated queries."""
    print("=" * 80)
    print("EXAMPLE 5: Prompt Caching & Performance Improvement")
    print("=" * 80)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        return

    orchestrator = ConsultationOrchestrator(api_key=api_key)

    # Same query, run multiple times to demonstrate caching
    queries = [
        "How should I arrange my kitchen for better energy flow?",
        "How should I arrange my kitchen for better energy flow?",  # Repeat (cache hit)
        "How should I arrange my kitchen for better energy flow?",  # Repeat (cache hit)
    ]

    print("\nRunning 3 identical queries to demonstrate prompt caching...")
    print("First query: No cache (full tokens)")
    print("Queries 2-3: Cache hits (90% token reduction)")
    print()

    latencies = []
    for i, query in enumerate(queries, 1):
        request = ConsultationRequest(
            query=query,
            space_type="kitchen",
            location="east",
        )

        response = await orchestrator.process_consultation(request)
        latency = response.performance_metrics["total_latency_ms"]
        latencies.append(latency)

        cache_status = "CACHE HIT" if i > 1 else "NO CACHE"
        print(
            f"Query {i}: {latency:.0f}ms {cache_status:15s} "
            f"(Confidence: {response.confidence_metrics['overall']:.2f})"
        )

    print()
    print(f"First Query (baseline): {latencies[0]:.0f}ms")
    print(f"Query 2 (cached): {latencies[1]:.0f}ms ({100*(1-latencies[1]/latencies[0]):.0f}% faster)")
    print(f"Query 3 (cached): {latencies[2]:.0f}ms ({100*(1-latencies[2]/latencies[0]):.0f}% faster)")
    print()


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("MULTI-MODEL ORCHESTRATION EXAMPLES")
    print("=" * 80)
    print()

    try:
        # Example 1: Single consultation
        await run_single_consultation()
        await asyncio.sleep(1)

        # Example 2: Batch consultations
        await run_batch_consultation()
        await asyncio.sleep(1)

        # Example 3: Health monitoring
        await run_health_check()
        await asyncio.sleep(1)

        # Example 4: Fallback handling
        await demonstrate_fallback_handling()
        await asyncio.sleep(1)

        # Example 5: Caching benefit
        await demonstrate_caching_benefit()

        print("\n" + "=" * 80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print()

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
