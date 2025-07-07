# Use multi-stage build
FROM node:22-slim AS builder

WORKDIR /app

# Copy package files
COPY package.json ./

# Install all dependencies including dev dependencies for building
# Use npm install instead of npm ci to handle lock file mismatches
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
# Use npm install with --omit=dev instead of npm ci
RUN npm install --omit=dev

# Copy built files from builder stage
COPY --from=builder /app/dist ./dist

# Set environment variables
ENV PORT=8001

# Expose the port
EXPOSE 8001

# Run the SSE server
CMD ["node", "dist/sse-server.js"]