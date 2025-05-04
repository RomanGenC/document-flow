SELECT
   relname,
   seq_scan,
   idx_scan,
   idx_scan/seq_scan as IndexStat
FROM pg_stat_all_tables
WHERE seq_scan <> 0
ORDER BY IndexStat DESC;
