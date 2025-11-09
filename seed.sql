CREATE DATABASE IF NOT EXISTS solapur_digital_hub;
USE solapur_digital_hub;

CREATE TABLE IF NOT EXISTS students (
  student_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  dob DATE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin (
  admin_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
  q_id INT AUTO_INCREMENT PRIMARY KEY,
  question TEXT NOT NULL,
  option1 TEXT NOT NULL,
  option2 TEXT NOT NULL,
  option3 TEXT,
  option4 TEXT,
  correct_ans VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS results (
  result_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  score INT NOT NULL,
  total INT NOT NULL,
  taken_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

-- Admin account (username: admin, password: admin123) stored hashed
INSERT INTO admin (username, password) VALUES ('admin', 'scrypt:32768:8:1$KH0ThVpyjg7I95Ub$5cc5575b26cd98a03eee6cbefb76aa0eaf0b2d3e81c651efaeb17bf171d7a03766d6c8952776431f75693e927e5ba5814911c1d605e70dfd8c17eb18a1a02ef7');

INSERT INTO questions (question, option1, option2, option3, option4, correct_ans) VALUES
('What is the capital of Maharashtra?', 'Pune', 'Mumbai', 'Nagpur', 'Nashik', 'Mumbai'),
('Which language is primarily used for web backend in this project?', 'C++', 'Python', 'Java', 'Ruby', 'Python'),
('HTML stands for?', 'HyperText Markup Language', 'Home Tool Markup Language', 'Hyperlink Markup Language', 'HyperText Makeup Language', 'HyperText Markup Language');
