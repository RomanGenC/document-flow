SELECT
   datname,
   usename,
   now() - xact_start AS TransactionDuration,
   now() - query_start as QueryDuration
FROM pg_stat_activity
WHERE state = 'active';
