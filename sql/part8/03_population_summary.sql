SELECT split_name, channel, COUNT(*) AS transactions, SUM(positive_exposure) AS exposure
FROM private_monitoring_mart
GROUP BY 1, 2;

