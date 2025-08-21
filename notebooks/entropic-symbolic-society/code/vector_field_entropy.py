import matplotlib.pyplot as plt
import numpy as np

# Symbolic parameters
alpha = np.linspace(0.1, 2.0, 20)
kappa = np.linspace(0.1, 4.0, 20)
A, K = np.meshgrid(alpha, kappa)

# Recursive entropy surface
E_r = K**2 / A
dE_dalpha = -(K**2) / A**2
dE_dkappa = 2 * K / A

# Vector field components
U = -dE_dalpha  # α-direction
V = dE_dkappa  # κ-direction

# Plot streamlines
fig, ax = plt.subplots(figsize=(10, 6))
stream = ax.streamplot(A, K, U, V, color=E_r, linewidth=1.2, cmap="plasma")
plt.colorbar(stream.lines, ax=ax, label="Recursive Entropy E_r")
ax.set_xlabel("Anchoring Coefficient α")
ax.set_ylabel("Semantic Curvature κ")
ax.set_title("Symbolic Vector Field: ∇E_r(α, κ)")
ax.grid(True)
plt.tight_layout()
plt.show()
