#!/usr/bin/env python3
"""
Biometric Neural Network Model

Siamese Network architecture for gesture-based authentication.
Uses 1D-CNN for spatial features + LSTM for temporal dynamics.

Architecture:
    Input: (batch, 3, 128) - [dx, dy, dt] channels
    Conv1D layers: Extract spatial patterns (sharp turns, jitters)
    LSTM layer: Capture temporal dynamics (rhythm, timing)
    Output: (batch, 128) - Embedding vector

Usage:
    model = TouchIDNet(embedding_dim=128)
    embedding = model(tensor)  # tensor shape: (batch, 3, 128)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class TouchIDNet(nn.Module):
    """
    Siamese Network for biometric gesture authentication.
    
    This network learns to map gestures into an embedding space where:
    - Same user's gestures are close together (high similarity)
    - Different users' gestures are far apart (low similarity)
    
    Architecture:
    1. Conv1D layers: Detect local patterns (curves, angles, speed changes)
    2. LSTM layer: Capture temporal dependencies (rhythm, hesitations)
    3. Fully connected: Project to embedding space
    """
    
    def __init__(self, embedding_dim: int = 128, dropout: float = 0.3):
        """
        Initialize TouchIDNet.
        
        Args:
            embedding_dim: Size of output embedding vector (default: 128)
            dropout: Dropout rate for regularization (default: 0.3)
        """
        super(TouchIDNet, self).__init__()
        
        self.embedding_dim = embedding_dim
        
        # Convolutional layers for spatial feature extraction
        # Input: (batch, 3, 128) - 3 channels [dx, dy, dt]
        
        # Conv1: Detect local patterns (kernel_size=5 sees 5 consecutive points)
        self.conv1 = nn.Conv1d(
            in_channels=3,      # [dx, dy, dt]
            out_channels=32,    # 32 feature maps
            kernel_size=5,
            padding=2           # Keep sequence length = 128
        )
        self.bn1 = nn.BatchNorm1d(32)
        
        # Conv2: Detect higher-level patterns
        self.conv2 = nn.Conv1d(
            in_channels=32,
            out_channels=64,
            kernel_size=5,
            padding=2
        )
        self.bn2 = nn.BatchNorm1d(64)
        
        # Conv3: Even higher-level patterns
        self.conv3 = nn.Conv1d(
            in_channels=64,
            out_channels=128,
            kernel_size=3,
            padding=1
        )
        self.bn3 = nn.BatchNorm1d(128)
        
        # Max pooling to reduce sequence length
        self.pool = nn.MaxPool1d(kernel_size=2, stride=2)  # 128 -> 64 -> 32 -> 16
        
        # LSTM for temporal dynamics
        # After 3 pooling layers: sequence length = 128 / 8 = 16
        self.lstm = nn.LSTM(
            input_size=128,      # From conv3 output channels
            hidden_size=128,     # LSTM hidden state size
            num_layers=2,        # 2-layer LSTM
            batch_first=True,
            dropout=dropout,
            bidirectional=True   # Bidirectional to see past and future context
        )
        
        # Fully connected layers to embedding
        # LSTM output: 128 * 2 (bidirectional) = 256
        self.fc1 = nn.Linear(256, 256)
        self.dropout1 = nn.Dropout(dropout)
        
        self.fc2 = nn.Linear(256, embedding_dim)
        
        # L2 normalization for embeddings (important for cosine similarity)
        self.l2_norm = True
    
    def forward(self, x):
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch, 3, 128)
               Channels: [dx, dy, dt]
        
        Returns:
            Embedding vector of shape (batch, embedding_dim)
        """
        # Input shape: (batch, 3, 128)
        
        # Convolutional feature extraction
        # Conv1 + ReLU + BatchNorm + Pool
        x = self.conv1(x)           # (batch, 32, 128)
        x = F.relu(x)
        x = self.bn1(x)
        x = self.pool(x)            # (batch, 32, 64)
        
        # Conv2 + ReLU + BatchNorm + Pool
        x = self.conv2(x)           # (batch, 64, 64)
        x = F.relu(x)
        x = self.bn2(x)
        x = self.pool(x)            # (batch, 64, 32)
        
        # Conv3 + ReLU + BatchNorm + Pool
        x = self.conv3(x)           # (batch, 128, 32)
        x = F.relu(x)
        x = self.bn3(x)
        x = self.pool(x)            # (batch, 128, 16)
        
        # Prepare for LSTM: (batch, channels, seq_len) -> (batch, seq_len, channels)
        x = x.permute(0, 2, 1)      # (batch, 16, 128)
        
        # LSTM for temporal dynamics
        # output: (batch, seq_len, hidden_size * 2)
        # hidden: tuple of (h_n, c_n)
        lstm_out, (h_n, c_n) = self.lstm(x)  # lstm_out: (batch, 16, 256)
        
        # Use last hidden state from both directions
        # h_n shape: (num_layers * 2, batch, hidden_size)
        # We want the last layer's forward and backward hidden states
        forward_hidden = h_n[-2, :, :]   # (batch, 128)
        backward_hidden = h_n[-1, :, :]  # (batch, 128)
        hidden = torch.cat([forward_hidden, backward_hidden], dim=1)  # (batch, 256)
        
        # Fully connected layers
        x = self.fc1(hidden)        # (batch, 256)
        x = F.relu(x)
        x = self.dropout1(x)
        
        x = self.fc2(x)             # (batch, embedding_dim)
        
        # L2 normalization (important for cosine similarity)
        if self.l2_norm:
            x = F.normalize(x, p=2, dim=1)
        
        return x
    
    def get_embedding(self, x):
        """
        Convenience method to get embedding (same as forward).
        
        Args:
            x: Input tensor of shape (batch, 3, 128)
        
        Returns:
            Embedding vector of shape (batch, embedding_dim)
        """
        return self.forward(x)


