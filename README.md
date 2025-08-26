# Fullstack AI Chatbot

A modern, full-stack AI-powered chatbot with RAG (Retrieval-Augmented Generation) capabilities. Built with Next.js, FastAPI, PostgreSQL, and integrated with advanced AI models.

## 🚀 Features

### Core Functionality
- **AI-Powered Conversations**: Intelligent chatbot with RAG capabilities
- **Document Upload & Processing**: Upload PDF documents for context-aware responses
- **Chat Sessions Management**: Create, organize, and manage multiple chat sessions
- **Real-time Responses**: Streaming responses for better user experience

### Authentication & Security
- **Secure Authentication**: Session-based authentication with HTTP-only cookies
- **User Registration**: Complete signup and login flow
- **Session Management**: Secure session handling with automatic cleanup
- **Password Security**: Strong password validation and bcrypt hashing

### User Interface
- **Modern Dark Theme**: Sleek, professional dark UI matching the chat application
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Toast Notifications**: Real-time feedback for user actions
- **Loading States**: Smooth loading indicators throughout the application
- **Form Validation**: Client-side validation with helpful error messages

## 🛠 Tech Stack

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icons
- **Sonner** - Toast notifications
- **Framer Motion** - Smooth animations

### Backend
- **FastAPI** - Modern, fast Python web framework
- **PostgreSQL** - Robust relational database
- **SQLAlchemy** - ORM for database operations
- **JWT** - JSON Web Tokens for authentication
- **bcrypt** - Password hashing

### AI & ML
- **RAG Implementation** - Retrieval-Augmented Generation
- **Vector Embeddings** - For semantic search
- **Document Processing** - PDF text extraction and indexing

## 📁 Project Structure

```
├── backend/
│   ├── models/          # Database models
│   ├── routers/         # API endpoints
│   ├── services/        # Business logic
│   ├── db/             # Database configuration
│   └── uploaded_files/ # Document storage
├── frontend/
│   ├── src/
│   │   ├── app/        # Next.js app directory
│   │   ├── components/ # Reusable components
│   │   └── lib/        # Utilities and contexts
│   └── public/         # Static assets
└── docker-compose.yml  # Development environment
```

## 🏃‍♂️ Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.9+ (for development)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fullstack-ai-chatbot
   ```

2. **Create environment file**
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **Start the development environment**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

### Manual Setup (Development)

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
uvicorn main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🔧 Environment Variables

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/chatbot_db

# Session Configuration
SESSION_SECRET_KEY=your-session-secret-key-here
SESSION_EXPIRE_MINUTES=30

# AI/ML (if applicable)
OPENAI_API_KEY=your-openai-api-key
EMBEDDING_MODEL=text-embedding-ada-002

# File Upload
UPLOAD_DIR=uploaded_files
MAX_FILE_SIZE=10485760  # 10MB
```

## 📡 API Documentation

### Authentication Endpoints
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout

### Chat Endpoints
- `GET /api/chat/sessions` - Get user chat sessions
- `GET /api/chat/history/{session_id}` - Get chat history
- `POST /api/chat` - Send message to chatbot
- `DELETE /api/chat/sessions/{session_id}` - Delete chat session

### File Upload
- `POST /api/upload` - Upload document for processing

## 🎨 UI/UX Features

### Authentication Pages
- **Dark Theme Integration**: Matches the main chat application aesthetic
- **Real-time Validation**: Instant feedback on form inputs
- **Password Strength Indicator**: Visual feedback for password security
- **Error Handling**: Comprehensive error messages with toast notifications
- **Loading States**: Smooth transitions during authentication processes

### Chat Interface
- **Sidebar Navigation**: Collapsible sidebar with chat sessions
- **Message History**: Persistent chat history with timestamps
- **File Upload**: Drag-and-drop document upload
- **Responsive Design**: Optimized for all screen sizes
- **Keyboard Shortcuts**: Efficient navigation and interaction

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with modern web technologies for optimal performance
- AI capabilities powered by advanced language models
- Inspired by the latest trends in conversational AI interfaces

## 📞 Support

For questions or support, please open an issue in the GitHub repository.

---

**Happy chatting! 🤖✨**
