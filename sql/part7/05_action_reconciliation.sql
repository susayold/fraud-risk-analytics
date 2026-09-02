SELECT COUNT(*) AS transactions,
       COUNT(*) FILTER (WHERE action='ALLOW') AS allow_count,
       COUNT(*) FILTER (WHERE action='REVIEW') AS review_count,
       COUNT(*) FILTER (WHERE action='BLOCK') AS block_count,
       COUNT(*) FILTER (WHERE action NOT IN ('ALLOW','REVIEW','BLOCK')) AS invalid_actions
FROM policy_actions;
