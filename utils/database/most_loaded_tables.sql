SELECT
   relname,
   n_tup_upd+n_tup_ins+n_tup_del AS operationsAmount
FROM pg_stat_all_tables
ORDER BY operationsAmount DESC;
