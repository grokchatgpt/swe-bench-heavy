lean# SWE-Bench Heavy: Installation Guide

## Prerequisites

### 1. Docker
**Required**: Docker Desktop or Docker Engine

#### macOS
```bash
# Install Docker Desktop
brew install --cask docker
# Or download from: https://www.docker.com/products/docker-desktop/
```

#### Linux (Ubuntu/Debian)
```bash
# Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (logout/login required)
sudo usermod -aG docker $USER
```

#### Windows
Download Docker Desktop from: https://www.docker.com/products/docker-desktop/

### 2. Python 3.8+
```bash
# Check Python version
python3 --version

# Install if needed (macOS)
brew install python3

# Install if needed (Ubuntu/Debian)
sudo apt update && sudo apt install python3 python3-pip
```

### 3. Git
```bash
# Check Git
git --version

# Install if needed (macOS)
brew install git

# Install if needed (Ubuntu/Debian)
sudo apt install git
```

## Installation

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd swe-bench-heavy
```

### 2. One-Step Setup
```bash
python3 setup.py
```

This automatically:
- ✅ Verifies Docker is working
- ✅ Downloads SWE-Bench Lite dataset (300 issues)
- ✅ Creates directory structure
- ✅ Cleans legacy files
- ✅ Configures Docker environment
- ✅ Creates default config.json

### 3. Verify Installation
```bash
# Check Docker images (should show SWE-Bench images)
docker images | grep swe-

# Test with a simple issue
python3 grading_docker.py sympy__sympy-11400
```

## System Requirements

### Minimum
- **CPU**: 2 cores
- **RAM**: 8GB
- **Disk**: 50GB free space
- **Network**: Stable internet for Docker pulls

### Recommended
- **CPU**: 4+ cores
- **RAM**: 16GB+
- **Disk**: 100GB+ SSD
- **Network**: Fast internet (Docker images are large)

## Docker Storage

### Expected Usage
- **Base images**: ~20GB (12 repositories)
- **Build cache**: ~10GB
- **Test results**: ~1GB
- **Total**: ~30-40GB

### Cleanup Commands
```bash
# Remove unused containers
docker container prune -f

# Remove unused images
docker image prune -f

# Remove everything (nuclear option)
docker system prune -a -f
```

## Troubleshooting

### Docker Permission Issues (Linux)
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again, then test
docker run hello-world
```

### Docker Desktop Not Starting (macOS/Windows)
1. Restart Docker Desktop
2. Check system resources (RAM/disk)
3. Reset Docker Desktop to factory defaults

### Network Issues
```bash
# Test Docker Hub connectivity
docker pull hello-world

# Check DNS resolution
nslookup registry-1.docker.io
```

### Disk Space Issues
```bash
# Check Docker disk usage
docker system df

# Clean up aggressively
docker system prune -a -f --volumes
```

### Python Issues
```bash
# Install required packages
pip3 install requests

# Check Python path
which python3
```

## Performance Tuning

### Docker Settings
- **Memory**: Allocate 8GB+ to Docker
- **CPU**: Use all available cores
- **Disk**: Use SSD if possible

### Build Optimization
```bash
# Parallel builds (if supported)
export DOCKER_BUILDKIT=1

# Use build cache
docker builder prune --keep-storage 10GB
```

## Security Notes

### Docker Security
- Images are pulled from official SWE-Bench registry
- Containers run in isolated environments
- No privileged access required

### Network Security
- Only outbound connections needed
- No incoming ports opened
- Safe for corporate networks

## Getting Help

### Common Issues
1. **"Docker not found"** → Install Docker and restart terminal
2. **"Permission denied"** → Add user to docker group (Linux)
3. **"No space left"** → Clean Docker cache or add disk space
4. **"Build failed"** → Check network and try again

### Debug Commands
```bash
# Check Docker status
docker info

# Check system resources
df -h
free -h

# Check network
ping google.com
```

### Support
- Check `instructions.md` for usage
- Review Docker logs: `docker logs <container_id>`
- File issues with full error output
