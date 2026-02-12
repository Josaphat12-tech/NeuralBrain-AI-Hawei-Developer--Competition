# Settings Integration Guide

Use this guide to integrate user settings throughout the NeuralBrain-AI application.

## Quick Reference

### Get User Settings in Any Route

```python
from models import UserSettings
from flask import session

@app.route('/my-page')
@login_required
def my_page():
    user_id = session.get('user', {}).get('id')
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    
    if settings:
        theme = settings.theme  # 'dark' or 'light'
        refresh_rate = settings.data_refresh_rate  # seconds
        alerts_enabled = settings.critical_alerts_enabled  # boolean
    
    return render_template('my_template.html', settings=settings)
```

### Apply Theme in Template

```html
<!-- In your template -->
<style>
    {% if settings.theme == 'light' %}
        :root {
            --bg-primary: #ffffff;
            --text-primary: #000000;
        }
    {% else %}
        :root {
            --bg-primary: #1a1a1a;
            --text-primary: #ffffff;
        }
    {% endif %}
</style>

<body class="theme-{{ settings.theme }}">
    <!-- content -->
</body>
```

### Use Data Refresh Rate

```javascript
// In frontend JavaScript
async function setupDataRefresh(refreshRateSeconds) {
    setInterval(async () => {
        const response = await fetch('/api/data');
        const data = await response.json();
        updateDashboard(data);
    }, refreshRateSeconds * 1000);
}

// Load from settings
fetch('/api/user/settings')
    .then(r => r.json())
    .then(data => setupDataRefresh(data.data.data_refresh_rate));
```

### Check Alert Settings

```python
# In services or routes
def should_send_alert(user_id, alert_type='critical'):
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    
    if alert_type == 'critical':
        return settings.critical_alerts_enabled if settings else True
    
    if alert_type == 'email':
        return settings.email_notifications if settings else True
    
    return True  # Default to enabled if no settings
```

### Export Format in Download Routes

```python
@app.route('/download-report')
@login_required
def download_report():
    user_id = session.get('user', {}).get('id')
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    format_type = settings.exports_format if settings else 'json'
    
    if format_type == 'csv':
        return generate_csv_report()
    else:
        return generate_json_report()
```

### Get User Timezone

```python
from datetime import datetime, timezone
import pytz

def get_localized_time(user_id):
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    tz_name = settings.timezone if settings else 'UTC'
    tz = pytz.timezone(tz_name)
    
    utc_time = datetime.now(timezone.utc)
    local_time = utc_time.astimezone(tz)
    
    return local_time
```

### Translate Based on Language Setting

```python
def get_translation(user_id, key):
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    language = settings.language if settings else 'en'
    
    translations = {
        'en': {'hello': 'Hello', 'goodbye': 'Goodbye'},
        'es': {'hello': 'Hola', 'goodbye': 'Adiós'},
    }
    
    return translations.get(language, {}).get(key, key)
```

---

## Common Integration Patterns

### Pattern 1: Per-User Dashboard Configuration

```python
@views_bp.route('/api/dashboard/config')
@login_required
def get_dashboard_config():
    user_id = session.get('user', {}).get('id')
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.session.add(settings)
        db.session.commit()
    
    return jsonify({
        'refresh_rate': settings.data_refresh_rate,
        'theme': settings.theme,
        'show_alerts': settings.critical_alerts_enabled,
        'timezone': settings.timezone,
        'language': settings.language,
    })
```

### Pattern 2: Conditional Features

```python
def is_feature_enabled_for_user(user_id, feature):
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    
    feature_flags = {
        'notifications': settings.critical_alerts_enabled,
        'email': settings.email_notifications,
        'export': settings.exports_format in ['json', 'csv'],
    }
    
    return feature_flags.get(feature, False)
```

### Pattern 3: Audit Trail with Settings

```python
def log_user_action(user_id, action, details=None):
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    
    log_entry = {
        'user_id': user_id,
        'action': action,
        'timestamp': datetime.utcnow(),
        'timezone': settings.timezone if settings else 'UTC',
        'language': settings.language if settings else 'en',
        'details': details
    }
    
    # Log to database or file
    return log_entry
```

