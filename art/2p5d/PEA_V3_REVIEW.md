# P/E/A Motion V3 Review

Status: IMPLEMENTATION_IN_PROGRESS

## Confirmed source layouts

- P: 3x2
- E: 3x2
- A: 2x3

A had been interpreted by the runtime as 3x2, which physically split its source poses incorrectly.

## Candidate pipeline

- preserve S as the existing 6-frame path
- normalize P/E/A key poses by foot anchor
- preserve meaningful disconnected creature components
- generate one single-silhouette optical-flow inbetween per key transition
- output P/E/A as 12-frame 4x3 sheets

## Review

Bidirectional blend candidate: REJECT (double heads/limbs on E/A).

Single-silhouette candidate after layout detection: KEEP FOR RUNTIME VALIDATION.

This does not mark P/E/A final art. Promotion depends on live desktop/mobile race review.
