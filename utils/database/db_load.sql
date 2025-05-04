SELECT
   datname,
   xact_commit + xact_rollback,
   stats_reset
FROM pg_stat_database;
