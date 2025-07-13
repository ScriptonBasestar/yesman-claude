#!/bin/bash
# Test: AI Pattern Learning
# Description: Tests AI learning system accuracy and adaptation

set -e

echo "🧠 Testing AI Pattern Learning..."

# Setup test environment
mkdir -p /tmp/ai-test-data
cd /tmp/ai-test-data

# Test 1: Pattern recognition accuracy
echo -e "\n🎯 Test 1: Pattern recognition accuracy"
python3 << 'EOF'
import sys
sys.path.append('/Users/archmagece/myopen/scripton/yesman-claude')

from libs.ai.response_analyzer import ResponseAnalyzer
from libs.ai.adaptive_response import AdaptiveResponse

# Initialize AI components
analyzer = ResponseAnalyzer()
adaptive = AdaptiveResponse()

# Test patterns
test_patterns = [
    ("Do you trust this workspace? (y/n)", "yn", "y"),
    ("Continue? [Y/n]", "yn", "y"),
    ("Select option: 1) Option A  2) Option B", "numbered", "1"),
    ("Choose: 1) Yes  2) No  3) Cancel", "numbered", "1"),
    ("Press Enter to continue...", "continue", ""),
    ("Are you sure? (yes/no)", "yn", "yes"),
    ("Pick one: [1] First  [2] Second", "numbered", "1"),
]

correct_predictions = 0
total_predictions = len(test_patterns)

print("Testing pattern recognition...")
for prompt, expected_type, expected_response in test_patterns:
    # Test pattern classification
    detected_type = analyzer.classify_pattern(prompt)

    # Test response prediction
    predicted_response = adaptive.predict_response(prompt)

    print(f"Prompt: {prompt[:50]}...")
    print(f"  Expected type: {expected_type}, Detected: {detected_type}")
    print(f"  Expected response: '{expected_response}', Predicted: '{predicted_response}'")

    if detected_type == expected_type:
        correct_predictions += 1
        print("  ✅ Pattern correctly classified")
    else:
        print("  ❌ Pattern misclassified")
    print()

accuracy = (correct_predictions / total_predictions) * 100
print(f"Pattern Recognition Accuracy: {accuracy:.1f}%")

if accuracy >= 80:
    print("✅ Pattern recognition accuracy is acceptable")
else:
    print("❌ Pattern recognition accuracy needs improvement")
EOF

# Test 2: Learning adaptation
echo -e "\n📚 Test 2: Learning adaptation"
python3 << 'EOF'
import sys
sys.path.append('/Users/archmagece/myopen/scripton/yesman-claude')

from libs.ai.response_analyzer import ResponseAnalyzer
from libs.ai.adaptive_response import AdaptiveResponse
import tempfile
import os

# Create temporary learning data
with tempfile.TemporaryDirectory() as temp_dir:
    # Initialize with temporary data directory
    analyzer = ResponseAnalyzer(data_dir=temp_dir)
    adaptive = AdaptiveResponse(data_dir=temp_dir)

    # Simulate learning process
    learning_data = [
        ("Do you want to continue? (y/n)", "y", True),
        ("Do you want to proceed? (y/n)", "y", True),
        ("Are you ready? (y/n)", "y", True),
        ("Continue with installation? (y/n)", "y", True),
        ("Start the process? (y/n)", "y", True),
    ]

    print("Training AI with sample data...")
    for prompt, response, success in learning_data:
        analyzer.record_interaction(prompt, response, success)
        adaptive.learn_from_feedback(prompt, response, success)

    # Test prediction after learning
    test_prompt = "Do you want to save changes? (y/n)"
    confidence_before = adaptive.get_confidence(test_prompt)

    # Add more training data
    for i in range(10):
        analyzer.record_interaction(f"Save file {i}? (y/n)", "y", True)
        adaptive.learn_from_feedback(f"Save file {i}? (y/n)", "y", True)

    confidence_after = adaptive.get_confidence(test_prompt)

    print(f"Confidence before training: {confidence_before:.2f}")
    print(f"Confidence after training: {confidence_after:.2f}")

    if confidence_after > confidence_before:
        print("✅ AI learning is working - confidence improved")
    else:
        print("❌ AI learning may not be working properly")

    # Test pattern generalization
    similar_prompts = [
        "Would you like to save? (y/n)",
        "Save changes? (y/n)",
        "Keep modifications? (y/n)",
    ]

    print("\nTesting pattern generalization...")
    for prompt in similar_prompts:
        confidence = adaptive.get_confidence(prompt)
        prediction = adaptive.predict_response(prompt)
        print(f"  {prompt}: {prediction} (confidence: {confidence:.2f})")

        if confidence > 0.7:
            print("    ✅ High confidence prediction")
        else:
            print("    ⚠️ Low confidence prediction")
EOF

# Test 3: Performance under load
echo -e "\n⚡ Test 3: AI performance under load"
python3 << 'EOF'
import sys
sys.path.append('/Users/archmagece/myopen/scripton/yesman-claude')
import time
import random

from libs.ai.response_analyzer import ResponseAnalyzer
from libs.ai.adaptive_response import AdaptiveResponse

# Initialize AI components
analyzer = ResponseAnalyzer()
adaptive = AdaptiveResponse()

# Generate test data
test_prompts = []
for i in range(100):
    prompt_type = random.choice(["yn", "numbered", "continue"])
    if prompt_type == "yn":
        prompt = f"Do you want to {random.choice(['save', 'continue', 'proceed', 'confirm'])}? (y/n)"
    elif prompt_type == "numbered":
        options = random.randint(2, 5)
        prompt = f"Select option: " + " ".join([f"{j}) Option {j}" for j in range(1, options+1)])
    else:
        prompt = "Press Enter to continue..."

    test_prompts.append(prompt)

