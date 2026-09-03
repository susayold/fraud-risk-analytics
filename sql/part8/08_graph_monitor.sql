SELECT operational_window_id,
       AVG(CASE WHEN pair_new THEN 1 ELSE 0 END) AS pair_new_rate,
       AVG(CASE WHEN cold_card THEN 1 ELSE 0 END) AS cold_card_rate,
       AVG(CASE WHEN new_merchant THEN 1 ELSE 0 END) AS new_merchant_rate,
       AVG(CASE WHEN cross_community THEN 1 ELSE 0 END) AS cross_community_rate
FROM monitoring_windows
GROUP BY 1;

