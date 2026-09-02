-- Join labels only in the evaluation layer, after actions were generated.
SELECT action, COUNT(*) AS rows, SUM(fraud_label) AS fraud_rows,
       SUM(positive_exposure * fraud_label) AS fraud_exposure
FROM policy_actions_with_evaluation_label
GROUP BY action;
