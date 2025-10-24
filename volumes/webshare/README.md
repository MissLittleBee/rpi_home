# Webshare.cz Search Application

A Python Flask web application that provides a user-friendly interface to search and download files from webshare.cz.

## Features

- 🔐 Automatic login using environment variables
- 🔍 Search for files using keywords
- 📋 View detailed file information (size, downloads, rating)
- ⬇️ Direct download links for selected files
- 📱 Responsive web interface
- 🐳 Docker containerized

## Configuration

### Set up Webshare.cz Credentials

Edit the `.env` file in the project rooplext directory and set your credentials:

```bash
WEBSHARE_USERNAME=your_username_here
WEBSHARE_PASSWORD=your_password_here
```

### Access the Application

Once the Docker container is running, access the application at:
- **Local:** http://localhost:5000
- **Network:** http://ha.local:5000 (or your server IP)

### How to Use

1. **Automatic Login**: Credentials are loaded from environment variables
2. **Search**: Type your search query and click "Search"
3. **Download**: Click the "Download" button next to any file to download it to `/home/jeyjey/videos`
4. **View Downloads**: Check the "Downloaded Files" section to see completed downloads

### File Information Display

For each search result, you'll see:
- File name and size
- File type
- Download count
- User rating
- Upload date

## Development

### Local Development

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

3. Access at http://localhost:5000

### Docker Build

The application is automatically built when you run docker-compose:

```bash
docker-compose up --build webshare-search
```

## Environment Variables

- `WEBSHARE_USERNAME`: Your webshare.cz username or email
- `WEBSHARE_PASSWORD`: Your webshare.cz password
- `DOWNLOAD_PATH`: Path where files are downloaded (default: /downloads, mapped to /home/jeyjey/videos)
- `PORT`: Server port (default: 5000)
- `DEBUG`: Enable debug mode (default: false)
- `SECRET_KEY`: Flask secret key for sessions

## Security Notes

- Your webshare.cz credentials are stored as environment variables
- Credentials are only used for API authentication
- All communication with webshare.cz uses HTTPS
- The application runs as a non-root user in the container
- Make sure to keep your `.env` file secure and don't commit it to version control

## Troubleshooting

### Login Issues
- Verify your webshare.cz credentials
- Check if webshare.cz is accessible from your network
- Look at the browser console for error messages

### Search Issues
- Make sure you're logged in first
- Try different search terms
- Check the network connection

### Docker Issues
- Check if port 5000 is available
- Review container logs: `docker-compose logs webshare-search`
- Ensure the build completed successfully

## API Endpoints

- `GET /`: Main application interface
- `POST /api/login`: Login to webshare.cz
- `POST /api/search`: Search for files
- `POST /api/download`: Get download links
- `GET /health`: Health check endpoint