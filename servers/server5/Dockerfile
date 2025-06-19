FROM node:20-slim

# Set working directory
WORKDIR /app

# Copy package files first (for better Docker layer caching)
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code (excluding node_modules)
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8004

# Start the application
CMD ["node", "main.js"]