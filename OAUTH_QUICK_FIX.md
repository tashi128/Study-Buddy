# 🚀 Quick Fix: OAuth Configuration Error

## The Issue
You got: **"Error 401: invalid_client"**

This means the OAuth credentials in your `.env` file are either:
- ❌ Missing (not filled in yet)
- ❌ Invalid (wrong values)
- ❌ Not configured (still have "YOUR_" placeholders)

## ✅ Quick Fix (3 Steps)

### Step 1: Get Google OAuth Credentials
1. Go to **[Google Cloud Console](https://console.cloud.google.com/)**
2. Create a new project called "Study Buddy"
3. Go to **APIs & Services → Credentials**
4. Click **Create Credentials → OAuth client ID**
5. Choose **Web application**
6. Add authorized redirect URI (exact): `http://localhost:8501`
7. Click **Create** and copy your **Client ID** and **Client Secret**

### Step 2: Get Apple OAuth Credentials
1. Go to **[Apple Developer](https://developer.apple.com/)**
2. Go to **Certificates, Identifiers & Profiles**
3. Create an **App ID** and **Service ID** (see `OAUTH_SETUP.md` for detailed steps)
4. Get your **Team ID**, **Key ID**, and **Private Key**

### Step 3: Update .env File
Open the `.env` file in your project root and replace the placeholders:

```bash
# Before:
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID_HERE.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET_HERE

# After:
GOOGLE_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123xyz
```

Do the same for Apple credentials.

## 💡 In the Meantime...

You can still use Study Buddy fully with **email/password authentication**:

✅ Click **Sign Up** to create an account
✅ Login with email and password
✅ Access all Study Buddy features
✅ Upload documents
✅ Practice questions
✅ Generate flashcards
✅ All features work!

The OAuth buttons will automatically work once you configure the credentials.

## 📚 For Detailed Instructions
See **`OAUTH_SETUP.md`** in the project root for step-by-step OAuth setup guide.

## 🔄 After Updating .env

1. **Reload the app** - Streamlit will automatically reload when `.env` changes
2. **Click a Google/Apple button** - It will now redirect to the actual login page
3. **Done!** 🎉

---

**Questions?** Check the setup messages that appear when you click the OAuth buttons!
