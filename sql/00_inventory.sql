-- Part 2 inventory helper. Replace the glob with the file names emitted by src/ingest.py.
SELECT file_name, file_size_mb, row_count, column_count, primary_grain, candidate_key, date_min, date_max
FROM read_csv_auto('reports/data_inventory.csv');
