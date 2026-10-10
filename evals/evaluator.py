import json
import re
import urllib.request
import urllib.error

API_URL = "http://localhost:8000/api/chat"
DATASET_FILE = "evals/dataset.jsonl"


def ask_fowforge(question):
    data = json.dumps({"question": question}).encode("utf-8")
    request = urllib.request.Request(API_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        print("API error:", error.code)
        print(error.read().decode("utf-8"))
        return None
    except Exception as error:
        print("Request failed:", error)
        return None


def evaluate_source(result, expected_source):
    if result is None:
        return False
    return any(source.get("document") == expected_source for source in result.get("sources", []))


def evaluate_citations(result):
    if result is None:
        return False
    answer = result.get("answer", "")
    if not answer.strip():
        return False
    return bool(re.findall(r"(?:\[S\d+\]|\u3010S\d+\u3011)", answer))


def evaluate_groundedness(result):
    if result is None:
        return False
    answer = result.get("answer", "")
    sources = result.get("sources", [])
    if not answer.strip() or not sources:
        return False
    context = " ".join(source.get("text", "") for source in sources).lower()
    answer_words = re.findall(r"\b[a-zA-Z]{5,}\b", answer.lower())
    if not answer_words:
        return False
    matched = sum(word in context for word in answer_words)
    return matched / len(answer_words) >= 0.30


def evaluate_unknown_handling(result):
    if result is None:
        return False
    answer = result.get("answer", "").lower()
    markers = ["not available", "does not contain", "not enough information", "cannot answer", "provided context"]
    return any(marker in answer for marker in markers)


def main():
    with open(DATASET_FILE, "r", encoding="utf-8") as file:
        cases = [json.loads(line) for line in file if line.strip()]
    metrics = {"retrieval": 0, "citation": 0, "groundedness": 0, "unknown": 0}
    total = len(cases)
    print("=" * 64)
    print("FowForge Evaluation v3")
    print("=" * 64)
    for i, case in enumerate(cases, 1):
        print(f"\nTest {i}/{total}: {case['question']}")
        result = ask_fowforge(case["question"])
        expected_answer = case.get("expect_answer", True)
        if expected_answer:
            checks = {
                "Retrieval": evaluate_source(result, case["expected_source"]),
                "Citation": evaluate_citations(result),
                "Groundedness": evaluate_groundedness(result),
            }
            metrics["retrieval"] += checks["Retrieval"]
            metrics["citation"] += checks["Citation"]
            metrics["groundedness"] += checks["Groundedness"]
        else:
            checks = {"Unknown handling": evaluate_unknown_handling(result)}
            metrics["unknown"] += checks["Unknown handling"]
        for name, ok in checks.items():
            print(f"{name}: {'PASS' if ok else 'FAIL'}")
        if result:
            print("Answer:", result.get("answer", ""))
    positive = sum(1 for c in cases if c.get("expect_answer", True))
    unknown_total = total - positive
    print("\n" + "=" * 64)
    print("Evaluation Summary")
    print("=" * 64)
    print(f"Retrieval Accuracy: {(metrics['retrieval']/positive)*100:.2f}%")
    print(f"Citation Accuracy: {(metrics['citation']/positive)*100:.2f}%")
    print(f"Groundedness Score: {(metrics['groundedness']/positive)*100:.2f}%")
    print(f"Unknown Handling: {(metrics['unknown']/unknown_total)*100:.2f}%" if unknown_total else "Unknown Handling: N/A")
    print("=" * 64)


if __name__ == "__main__":
    main()