### Pattern 4: Batch Operations Respecting User Preferences

```python
def send_daily_reports(user_list):
    for user_id in user_list:
        settings = UserSettings.query.filter_by(user_id=user_id).first()
        
        # Skip if user disabled email notifications
        if settings and not settings.email_notifications:
            continue
        
        # Generate report in user's preferred format
        format_type = settings.exports_format if settings else 'json'
        report = generate_report(user_id, format_type)
        
        # Send in user's timezone
        tz = settings.timezone if settings else 'UTC'
        send_email(user_id, report, timezone=tz)
```

---

## Frontend Integration

### Load Settings on Page Load

```javascript
async function initializePageWithUserSettings() {
    try {
        const response = await fetch('/api/user/settings');
        const data = await response.json();
        
        if (data.success) {
            const settings = data.data;
            
            // Apply theme
            applyTheme(settings.theme);
            
            // Start refresh interval
            startDataRefresh(settings.data_refresh_rate);
            
            // Configure notifications
            configureNotifications(settings.critical_alerts_enabled);
            
            // Set language
            setLanguage(settings.language);
            
            // Store in localStorage for offline use
            localStorage.setItem('userSettings', JSON.stringify(settings));
        }
    } catch (error) {
        console.error('Failed to load settings:', error);
    }
}

document.addEventListener('DOMContentLoaded', initializePageWithUserSettings);
```

### Real-Time Settings Updates

```javascript
class SettingsManager {
    constructor() {
        this.settings = null;
        this.subscribers = [];
    }
    
    subscribe(callback) {
        this.subscribers.push(callback);
    }
    
    async load() {
        const response = await fetch('/api/user/settings');
        this.settings = await response.json();
        this.notifySubscribers();
    }
    
    async save(updates) {
        const response = await fetch('/api/user/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        
        if (response.ok) {
            await this.load();
        }
    }
    
    notifySubscribers() {
        this.subscribers.forEach(cb => cb(this.settings));
    }
    
    get(key) {
        return this.settings?.data?.[key];
    }
}

const settingsManager = new SettingsManager();

// Usage
settingsManager.subscribe((settings) => {
    console.log('Settings updated:', settings);
});

await settingsManager.load();
await settingsManager.save({ theme: 'light' });
```

### Theme Switching

```javascript
function applyTheme(theme) {
    const root = document.documentElement;
    
    if (theme === 'light') {
        root.style.setProperty('--bg-primary', '#ffffff');
        root.style.setProperty('--text-primary', '#000000');
        root.style.setProperty('--border-color', '#e0e0e0');
        document.body.classList.remove('dark-mode');
        document.body.classList.add('light-mode');
    } else {
        root.style.setProperty('--bg-primary', '#1a1a1a');
        root.style.setProperty('--text-primary', '#ffffff');
        root.style.setProperty('--border-color', '#333333');
        document.body.classList.remove('light-mode');
        document.body.classList.add('dark-mode');
    }
    
    // Persist to localStorage
    localStorage.setItem('theme', theme);
}

// Toggle theme button
document.getElementById('themeToggle').addEventListener('click', async () => {
    const currentTheme = settingsManager.get('theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    applyTheme(newTheme);
    await settingsManager.save({ theme: newTheme });
});
```

---

## Database Queries

### Find Users with Specific Settings

```python
from models import UserSettings

# Users with critical alerts enabled
alert_users = UserSettings.query.filter_by(critical_alerts_enabled=True).all()

# Users with dark theme
dark_mode_users = UserSettings.query.filter_by(theme='dark').all()

# Users with 30-second refresh rate
fast_refresh_users = UserSettings.query.filter_by(data_refresh_rate=30).all()

# Users in specific timezone
ny_users = UserSettings.query.filter_by(timezone='America/New_York').all()

# Count users by language
en_count = UserSettings.query.filter_by(language='en').count()
es_count = UserSettings.query.filter_by(language='es').count()
```

### Bulk Updates

```python
# Disable alerts for all users
UserSettings.query.update({'critical_alerts_enabled': False})
db.session.commit()

# Change all to 60-second refresh
UserSettings.query.update({'data_refresh_rate': 60})
db.session.commit()

# Set all to UTC timezone
UserSettings.query.update({'timezone': 'UTC'})
db.session.commit()
```

