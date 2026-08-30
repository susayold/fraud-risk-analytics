/* Matrix contract is checked in Python before fit. Identifiers and outcomes are audit-only. */
DESCRIBE analytics.part4_evaluation_v1;

/* The executable contract excludes the following audit-only columns:
   source_row_id, user_id, card_key, merchant_id_raw, split_name, fraud_label. */
/*
SELECT column_name, data_type
FROM pragma_table_info('analytics.part4_evaluation_v1')
WHERE column_name NOT IN ('source_row_id','user_id','card_key','merchant_id_raw','split_name','fraud_label');
*/
