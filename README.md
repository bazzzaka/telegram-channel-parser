# Telegram Channel Parser

A comprehensive application for parsing Telegram channels to extract location data and dangerous information from messages. 
The system is specifically designed to handle Ukrainian text and generate map links for identified locations.

## Features

- Connect to Telegram channels using a user account (with bot fallback)
- Parse messages to identify locations and dangerous information in Ukrainian
- Generate map redirect URLs for identified locations (Google Maps, OpenStreetMap, Apple Maps)
- Store processed data in a PostgreSQL database
- RESTful API for accessing parsed data
- Dockerized for easy deployment

## Technologies Used

- Python 3.11
- FastAPI
- SQLAlchemy (async)
- Telethon / Pyrogram (Telegram API)
- PostgreSQL
- Docker & Docker Compose
- Poetry for dependency management

## Project Structure

```
/
├── src/
│   ├── api/              # API endpoints
│   ├── database/         # Database models and connection
│   ├── location/         # Location extraction and map services
│   ├── telegram/         # Telegram client and message handling
│   ├── config.py         # Application configuration
│   └── main.py           # Application entry point
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── poetry.lock
├── .env.example
└── README.md
```

## Setup and Installation

### Prerequisites

- Docker and Docker Compose
- Telegram API credentials (API ID and API Hash)
- (Optional) Telegram Bot token (fallback method)

### Configuration

1. Copy the example environment file and edit it with your settings:

```bash
cp .env.example .env
```

2. Edit `.env` file with your Telegram API credentials and other settings.

### Building and Running

Using the provided Makefile:

```bash
# Setup project locally (if developing without Docker)
make setup

# Build Docker containers
make build

# Run the application in Docker
make run

# View logs
make logs

# Stop the application
make stop

# Clean up Docker resources
make clean
```

## Using the Application

### Telegram Authentication

The application attempts to connect using a user account first:

1. You'll need to provide your Telegram API ID, API Hash, and phone number in the .env file
2. On first run, you may need to enter the verification code sent to your Telegram account
3. If user authentication fails, the application will fall back to bot mode (requires a bot token)

### Monitoring Channels

Specify the channels to monitor in the .env file:

```
TG_CHANNELS=channel1,channel2,channel3
```

You can use channel usernames or IDs.

### API Endpoints

The application exposes several API endpoints for accessing the parsed data:

- `/api/channels` - List all monitored channels
- `/api/messages` - Get messages with optional filtering
- `/api/locations` - Get extracted locations
- `/api/danger-info` - Get extracted danger information
- `/api/stats` - Get statistics about parsed data

## Security Considerations

- The application stores Telegram session data for authentication
- Sensitive information is stored in the .env file, which should be kept secure
- API endpoints do not implement authentication by default (add as needed)

## License

This project is licensed under the MIT License - see the LICENSE file for details.