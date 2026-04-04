# 🐳 Docker Compose Setup Guide

This project uses Docker Compose to run all services (backend, database, etc.) in a containerized environment.

---

## 📋 Prerequisites

Make sure you have installed:

* Docker
* Docker Compose

Check installation:

```bash
docker --version
docker compose version
```

---

## 📁 Project Structure

```
project-root/
│── docker-compose.yml
│── Dockerfile
│── .env
│── app/
```

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory:

```
DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=db
DB_PORT=5432
```

---

## 🏗️ Build and Run Containers

To build and start all services:

```bash
docker compose build
docker compose up -d
```

To run in background:

```bash
docker compose up --build -d
```

---

## 🛑 Stop Containers

```bash
docker compose down
```

---



---

## 📊 View Running Containers

```bash
docker ps
```

---

## 🧹 Clean Up (Remove Containers)

```bash
docker compose down
```

---

## 🐛 Common Issues

### Permission Denied (Docker)

Make sure your user is added to docker group:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

### Port Already in Use

Check running services:

```bash
sudo lsof -i :8000
```

---

## 🚀 Access Application

Once running:

* Backend: http://localhost:8000
* Database: localhost:5432

---

## 📌 Notes

* Use `.env` for sensitive configs
* Do not commit secrets
* Always rebuild after dependency changes

---

## 💡 Useful Commands

```bash
# Run command inside container
docker compose exec -it app_name bash

# View logs
docker compose logs -f

# View app specific logs
docker logs -f app_name

# Restart service
docker compose restart
```

---

## 🎯 Summary

* `docker compose up --build` → Start everything
* `docker compose down` → Stop everything
* `docker compose logs` → Debug issues

---

Happy Coding 🚀
