import { Hono } from "hono";
import { cors } from 'hono/cors';
import { getCookie, setCookie } from 'hono/cookie';
import {
  exchangeCodeForSessionToken,
  getOAuthRedirectUrl,
  authMiddleware,
  deleteSession,
  MOCHA_SESSION_TOKEN_COOKIE_NAME,
} from "@getmocha/users-service/backend";

interface Env {
  MOCHA_USERS_SERVICE_API_URL: string;
  MOCHA_USERS_SERVICE_API_KEY: string;
  DB: D1Database;
}

const app = new Hono<{ Bindings: Env }>();

// Enable CORS
app.use('*', cors({
  origin: ['http://localhost:5173', 'https://aurion.app'],
  credentials: true,
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
}));

// Auth routes
app.get('/api/oauth/google/redirect_url', async (c) => {
  const redirectUrl = await getOAuthRedirectUrl('google', {
    apiUrl: c.env.MOCHA_USERS_SERVICE_API_URL,
    apiKey: c.env.MOCHA_USERS_SERVICE_API_KEY,
  });

  return c.json({ redirectUrl }, 200);
});

app.post("/api/sessions", async (c) => {
  const body = await c.req.json();

  if (!body.code) {
    return c.json({ error: "No authorization code provided" }, 400);
  }

  const sessionToken = await exchangeCodeForSessionToken(body.code, {
    apiUrl: c.env.MOCHA_USERS_SERVICE_API_URL,
    apiKey: c.env.MOCHA_USERS_SERVICE_API_KEY,
  });

  setCookie(c, MOCHA_SESSION_TOKEN_COOKIE_NAME, sessionToken, {
    httpOnly: true,
    path: "/",
    sameSite: "none",
    secure: true,
    maxAge: 60 * 24 * 60 * 60, // 60 days
  });

  return c.json({ success: true }, 200);
});

app.get("/api/users/me", authMiddleware, async (c) => {
  const user = c.get("user");
  
  // Check if user exists in our database, create if not
  const existingUser = await c.env.DB.prepare(
    "SELECT * FROM users WHERE id = ?"
  ).bind(user!.id).first();

  if (!existingUser) {
    await c.env.DB.prepare(
      "INSERT INTO users (id, email, display_name, avatar_url) VALUES (?, ?, ?, ?)"
    ).bind(
      user!.id,
      user!.email,
      user!.google_user_data.name || user!.email.split('@')[0],
      user!.google_user_data.picture
    ).run();
  }

  return c.json(user);
});

app.get('/api/logout', async (c) => {
  const sessionToken = getCookie(c, MOCHA_SESSION_TOKEN_COOKIE_NAME);

  if (typeof sessionToken === 'string') {
    await deleteSession(sessionToken, {
      apiUrl: c.env.MOCHA_USERS_SERVICE_API_URL,
      apiKey: c.env.MOCHA_USERS_SERVICE_API_KEY,
    });
  }

  setCookie(c, MOCHA_SESSION_TOKEN_COOKIE_NAME, '', {
    httpOnly: true,
    path: '/',
    sameSite: 'none',
    secure: true,
    maxAge: 0,
  });

  return c.json({ success: true }, 200);
});

// Chat sessions
app.get('/api/chat/sessions', authMiddleware, async (c) => {
  const user = c.get("user");
  const { results } = await c.env.DB.prepare(
    "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC"
  ).bind(user!.id).all();

  return c.json(results);
});

app.post('/api/chat/sessions', authMiddleware, async (c) => {
  const user = c.get("user");
  const body = await c.req.json();
  const sessionId = crypto.randomUUID();

  await c.env.DB.prepare(
    "INSERT INTO chat_sessions (id, user_id, title) VALUES (?, ?, ?)"
  ).bind(sessionId, user!.id, body.title || 'New Chat').run();

  return c.json({ id: sessionId, title: body.title || 'New Chat' });
});

app.put('/api/chat/sessions/:id', authMiddleware, async (c) => {
  const user = c.get("user");
  const sessionId = c.req.param('id');
  const body = await c.req.json();

  await c.env.DB.prepare(
    "UPDATE chat_sessions SET title = ?, is_pinned = ?, is_saved = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?"
  ).bind(body.title, body.is_pinned, body.is_saved, sessionId, user!.id).run();

  return c.json({ success: true });
});

app.delete('/api/chat/sessions/:id', authMiddleware, async (c) => {
  const user = c.get("user");
  const sessionId = c.req.param('id');

  await c.env.DB.prepare(
    "DELETE FROM messages WHERE session_id = ? AND user_id = ?"
  ).bind(sessionId, user!.id).run();
  
  await c.env.DB.prepare(
    "DELETE FROM chat_sessions WHERE id = ? AND user_id = ?"
  ).bind(sessionId, user!.id).run();

  return c.json({ success: true });
});

