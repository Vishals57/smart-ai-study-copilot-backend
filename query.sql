CREATE DATABASE IF NOT EXISTS study_copilot;
USE study_copilot;

-- 1. Users Table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Study Plans Table
CREATE TABLE study_plans (
    plan_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    goal_title VARCHAR(255) NOT NULL,
    duration_days INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 3. Daily Tasks Table
CREATE TABLE tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    plan_id INT,
    day_number INT NOT NULL,
    task_description TEXT NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (plan_id) REFERENCES study_plans(plan_id) ON DELETE CASCADE
);

-- 4. Initial Test User
INSERT INTO users (name, email) VALUES ('Vishal Shinde', 'vishal@example.com');