class SiameseNetwork(nn.Module):
    """
    Siamese Network wrapper for training with pairs/triplets.
    
    Uses the same TouchIDNet for both inputs to ensure
    weight sharing (critical for Siamese architecture).
    """
    
    def __init__(self, embedding_dim: int = 128, dropout: float = 0.3):
        """
        Initialize Siamese Network.
        
        Args:
            embedding_dim: Size of embedding vector
            dropout: Dropout rate
        """
        super(SiameseNetwork, self).__init__()
        
        # Single shared network
        self.embedding_net = TouchIDNet(embedding_dim=embedding_dim, dropout=dropout)
    
    def forward(self, x1, x2=None, x3=None):
        """
        Forward pass for pairs or triplets.
        
        Args:
            x1: Anchor tensor (batch, 3, 128)
            x2: Positive/Comparison tensor (batch, 3, 128) [optional]
            x3: Negative tensor (batch, 3, 128) [optional for triplet]
        
        Returns:
            If x2 and x3 provided: (anchor_emb, positive_emb, negative_emb)
            If only x2 provided: (anchor_emb, comparison_emb)
            If only x1 provided: anchor_emb
        """
        emb1 = self.embedding_net(x1)
        
        if x2 is not None:
            emb2 = self.embedding_net(x2)
            
            if x3 is not None:
                emb3 = self.embedding_net(x3)
                return emb1, emb2, emb3
            
            return emb1, emb2
        
        return emb1
    
    def get_embedding(self, x):
        """Get embedding for a single input."""
        return self.embedding_net(x)


def cosine_similarity(emb1, emb2):
    """
    Compute cosine similarity between embeddings.
    
    Args:
        emb1: Embedding tensor (batch, embedding_dim) or (embedding_dim,)
        emb2: Embedding tensor (batch, embedding_dim) or (embedding_dim,)
    
    Returns:
        Similarity score in range [-1, 1]
        1 = identical, 0 = orthogonal, -1 = opposite
    """
    return F.cosine_similarity(emb1, emb2, dim=-1)


def euclidean_distance(emb1, emb2):
    """
    Compute Euclidean distance between embeddings.
    
    Args:
        emb1: Embedding tensor (batch, embedding_dim)
        emb2: Embedding tensor (batch, embedding_dim)
    
    Returns:
        Distance (lower = more similar)
    """
    return torch.norm(emb1 - emb2, p=2, dim=-1)


if __name__ == "__main__":
    print("TouchIDNet - Biometric Neural Network")
    print("=" * 60)
    
    # Test model
    model = TouchIDNet(embedding_dim=128)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"Model: TouchIDNet")
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    
    # Test forward pass
    batch_size = 4
    dummy_input = torch.randn(batch_size, 3, 128)
    
    print(f"\nTest forward pass:")
    print(f"  Input shape: {dummy_input.shape}")
    
    with torch.no_grad():
        output = model(dummy_input)
    
    print(f"  Output shape: {output.shape}")
    print(f"  Output norm: {torch.norm(output, p=2, dim=1).mean():.4f} (should be ~1.0)")
    
    # Test Siamese Network
    print(f"\nTest Siamese Network:")
    siamese = SiameseNetwork(embedding_dim=128)
    
    anchor = torch.randn(batch_size, 3, 128)
    positive = torch.randn(batch_size, 3, 128)
    negative = torch.randn(batch_size, 3, 128)
    
    with torch.no_grad():
        emb_a, emb_p, emb_n = siamese(anchor, positive, negative)
    
    print(f"  Anchor embedding: {emb_a.shape}")
    print(f"  Positive embedding: {emb_p.shape}")
    print(f"  Negative embedding: {emb_n.shape}")
    
    # Test similarity
    sim_pos = cosine_similarity(emb_a, emb_p).mean()
    sim_neg = cosine_similarity(emb_a, emb_n).mean()
    
    print(f"\n  Cosine similarity (anchor-positive): {sim_pos:.4f}")
    print(f"  Cosine similarity (anchor-negative): {sim_neg:.4f}")
    print(f"  (After training, positive should be > negative)")
    
    print("\n✓ Model architecture validated")
