# 🌐 Network Access Guide - Why Your App May Not Be Accessible

## ✅ Good News: Your App IS Correctly Configured!

Your `app.py` is already set up for network access:
```python
host = os.getenv('FLASK_HOST', '0.0.0.0')  # Listens on all interfaces
port = int(os.getenv('FLASK_PORT', 5000))   # Port 5000
```

**This means**:
- ✅ App listens on `0.0.0.0:5000` (all network interfaces)
- ✅ Should be accessible from `192.168.100.87:5000`
- ✅ Should be accessible from `127.0.0.1:5000` (localhost)

---

## 🔍 Troubleshooting: Why Can't You Access It?

### Common Issues (and fixes):

#### 1. **App Not Running**
```bash
# VERIFY: Is Flask actually running?
ps aux | grep "python.*app.py"

# SOLUTION: Start it in a proper terminal
cd /home/josaphat/Projects/Projects/NeuralBrain-AI-Hawei-Developer--Competition/NeuralBrain-AI
python3 app.py
```

**Expected output:**
```
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:5000
* Running on http://192.168.100.87:5000
```

#### 2. **Port Already in Use**
```bash
# CHECK: Is port 5000 already being used?
lsof -i :5000
# or
netstat -tlnp | grep 5000

# SOLUTION: Use different port
export FLASK_PORT=5001
python3 app.py
```

#### 3. **Firewall Blocking Port 5000**
```bash
# CHECK: Firewall status
sudo ufw status

# SOLUTION: Allow port 5000
sudo ufw allow 5000
sudo ufw reload

# Or temporarily disable firewall (for testing only)
sudo ufw disable
```

#### 4. **Can't Reach 192.168.100.87 from Another Device**
```bash
# VERIFY your IP is correct:
hostname -I
# Should show: 192.168.100.87 ...

# TEST connectivity:
# From another device on same network:
ping 192.168.100.87        # Should respond
curl http://192.168.100.87:5000  # Should show HTML

# NOT on same network?
# Ask: "What's the error when you try to access it?"
# - Connection refused?  → Firewall or port not listening
# - Connection timeout?  → Device not on same network
# - Page loads but shows error? → App crashed
```

#### 5. **DNS or Network Issues**
```bash
# CHECK: Network interface is UP
ip link show
# Should show: wlp4s0: <BROADCAST,MULTICAST,UP,...>

# CHECK: IP address is assigned
ip addr | grep "192.168"
# Should show your IP

# SOLUTION: If not showing, restart networking:
sudo systemctl restart networking
```

#### 6. **Browser Caching**
```
# Try in different browser or incognito mode
# Or clear cache: Ctrl+Shift+Delete

# Force refresh: Ctrl+F5 (hard refresh)
```

#### 7. **Flask App Has Errors**
```bash
# WATCH for startup errors:
python3 app.py 2>&1 | grep -i "error\|traceback"

# Common errors:
# - ModuleNotFoundError → Missing dependency
# - Address already in use → Port conflict
# - Failed to load → Config error
```

---

## ✅ Quick Test: Is Your App Accessible?

### Test 1: Localhost (On Same Machine)
```bash
# Start app in terminal 1:
cd /home/josaphat/Projects/Projects/NeuralBrain-AI-Hawei-Developer--Competition/NeuralBrain-AI
python3 app.py

# In terminal 2, test access:
curl http://localhost:5000          # Should work
curl http://127.0.0.1:5000          # Should work
curl http://192.168.100.87:5000     # Should work (if on same network)
```

**Expected response**:
- Should return HTML (dashboard page)
- Or a specific page (redirect, login, etc.)
- NOT "Connection refused"

### Test 2: Network Access (From Another Device)
```bash
# From another device on 192.168.100.0/24 network:

# Linux/Mac:
curl http://192.168.100.87:5000

# Windows PowerShell:
Invoke-WebRequest http://192.168.100.87:5000

# Or just open in browser:
http://192.168.100.87:5000
```

---

## 🚀 Production Network Setup

### For Public Network Access (Outside LAN):

#### Option 1: Use Ngrok (Easiest)
```bash
# Install:
curl https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo apt-key add - && \
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list && \
sudo apt update && \
sudo apt install ngrok

# Run:
python3 app.py &
ngrok http 5000

# Get public URL: https://xxxxx.ngrok.io
```

