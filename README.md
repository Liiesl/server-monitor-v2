# Node.js Server Manager

A PySide6 application for managing Node.js servers with system tray support. The application can run in the background without keeping the GUI window open.

## Features

- **Server Management**: Add, edit, and remove Node.js server configurations
- **Process Control**: Start, stop, and restart Node.js servers
- **System Tray**: Run in the background with system tray icon
- **Status Monitoring**: Real-time status updates for all servers
- **Persistent Storage**: Server configurations are saved to `servers.json`

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. **Adding a Server**:
   - Click "Add Server"
   - Enter server name, path to your Node.js application, command (default: `node`), optional arguments, and optional port
   - Click OK

3. **Managing Servers**:
   - Select a server from the table
   - Use Start, Stop, or Restart buttons to control the server
   - Edit or Remove servers as needed

4. **Background Mode**:
   - Close the window to minimize to system tray
   - Right-click the tray icon to show/hide window or quit
   - Double-click the tray icon to toggle window visibility

## Server Configuration

- **Server Name**: Unique identifier for the server
- **Server Path**: Path to your Node.js application file (e.g., `app.js`, `server.js`) or directory
- **Command**: Command to run (e.g., `node`, `npm`, `yarn`)
- **Arguments**: Additional arguments (e.g., `start`, `run dev`, `--port 3000`)
- **Port**: Optional port number (for reference only)

## Example Configurations

### Basic Node.js Server
- Name: `My API Server`
- Path: `C:\projects\my-api\server.js`
- Command: `node`
- Arguments: (empty)
- Port: `3000`

### npm Script
- Name: `Development Server`
- Path: `C:\projects\my-app`
- Command: `npm`
- Arguments: `run dev`
- Port: `8080`

### Yarn Script
- Name: `Production Server`
- Path: `C:\projects\my-app`
- Command: `yarn`
- Arguments: `start`
- Port: `3000`

## Files

- `main.py`: Main application with GUI and system tray
- `server_manager.py`: Server process management logic
- `servers.json`: Persistent storage for server configurations (auto-generated)

## Notes

- The application will continue running in the system tray even when the window is closed
- All running servers will be stopped when you quit the application
- Server status is automatically updated every 2 seconds
- Make sure Node.js is installed and accessible in your system PATH

