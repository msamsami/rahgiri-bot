# Rahgiri Bot

![](https://img.shields.io/badge/release-v0.5.2-blue)
![](https://img.shields.io/badge/python-3.11-green)


## Introduction
Rahgiri Bot is a Telegram bot that helps users track their parcels through the Iran Post Tracking System. It provides an easy-to-use interface for checking the status of postal packages and keeping track of multiple parcels.

### Features
- 📦 Track parcels using tracking numbers
- 🔄 Real-time status updates
- 📄 View tracking results in text or as image
- 📝 Save and manage multiple tracking numbers (coming soon)
- 🔔 Automatic status notifications (coming soon)

## Deployment
You can easily deploy the Rahgiri Bot using Docker. Follow the steps below to get started:

### Prerequisites
Make sure you have Docker installed on your machine. You can download it from [Docker's official website](https://www.docker.com/get-started).

### Environment Variables
Create a _.env_ file in the project root and add the necessary environment variables.
```bash
cp .env.example .env
vim .env
```

### Build the Docker Image
Build the Docker image using the following command:
```bash
docker build -t rahgiri-bot .
```

### Run the Docker Container
After building the image, you can run the container with the following command:
```bash
docker run -d -it --name rahgiri-telegram-bot --network host rahgiri-bot
```

### Accessing the Bot
Once the container is running, you can interact with the bot on Telegram using the bot token you provided.

## Acknowledgments
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - The Python wrapper for Telegram's Bot API
- [Iran Post Tracking](https://tracking.post.ir/) - For providing the tracking service

## Support
💡 If you encounter any problems or have suggestions, please [open an issue](https://github.com/msamsami/rahgiri-bot/issues).

⭐ Don't forget to star the repository if you find it useful!

---

Made with ❤️ for the Iranian community