### Statistics

```python
from sqlalchemy import func

# Average refresh rate
avg_refresh = db.session.query(func.avg(UserSettings.data_refresh_rate)).scalar()

# Most common theme
from sqlalchemy import func
common_theme = db.session.query(
    UserSettings.theme,
    func.count(UserSettings.id)
).group_by(UserSettings.theme).order_by(func.count(UserSettings.id).desc()).first()

# Export format distribution
formats = db.session.query(
    UserSettings.exports_format,
    func.count(UserSettings.id)
).group_by(UserSettings.exports_format).all()
```

---

## Testing User Settings

### Unit Test Example

```python
import pytest
from models import db, User, UserSettings

def test_user_settings_creation(app, client):
    with app.app_context():
        # Create user
        user = User(
            id='test_user',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        db.session.add(user)
        db.session.commit()
        
        # Create settings
        settings = UserSettings(
            user_id='test_user',
            theme='dark',
            data_refresh_rate=60
        )
        db.session.add(settings)
        db.session.commit()
        
        # Verify
        retrieved = UserSettings.query.filter_by(user_id='test_user').first()
        assert retrieved.theme == 'dark'
        assert retrieved.data_refresh_rate == 60

def test_settings_defaults(app):
    with app.app_context():
        settings = UserSettings(user_id='new_user')
        assert settings.theme == 'dark'
        assert settings.data_refresh_rate == 60
        assert settings.critical_alerts_enabled == True
```

### Integration Test Example

```python
def test_save_settings_api(client, auth_header):
    response = client.post(
        '/api/user/settings',
        json={
            'theme': 'light',
            'data_refresh_rate': 30,
            'critical_alerts_enabled': False
        },
        headers=auth_header
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert data['data']['theme'] == 'light'
    assert data['data']['data_refresh_rate'] == 30
```

---

## Troubleshooting Integration Issues

### Settings Always Return Defaults
**Cause**: UserSettings record not being created  
**Solution**:
```python
user_id = session.get('user', {}).get('id')
settings = UserSettings.query.filter_by(user_id=user_id).first()
if not settings:
    settings = UserSettings(user_id=user_id)
    db.session.add(settings)
    db.session.commit()
```

### Theme Not Applying
**Cause**: CSS variables not set correctly  
**Solution**: Ensure CSS loads after settings are applied:
```javascript
// Load settings first
await settingsManager.load();

// Then apply CSS
applyTheme(settingsManager.get('theme'));

// Then render page
renderPage();
```

### Settings Changes Not Persisting
**Cause**: Session not updated or DB not committed  
**Solution**:
```python
# Update DB
db.session.commit()

# Update session
session['user_settings'] = settings.to_dict()
session.modified = True
```

### 401 Unauthorized on API
**Cause**: Missing @login_required decorator  
**Solution**: Ensure all settings routes have:
```python
@views_bp.route('/api/user/settings')
@login_required
def get_settings():
    # ...
```

---

## Best Practices

1. **Always Check for None**
   ```python
   settings = UserSettings.query.filter_by(user_id=user_id).first()
   if settings:
       use_setting = settings.theme
   else:
       use_setting = 'dark'  # Default
   ```

2. **Cache Settings**
   ```python
   # In session or Redis for frequently accessed settings
   user_settings_cache[user_id] = settings.to_dict()
   ```

3. **Validate Input**
   ```python
   valid_themes = ['dark', 'light']
   if new_theme not in valid_themes:
       new_theme = 'dark'  # Reset to default
   ```

4. **Log Changes**
   ```python
   logger.info(f"User {user_id} changed theme to {new_theme}")
   ```

5. **Async Loading**
   ```javascript
   // Don't block page render
   settingsManager.load().catch(err => console.error(err));
   ```

---

## Performance Tips

- Load settings once on page load, cache result
- Use localStorage for offline availability
- Batch settings updates when possible
- Index user_id for fast lookups (already done)
- Consider Redis cache for frequently accessed settings
- Lazy load theme application (after initial render)

---

For more information, see `SETTINGS_PROFILE_IMPLEMENTATION.md`
