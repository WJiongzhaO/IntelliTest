import requests
import json

# 使用嵌套对象格式
req = {
    'requirement': {
        'id': 'T1',
        'raw_text': 'test requirement',
        'input_fields': ['age'],
        'data_ranges': ['Age between 18 and 120'],
        'conditions': ['If age >= 18'],
        'expected_actions': ['Register user']
    },
    'selected_techniques': ['EP', 'BVA']
}

r = requests.post(
    'http://localhost:8000/api/v1/blackbox/generate/with-coverage',
    json=req
)

print(f'Status: {r.status_code}')

if r.status_code == 200:
    result = r.json()
    print(f'✅ Success! Generated {len(result.get("test_cases", []))} test cases')
    print(f'   Coverage items: {len(result.get("coverage_items", []))}')
    print(f'   Coverage: {result.get("coverage_report", {}).get("coverage_percentage", 0)}%')
else:
    print('❌ Error:')
    print(json.dumps(r.json(), indent=2))
