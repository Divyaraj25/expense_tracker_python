# Expense Tracker Application

A comprehensive web-based expense tracking application built with Python, Flask, and MongoDB. This application helps users manage their personal finances by tracking expenses, income, and budgets.

## Features

- User authentication (register, login, logout)
- Track expenses and income with categories
- Set and manage budgets
- Visualize spending with charts and reports
- Responsive design for desktop and mobile
- Secure password hashing
- JWT-based authentication
- RESTful API endpoints

## Tech Stack

- **Backend**: Python 3.8+
- **Web Framework**: Flask 2.0+
- **Database**: MongoDB
- **Authentication**: Flask-Login & JWT
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Caching**: Redis
- **Deployment**: Gunicorn

## Prerequisites

- Python 3.8 or higher
- MongoDB server
- Redis server (optional, for caching)
- pip (Python package manager)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/expense-tracker.git
   cd expense-tracker
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory with the following variables:
   ```
   SECRET_KEY=your-secret-key-here
   MONGODB_URI=mongodb://localhost:27017/expense_tracker
   REDIS_URL=redis://localhost:6379/0
   JWT_SECRET_KEY=your-jwt-secret-key
   ```

5. **Run the application**
   ```bash
   python run.py
   ```
   The application will be available at `http://localhost:5000`

## Project Structure

```
expense_tracker/
├── app/
│   ├── __init__.py
│   ├── models/         # Database models
│   ├── routes/         # Application routes
│   ├── static/         # Static files (CSS, JS, images)
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── templates/      # HTML templates
│       ├── auth/       # Authentication templates
│       ├── errors/     # Error pages
│       └── ...
├── config.py           # Configuration settings
├── requirements.txt    # Project dependencies
└── run.py             # Application entry point
```

## API Documentation

The application provides a RESTful API for programmatic access. See the [API Documentation](API_DOCS.md) for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/)
- [MongoDB](https://www.mongodb.com/)
- [Bootstrap](https://getbootstrap.com/)
- [Chart.js](https://www.chartjs.org/)
