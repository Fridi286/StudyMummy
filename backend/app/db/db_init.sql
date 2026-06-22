-- StudyMummy Database Schema Initialization

-- Enable extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    avatar_url VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    coins INT DEFAULT 0 CHECK (coins >= 0),
    experience INT DEFAULT 0 CHECK (experience >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Learning Profiles Table
CREATE TABLE IF NOT EXISTS learning_profiles (
    user_id VARCHAR(255) PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    sessions_count INT DEFAULT 0 CHECK (sessions_count >= 0),
    error_patterns JSONB DEFAULT '[]'::jsonb,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);



-- 5. Confidence Scores Table
CREATE TABLE IF NOT EXISTS confidence_scores (
    score_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    confidence NUMERIC(3, 2) NOT NULL DEFAULT 0.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, tag)
);

-- 6. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    document_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Tasks Table
CREATE TABLE IF NOT EXISTS tasks (
    task_id VARCHAR(255) PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    difficulty INT NOT NULL CHECK (difficulty >= 1 AND difficulty <= 5),
    task_text TEXT NOT NULL,
    key_concepts JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'open'
);

-- 8. Sessions Table
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    current_task_id VARCHAR(255) REFERENCES tasks(task_id) ON DELETE SET NULL,
    help_level INT NOT NULL DEFAULT 1 CHECK (help_level >= 1 AND help_level <= 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);

-- 9. Chat Logs Table
CREATE TABLE IF NOT EXISTS chat_logs (
    message_id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    action_taken VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. Quizzes Table
CREATE TABLE IF NOT EXISTS quizzes (
    quiz_id VARCHAR(255) PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- 11. Quiz Attempts Table
CREATE TABLE IF NOT EXISTS quiz_attempts (
    attempt_id VARCHAR(255) PRIMARY KEY,
    quiz_id VARCHAR(255) NOT NULL REFERENCES quizzes(quiz_id) ON DELETE CASCADE,
    score INT NOT NULL DEFAULT 0,
    total_questions INT NOT NULL,
    answers JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 12. Quiz Questions Table
CREATE TABLE IF NOT EXISTS quiz_questions (
    question_id VARCHAR(255) PRIMARY KEY,
    quiz_id VARCHAR(255) NOT NULL REFERENCES quizzes(quiz_id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    options JSONB NOT NULL DEFAULT '[]'::jsonb,
    correct_answer VARCHAR(255) NOT NULL,
    explanation TEXT,
    key_concepts JSONB DEFAULT '[]'::jsonb
);

-- 13. Cheatsheets Table
CREATE TABLE IF NOT EXISTS cheatsheets (
    cheatsheet_id VARCHAR(255) PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    key_concepts JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 13.5 Document Chunks Table (for pgvector RAG)
CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id VARCHAR(255) PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    embedding vector(1536),
    chunk_index INT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- 14. Friendships Table
CREATE TABLE IF NOT EXISTS friendships (
    friendship_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    friend_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, friend_id),
    CHECK (user_id != friend_id)
);

-- 15. Chatrooms Table
CREATE TABLE IF NOT EXISTS chatrooms (
    room_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    is_group BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 16. Chatroom Members Table
CREATE TABLE IF NOT EXISTS chatroom_members (
    room_id VARCHAR(255) NOT NULL REFERENCES chatrooms(room_id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (room_id, user_id)
);

-- 17. Chat Messages Table
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id VARCHAR(255) PRIMARY KEY,
    room_id VARCHAR(255) NOT NULL REFERENCES chatrooms(room_id) ON DELETE CASCADE,
    sender_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 18. Items Table
CREATE TABLE IF NOT EXISTS items (
    item_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,
    icon_url VARCHAR(255),
    effects JSONB,
    cost INT NOT NULL DEFAULT 0,
    is_buyable BOOLEAN DEFAULT TRUE NOT NULL
);

-- 19. Inventory Items Table
CREATE TABLE IF NOT EXISTS inventory_items (
    inventory_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    item_id VARCHAR(255) NOT NULL REFERENCES items(item_id) ON DELETE CASCADE,
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity >= 0),
    acquired_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, item_id)
);

-- 20. Active Items Table
CREATE TABLE IF NOT EXISTS active_items (
    active_item_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    item_id VARCHAR(255) NOT NULL REFERENCES items(item_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    effects JSONB NOT NULL,
    activated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- 21. Slot Machine Logs Table
CREATE TABLE IF NOT EXISTS slot_machine_logs (
    log_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    bet_amount INT NOT NULL,
    payout INT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 22. Trades Table
CREATE TABLE IF NOT EXISTS trades (
    trade_id VARCHAR(255) PRIMARY KEY,
    sender_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    receiver_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    sender_coins INT NOT NULL DEFAULT 0 CHECK (sender_coins >= 0),
    receiver_coins INT NOT NULL DEFAULT 0 CHECK (receiver_coins >= 0),
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CHECK (sender_id != receiver_id)
);

-- 23. Trade Items Table
CREATE TABLE IF NOT EXISTS trade_items (
    trade_item_id VARCHAR(255) PRIMARY KEY,
    trade_id VARCHAR(255) NOT NULL REFERENCES trades(trade_id) ON DELETE CASCADE,
    owner_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    item_id VARCHAR(255) NOT NULL REFERENCES items(item_id) ON DELETE CASCADE,
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0)
);
