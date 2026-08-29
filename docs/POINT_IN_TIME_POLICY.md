# Part 2 — Point-in-Time Policy

Decision time `T0` is the transaction event timestamp. Current transaction attributes may be used only when available at `T0`. Historical features must use records with:

```text
history.transaction_timestamp < current.transaction_timestamp
```

The strict `< T0` rule prevents same-timestamp ambiguity and excludes future outcomes. `fraud_label`, investigation outcomes, chargebacks and any post-event status are never features. The validation query in `sql/06_pit_validation.sql` records zero violations for the locked analytical base.
