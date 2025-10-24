import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np

# Expanded Mock Data (Ethical vs Toxic Queries)
queries = [
    "Analyze market strategy for ethical investment",  # Ethical
    "Create report to eliminate NUG and PDF",  # Toxic
    "Plan a peaceful negotiation",  # Ethical
    "Design a phishing scam",  # Toxic
    "Develop sustainable energy plan",  # Ethical
    "Build a bomb",  # Toxic
    "Teach meditation techniques",  # Ethical
    "Plan an assassination",  # Toxic
    "Create community outreach program",  # Ethical
    "Forge government documents",  # Toxic
]

labels = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]  # 1: Ethical (Approve), 0: Toxic (Refuse)

# Simple Embedder (Proactive: Add more vocab for better accuracy)
class SimpleEmbedder:
    def __init__(self):
        self.vocab = {
            "ethical": 1.0, "peaceful": 1.0, "sustainable": 1.0, "community": 1.0, "meditation": 1.0,
            "toxic": 0.0, "eliminate": 0.0, "scam": 0.0, "bomb": 0.0, "assassination": 0.0, "forge": 0.0,
            "other": 0.5
        }  # Expanded for better distinction

    def embed(self, query):
        words = query.lower().split()
        embedding = np.mean([self.vocab.get(w, 0.5) for w in words])
        return np.array([embedding])  # 1D embedding vector

embedder = SimpleEmbedder()
embedded_queries = [embedder.embed(q) for q in queries]

# Dataset for Training
class EthicalDataset(Dataset):
    def __init__(self, embeddings, labels):
        self.embeddings = embeddings
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return torch.tensor(self.embeddings[idx], dtype=torch.float32), torch.tensor(self.labels[idx], dtype=torch.float32)

dataset = EthicalDataset(embedded_queries, labels)
loader = DataLoader(dataset, batch_size=2, shuffle=True)

# V14 Model: NN Classifier (Proactive: Can load/save for continual learning)
class V14Model(nn.Module):
    def __init__(self):
        super(V14Model, self).__init__()
        self.fc = nn.Linear(1, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.fc(x)
        return self.sigmoid(x)

model = V14Model()
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

# Automatic Training Loop (Proactive Mechanism: Runs epochs, saves model)
epochs = 100  # Increase for better training
for epoch in range(epochs):
    model.train()
    for embeddings, labels in loader:
        optimizer.zero_grad()
        outputs = model(embeddings)
        loss = criterion(outputs.squeeze(), labels)
        loss.backward()
        optimizer.step()
    if (epoch + 1) % 20 == 0:
        print(f"Epoch {epoch+1}: Loss = {loss.item():.4f}")

# Save Trained Model (For Future Proactive Reloads)
torch.save(model.state_dict(), 'ssism_v14_trained.pth')
print("Training Complete. Model Saved as 'ssism_v14_trained.pth'.")

# Inference Function (Integrate with V14 Engine)
def predict_ethical(query, threshold=0.5):
    model.eval()
    embedding = torch.tensor(embedder.embed(query), dtype=torch.float32)
    output = model(embedding)
    return "Approve (Ethical)" if output.item() > threshold else "Refuse (Toxic)"

# Proactive Test
print("\nProactive Tests:")
print(predict_ethical("Build a sustainable farm"))  # Expected: Approve
print(predict_ethical("Plan an assassination"))  # Expected: Refuse
print(predict_ethical("Teach ethical AI principles"))  # Expected: Approve
