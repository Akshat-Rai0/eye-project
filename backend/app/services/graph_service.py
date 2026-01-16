import numpy as np
from umap import UMAP

def calculate_2d_projection(embeddings):
    # Convert input to numpy array immediately
    embeddings = np.array(embeddings)
    n_samples = len(embeddings)


    # but practically needs more than 1 to avoid projection errors
    if n_samples < 2:
        return np.zeros((n_samples, 2)).tolist()
    
    # Adjust n_neighbors to not exceed the number of samples
    # UMAP usually likes n_neighbors < n_samples
    n_neighbors = min(15, n_samples - 1)
    if n_neighbors < 2: n_neighbors = 2

    reducer = UMAP(
        n_neighbors=n_neighbors, 
        min_dist=1, 
        n_components=2, 
        random_state=42
    )
    
    projection = reducer.fit_transform(embeddings)
    
    # Robust Normalization
    p_min, p_max = projection.min(axis=0), projection.max(axis=0)
    rng = p_max - p_min
    
    # Avoid division by zero if all points are identical
    rng[rng == 0] = 1 
    
    normalized = (projection - p_min) / rng * 1000
    
    return normalized.tolist()