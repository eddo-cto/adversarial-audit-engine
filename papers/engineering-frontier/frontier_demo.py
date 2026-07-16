#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""frontier_demo.py — runnable demonstration for THE_ENGINEERING_FRONTIER.md.
Standard library only. Prints every number quoted in the note.

Exhibit A: reducible vacuity is bounded by the independence supply.
  Correlated evidence (intraclass error-correlation rho with the evaluator's nature) carries
  effective count n_eff = N/(1+(N-1)rho), NOT N. Vacuity u = W/(W + n_eff*rbar) therefore
  plateaus at u_inf(rho) = W/(W + rbar/rho) > 0 for rho>0, and -> 0 only for rho=0.
  We SIMULATE correlated Bernoulli evidence and recover n_eff empirically (matches Kish),
  then read off the vacuity floor.

Exhibit B: without an anchor you cannot measure rho / correctness.
  Internal agreement is symmetric under p <-> 1-p: a consensus that is right w.p. p and one
  that is wrong w.p. p (i.e. right w.p. 1-p) AGREE EXACTLY AS MUCH. So no function of internal
  agreement identifies correctness (internal LLR = 0). One external (anchored) draw separates
  them (KL > 0). This is the peer-prediction / Schelling-oracle wall.
"""
import random, math, statistics
from collections import Counter

random.seed(20260716)

# ----------------------------------------------------------------------
# Exhibit A
# ----------------------------------------------------------------------
def kish_neff(N, rho):
    return N / (1.0 + (N - 1) * rho)

def correlated_bernoulli(N, theta, rho):
    """N Bernoulli(theta) with pairwise intraclass correlation exactly rho.
       Copying a shared latent Z~Bern(theta) with prob c gives Corr = c^2, so use c = sqrt(rho)."""
    c = math.sqrt(rho)
    Z = 1 if random.random() < theta else 0
    return [Z if random.random() < c else (1 if random.random() < theta else 0) for _ in range(N)]

def empirical_neff(N, theta, rho, reps=40000):
    """n_eff = theta(1-theta) / Var(mean of N equicorrelated draws)."""
    means = []
    for _ in range(reps):
        s = correlated_bernoulli(N, theta, rho)
        means.append(sum(s) / N)
    var_corr = statistics.pvariance(means)
    return (theta * (1 - theta)) / var_corr if var_corr > 0 else float('inf')

def vacuity(n_eff, W, rbar):
    return W / (W + n_eff * rbar)

def exhibit_A():
    W, rbar, theta = 2.0, 1.0, 0.5
    print("=" * 74)
    print("EXHIBIT A  -  reducible vacuity is bounded by the independence supply")
    print("           W=%.1f, r_bar=%.1f, theta=%.1f" % (W, rbar, theta))
    print("=" * 74)
    print("%5s | %6s | %10s | %10s | %8s | %10s"
          % ("rho", "N", "n_eff Kish", "n_eff emp.", "u(N)", "u_inf(rho)"))
    print("-" * 74)
    for rho in (0.0, 0.01, 0.1, 0.5, 1.0):
        u_inf = 0.0 if rho == 0 else vacuity(1.0 / rho, W, rbar)
        for N in (1, 10, 100, 1000):
            nk = kish_neff(N, rho)
            ne = empirical_neff(N, theta, rho) if N in (10, 100) else float('nan')
            ne_s = ("%10.2f" % ne) if ne == ne else ("%10s" % "-")
            print("%5.2f | %6d | %10.2f | %s | %8.4f | %10.4f"
                  % (rho, N, nk, ne_s, vacuity(nk, W, rbar), u_inf))
        print("-" * 74)
    print("Reading: rho=0  -> n_eff=N, u -> 0            (anchored stratum: engineering closes it)")
    print("         rho=1  -> n_eff=1 for all N, u pinned (self-ref stratum: no internal probe closes it)")
    print("         empirical n_eff matches the Kish formula -> the floor is real, not an artifact.\n")

# ----------------------------------------------------------------------
# Exhibit B
# ----------------------------------------------------------------------
def agree_prob(p):
    """P(two independent sources give the same label), each correct w.p. p about a fixed truth."""
    return p * p + (1 - p) * (1 - p)

def exhibit_B(p=0.8, N=9, reps=200000):
    q = 1 - p
    A_right, A_wrong = agree_prob(p), agree_prob(q)
    print("=" * 74)
    print("EXHIBIT B  -  internal agreement does not identify correctness (no anchor)")
    print("           truth=1; World_right: each source correct w.p. p=%.2f" % p)
    print("                    World_wrong: each source correct w.p. q=1-p=%.2f" % q)
    print("=" * 74)
    print("internal P(two agree):  right=%.4f   wrong=%.4f   identical? %s"
          % (A_right, A_wrong, math.isclose(A_right, A_wrong)))
    def votes(pc):
        return sum(1 if random.random() < pc else 0 for _ in range(N))
    hist_r, hist_w = Counter(), Counter()
    for _ in range(reps):
        hist_r[votes(p)] += 1
        hist_w[votes(q)] += 1
    flip_match = all(abs(hist_r[k] / reps - hist_w[N - k] / reps) < 0.01 for k in range(N + 1))
    print("vote-count histogram of 'wrong' equals the label-flipped histogram of 'right': %s" % flip_match)
    print("  -> the two worlds are observationally identical up to an unobservable label flip")
    print("     (a confidently-wrong consensus agrees exactly as much as a confidently-right one).")
    def kl(a, b):
        return a * math.log(a / b) + (1 - a) * math.log((1 - a) / (1 - b))
    print("\nONE anchored draw (source vs ground truth):  P(match) right=%.2f, wrong=%.2f" % (p, q))
    print("   KL(right || wrong) = %.4f nats  > 0   -> a single external draw separates them." % kl(p, q))
    print("   correctness gap |p-q| = %.2f, invisible internally, visible with an anchor.\n" % abs(p - q))

if __name__ == "__main__":
    exhibit_A()
    exhibit_B()
    print("=" * 74)
    print("Frontier: both exhibits turn on the SAME quantity, the independence/error-correlation rho.")
    print("A prices the irreducible residue u_inf(rho); B shows rho itself is unmeasurable without an")
    print("anchor. Non-closure = the engine certifying it has reached rho-saturation and routing the")
    print("residue to an external, different-nature eye. Closure - of this note too - is external.")
    print("=" * 74)
