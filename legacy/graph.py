import matplotlib.pyplot as plt

# Input sentence indices
sentences = [0, 1, 2, 3, 4, 5, 6]

# Vocabulary Utilization values from updated table
utilization = [0.13, 0.087, 0.087, 0.043, 0.065, 0.109, 0.043]

plt.figure(figsize=(7,5))

bars = plt.bar(sentences, utilization)

# Labels
plt.xlabel("Sentence Index")
plt.ylabel("Vocabulary Utilization")
plt.title("Vocabulary Utilization Across Inputs")

# Add values above bars
for bar, val in zip(bars, utilization):
    plt.text(
        bar.get_x() + bar.get_width()/2,
        bar.get_height() + 0.003,
        str(val),
        ha='center'
    )

plt.ylim(0, 0.15)

plt.tight_layout()
plt.show()