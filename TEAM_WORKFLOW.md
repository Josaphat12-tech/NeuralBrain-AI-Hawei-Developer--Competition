# 👥 Team Workflow - How to Work With Branch Protection

## The Simple Rule
**Never push to `main`**  
**Always use a feature branch**

---

## Step-by-Step Workflow

### 1️⃣ Start New Work
```bash
git checkout main           # Switch to main
git pull origin main        # Get latest code
git checkout -b feature/my-feature    # Create YOUR branch
```

### 2️⃣ Make Your Changes
```bash
# Edit files, write code, test it
git add .
git commit -m "add new feature"
```

### 3️⃣ Push to YOUR Branch (NOT main)
```bash
git push origin feature/my-feature
```

### 4️⃣ Create Pull Request on GitHub
1. Go to GitHub repo
2. You'll see a notification: **"feature/my-feature had recent pushes"**
3. Click **"Compare & pull request"** button
4. Add description of what you did
5. Click **"Create pull request"**

### 5️⃣ Wait for Approval
- Someone will review your code
- If OK, they click **"Approve"**
- Then you can click **"Merge pull request"**

### 6️⃣ Delete Your Branch (cleanup)
```bash
git checkout main
git pull origin main
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```

---

## Branch Naming Examples
- `feature/add-dashboard` ← New feature
- `fix/data-explorer-bug` ← Fixing a bug
- `docs/update-readme` ← Documentation
- `refactor/optimize-queries` ← Code cleanup

---

## ⚠️ Common Mistakes to AVOID

### ❌ DON'T: Push to main
```bash
git push origin main    # WRONG! Will be rejected
```

### ❌ DON'T: Commit to local main then push
```bash
git checkout main
git commit -m "..."
git push origin main    # WRONG!
```

### ✅ DO: Always use a feature branch
```bash
git checkout -b feature/your-name
git commit -m "..."
git push origin feature/your-name   # RIGHT!
```

---

## 🆘 If You Accidentally Committed to Local Main

```bash
# Don't panic! Just undo it:
git reset HEAD~1        # Undo the commit (code still there)
git checkout -b feature/new-branch
git push origin feature/new-branch
```

---

## ❓ Questions?

**Q: Why do we need this?**  
A: Prevents bad code getting on main. Everyone's code gets reviewed first.

**Q: What if I'm the owner and need to bypass?**  
A: You can temporarily disable the rule in Settings, push, then re-enable.

**Q: How long does approval take?**  
A: Usually a few hours. Depends on team availability.

---

## Summary
| Before Protection | After Protection |
|---|---|
| Push directly to main ❌ | Create feature branch ✅ |
| No review needed ❌ | Need 1 approval ✅ |
| Bad code gets deployed ❌ | Code reviewed first ✅ |
| Anyone can push anything ❌ | Controlled process ✅ |
