# Reviewer Under Review — Public Release Manifest

## Release identity

**Project**: Reviewer Under Review  
**Public version**: v0.1.0  
**Snapshot**: af50c66 public release  
**Canonical framing**: benchmark and debugging harness for AI paper-review systems

## What this public release includes

This public release combines two distinct layers of evidence.

### 1. Benchmark-wide headline totals

These numbers describe the full released calibration benchmark used by the public website headline and benchmark table.

- **48 papers**
- **24 accepted / 24 rejected**
- **864 match graphs**
- **670 official concerns**
- **79 decisive blockers**

These headline totals should be used when describing the benchmark as a whole.

### 2. Named Papers public artifact slice

These numbers describe the smaller public slice for which end-to-end raw artifacts are included and linked in the demo.

- **9 named papers**
- **7 accepted / 2 rejected**
- **54 released match graphs**
- **150 official concerns**
- **102 resolved in rebuttal**
- **48 unresolved**
- **7 decisive blockers in the public slice**

These totals should be used when describing the case studies, the Named Papers section, or the files present in the public zip.

## How to describe the release

Reviewer Under Review includes a 48-paper safety/alignment benchmark (the calibration set behind the paper's headline numbers and 864 match graphs) and a separate 9-paper Named Papers public slice with end-to-end artifacts and a follow-up verdict-inference audit using the same methodology. The 9-paper slice is intended for case-study reading and end-to-end verification, and strengthens the case studies; it is **not** part of the 48-paper benchmark or the paper appendix and should not be described as drawn from it.

## Structural note about the local zip

The public zip is best read as a review and artifact packet rather than a full source checkout. It ships the demo, benchmark-wide aggregate metrics, and the raw end-to-end artifacts for the nine Named Papers, and is intended for reading and verification rather than as a complete development environment.
