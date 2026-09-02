SELECT *, amount AS signed_amount,
       GREATEST(amount, 0) AS positive_exposure,
       ABS(amount) AS absolute_exposure
FROM decision_input;
