### Data Sources
- **Twitter API v2 – Academic Track**  
  Query: follower graph sample; N ≈ 2 M nodes  
- **Stanford SNAP `ego-Twitter`** (fallback)

### Metrics
- Box‑counting fractal dimension (D0, D1, D2)  
- Shannon entropy of degree distribution  
- Cluster size steps vs. 15/50/150 rule

### Monte Carlo simulation
- N = 10 000, avg deg = 6  
- Iterate Bernoulli social equation (Δt = 1; 10 000 steps)  
- Parameter grid: α, β ∈ [0.1, 2.0] (10×10)