import matplotlib.pyplot as plt
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

accuracy, recall, coverage = [], [], []

for s, gt in sentences:
    m = sentence_metrics(s, gt)
    accuracy.append(m["accuracy"])
    recall.append(m["recall"])
    coverage.append(m["coverage"])

avg_accuracy = sum(accuracy) / len(accuracy)
avg_recall = sum(recall) / len(recall)
avg_coverage = sum(coverage) / len(coverage)

# Existing work values (TAKEN FROM LITERATURE – NOT CLAIMED AS SAME TASK)
existing_accuracy = 0.82
existing_recall = 0.80
existing_coverage = 0.70

labels = ["Accuracy", "Recall", "Vocabulary Coverage"]
existing_vals = [existing_accuracy, existing_recall, existing_coverage]
proposed_vals = [avg_accuracy, avg_recall, avg_coverage]

x = range(len(labels))
width = 0.35

plt.figure(figsize=(7, 5))
plt.bar(x, existing_vals, width, label="Existing Systems")
plt.bar([i + width for i in x], proposed_vals, width, label="Proposed System")

plt.xticks([i + width / 2 for i in x], labels)
plt.ylabel("Metric Value")
plt.title("Performance Comparison with Existing Systems")
plt.legend()
plt.ylim(0, 1)
plt.tight_layout()
plt.show()
