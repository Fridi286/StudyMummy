FROM node:22-alpine

WORKDIR /app

# Install dependencies first for caching
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

# Copy the rest of the application
COPY . .

# Expose the Angular dev server port
EXPOSE 4200

# Start the Angular dev server (binding to 0.0.0.0 so it's accessible outside the container)
CMD ["npm", "start", "--", "--host", "0.0.0.0"]
