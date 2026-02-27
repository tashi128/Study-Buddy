# 🚀 Quick Start Guide - Study Buddy with Authentication

## Getting Started

### 1. Run the Application
```bash
cd /Users/tashi/Desktop/ai-study-assistant
streamlit run app.py
```

The app will open at: `http://localhost:8501`

### 2. What You'll See

**First Load:**
- Beautiful animated landing page
- Welcome text with smooth fade-in animations
- Floating glassmorphism authentication card

**Choose Your Path:**
- **New User:** Click "Sign Up" tab
- **Returning User:** Click "Login" tab

---

## 📝 How to Sign Up

1. Click the **"Sign Up"** tab
2. Fill in the form:
   - **Full Name:** Your name (2+ characters)
   - **Email:** Valid email address
   - **Password:** 8+ characters (mix of letters, numbers recommended)
   - **Confirm Password:** Re-enter your password
3. Click **"Create Account"**
4. See success message
5. Login with your new credentials

**Password Requirements:**
- Minimum 8 characters
- Can include: letters, numbers, symbols
- Should be unique and secure

---

## 🔑 How to Login

1. Click the **"Login"** tab
2. Enter your credentials:
   - **Email:** Your registered email
   - **Password:** Your password
3. Click **"Sign In"**
4. You'll be redirected to the dashboard

**Your First Login:**
- Sidebar shows your name
- Sidebar shows your email
- Access to all Study Buddy features

---

## 🚪 How to Logout

1. Look at the top of the sidebar
2. Click the **"🚪 Logout"** button
3. You'll return to the landing page
4. Your session is destroyed

---

## 🎯 Features You Can Use

Once logged in, you have access to:

### 📖 Upload Notes
- Upload PDF, Word, or text files
- AI automatically extracts topics

### 🎓 Practice Tests
- AI-generated practice questions
- Real-time scoring
- Quiz Helper chat (🌸) for hints

### 📚 Flashcards
- Generate study flashcards
- Organize by topic
- Beautiful card design

### 💬 AI Doubt Chat
- Ask questions about any topic
- AI tutor responses
- Context-aware answers

### 📝 Notes Summary
- Auto-summarize your notes
- Key points extraction
- Quick reference

### 🗓️ Study Plan
- AI creates personalized study plans
- Time estimation
- Daily schedules

### 📊 Progress Tracking
- Track your scores
- See weak areas
- Performance analytics

---

## 🔐 Security & Privacy

Your data is:
- ✅ **Encrypted:** Passwords use PBKDF2-SHA256 hashing
- ✅ **Secure:** 100,000 iteration salt-based hashing
- ✅ **Protected:** Database-backed storage
- ✅ **Private:** Session tokens for security
- ✅ **Never Shared:** Your data stays in your database

---

## 🎨 Design Features

### Landing Page
- **Animated Gradient:** Smooth color transitions
- **Floating Blobs:** Glassmorphism effect
- **Smooth Text:** Fade-in animations
- **Responsive:** Works on mobile and desktop

### Authentication UI
- **Modern Design:** Glassmorphism card
- **Tab-based:** Easy switching between login/signup
- **Form Validation:** Real-time error checking
- **Smooth Transitions:** Professional animations

### Dashboard
- **User Info:** Your name and email in sidebar
- **Easy Navigation:** Clear menu options
- **Dark Mode:** Built-in theme toggle
- **Responsive:** Adapts to screen size

---

## 🆘 Troubleshooting

### Problem: Landing page not showing
**Solution:** Make sure `auth.py` and `landing.py` are in the same folder as `app.py`

### Problem: Can't create account
**Possible Issues:**
- Email already registered
- Password too short (needs 8+ characters)
- Email format invalid
- **Solution:** Check error message and try again

### Problem: Can't login
**Possible Issues:**
- Email not found
- Wrong password (case-sensitive)
- **Solution:** Check email/password and try again

### Problem: Logged out after refresh
**Possible Causes:**
- Browser cookies disabled
- Session timeout
- Database issue
- **Solution:** Try signing up again or check database

### Problem: Database errors
**Solution:** 
```bash
# Delete the database to rebuild it
rm database/study.db

# Restart the app
streamlit run app.py
```

---

## 📱 Mobile vs Desktop

### Desktop (1200px+)
- Large animated text
- Full gradient animations
- Wide authentication card
- All features visible

### Tablet (768px-1200px)
- Optimized text sizing
- Adjusted animations
- Responsive card layout
- Touch-friendly buttons

### Mobile (<768px)
- Compact text
- Full-width forms
- Touch-optimized interface
- Simplified animations

---

## 🔄 Typical User Journey

```
1. First Visit
   → Open http://localhost:8501
   → See landing page with animations
   → Click "Sign Up"
   → Create account
   → Login
   → See dashboard

2. Return Visit
   → Open http://localhost:8501
   → See landing page
   → Click "Login"
   → Enter credentials
   → See dashboard

3. End of Session
   → Click "🚪 Logout"
   → Return to landing page
   → Session destroyed
```

---

## 💡 Tips & Tricks

### Password Management
- Use a strong, unique password
- Mix uppercase, lowercase, numbers
- Don't share your password
- Consider using a password manager

### Staying Logged In
- Sessions persist across page refreshes
- Logout clears your session
- Your data is saved in the database
- Can safely close and reopen

### Profile Information
- Your email is shown in sidebar
- Your name appears when logged in
- Edit profile coming soon (future feature)

### Study Buddy Features
- Use Quiz Helper for hints during practice
- Ask AI Doubt Chat for explanations
- Generate study plans for better organization
- Review your progress regularly

---

## 🎓 Study Tips with Study Buddy

1. **Upload Notes First**
   - Upload your course materials
   - Let AI extract topics
   - Build your knowledge base

2. **Generate Practice Tests**
   - Test your knowledge
   - Use Quiz Helper if stuck
   - Review wrong answers

3. **Create Study Plans**
   - Get personalized schedules
   - Follow the AI recommendations
   - Track your progress

4. **Use Flashcards**
   - Review key concepts
   - Study by topic
   - Spaced repetition learning

5. **Ask Questions**
   - Use AI Doubt Chat
   - Get instant explanations
   - Clarify difficult concepts

---

## 🆘 Need Help?

Check the documentation:
- `AUTHENTICATION.md` - Full technical details
- `README.md` - General project info

Or review the code:
- `auth.py` - Authentication system
- `landing.py` - Landing page design
- `app.py` - Main application

---

## 🚀 You're Ready!

Your Study Buddy is now fully set up with:
- ✅ Modern landing page
- ✅ Secure authentication
- ✅ Full study features
- ✅ Professional design

**Start learning! 🧠**

---

**Version:** 1.0.0  
**Last Updated:** February 27, 2026
