# Use multi-stage build
FROM node:22-slim AS builder

WORKDIR /app

# Copy package files
COPY package.json ./

# Install all dependencies including dev dependencies for building
RUN npm install

# Copy source files
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:22-slim

WORKDIR /app

# Copy package files
COPY package.json ./

# Install only production dependencies
RUN npm install --omit=dev

# Copy built files from builder stage
COPY --from=builder /app/dist ./dist

# Set environment variables
ENV PORT=8001
ENV SSE_LOCAL=true

# Expose the port
EXPOSE 8001

# Run the SSE server instead of the main index
CMD ["node", "dist/sse-server.js"]