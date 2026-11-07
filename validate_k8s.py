import yaml
import glob
import sys

def validate_yaml():
    print("Validating Kubernetes Manifests...")
    files = glob.glob("k8s/*.yaml")
    if not files:
        print("No YAML files found.")
        sys.exit(1)
        
    for file in files:
        try:
            with open(file, "r") as f:
                docs = yaml.safe_load_all(f)
                count = 0
                for doc in docs:
                    if doc is not None:
                        count += 1
                        if "apiVersion" not in doc or "kind" not in doc:
                            raise ValueError(f"Missing apiVersion or kind in {file}")
                print(f"  [OK] {file} ({count} documents parsed)")
        except Exception as e:
            print(f"  [ERROR] {file}: {e}")
            sys.exit(1)
    print("All manifests are valid YAML.")

if __name__ == "__main__":
    validate_yaml()