#### Option 2: AWS EC2 / Cloud VM
```bash
# Deploy to cloud with public IP
# Then allow port 5000 in security group
```

#### Option 3: Gunicorn (Production Ready)
```bash
# Install:
pip install gunicorn

# Run:
gunicorn --bind 0.0.0.0:5000 app:flask_app

# For SSL:
gunicorn --certfile=cert.pem --keyfile=key.pem --bind 0.0.0.0:5000 app:flask_app
```

---

## 📋 Configuration Reference

### Environment Variables (in .env):

```bash
# Flask Settings
FLASK_HOST=0.0.0.0      # Listen on all interfaces
FLASK_PORT=5000          # Port to use
FLASK_DEBUG=True         # Debug mode (set to False in production)

# If you want to change these:
echo "FLASK_HOST=0.0.0.0" >> .env
echo "FLASK_PORT=5000" >> .env
```

### Check Current Config:
```bash
grep -E "FLASK_HOST|FLASK_PORT|FLASK_DEBUG" .env
```

---

## 🎯 Complete Network Diagnostic Script

Save this as `test_network.sh`:

```bash
#!/bin/bash

echo "🌐 NEURALBRAIN-AI NETWORK DIAGNOSTICS"
echo "======================================"
echo ""

# 1. Check app is running
echo "1️⃣ Checking if Flask is running..."
if ps aux | grep -v grep | grep "python.*app.py" > /dev/null; then
    echo "   ✅ Flask IS running"
else
    echo "   ❌ Flask NOT running"
    echo "   → Start with: python3 app.py"
    exit 1
fi

# 2. Check network interfaces
echo ""
echo "2️⃣ Network Interfaces:"
hostname -I

# 3. Check port listening
echo ""
echo "3️⃣ Port 5000 Status:"
if netstat -tlnp 2>/dev/null | grep :5000; then
    echo "   ✅ Port 5000 is LISTENING"
else
    echo "   ❌ Port 5000 NOT listening"
fi

# 4. Test localhost
echo ""
echo "4️⃣ Testing localhost (127.0.0.1:5000):"
if curl -s http://127.0.0.1:5000 > /dev/null; then
    echo "   ✅ Accessible on localhost"
else
    echo "   ❌ Cannot access localhost"
fi

# 5. Test network IP
echo ""
echo "5️⃣ Testing network IP (192.168.100.87:5000):"
if curl -s http://192.168.100.87:5000 > /dev/null; then
    echo "   ✅ Accessible on network IP"
else
    echo "   ❌ Cannot access network IP"
fi

# 6. Check firewall
echo ""
echo "6️⃣ Firewall Status:"
sudo ufw status 2>/dev/null || echo "   ℹ️ UFW not active"

echo ""
echo "======================================"
echo "If you see ❌ issues, check the guide above!"
```

**Run it**:
```bash
chmod +x test_network.sh
./test_network.sh
```

---

## 🆘 Still Can't Access? Share These Details:

When asking for help, provide:

1. **What error do you get?**
   - "Connection refused"
   - "Connection timeout"
   - "Connection reset"
   - Page loads but shows error?

2. **Where are you trying to access from?**
   - Same machine? Different machine?
   - Same network (192.168.100.x)?

3. **What does Flask say on startup?**
   - Paste the startup logs

4. **Run this and share output:**
   ```bash
   hostname -I
   ps aux | grep "app.py" | grep -v grep
   netstat -tlnp | grep 5000
   sudo ufw status
   ```

---

## ✨ Summary

**Your app IS configured correctly for network access:**
- ✅ Listens on `0.0.0.0:5000` (all interfaces)
- ✅ Should be accessible from `192.168.100.87:5000`
- ✅ Firewall is inactive (allowing all traffic)
- ✅ Network configuration is correct

**Most likely issues:**
1. App not actually running
2. Port 5000 already in use
3. Wrong IP address for device
4. Different network than expected

**Next Steps:**
1. Start Flask: `python3 app.py`
2. Verify it's running: `ps aux | grep app.py`
3. Test locally: `curl http://localhost:5000`
4. Test network: `curl http://192.168.100.87:5000`
5. If still stuck, share the error message

---

**Document Created**: February 9, 2026  
**Last Updated**: 11:35 UTC
