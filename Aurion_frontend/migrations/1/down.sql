
-- Drop indexes
DROP INDEX IF EXISTS idx_file_uploads_user_id;
DROP INDEX IF EXISTS idx_mini_threads_message_id;
DROP INDEX IF EXISTS idx_mini_threads_user_id;
DROP INDEX IF EXISTS idx_highlights_user_id;
DROP INDEX IF EXISTS idx_highlights_message_id;
DROP INDEX IF EXISTS idx_tasks_status;
DROP INDEX IF EXISTS idx_tasks_user_id;
DROP INDEX IF EXISTS idx_messages_user_id;
DROP INDEX IF EXISTS idx_messages_session_id;
DROP INDEX IF EXISTS idx_chat_sessions_user_id;

-- Drop tables
DROP TABLE IF EXISTS file_uploads;
DROP TABLE IF EXISTS mini_threads;
DROP TABLE IF EXISTS highlights;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS chat_sessions;
DROP TABLE IF EXISTS users;
