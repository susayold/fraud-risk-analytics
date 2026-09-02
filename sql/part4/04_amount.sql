/* Positive-purchase velocity and prior amount baselines. Current amount is used only after prior aggregates are computed. */
CREATE OR REPLACE TABLE analytics.part4_amount_features AS
WITH prior AS (
  SELECT source_row_id, amount,
         COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) OVER w_24h, 0) AS user_positive_amount_sum_24h,
         COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) OVER w_7d, 0) AS user_positive_amount_sum_7d,
         COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) OVER c_24h, 0) AS card_positive_amount_sum_24h,
         COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) OVER c_7d, 0) AS card_positive_amount_sum_7d,
         AVG(amount) FILTER (WHERE amount > 0) OVER w_all AS user_prior_positive_amount_mean,
         STDDEV_SAMP(amount) FILTER (WHERE amount > 0) OVER w_all AS user_prior_positive_amount_std,
         COUNT(*) FILTER (WHERE amount > 0) OVER w_all AS user_prior_positive_amount_count,
         AVG(amount) FILTER (WHERE amount > 0) OVER c_all AS card_prior_positive_amount_mean,
         STDDEV_SAMP(amount) FILTER (WHERE amount > 0) OVER c_all AS card_prior_positive_amount_std,
         COUNT(*) FILTER (WHERE amount > 0) OVER c_all AS card_prior_positive_amount_count
  FROM analytics.part4_behavior_source
  WINDOW w_all AS (PARTITION BY user_id ORDER BY transaction_timestamp RANGE BETWEEN UNBOUNDED PRECEDING AND INTERVAL '1 microsecond' PRECEDING),
         w_24h AS (PARTITION BY user_id ORDER BY transaction_timestamp RANGE BETWEEN INTERVAL '24 hours' PRECEDING AND INTERVAL '1 microsecond' PRECEDING),
         w_7d AS (PARTITION BY user_id ORDER BY transaction_timestamp RANGE BETWEEN INTERVAL '7 days' PRECEDING AND INTERVAL '1 microsecond' PRECEDING),
         c_all AS (PARTITION BY card_key ORDER BY transaction_timestamp RANGE BETWEEN UNBOUNDED PRECEDING AND INTERVAL '1 microsecond' PRECEDING),
         c_24h AS (PARTITION BY card_key ORDER BY transaction_timestamp RANGE BETWEEN INTERVAL '24 hours' PRECEDING AND INTERVAL '1 microsecond' PRECEDING),
         c_7d AS (PARTITION BY card_key ORDER BY transaction_timestamp RANGE BETWEEN INTERVAL '7 days' PRECEDING AND INTERVAL '1 microsecond' PRECEDING)
)
SELECT source_row_id,
       amount > 0 AS current_positive_amount,
       user_positive_amount_sum_24h, user_positive_amount_sum_7d,
       card_positive_amount_sum_24h, card_positive_amount_sum_7d,
       user_prior_positive_amount_mean, user_prior_positive_amount_std,
       card_prior_positive_amount_mean, card_prior_positive_amount_std,
       CASE WHEN amount > 0 AND user_prior_positive_amount_mean > 0 THEN amount / user_prior_positive_amount_mean ELSE NULL END AS current_positive_amount_vs_user_mean,
       CASE WHEN amount > 0 AND card_prior_positive_amount_mean > 0 THEN amount / card_prior_positive_amount_mean ELSE NULL END AS current_positive_amount_vs_card_mean,
       CASE WHEN amount > 0 AND user_prior_positive_amount_count >= 5 AND user_prior_positive_amount_std > 0 THEN (amount - user_prior_positive_amount_mean) / user_prior_positive_amount_std ELSE NULL END AS current_positive_amount_user_z,
       CASE WHEN amount > 0 AND card_prior_positive_amount_count >= 5 AND card_prior_positive_amount_std > 0 THEN (amount - card_prior_positive_amount_mean) / card_prior_positive_amount_std ELSE NULL END AS current_positive_amount_card_z
FROM prior;

