/* Predefined OOT subgroup definitions. No post-OOT tuning is allowed. */
SELECT source_row_id,
       CASE WHEN use_chip = 'Online Transaction' THEN 'Online'
            WHEN use_chip = 'Swipe Transaction' THEN 'Swipe'
            WHEN use_chip = 'Chip Transaction' THEN 'Chip'
            ELSE 'Other/Unknown' END AS channel_group,
       CASE WHEN card_cold_start = 1 THEN 'cold_start_card' ELSE 'established_card' END AS card_history_group,
       CASE WHEN card_merchant_is_new = 1 THEN 'new_card_merchant' ELSE 'known_card_merchant' END AS relationship_group
FROM analytics.part4_evaluation_v1;
