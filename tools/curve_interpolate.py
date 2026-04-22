#!/usr/bin/env python3
"""
Generate non-linear source curve from 3 data points via quadratic interpolation.

Usage:
    python tools/curve_interpolate.py 25,0 60,12 100,18 --step 5
    python tools/curve_interpolate.py 25,0 60,12 100,18 --step 5 -o curve.json
    python tools/curve_interpolate.py 25,0 60,12 100,18 --step 5 --csv curve.csv
"""

import argparse
import csv
import json
import sys


def fit_quadratic(p1, p2, p3):
    """Fit P = aT^2 + bT + c from 3 (T, P) points. Returns (a, b, c)."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    denom = (x1 - x2) * (x1 - x3) * (x2 - x3)
    if abs(denom) < 1e-15:
        raise ValueError("Three points must have distinct temperatures")

    a = (x3 * (y2 - y1) + x2 * (y1 - y3) + x1 * (y3 - y2)) / denom
    b = (x3 * x3 * (y1 - y2) + x2 * x2 * (y3 - y1) + x1 * x1 * (y2 - y3)) / denom
    c = (x2 * x3 * (x2 - x3) * y1 + x3 * x1 * (x3 - x1) * y2 + x1 * x2 * (x1 - x2) * y3) / denom
    return a, b, c


def evaluate(a, b, c, t):
    return a * t * t + b * t + c


def main():
    parser = argparse.ArgumentParser(
        description="Generate curve from 3 data points (quadratic interpolation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/curve_interpolate.py 25,0 60,12 100,18 --step 5
  python tools/curve_interpolate.py 25,0 60,12 100,18 --step 5 -o curve.json
  python tools/curve_interpolate.py 25,0 60,12 100,18 --step 5 --csv curve.csv

Output JSON is compatible with floxml_nonlinear_source.py:
  python -m floxml_tools.floxml_nonlinear_source input.xml --config curve.json -o output.xml
        """,
    )
    parser.add_argument("p1", help="Start point: temperature,power (e.g. 25,0)")
    parser.add_argument("p2", help="Middle point: temperature,power (e.g. 60,12)")
    parser.add_argument("p3", help="End point: temperature,power (e.g. 100,18)")
    parser.add_argument("--step", type=float, default=5, help="Temperature step (default: 5)")
    parser.add_argument("--name", default="Source", help="Source name for JSON output (default: Source)")
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

    # Sort by temperature
    points = sorted([p1, p2, p3], key=lambda p: p[0])
    a, b, c = fit_quadratic(points[0], points[1], points[2])

    t_min = points[0][0]
    t_max = points[2][0]
    step = args.step

    # Generate curve
    curve = []
    t = t_min
    while t <= t_max + step * 0.01:
        t_clamped = min(t, t_max)
        p = evaluate(a, b, c, t_clamped)
        curve.append({"temperature": round(t_clamped, 6), "power": round(p, 6)})
        t += step

    # Print
    print(f"Fitted: P = {a:.6g} * T^2 + {b:.6g} * T + {c:.6g}")
    print(f"Range: T = {t_min} to {t_max}, step = {step}")
    print(f"Points ({len(curve)}):")
    for pt in curve:
        print(f"  T={pt['temperature']:>8.2f}  P={pt['power']:>10.4f}")

    # JSON output
    if args.output:
        config = {"sources": [{"name": args.name, "curve": curve}]}
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] JSON: {args.output}")

    # CSV output
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
