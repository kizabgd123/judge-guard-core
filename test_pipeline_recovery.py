#!/usr/bin/env python3
import os
import subprocess
import time
from deployment_pipeline_v2 import SelfHealingPipeline

def test_dependency_healing():
    print("\n--- Test Case: Dependency Healing ---")
    # Temporarily uninstall a dependency
    subprocess.run(["pip", "uninstall", "-y", "python-dotenv"])

    pipeline = SelfHealingPipeline()
    success = pipeline.run()

    # Verify it was reinstalled
    import importlib.util
    spec = importlib.util.find_spec("dotenv")
    if spec:
        print("✅ python-dotenv reinstalled successfully")
    else:
        print("❌ python-dotenv NOT reinstalled")

    return success

def test_rollback_on_failure():
    print("\n--- Test Case: Rollback on Unfixable Failure ---")
    # Introduce a code error that cannot be fixed automatically
    with open("tests/test_judge_guard.py", "a") as f:
        f.write("\ndef test_intentional_fail(): assert False\n")

    pipeline = SelfHealingPipeline()
    success = pipeline.run()

    # Check if file was restored by rollback
    with open("tests/test_judge_guard.py", "r") as f:
        content = f.read()
        if "test_intentional_fail" not in content:
            print("✅ Rollback restored tests/test_judge_guard.py")
        else:
            print("❌ Rollback failed to restore tests/test_judge_guard.py")

    return not success # Should be False if rollback worked

if __name__ == "__main__":
    s1 = test_dependency_healing()
    s2 = test_rollback_on_failure()

    if s1 and s2:
        print("\n🏆 All recovery tests passed!")
    else:
        print("\n⚠️ Some recovery tests failed.")
