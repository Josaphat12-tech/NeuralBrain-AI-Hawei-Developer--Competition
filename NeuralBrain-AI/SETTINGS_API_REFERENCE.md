# 🧩 Settings & Profile API Reference Card

**Quick Lookup for Developers**

---

## 📍 Base Endpoint
All endpoints require authentication (`@login_required`)

```
https://localhost:5000
```

---

## 📋 Endpoints

### 1️⃣ Get User Settings
```
GET /api/user/settings
```
**Returns**: All user preferences from database
```json
{
  "success": true,
  "data": {
    "theme": "dark",
    "data_refresh_rate": 60,
    "critical_alerts_enabled": true
  }
}
```

---

### 2️⃣ Save User Settings
```
POST /api/user/settings
Content-Type: application/json
```
**Body**:
```json
{
  "theme": "dark",
  "data_refresh_rate": 60,
  "critical_alerts_enabled": true,
  "email_notifications": true,
  "timezone": "UTC",
  "language": "en",
  "exports_format": "json"
}
```
**Response**: 200 OK with updated settings

---

### 3️⃣ Get User Profile
```
GET /api/user/profile
```
**Returns**: User account information
```json
{
  "success": true,
  "data": {
    "id": "user_id",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile_image": "/static/uploads/avatars/user_avatar.jpg",
    "role": "admin",
    "created_at": "2026-02-09T10:00:00",
    "last_login": "2026-02-09T15:45:00"
  }
}
```

---

### 4️⃣ Upload Avatar
```
POST /api/user/profile/avatar
Content-Type: multipart/form-data
```
**Form Data**:
- `avatar`: PNG, JPG, JPEG, GIF, or WebP file

**Response**:
```json
{
  "success": true,
  "url": "/static/uploads/avatars/user_id_avatar.jpg"
}
```

---

### 5️⃣ Export Health Data
```
POST /api/data/export
Content-Type: application/json
```
**Body**:
```json
{
  "format": "json",
  "days": 30
}
```
**Response**: File download (JSON or CSV)

---

## 🎯 Settings Fields Explained

| Field | Type | Values | Default | Purpose |
|-------|------|--------|---------|---------|
| `theme` | string | `'dark'`, `'light'` | `'dark'` | Color scheme |
| `data_refresh_rate` | int | 30, 60, 120, 300 | 60 | Dashboard update frequency (seconds) |
| `critical_alerts_enabled` | bool | `true`, `false` | `true` | Show critical warnings |
| `email_notifications` | bool | `true`, `false` | `true` | Email alerts |
| `timezone` | string | `'UTC'`, `'America/New_York'`, etc | `'UTC'` | User timezone |
| `language` | string | `'en'`, `'es'`, `'fr'` | `'en'` | UI language |
| `exports_format` | string | `'json'`, `'csv'` | `'json'` | Export file format |

---

## 🔄 Data Flow

```
User Updates Settings
        ↓
JavaScript POST /api/user/settings
        ↓
Flask validates request
        ↓
Load UserSettings from DB
        ↓
Update fields
        ↓
Save to database (auto-timestamp)
        ↓
Update session cache
        ↓
Return 200 + data
        ↓
JavaScript shows success toast
        ↓
Settings applied (theme, refresh rate, etc)
```

---

## ⚠️ Error Responses

### 401 Unauthorized
```json
{
  "error": "User not found"
}
```
**Cause**: User not logged in or session expired

### 400 Bad Request
```json
{
  "success": false,
  "error": "Invalid file type. Allowed: png, jpg, jpeg, gif, webp"
}
```
**Cause**: Invalid input or file type

### 404 Not Found
```json
{
  "error": "User not found"
}
```
**Cause**: User not in database

---

## 💡 Usage Examples

### Update Theme
```javascript
await fetch('/api/user/settings', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ theme: 'light' })
});
```

### Change Refresh Rate
```javascript
await fetch('/api/user/settings', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ data_refresh_rate: 120 })
});
```

### Upload Avatar
```javascript
const formData = new FormData();
formData.append('avatar', fileInput.files[0]);

const response = await fetch('/api/user/profile/avatar', {
  method: 'POST',
  body: formData
});
```

### Export Data
```javascript
await fetch('/api/data/export', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    format: 'json',
    days: 30
  })
});
```

---

## 🔐 Authentication

All endpoints require valid session. Attach to requests:

**From Browser**: Automatic (cookies)  
**From API**: `Authorization: Bearer <token>`

---

## 📱 UI Integration Points

### Settings Page
```
GET /settings → Loads form with current user data and settings
POST /settings → Updates profile (form submission)
```

### Dashboard
Use `user.settings.data_refresh_rate` for auto-refresh interval

### Alerts
Check `user.settings.critical_alerts_enabled` before showing alerts

### Theme
Apply `user.settings.theme` to `data-theme` attribute

---

## 🚨 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Settings not saving | DB error | Check logs, verify table exists |
| Avatar not uploading | Invalid file | Only PNG/JPG/GIF/WebP allowed |
| Export fails | No data | Ensure health records exist |
| API returns 401 | Not logged in | Login first, check session |

---

## 📊 Database Schema

```sql
CREATE TABLE user_settings (
  id INTEGER PRIMARY KEY,
  user_id VARCHAR(100) UNIQUE NOT NULL,
  theme VARCHAR(20) DEFAULT 'dark',
  data_refresh_rate INTEGER DEFAULT 60,
  critical_alerts_enabled BOOLEAN DEFAULT TRUE,
  email_notifications BOOLEAN DEFAULT TRUE,
  timezone VARCHAR(50) DEFAULT 'UTC',
  language VARCHAR(10) DEFAULT 'en',
  exports_format VARCHAR(20) DEFAULT 'json',
  created_at DATETIME,
  updated_at DATETIME,
  FOREIGN KEY(user_id) REFERENCES users(id)
);
```

---

## ✅ Checklist for Implementation

- [ ] `UserSettings` model created
- [ ] API endpoints defined
- [ ] Settings template with forms
- [ ] Avatar upload working
- [ ] Data export tested
- [ ] Database persistence verified
- [ ] All tests passing
- [ ] Responsive design verified
- [ ] Error handling tested
- [ ] Documentation complete

---

**Last Updated**: February 9, 2026  
**Version**: 1.0.0  
**Status**: Production Ready
