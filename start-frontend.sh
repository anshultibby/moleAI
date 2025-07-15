#!/bin/bash

echo "Starting Shopping Deals Chat Agent Frontend..."

# Navigate to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the Next.js development server
echo "Starting Next.js server on http://localhost:3000"
npm run dev 