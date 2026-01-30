# 🔒 Branch Protection - Simple Explanation

## What Is It?

**Branch protection** means: **Nobody can push code directly to `main` branch**

Without it → Team members can push bad code directly to main  
With it → All code goes through Pull Requests with approval first

---

## What Will Happen After We Enable It

### ❌ This will NOT work anymore:
```bash
git push origin main
```
**Error:** "Direct pushes to main are blocked"

### ✅ This IS the new required way:
```bash
git checkout -b feature/my-feature     # Create branch
git push origin feature/my-feature     # Push to YOUR branch
# Then create Pull Request on GitHub for approval
```

---

## 4 Easy Steps to Enable Protection

### STEP 1: Go to GitHub Website
- Open: https://github.com/Josaphat12-tech/NeuralBrain-AI-Hawei-Developer--Competition
- Click **Settings** tab (top right)

### STEP 2: Click "Branches" (left menu)
- Look for **"Branches"** in the left sidebar
- Click it

### STEP 3: Click "Add rule"
- Click **"Add rule"** button

### STEP 4: Fill Out the Form
**Branch name pattern:** type `main`

**Check these boxes:**
- ☑️ Require a pull request before merging
- ☑️ Require approvals: `1` (just one person needs to approve)
- ☑️ Dismiss stale pull request approvals when new commits are pushed
- ☑️ Require status checks to pass before merging (optional but good)

**Scroll down and click "Create"**

---

## Done! ✅

Your main branch is now protected!

Now tell your team members to read: **TEAM_WORKFLOW.md**
