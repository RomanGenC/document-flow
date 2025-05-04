SELECT state, count(*)
FROM pg_stat_activity
GROUP BY state;
