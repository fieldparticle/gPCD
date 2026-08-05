# TODO

## Internal Momentum Diagnostic

- Current `INTERNAL_MOMENTUM` coloring uses `length(P[index].parms.yzw)`.
- `parms.yzw` is a diagnostic/recoverable internal momentum accumulator updated from contact impulse-like force integration.
- This is not yet the desired collision-start accounting model:
  `mv(start of collision) = mv(collision point) + mv(stored during collision)`.
- Revisit this before adding new behavior such as bonding, compression/rebound storage, or contact-owned energy transfer.
