FROM node:20-alpine

WORKDIR /app

# Install build dependencies
COPY package*.json ./
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps

# Copy source files
COPY . .

# Disable Next.js telemetry
ENV NEXT_TELEMETRY_DISABLED=1

# Build Next.js application
RUN npm run build

# Expose port
EXPOSE 3000

# Start Next.js server
CMD ["npm", "run", "start"]
