# Server Monitor v2

A modern PySide6 application for managing and monitoring Node.js servers with real-time metrics, performance graphs, and system tray support. The application provides a comprehensive dashboard for tracking server status, CPU usage, memory consumption, and logs.

## Features

- **Server Management**: Add, edit, and remove Node.js server configurations
- **Process Control**: Start, stop, and restart Node.js servers with a single click
- **Real-time Monitoring**: Track CPU usage and RAM consumption in real-time
- **Performance Graphs**: Visualize server performance metrics over time with interactive charts
- **Log Viewer**: View server logs with syntax highlighting and error detection
- **Dashboard**: Overview of all servers with summary statistics
- **System Tray**: Run in the background with system tray icon support
- **Data Persistence**: Automatic saving of logs and metrics for historical analysis
- **Modern UI**: Clean, responsive interface built with PySide6

## Screenshots

*Add screenshots here if available*

## Installation

### Prerequisites

- Python 3.8 or higher
- Node.js (for running the servers you want to monitor)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd server-monitor-v2
   ```

2. Install dependencies:
   ```bash
   pip install PySide6 psutil
   ```

   Or create a `requirements.txt` file:
   ```
   PySide6>=6.0.0
   psutil>=5.9.0
   ```

   Then install:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Application

Run the application:
```bash
python main.py
```

### Adding a Server

1. Click "Add Server" button
2. Fill in the server configuration:
   - **Server Name**: Unique identifier for the server
   - **Server Path**: Path to your Node.js application file (e.g., `app.js`, `server.js`) or directory
   - **Command**: Command to run (e.g., `node`, `npm`, `yarn`)
   - **Arguments**: Additional arguments (e.g., `start`, `run dev`, `--port 3000`)
   - **Port**: Optional port number (for reference only)
3. Click OK to save

### Managing Servers

- **Dashboard View**: See overview of all servers with total, running, and stopped counts
- **Server Detail View**: Click on a server to view detailed information, metrics, and logs
- **Start/Stop/Restart**: Use the control buttons to manage server processes
- **Edit/Remove**: Right-click on a server to edit or remove it

### Monitoring Features

- **Real-time Metrics**: CPU and RAM usage are updated every second
- **Performance Graphs**: View historical performance data with interactive charts
- **Log Viewer**: Monitor server output with automatic error highlighting
- **Status Updates**: Server status is automatically updated every second

### Background Mode

- Close the window to minimize to system tray
- Right-click the tray icon to show/hide window or quit
- Double-click the tray icon to toggle window visibility
- The application continues monitoring servers in the background

## Server Configuration Examples

### Basic Node.js Server
- **Name**: `My API Server`
- **Path**: `C:\projects\my-api\server.js`
- **Command**: `node`
- **Arguments**: (empty)
- **Port**: `3000`

### npm Script
- **Name**: `Development Server`
- **Path**: `C:\projects\my-app`
- **Command**: `npm`
- **Arguments**: `run dev`
- **Port**: `8080`

### Yarn Script
- **Name**: `Production Server`
- **Path**: `C:\projects\my-app`
- **Command**: `yarn`
- **Arguments**: `start`
- **Port**: `3000`

## Project Structure

```
server-monitor-v2/
├── main.py                 # Main application entry point
├── server_manager.py       # Server process management logic
├── log_persistence.py      # Log data persistence handler
├── metrics_persistence.py  # Metrics data persistence handler
├── servers.json            # Server configurations (auto-generated)
├── ui/
│   ├── dashboard.py        # Dashboard view component
│   ├── server_detail.py    # Server detail view component
│   ├── sidebar.py          # Sidebar navigation component
│   ├── server_dialog.py    # Add/Edit server dialog
│   ├── metrics_monitor.py  # Background metrics monitoring thread
│   ├── log_reader.py       # Log reading and processing
│   ├── performance_graph.py # Performance graph visualization
│   ├── styles.py           # UI styling definitions
│   └── constants.py        # UI constants
├── logs/                   # Server log files (auto-generated)
└── metrics/                # Server metrics data (auto-generated)
```

## Data Persistence

The application automatically saves:
- **Logs**: Server output is saved to `logs/<server-name>.log`
- **Metrics**: Performance metrics are saved to `metrics/<server-name>.json`
- **Configurations**: Server settings are saved to `servers.json`

All data is persisted across application restarts.

## Notes

- The application will continue running in the system tray even when the window is closed
- All running servers will be stopped when you quit the application
- Server status is automatically updated every second
- Metrics are recorded every second for graph visualization
- Make sure Node.js is installed and accessible in your system PATH
- Logs and metrics are automatically cleaned up to prevent excessive disk usage

## Requirements

- Python 3.8+
- PySide6 (Qt for Python)
- psutil (for system metrics)

## License

*Add your license here*

## Contributing

*Add contribution guidelines here*

## Author

*Add your name/contact information here*
