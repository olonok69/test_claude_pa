FROM node:20-slim

# Set working directory
WORKDIR /app

# Copy package.json
COPY package.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8004

# Start the application
CMD ["node", "main.js"]