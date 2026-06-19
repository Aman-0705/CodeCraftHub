# CodeCraftHub

A personalized learning management platform that helps developers track, manage, and monitor their learning journey.

## Overview

CodeCraftHub is a full-stack web application that enables users to manage courses they want to learn, monitor progress, and maintain a structured learning roadmap.

The project demonstrates REST API development using Flask and frontend integration using HTML, CSS, and JavaScript.

## Features

* Add new courses
* View all courses
* Update existing courses
* Delete courses
* Track learning status
* Set target completion dates
* Responsive user interface
* RESTful API architecture
* JSON-based data persistence

## Course Attributes

Each course includes:

* Course Name
* Description
* Target Completion Date
* Status

  * Not Started
  * In Progress
  * Completed
* Created Timestamp

## Tech Stack

### Frontend

* HTML5
* CSS3
* JavaScript

### Backend

* Python
* Flask

### Data Storage

* JSON File Storage

## REST API Endpoints

### Get All Courses

GET /api/courses

### Get Specific Course

GET /api/courses?id=<course_id>

### Create Course

POST /api/courses

### Update Course

PUT /api/courses/

Request Body:

{
"id": 1,
"name": "Updated Course",
"description": "Updated Description",
"target_date": "2026-12-31",
"status": "Completed"
}

### Delete Course

DELETE /api/courses/

Request Body:

{
"id": 1
}

### Course Statistics

GET /api/courses/stats

## Project Structure

CodeCraftHub/

├── app.py

├── courses.json

├── courses.html

└── README.md

## Installation

### Clone Repository

git clone <repository-url>

### Navigate to Project

cd CodeCraftHub

### Install Dependencies

pip install flask

### Run Application

python app.py

### Open Frontend

Open courses.html in your browser.

## Future Enhancements

* User Authentication
* Database Integration
* Cloud Deployment
* Course Categories
* Progress Analytics Dashboard
* Learning Recommendations
* Mobile Responsive Enhancements

## Learning Outcomes

This project demonstrates:

* REST API Development
* CRUD Operations
* JSON Data Handling
* Frontend-Backend Integration
* Flask Application Development
* Error Handling
* Client-Side Validation

## Author

Aman Sharma

2025 Computer Science Graduate

