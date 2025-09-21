# Horizon - Complete Backend Integration

This document describes the complete integration of the Horizon frontend with the backend APIs.

## 🚀 Quick Start

### 1. Start Backend Services

```bash
# Terminal 1 - Main Backend
cd backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2 - JobForge Service
cd jobForge
python -m uvicorn app.main:app --reload --port 8001

# Terminal 3 - Frontend
cd frontend
npm start
```

### 2. Test Integration

```bash
python test_integration.py
```

## 🔗 API Integration Overview

### Backend Services

#### Main Backend (Port 8000)
- **User Registration**: `POST /user/register`
- **User Login**: `POST /auth/login`
- **Resume Upload**: `POST /user/resume`
- **MBTI Questions**: `GET /user/questions`
- **Personality Scoring**: `POST /user/answers`
- **Career Tree**: `POST /careertree/generate/{name}`

#### JobForge Service (Port 8001)
- **Job Recommendations**: `GET /recommend/{user_id}`
- **Job Search**: `POST /search/{user_id}`

## 📱 Frontend Integration Details

### 1. User Registration & Login

**LoginPage.tsx**
- Integrates with `POST /auth/login`
- Stores access token and user ID in localStorage
- Redirects to jobs page on successful login

**RegisterPage.tsx**
- Collects basic user information
- Redirects to ProfileSetupPage for complete registration

### 2. Profile Setup

**ProfileSetupPage.tsx**
- **Step 1**: Resume upload via `POST /user/resume`
- **Step 2**: Skills selection
- **Step 3**: Interest domains
- **Step 4**: MBTI questionnaire via `GET /user/questions` and `POST /user/answers`
- **Final**: Complete registration via `POST /user/register`

### 3. Job Listings

**JobListingsPage.tsx**
- **Default Load**: Fetches recommendations via `GET /recommend/{user_id}`
- **Search**: Uses `POST /search/{user_id}` with search terms
- **Real-time**: Updates based on user ID from localStorage

### 4. Career Tree

**CareerTreePage.tsx**
- Generates career tree via `POST /careertree/generate/{name}`
- Displays interactive career paths and opportunities

## 🔄 Data Flow

### User Registration Flow
1. User fills registration form → ProfileSetupPage
2. Upload resume → Parse and store in cloud
3. Complete MBTI questionnaire → Get personality scores
4. Submit complete profile → Register user
5. Store user ID → Redirect to jobs

### Job Search Flow
1. Page loads → Fetch recommendations for user
2. User searches → Send search query to JobForge
3. Display results → Show relevance scores and details
4. User applies → Open external application link

## 📊 API Response Formats

### Job Recommendation Response
```json
{
  "user_id": "x",
  "count": 2,
  "results": [
    {
      "id": 90,
      "title": "Software Engineer III, AI/ML, Core",
      "company": "Google",
      "apply_link": "https://...",
      "description": "<p>...</p>",
      "publish_date": "2025-09-10T10:28:44.482Z",
      "locations": ["Bengaluru, Karnataka, India"],
      "skills": ["Software development", "Python", ...],
      "education": ["Bachelor's degree", "Master's degree"],
      "relevance": 49
    }
  ]
}
```

### Job Search Response
```json
{
  "user_id": "x",
  "query_titles": ["Software Engineer"],
  "count": 2,
  "results": [...]
}
```

### MBTI Questions Response
```json
{
  "questions": [
    {
      "id": "q1",
      "question": "At a party, you would rather:",
      "options": [
        {"text": "Meet new people and socialize", "value": "E"},
        {"text": "Have deep conversations with a few close friends", "value": "I"}
      ]
    }
  ]
}
```

### Personality Scores Response
```json
{
  "personality scores": {
    "E": 0.7,
    "S": 0.6,
    "T": 0.8,
    "J": 0.5
  }
}
```

## 🛠️ Configuration

### Environment Variables
- `MONGODB_URI`: MongoDB connection string
- `FUZZY_TITLE_THRESHOLD`: Job title matching threshold (default: 70.0)
- `SKILL_FUZZY_THRESHOLD`: Skill matching threshold (default: 78.0)

### Default User ID
- Uses "x" as default user ID when no user is logged in
- Stored in localStorage after successful registration/login

## 🧪 Testing

Run the integration test:
```bash
python test_integration.py
```

This will test:
- Backend endpoints availability
- JobForge service connectivity
- Career tree generation
- API response formats

## 🚨 Error Handling

### Frontend Error Handling
- Network errors are caught and displayed to users
- Fallback to empty states when APIs fail
- Loading states during API calls
- Form validation before API calls

### Backend Error Handling
- Proper HTTP status codes
- Detailed error messages
- Graceful degradation

## 📝 Notes

- All API calls use axios with proper error handling
- User authentication state is managed via localStorage
- Resume uploads are processed and stored in cloud storage
- Personality assessment is required for user registration
- Job recommendations are personalized based on user profile

## 🔧 Troubleshooting

### Common Issues
1. **CORS Errors**: Ensure backend services are running on correct ports
2. **API Timeouts**: Check if MongoDB is connected and services are running
3. **Empty Results**: Verify user ID exists in database
4. **File Upload Issues**: Check cloud storage configuration

### Debug Steps
1. Check browser console for errors
2. Verify API endpoints with test script
3. Check backend logs for errors
4. Ensure all services are running