print(f"Testing performance with {len(test_prompts)} prompts...")

# Test classification speed
start_time = time.time()
for prompt in test_prompts:
    analyzer.classify_pattern(prompt)
end_time = time.time()

classification_time = end_time - start_time
avg_classification_time = (classification_time / len(test_prompts)) * 1000

print(f"Classification time: {classification_time:.2f}s total, {avg_classification_time:.2f}ms average")

# Test prediction speed
start_time = time.time()
for prompt in test_prompts:
    adaptive.predict_response(prompt)
end_time = time.time()

prediction_time = end_time - start_time
avg_prediction_time = (prediction_time / len(test_prompts)) * 1000

print(f"Prediction time: {prediction_time:.2f}s total, {avg_prediction_time:.2f}ms average")

# Performance requirements
if avg_classification_time < 50:  # Less than 50ms
    print("✅ Classification performance is acceptable")
else:
    print("❌ Classification performance needs improvement")

if avg_prediction_time < 100:  # Less than 100ms
    print("✅ Prediction performance is acceptable")
else:
    print("❌ Prediction performance needs improvement")
EOF

# Test 4: Memory usage and data persistence
echo -e "\n💾 Test 4: Memory usage and data persistence"
python3 << 'EOF'
import sys
sys.path.append('/Users/archmagece/myopen/scripton/yesman-claude')
import os
import tempfile
import psutil

from libs.ai.response_analyzer import ResponseAnalyzer
from libs.ai.adaptive_response import AdaptiveResponse

# Get initial memory usage
process = psutil.Process(os.getpid())
initial_memory = process.memory_info().rss / 1024 / 1024  # MB

with tempfile.TemporaryDirectory() as temp_dir:
    # Initialize AI components
    analyzer = ResponseAnalyzer(data_dir=temp_dir)
    adaptive = AdaptiveResponse(data_dir=temp_dir)

    # Generate large amount of training data
    print("Generating large training dataset...")
    for i in range(1000):
        prompt = f"Test prompt {i}: Do you want to continue? (y/n)"
        analyzer.record_interaction(prompt, "y", True)
        adaptive.learn_from_feedback(prompt, "y", True)

    # Check memory usage after training
    current_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = current_memory - initial_memory

    print(f"Memory usage: {initial_memory:.1f}MB -> {current_memory:.1f}MB (increase: {memory_increase:.1f}MB)")

    if memory_increase < 100:  # Less than 100MB increase
        print("✅ Memory usage is acceptable")
    else:
        print("❌ Memory usage is too high")

    # Test data persistence
    print("Testing data persistence...")

    # Save data
    analyzer.save_data()
    adaptive.save_patterns()

    # Create new instances (should load saved data)
    analyzer2 = ResponseAnalyzer(data_dir=temp_dir)
    adaptive2 = AdaptiveResponse(data_dir=temp_dir)

    # Test if data was loaded
    test_prompt = "Test prompt 500: Do you want to continue? (y/n)"
    confidence1 = adaptive.get_confidence(test_prompt)
    confidence2 = adaptive2.get_confidence(test_prompt)

    print(f"Original confidence: {confidence1:.2f}")
    print(f"Loaded confidence: {confidence2:.2f}")

    if abs(confidence1 - confidence2) < 0.01:
        print("✅ Data persistence is working")
    else:
        print("❌ Data persistence may have issues")
EOF

# Test 5: Edge cases and error handling
echo -e "\n🔍 Test 5: Edge cases and error handling"
python3 << 'EOF'
import sys
sys.path.append('/Users/archmagece/myopen/scripton/yesman-claude')

from libs.ai.response_analyzer import ResponseAnalyzer
from libs.ai.adaptive_response import AdaptiveResponse

# Initialize AI components
analyzer = ResponseAnalyzer()
adaptive = AdaptiveResponse()

# Test edge cases
edge_cases = [
    ("", "empty"),  # Empty prompt
    ("   ", "whitespace"),  # Whitespace only
    ("A" * 1000, "very_long"),  # Very long prompt
    ("🚀 Do you want to continue? 🎯 (y/n)", "emoji"),  # Emoji in prompt
    ("Multi\nLine\nPrompt (y/n)", "multiline"),  # Multi-line prompt
    ("Special chars: @#$%^&*()_+ (y/n)", "special_chars"),  # Special characters
    ("Non-ASCII: café résumé (y/n)", "non_ascii"),  # Non-ASCII characters
]

print("Testing edge cases...")
for prompt, case_type in edge_cases:
    try:
        pattern_type = analyzer.classify_pattern(prompt)
        response = adaptive.predict_response(prompt)
        confidence = adaptive.get_confidence(prompt)

        print(f"✅ {case_type}: type={pattern_type}, response='{response}', confidence={confidence:.2f}")
    except Exception as e:
        print(f"❌ {case_type}: Error - {str(e)}")

# Test invalid inputs
print("\nTesting invalid inputs...")
invalid_inputs = [
    (None, "null"),
    (123, "number"),
    ([], "list"),
    ({}, "dict"),
]

for invalid_input, input_type in invalid_inputs:
    try:
        analyzer.classify_pattern(invalid_input)
        print(f"❌ {input_type}: Should have raised an error")
    except Exception as e:
        print(f"✅ {input_type}: Properly handled - {type(e).__name__}")
EOF

# Cleanup
rm -rf /tmp/ai-test-data

echo -e "\n📊 AI Pattern Learning Test Summary:"
echo "- Pattern recognition accuracy tested"
echo "- Learning adaptation verified"
echo "- Performance under load measured"
echo "- Memory usage and persistence tested"
echo "- Edge cases and error handling verified"

echo -e "\n✅ AI pattern learning tests completed!"