// Messages
app.get('/api/chat/sessions/:id/messages', authMiddleware, async (c) => {
  const user = c.get("user");
  const sessionId = c.req.param('id');
  
  const { results } = await c.env.DB.prepare(
    "SELECT * FROM messages WHERE session_id = ? AND user_id = ? ORDER BY created_at ASC"
  ).bind(sessionId, user!.id).all();

  return c.json(results);
});

app.post('/api/chat/sessions/:id/messages', authMiddleware, async (c) => {
  const user = c.get("user");
  const sessionId = c.req.param('id');
  const body = await c.req.json();
  const messageId = crypto.randomUUID();

  await c.env.DB.prepare(
    "INSERT INTO messages (id, session_id, user_id, content, message_type, attachments, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)"
  ).bind(
    messageId,
    sessionId,
    user!.id,
    body.content,
    body.message_type,
    JSON.stringify(body.attachments || []),
    JSON.stringify(body.metadata || {})
  ).run();

  return c.json({ id: messageId });
});

// Tasks
app.get('/api/tasks', authMiddleware, async (c) => {
  const user = c.get("user");
  const status = c.req.query('status');
  
  let query = "SELECT * FROM tasks WHERE user_id = ?";
  const params = [user!.id];
  
  if (status) {
    query += " AND status = ?";
    params.push(status);
  }
  
  query += " ORDER BY created_at DESC";
  
  const { results } = await c.env.DB.prepare(query).bind(...params).all();
  return c.json(results);
});

app.post('/api/tasks', authMiddleware, async (c) => {
  const user = c.get("user");
  const body = await c.req.json();
  const taskId = crypto.randomUUID();

  await c.env.DB.prepare(
    "INSERT INTO tasks (id, user_id, title, description, status, priority, due_date, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
  ).bind(
    taskId,
    user!.id,
    body.title,
    body.description || null,
    body.status || 'pending',
    body.priority || 'medium',
    body.due_date || null,
    JSON.stringify(body.tags || [])
  ).run();

  return c.json({ id: taskId });
});

app.put('/api/tasks/:id', authMiddleware, async (c) => {
  const user = c.get("user");
  const taskId = c.req.param('id');
  const body = await c.req.json();

  await c.env.DB.prepare(
    "UPDATE tasks SET title = ?, description = ?, status = ?, priority = ?, due_date = ?, tags = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?"
  ).bind(
    body.title,
    body.description,
    body.status,
    body.priority,
    body.due_date,
    JSON.stringify(body.tags || []),
    taskId,
    user!.id
  ).run();

  return c.json({ success: true });
});

app.delete('/api/tasks/:id', authMiddleware, async (c) => {
  const user = c.get("user");
  const taskId = c.req.param('id');

  await c.env.DB.prepare(
    "DELETE FROM tasks WHERE id = ? AND user_id = ?"
  ).bind(taskId, user!.id).run();

  return c.json({ success: true });
});

// Highlights
app.post('/api/highlights', authMiddleware, async (c) => {
  const user = c.get("user");
  const body = await c.req.json();
  const highlightId = crypto.randomUUID();

  await c.env.DB.prepare(
    "INSERT INTO highlights (id, user_id, message_id, text_content, color, start_offset, end_offset, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
  ).bind(
    highlightId,
    user!.id,
    body.message_id,
    body.text_content,
    body.color,
    body.start_offset,
    body.end_offset,
    body.notes || null
  ).run();

  return c.json({ id: highlightId });
});

app.get('/api/highlights/:messageId', authMiddleware, async (c) => {
  const user = c.get("user");
  const messageId = c.req.param('messageId');
  
  const { results } = await c.env.DB.prepare(
    "SELECT * FROM highlights WHERE message_id = ? AND user_id = ? ORDER BY start_offset ASC"
  ).bind(messageId, user!.id).all();

  return c.json(results);
});

// File uploads (placeholder - would integrate with R2 in production)
app.post('/api/upload', authMiddleware, async (c) => {
  const user = c.get("user");
  const formData = await c.req.formData();
  const file = formData.get('file') as File;
  
  if (!file) {
    return c.json({ error: 'No file provided' }, 400);
  }

  const fileId = crypto.randomUUID();
  const filename = file.name;
  const fileType = file.type;
  const fileSize = file.size;
  
  // In production, upload to R2 bucket
  const fileUrl = `https://placeholder-cdn.com/${fileId}/${filename}`;

  await c.env.DB.prepare(
    "INSERT INTO file_uploads (id, user_id, filename, file_type, file_size, file_url) VALUES (?, ?, ?, ?, ?, ?)"
  ).bind(fileId, user!.id, filename, fileType, fileSize, fileUrl).run();

  return c.json({
    id: fileId,
    filename,
    file_type: fileType,
    file_size: fileSize,
    file_url: fileUrl
  });
});

export default app;
