SELECT *, CASE
  WHEN COALESCE(cold_card,false) AND COALESCE(new_merchant,false) THEN 'BOTH_NODES_UNSEEN'
  WHEN COALESCE(cold_card,false) THEN 'NEW_CARD_ONLY'
  WHEN COALESCE(new_merchant,false) THEN 'NEW_MERCHANT_ONLY'
  WHEN COALESCE(pair_new,false) THEN 'WARM_PAIR_NEW'
  ELSE 'WARM_PAIR_SEEN'
END AS cold_start_segment
FROM decision_input;
