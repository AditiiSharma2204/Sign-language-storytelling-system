from sentence_evaluation import sentence_metrics

sentences = [
    ("the cat want to play", ["cat", "want", "play"]),
    ("the dog drink water", ["dog", "drink", "water"]),
    ("the family play together", ["family", "play"]),
    ("the girl go school", ["girl", "go", "school"]),
    ("the cat wantzz to play", ["cat", "want", "play"]),
    ("the boy and dog play", ["boy", "dog", "play"]),
    ("the bird fly in sky", ["bird", "fly"]),
    ("the woman walk to school", ["woman", "walk", "school"])
]

results = []

for s, gt in sentences:
    metrics = sentence_metrics(s, gt)
    results.append(metrics)

# Compute averages
avg_accuracy = sum(r["accuracy"] for r in results) / len(results)
avg_recall = sum(r["recall"] for r in results) / len(results)
avg_coverage = sum(r["coverage"] for r in results) / len(results)

print("\n=== OUR SYSTEM AVERAGE METRICS ===")
print(f"Accuracy  : {round(avg_accuracy, 3)}")
print(f"Recall    : {round(avg_recall, 3)}")
print(f"Coverage  : {round(avg_coverage, 3)}")
