"""Example script demonstrating black-box test generation.

This script shows how to use the BlackBoxTestGenerator to create
test cases from a structured requirement.
"""

import json

from app.engines.blackbox_generator import BlackBoxTestGenerator
from app.models.requirement import StructuredRequirement


def main():
    """Demonstrate black-box test case generation."""
    
    print("=" * 80)
    print("IntelliTest - Black-Box Test Generation Demo")
    print("=" * 80)
    
    # Step 1: Create a sample structured requirement
    print("\n1. Creating sample requirement...")
    requirement = StructuredRequirement(
        id="REQ_USER_REG",
        raw_text=(
            "User registration system requires: "
            "Age between 18 and 120 years, "
            "Valid email address, "
            "Password minimum 8 characters, "
            "If user is over 65, offer senior discount, "
            "If membership type is premium, enable advanced features"
        ),
        input_fields=["age", "email", "password", "membership_type"],
        data_ranges=[
            "Age must be between 18 and 120",
            "Password length minimum 8 characters",
        ],
        conditions=[
            "If age >= 65",
            "If membership_type is premium",
        ],
        expected_actions=[
            "Create user account",
            "Send verification email",
            "Apply discounts if eligible"
        ],
        risk_score=15,
        priority="High"
    )
    
    print(f"   Requirement ID: {requirement.id}")
    print(f"   Input Fields: {', '.join(requirement.input_fields)}")
    print(f"   Conditions: {len(requirement.conditions)}")
    
    # Step 2: Initialize the generator engine
    print("\n2. Initializing BlackBoxTestGenerator...")
    engine = BlackBoxTestGenerator()
    
    # Step 3: Get technique information
    print("\n3. Available Testing Techniques:")
    techniques = engine.get_technique_info()
    for tech_code, info in techniques.items():
        print(f"\n   [{tech_code}] {info['name']}")
        print(f"       {info['description']}")
        print(f"       Best for: {info['best_for']}")
    
    # Step 4: Generate test cases with coverage tracking
    print("\n4. Generating test cases with all techniques...")
    result = engine.generate_with_coverage_tracking(requirement)
    
    test_cases = result['test_cases']
    coverage_items = result['coverage_items']
    coverage_report = result['coverage_report']
    
    print(f"\n   Generated {len(test_cases)} test cases")
    print(f"   Identified {len(coverage_items)} coverage items")
    
    # Step 5: Display coverage report
    print("\n5. Coverage Report:")
    print(f"   Total Coverage Items: {coverage_report['total_coverage_items']}")
    print(f"   Covered Items: {coverage_report['covered_items']}")
    print(f"   Uncovered Items: {coverage_report['uncovered_items']}")
    print(f"   Coverage Percentage: {coverage_report['coverage_percentage']:.1f}%")
    
    print("\n   Technique Usage:")
    for technique, count in coverage_report['technique_usage'].items():
        print(f"     - {technique}: {count} test cases")
    
    # Step 6: Display sample test cases by technique
    print("\n6. Sample Test Cases by Technique:")
    
    techniques_found = {}
    for tc in test_cases:
        tech = tc.technique.value if tc.technique else "Unknown"
        if tech not in techniques_found:
            techniques_found[tech] = []
        techniques_found[tech].append(tc)
    
    for tech, cases in techniques_found.items():
        print(f"\n   [{tech}] - {len(cases)} test cases")
        print("   " + "-" * 70)
        
        # Show first 2 test cases as examples
        for tc in cases[:2]:
            print(f"     ID: {tc.id}")
            print(f"     Title: {tc.title}")
            print(f"     Test Data: {tc.test_data}")
            print(f"     Expected: {tc.expected_result[:60]}...")
            print(f"     Priority: {tc.priority.value}")
            print()
        
        if len(cases) > 2:
            print(f"     ... and {len(cases) - 2} more test cases\n")
    
    # Step 7: Export to JSON (for demonstration)
    print("7. Exporting Results:")
    
    export_data = {
        'requirement_id': requirement.id,
        'test_cases': [tc.model_dump() for tc in test_cases],
        'coverage_report': coverage_report
    }
    
    json_output = json.dumps(export_data, indent=2, ensure_ascii=False)
    
    # Save to file
    output_file = "blackbox_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json_output)
    
    print(f"   Results exported to: {output_file}")
    print(f"   File size: {len(json_output)} bytes")
    
    print("\n" + "=" * 80)
    print("Demo completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
