FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies (including dev dependencies for development)
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3005

# Command to run the application
CMD ["npm", "run", "dev", "--", "--port", "3005"] 