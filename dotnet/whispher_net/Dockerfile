# Build stage
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /App

# Copy everything
COPY . ./
# Restore and build
RUN dotnet restore && \
    dotnet build -c Release -o /App/build

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /App

# Install FFmpeg and clean up
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy build output
COPY --from=build /App/build .

# Expose port
EXPOSE 8899

# Copy the Whisper model to a single location
COPY ggml-base.bin ./

ENTRYPOINT ["dotnet", "AudioUpload.dll"]