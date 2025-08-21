import matplotlib.pyplot as plt
import numpy as np

# Time vector
t = np.linspace(0, 10, 500)


# Gamma function: symbolic deviation
def gamma(t, alpha, kappa, noise_amplitude=0.0):
    noise = noise_amplitude * np.random.normal(0, 1, len(t))
    return np.exp(-alpha * t) * np.sin(kappa * t) + noise


# Simulated profiles
gamma_2e = gamma(t, alpha=0.8, kappa=2.5, noise_amplitude=0.05)
gamma_stable = gamma(t, alpha=1.5, kappa=0.5, noise_amplitude=0.01)
gamma_collapse = gamma(t, alpha=0.3, kappa=3.5, noise_amplitude=0.15)

# Plot
plt.figure(figsize=(10, 5))
plt.plot(t, gamma_2e, label="2e Profile", color="orange")
plt.plot(t, gamma_stable, label="Stable Profile", color="green")
plt.plot(t, gamma_collapse, label="Collapse Profile", color="red")
plt.axhline(0, color="gray", linestyle="--", linewidth=1)
plt.xlabel("Time (t)")
plt.ylabel("Symbolic Deviation γ(t)")
plt.title("Simulated Symbolic Trajectories")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
