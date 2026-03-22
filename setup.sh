#!/bin/bash

# Navigate to project directory
cd /Users/duber.rodriguez/Desktop/clip-generator || exit

echo "Checking for ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg not found. Installing via Homebrew..."
    brew install ffmpeg
else
    echo "ffmpeg is already installed."
fi

echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete!"
