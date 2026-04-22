#!/usr/bin/env python3
"""
Generate non-linear source curve from 3 data points.

Supports curve types:
  exponential:  P = a * exp(b * T) + c  (3-param, exact fit through all points, default)
  exponential2: P = a * exp(b * T)       (2-param, least squares on log)
  quadratic:    P = a * T^2 + b * T + c  (exact fit through all points)

Usage:
    python tools/curve_interpolate.py 25,0 60,12 100,18 --step 5
    python tools/curve_interpolate.py 25,1 60,12 100,18 --step 5 -o curve.json
    python tools/curve_interpolate.py 25,0 60,12 100,18 --step 5 --csv curve.csv
    python tools/curve_interpolate.py 25,0 60,12 100,18 --step 5 --type quadratic
"""

import argparse
import csv
import json
import math
import sys


def fit_quadratic(p1, p2, p3):
    """Fit P = aT^2 + bT + c from 3 points. Returns (eval_fn, formula_str)."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    denom = (x1 - x2) * (x1 - x3) * (x2 - x3)
    if abs(denom) < 1e-15:
        raise ValueError("Three points must have distinct temperatures")

    a = (x3 * (y2 - y1) + x2 * (y1 - y3) + x1 * (y3 - y2)) / denom
    b = (x3**2 * (y1 - y2) + x2**2 * (y3 - y1) + x1**2 * (y2 - y3)) / denom
    c = (x2 * x3 * (x2 - x3) * y1 + x3 * x1 * (x3 - x1) * y2 + x1 * x2 * (x1 - x2) * y3) / denom

    def eval_fn(t):
        return a * t * t + b * t + c

    return eval_fn, f"P = {a:.6g} * T^2 + ({b:.6g}) * T + ({c:.6g})"


def fit_exponential(p1, p2, p3):
    """Fit P = a * exp(b * T) + c from 3 points exactly. Returns (eval_fn, formula_str).

    Solves for c via bisection on two intervals:
      1. c < min(P): all (Pi - c) > 0, gives a > 0
      2. c > max(P): all (Pi - c) < 0, gives a < 0
    """
    t1, y1 = p1
    t2, y2 = p2
    t3, y3 = p3
    y_min = min(y1, y2, y3)
    y_max = max(y1, y2, y3)

    def _h(c):
        d1, d2, d3 = y1 - c, y2 - c, y3 - c
        if d1 * d2 <= 0 or d2 * d3 <= 0:
            return None
        return math.log(d1 / d2) / (t1 - t2) - math.log(d2 / d3) / (t2 - t3)

    # Try bisection on two intervals
    intervals = [
        (y_min - 1e8, y_min - 1e-12),   # c < min(P)
        (y_max + 1e-12, y_max + 1e8),    # c > max(P)
    ]

    for c_lo, c_hi in intervals:
        h_lo, h_hi = _h(c_lo), _h(c_hi)
        if h_lo is None or h_hi is None:
            continue
        if h_lo * h_hi > 0:
            continue

        for _ in range(200):
            c_mid = (c_lo + c_hi) / 2
            h_mid = _h(c_mid)
            if h_mid is None:
                if c_lo < y_min or c_lo > y_max:
                    c_hi = c_mid
                else:
                    c_lo = c_mid
                continue
            if abs(h_mid) < 1e-14 or (c_hi - c_lo) < 1e-14:
                break
            if h_mid * h_lo < 0:
                c_hi = c_mid
            else:
                c_lo = c_mid
                h_lo = h_mid
        else:
            continue
        break
    else:
        raise ValueError(
            "Cannot fit P = a*exp(b*T)+c to these points.\n"
            "Try --type exponential2 (2-param) or --type quadratic."
        )

    c = (c_lo + c_hi) / 2
    b = math.log((y1 - c) / (y2 - c)) / (t1 - t2)
    a = (y1 - c) / math.exp(b * t1)

    def eval_fn(t):
        return a * math.exp(b * t) + c

    return eval_fn, f"P = {a:.6g} * exp({b:.6g} * T) + ({c:.6g})"


def fit_exponential2(p1, p2, p3):
    """Fit P = a * exp(b * T) via log-linear least squares. Returns (eval_fn, formula_str).

    All power values must be > 0.
    """
    points = [p1, p2, p3]
    for label, (_, p) in zip(["1st", "2nd", "3rd"], points):
        if p <= 0:
            raise ValueError(
                f"exponential2 requires all P > 0, but {label} point has P={p}.\n"
                f"Use --type exponential or --type quadratic."
            )

    xs = [p[0] for p in points]
    ys = [math.log(p[1]) for p in points]
    n = 3
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xx = sum(x * x for x in xs)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    denom = n * sum_xx - sum_x**2
    b = (n * sum_xy - sum_x * sum_y) / denom
    a = math.exp((sum_y - b * sum_x) / n)

    def eval_fn(t):
        return a * math.exp(b * t)

    return eval_fn, f"P = {a:.6g} * exp({b:.6g} * T)"


def generate_curve(eval_fn, t_min, t_max, step):
    curve = []
    t = t_min
    while t <= t_max + step * 0.01:
        tc = min(t, t_max)
        curve.append({"temperature": round(tc, 6), "power": round(eval_fn(tc), 6)})
        t += step
    return curve


def main():
    parser = argparse.ArgumentParser(
        description="Generate curve from 3 data points",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Exponential 3-param (default, exact fit)
  python tools/curve_interpolate.py 25,0 60,12 100,18 --step 5

  # Exponential 2-param (least squares, all P must be > 0)
  python tools/curve_interpolate.py 25,1 60,12 100,18 --step 5 --type exponential2

  # Quadratic
  python tools/curve_interpolate.py 25,0 60,12 100,18 --step 5 --type quadratic

  # Output JSON / CSV
  python tools/curve_interpolate.py 25,0 60,12 100,18 --step 5 -o curve.json --csv curve.csv

Output JSON is compatible with floxml_nonlinear_source.py:
  python -m floxml_tools.floxml_nonlinear_source input.xml --config curve.json -o output.xml
        """,
    )
    parser.add_argument("p1", help="Start point: temperature,power (e.g. 25,0)")
    parser.add_argument("p2", help="Middle point: temperature,power (e.g. 60,12)")
    parser.add_argument("p3", help="End point: temperature,power (e.g. 100,18)")
    parser.add_argument("--step", type=float, default=5, help="Temperature step (default: 5)")
    parser.add_argument("--type", choices=["exponential", "exponential2", "quadratic"],
                        default="exponential",
                        help="Curve type (default: exponential)")
    parser.add_argument("--name", default="Source", help="Source name for JSON output")
    parser.add_argument("-o", "--output", help="Output JSON file")
    parser.add_argument("--csv", help="Output CSV file")
    args = parser.parse_args()

    def parse_point(s):
        parts = s.split(",")
        if len(parts) != 2:
            raise ValueError(f"Invalid point '{s}', expected format: temperature,power")
        return float(parts[0]), float(parts[1])

    p1 = parse_point(args.p1)
    p2 = parse_point(args.p2)
    p3 = parse_point(args.p3)
    points = sorted([p1, p2, p3], key=lambda p: p[0])

    fitters = {
        "exponential": fit_exponential,
        "exponential2": fit_exponential2,
        "quadratic": fit_quadratic,
    }
    eval_fn, formula_str = fitters[args.type](points[0], points[1], points[2])

    t_min, t_max = points[0][0], points[2][0]
    curve = generate_curve(eval_fn, t_min, t_max, args.step)

    # Print
    print(f"Fitted: {formula_str}")
    print(f"Input points vs fitted:")
    for tp, pp in points:
        pf = eval_fn(tp)
        err = abs(pf - pp) / max(abs(pp), 1e-10) * 100
        print(f"  T={tp:>8.1f}  P_input={pp:>10.4f}  P_fit={pf:>10.4f}  err={err:.4f}%")
    print(f"\nRange: T = {t_min} to {t_max}, step = {args.step}")
    print(f"Output ({len(curve)} points):")
    for pt in curve:
        print(f"  T={pt['temperature']:>8.2f}  P={pt['power']:>10.4f}")

    if args.output:
        config = {"sources": [{"name": args.name, "curve": curve}]}
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] JSON: {args.output}")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["temperature", "power"])
            for pt in curve:
                writer.writerow([pt["temperature"], pt["power"]])
        print(f"[OK] CSV: {args.csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
