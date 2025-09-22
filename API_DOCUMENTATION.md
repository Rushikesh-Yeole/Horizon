# 📚 GenAI Career Platform - Complete API Documentation

## 🏗️ Architecture Overview

The platform consists of three main services:
- **Main Backend API** (Port 8000) - User management, authentication, resume processing
- **Career Tree Service** (Port 8000) - AI-powered career path generation  
- **JobForge Engine** (Port 8001) - Job recommendation and search system

---

## 🔐 Authentication

### JWT Token Authentication
All protected endpoints require a Bearer token in the Authorization header:
\`\`\`
Authorization: Bearer <your_jwt_token>
\`\`\`

---

## 📡 Main Backend API Endpoints

### 👤 User Management

#### **POST** `/user/register`
Register a new user with complete profile information.

**Request Body:**
\`\`\`json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "linkedin": "https://linkedin.com/in/johndoe",
  "github": "https://github.com/johndoe",
  "preferences": {
    "location": "San Francisco, CA",
    "role": "Software Engineer",
    "salary_range": "100k-150k"
  },
  "education": [
    {
      "degree": "Bachelor of Science",
      "branch": "Computer Science",
      "college": "Stanford University"
    }
  ],
  "skills": ["Python", "JavaScript", "React", "Machine Learning"],
  "projects": [
    {
      "title": "AI Chatbot",
      "desc": "Built an intelligent chatbot using NLP and machine learning"
    }
  ],
  "personality": {
    "E": 0.7,
    "S": 0.4,
    "T": 0.8,
    "J": 0.6
  },
  "password": "securepassword123"
}
\`\`\`

**Response:**
\`\`\`json
{
  "user_id": "507f1f77bcf86cd799439011"
}
\`\`\`

**Status Codes:**
- `200` - User registered successfully
- `400` - MBTI questionnaire not completed or validation error

---

#### **POST** `/user/resume`
Upload and parse a resume file.

**Request:**
- **Content-Type:** `multipart/form-data`
- **File:** Resume file (PDF, DOC, DOCX)

**Response:**
\`\`\`json
{
  "bucket": "resume-storage-bucket",
  "dest_blob": "resumes/user123_resume.pdf",
  "parsed_resume": {
    "skills": ["Python", "Data Analysis", "SQL"],
    "experience": [
      {
        "company": "Tech Corp",
        "position": "Data Scientist",
        "duration": "2020-2023"
      }
    ],
    "education": [
      {
        "degree": "MS Computer Science",
        "institution": "MIT"
      }
    ]
  }
}
\`\`\`

**Status Codes:**
- `200` - Resume uploaded and parsed successfully
- `400` - Invalid file format
- `500` - Processing error

---

### 🧠 MBTI Personality Assessment

#### **GET** `/user/questions`
Retrieve MBTI personality assessment questions.

**Response:**
\`\`\`json
{
  "questions": [
    {
      "id": 1,
      "question": "You prefer to work in a team rather than alone",
      "dimension": "E",
      "type": "likert"
    },
    {
      "id": 2,
      "question": "You focus on details rather than the big picture",
      "dimension": "S",
      "type": "likert"
    }
  ]
}
\`\`\`

---

#### **POST** `/user/answers`
Submit MBTI questionnaire responses for personality scoring.

**Request Body:**
\`\`\`json
{
  "answers": [
    {
      "question_id": 1,
      "answer": 4,
      "dimension": "E"
    },
    {
      "question_id": 2,
      "answer": 2,
      "dimension": "S"
    }
  ]
}
\`\`\`

**Response:**
\`\`\`json
{
  "personality scores": {
    "E": 0.75,
    "S": 0.35,
    "T": 0.80,
    "J": 0.60
  }
}
\`\`\`

**Status Codes:**
- `200` - Personality scores calculated successfully
- `400` - Invalid answer format or processing error

---

### 🔑 Authentication

#### **POST** `/auth/login`
Authenticate user and receive JWT token.

**Request Body:**
\`\`\`json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
\`\`\`

**Response:**
\`\`\`json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
\`\`\`

**Status Codes:**
- `200` - Authentication successful
- `401` - Invalid credentials

---

### 🌳 Career Tree Generation

#### **POST** `/careertree/generate/{name}`
Generate an AI-powered career tree for a specific role.

**Parameters:**
- `name` (path) - Target career role/position

**Response:**
\`\`\`json
{
  "career_tree": {
    "root": "Software Engineer",
    "paths": [
      {
        "level": 1,
        "positions": ["Senior Software Engineer", "Tech Lead"],
        "skills_required": ["Leadership", "System Design"],
        "timeline": "2-3 years"
      },
      {
        "level": 2,
        "positions": ["Engineering Manager", "Principal Engineer"],
        "skills_required": ["Team Management", "Strategic Planning"],
        "timeline": "4-6 years"
      }
    ]
  }
}
\`\`\`

---

#### **GET** `/careertree/health`
Health check for career tree service.

**Response:**
\`\`\`json
{
  "status": "ok",
  "time": "2024-01-15T10:30:00Z"
}
\`\`\`

---

## 🎯 JobForge Recommendation Engine

### 🔍 Job Recommendations

#### **GET** `/recommend/{user_id}`
Get personalized job recommendations for a user.

**Parameters:**
- `user_id` (path) - User identifier
- `top_k` (query, optional) - Maximum number of results (default: all)
- `min_relevance` (query, optional) - Minimum relevance score (0-100)

**Example Request:**
\`\`\`
GET /recommend/507f1f77bcf86cd799439011?top_k=20&min_relevance=70
\`\`\`

**Response:**
\`\`\`json
{
  "user_id": "507f1f77bcf86cd799439011",
  "count": 15,
  "results": [
    {
      "id": "job_12345",
      "title": "Senior Python Developer",
      "company": "TechCorp Inc.",
      "apply_link": "https://techcorp.com/careers/senior-python-dev",
      "description": "We're looking for an experienced Python developer...",
      "publish_date": "2024-01-10T09:00:00Z",
      "locations": ["San Francisco, CA", "Remote"],
      "skills": ["Python", "Django", "PostgreSQL", "AWS"],
      "education": ["Bachelor's Degree in Computer Science"],
      "relevance": 87
    }
  ]
}
\`\`\`

**Relevance Scoring Algorithm:**
- **Skills Match (60%)** - Fuzzy matching between job requirements and user skills
- **Personality Fit (25%)** - MBTI compatibility using cosine similarity
- **Recency (15%)** - Job posting freshness factor

---

#### **POST** `/search/{user_id}`
Search jobs by specific titles with personalized scoring.

**Parameters:**
- `user_id` (path) - User identifier

**Request Body:**
\`\`\`json
{
  "titles": ["Data Scientist", "Machine Learning Engineer", "AI Researcher"],
  "top_k": 25,
  "min_relevance": 60
}
\`\`\`

**Response:**
\`\`\`json
{
  "user_id": "507f1f77bcf86cd799439011",
  "query_titles": ["Data Scientist", "Machine Learning Engineer"],
  "count": 18,
  "results": [
    {
      "id": "job_67890",
      "title": "Senior Data Scientist",
      "company": "DataTech Solutions",
      "apply_link": "https://datatech.com/jobs/senior-data-scientist",
      "description": "Join our AI team to build cutting-edge ML models...",
      "publish_date": "2024-01-12T14:30:00Z",
      "locations": ["New York, NY", "Boston, MA"],
      "skills": ["Python", "TensorFlow", "Statistics", "SQL"],
      "education": ["PhD in Data Science or related field"],
      "relevance": 92
    }
  ]
}
\`\`\`

---

## ⚙️ Configuration Parameters

### JobForge Engine Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `FUZZY_TITLE_THRESHOLD` | 70.0 | Minimum similarity score for title matching |
| `ACTIVE_FUZZY_TITLE_THRESHOLD` | 60.0 | Threshold for active job search |
| `SKILL_FUZZY_THRESHOLD` | 78.0 | Minimum score for skill matching |
| `MAX_TITLE_MATCHES` | 50 | Maximum title matches to consider |
| `W_SKILLS` | 0.60 | Weight for skills in relevance scoring |
| `W_PERSONALITY` | 0.25 | Weight for personality fit |
| `W_RECENCY` | 0.15 | Weight for job posting recency |
| `SCORING_CONCURRENCY` | 32 | Concurrent job scoring operations |

---

## 🗄️ Database Schema

### Users Collection (`users_db.users`)
\`\`\`json
{
  "_id": "ObjectId",
  "name": "string",
  "email": "string (unique)",
  "phone": "string",
  "linkedin": "string",
  "github": "string",
  "preferences": {
    "location": "string",
    "role": "string",
    "salary_range": "string"
  },
  "education": [
    {
      "degree": "string",
      "branch": "string",
      "college": "string"
    }
  ],
  "skills": ["string"],
  "projects": [
    {
      "title": "string",
      "desc": "string"
    }
  ],
  "personality": {
    "E": "float (0-1)",
    "S": "float (0-1)", 
    "T": "float (0-1)",
    "J": "float (0-1)"
  },
  "password": "string (hashed)",
  "bucket": "string (optional)",
  "destination_blob": "string (optional)",
  "created_at": "datetime"
}
\`\`\`

### Jobs Collection (`job_listings.jobs`)
\`\`\`json
{
  "_id": "ObjectId",
  "id": "string",
  "title": "string",
  "company": "string",
  "apply_link": "string",
  "description": "string",
  "publish_date": "datetime",
  "locations": ["string"],
  "skills": ["string"],
  "education": ["string"],
  "personality": {
    "E": "float (0-1)",
    "S": "float (0-1)",
    "T": "float (0-1)", 
    "J": "float (0-1)"
  }
}
\`\`\`

### Career Trees Collection (`career_db.trees`)
\`\`\`json
{
  "_id": "ObjectId",
  "user_id": "string",
  "root_position": "string",
  "generated_at": "datetime",
  "tree_data": {
    "levels": [
      {
        "level": "number",
        "positions": ["string"],
        "skills_required": ["string"],
        "timeline": "string"
      }
    ]
  }
}
\`\`\`

---

## 🚨 Error Handling

### Standard Error Response Format
\`\`\`json
{
  "detail": "Error message description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
\`\`\`

### Common HTTP Status Codes
- `200` - Success
- `400` - Bad Request (validation errors, missing required fields)
- `401` - Unauthorized (invalid or missing authentication)
- `404` - Not Found (user, job, or resource not found)
- `422` - Unprocessable Entity (invalid data format)
- `500` - Internal Server Error (server-side processing errors)

---

## 🔧 Development & Testing

### Running Tests
\`\`\`bash
# Backend tests
cd backend
pytest tests/

# JobForge tests  
cd jobForge
pytest tests/

# Frontend tests
cd frontend
npm test
\`\`\`

### API Testing with cURL

**User Registration:**
\`\`\`bash
curl -X POST "http://localhost:8000/user/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "testpass123",
    "personality": {"E": 0.7, "S": 0.4, "T": 0.8, "J": 0.6},
    "skills": ["Python", "JavaScript"]
  }'
\`\`\`

**Get Job Recommendations:**
\`\`\`bash
curl -X GET "http://localhost:8001/recommend/USER_ID?top_k=10&min_relevance=70" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
\`\`\`

---

## 📈 Performance Considerations

### Optimization Features
- **Caching**: LRU cache for personality computations and frequent queries
- **Concurrency**: Async processing with configurable concurrency limits
- **Indexing**: MongoDB indexes on frequently queried fields
- **Fuzzy Matching**: Optimized string similarity algorithms

### Scaling Recommendations
- Use MongoDB sharding for large datasets
- Implement Redis caching for frequently accessed data
- Consider horizontal scaling for JobForge recommendation engine
- Use CDN for static assets and resume storage

---

## 🔒 Security Features

- **Password Hashing**: bcrypt with salt for secure password storage
- **JWT Authentication**: Stateless token-based authentication
- **CORS Configuration**: Configurable cross-origin resource sharing
- **Input Validation**: Pydantic models for request validation
- **Environment Variables**: Secure configuration management

---


